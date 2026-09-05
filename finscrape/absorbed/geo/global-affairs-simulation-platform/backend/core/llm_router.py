"""
LLM调用统一路由，所有Claude API调用都走这里，别写死在业务代码里
"""
import asyncio
import json
import logging
import random
import re
import time
import uuid
from typing import Any, Optional
from backend.core.config import settings

logger = logging.getLogger("llm_router")
_client_cache: dict = {}

# 区分"没传fallback"和"传了None当fallback"的哨兵
_UNSET = object()


# --- 任务配置 ---
TASK_CONFIGS = {
    "cluster_summarization": {
        "max_tokens": 4000,
        "temperature_hint": "analytical",
        "cache": True,
        "retry_times": 0,   # 每批60s超时不重试，4批最坏240s
    },
    "event_abstraction": {
        "max_tokens": 2000,
        "temperature_hint": "precise",
        "cache": True,
        "retry_times": 0,
    },
    "theory_analysis": {
        "max_tokens": 3000,          # 1500不够，9字段中文要2000-2800
        "temperature_hint": "scholarly",
        "cache": True,
        "retry_times": 0,
    },
    "scenario_generation": {
        "max_tokens": 5000,
        "temperature_hint": "creative_constrained",
        "cache": False,
        "retry_times": 0,
    },
    "branch_regeneration": {
        "max_tokens": 4000,
        "temperature_hint": "analytical",
        "cache": False,
    },
    "prediction_review": {
        "max_tokens": 3000,
        "temperature_hint": "critical",
        "cache": False,
    },
    "actor_profile_generation": {
        "max_tokens": 2500,
        "temperature_hint": "precise",
        "cache": True,
        "retry_times": 0,
    },
    "trigger_extraction": {
        "max_tokens": 3000,
        "temperature_hint": "analytical",
        "cache": True,
        "retry_times": 0,
    },
    "constraint_extraction": {          # 独立task，不复用trigger
        "max_tokens": 3000,
        "temperature_hint": "analytical",
        "cache": True,
        "retry_times": 0,
    },
    "anti_template_check": {
        "max_tokens": 1000,
        "temperature_hint": "critical",
        "cache": False,
        "retry_times": 0,
    },
    "analogy_matching": {
        "max_tokens": 4000,
        "temperature_hint": "scholarly",
        "cache": True,
    },
}


def get_client(timeout_seconds: int = 300):
    """获取Anthropic客户端，按超时参数缓存复用连接池"""
    import anthropic
    import httpx
    _key = timeout_seconds
    if _key in _client_cache:
        return _client_cache[_key]
    http_timeout = httpx.Timeout(
        connect=10.0,
        read=float(timeout_seconds),
        write=30.0,
        pool=10.0,
    )
    client = anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        base_url=settings.ANTHROPIC_BASE_URL,
        timeout=http_timeout,
    )
    _client_cache[_key] = client
    return client


def llm_call(
    task_type: str,
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    extra_config: Optional[dict] = None,
    retry_times: int = 1,
    timeout_seconds: int = 300,
    trace_id: Optional[str] = None,
) -> str:
    """统一LLM调用入口，带trace日志"""
    config = TASK_CONFIGS.get(task_type, {"max_tokens": 2000, "cache": True})
    if extra_config:
        config = {**config, **extra_config}

    model = model or settings.CLAUDE_MODEL
    use_cache = config.get("cache", True)
    effective_retry = config.get("retry_times", retry_times)
    trace_id = trace_id or str(uuid.uuid4())[:8]

    system = [
        {
            "type": "text",
            "text": system_prompt,
            **({} if not use_cache else {"cache_control": {"type": "ephemeral"}}),
        }
    ]

    start_time = time.time()
    last_error = None
    error_type = "none"

    for attempt in range(effective_retry + 1):
        try:
            client = get_client(timeout_seconds=timeout_seconds)
            response = client.messages.create(
                model=model,
                max_tokens=config.get("max_tokens", 2000),
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            # Claude返回空content时别IndexError，转成可识别的ValueError
            if not response.content:
                raise ValueError(
                    f"Claude returned empty content list "
                    f"(stop_reason={response.stop_reason}, "
                    f"usage={response.usage})"
                )
            text = response.content[0].text
            latency = round(time.time() - start_time, 2)

            logger.info(
                f"[llm] ✓ trace={trace_id} task={task_type} model={model} "
                f"latency={latency}s input_len={len(user_message)} output_len={len(text)}"
            )
            return text

        except Exception as e:
            last_error = e
            error_type = _classify_error(e)
            latency = round(time.time() - start_time, 2)

            if attempt < effective_retry:
                wait = min(2 ** attempt + random.uniform(0, 1), 60)
                logger.warning(
                    f"[llm] ✗ trace={trace_id} task={task_type} error_type={error_type} "
                    f"attempt={attempt+1}/{effective_retry+1} latency={latency}s "
                    f"error={type(e).__name__}: {str(e)[:100]} → 等待{wait:.1f}s重试"
                )
                time.sleep(wait)
            else:
                logger.error(
                    f"[llm] ✗✗ trace={trace_id} task={task_type} error_type={error_type} "
                    f"FINAL_FAILURE attempts={effective_retry+1} latency={latency}s "
                    f"error={type(e).__name__}: {str(e)[:200]}"
                )

    raise RuntimeError(
        f"LLM call failed [{error_type}] after {effective_retry+1} attempts "
        f"(task={task_type}, trace={trace_id}): {last_error}"
    ) from last_error


async def async_llm_call(
    task_type: str,
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    extra_config: Optional[dict] = None,
    retry_times: int = 1,
    timeout_seconds: int = 300,
    trace_id: Optional[str] = None,
) -> str:
    """异步LLM调用入口，不阻塞事件循环"""
    return await asyncio.to_thread(
        llm_call, task_type, system_prompt, user_message, model,
        extra_config, retry_times, timeout_seconds, trace_id
    )


async def async_llm_call_json(
    task_type: str,
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    fallback_value: Any = _UNSET,
    timeout_seconds: int = 300,
    trace_id: Optional[str] = None,
) -> Any:
    """异步JSON LLM调用入口，不阻塞事件循环"""
    return await asyncio.to_thread(
        llm_call_json, task_type, system_prompt, user_message, model,
        fallback_value, timeout_seconds, trace_id
    )


def llm_call_json(
    task_type: str,
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    fallback_value: Any = _UNSET,
    timeout_seconds: int = 300,
    trace_id: Optional[str] = None,
) -> Any:
    """
    期望JSON返回的调用入口，失败分四类：request_failed / empty_response / parse_failed / fallback_used
    没传fallback就返回结构化错误，传了就返回fallback并打日志
    """
    trace_id = trace_id or str(uuid.uuid4())[:8]
    start_time = time.time()

    # --- 调用LLM ---
    try:
        raw = llm_call(task_type, system_prompt, user_message, model,
                       timeout_seconds=timeout_seconds, trace_id=trace_id)
    except Exception as e:
        error_type = _classify_error(e)
        latency = round(time.time() - start_time, 2)
        logger.error(
            f"[llm_json] FALLBACK trace={trace_id} task={task_type} "
            f"error_type={error_type} latency={latency}s reason=request_failed"
        )
        return _handle_failure(task_type, trace_id, "request_failed", str(e), fallback_value)

    # --- 检查空响应 ---
    if not raw or not raw.strip():
        logger.error(
            f"[llm_json] FALLBACK trace={trace_id} task={task_type} reason=empty_response"
        )
        return _handle_failure(task_type, trace_id, "empty_response", "LLM returned empty string", fallback_value)

    # --- 解析JSON ---
    try:
        parsed = _parse_json(raw)
        latency = round(time.time() - start_time, 2)
        logger.info(
            f"[llm_json] ✓ trace={trace_id} task={task_type} "
            f"latency={latency}s parse=ok keys={list(parsed.keys()) if isinstance(parsed, dict) else 'list'}"
        )
        return parsed
    except Exception as parse_err:
        latency = round(time.time() - start_time, 2)
        logger.error(
            f"[llm_json] FALLBACK trace={trace_id} task={task_type} "
            f"reason=parse_failed latency={latency}s "
            f"raw_preview={raw[:200].replace(chr(10),' ')} "
            f"parse_error={parse_err}"
        )
        return _handle_failure(task_type, trace_id, "parse_failed", str(parse_err), fallback_value)


def _handle_failure(
    task_type: str,
    trace_id: str,
    error_type: str,
    error_msg: str,
    fallback_value: Any,
) -> Any:
    """统一失败处理，始终记日志不静默，有fallback就打标记返回"""
    if fallback_value is not _UNSET:
        # fallback上打标记，下游能检测到
        if isinstance(fallback_value, dict):
            fallback_value = {
                **fallback_value,
                "_fallback_used": True,
                "_fallback_reason": error_type,
                "_trace_id": trace_id,
                "_task_type": task_type,
            }
        logger.warning(
            f"[llm_json] ⚠ FALLBACK_USED trace={trace_id} task={task_type} "
            f"error_type={error_type} fallback_type={type(fallback_value).__name__}"
        )
        return fallback_value

    return {
        "parse_error": True,
        "error_type": error_type,
        "error": error_msg,
        "trace_id": trace_id,
        "task_type": task_type,
        "_fallback_used": True,
    }


def _classify_error(e: Exception) -> str:
    """异常分类成可读的错误类型"""
    name = type(e).__name__
    msg = str(e).lower()
    if "timeout" in name.lower() or "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "connect" in name.lower() or "connection" in msg:
        return "connection_error"
    if "rate" in msg and "limit" in msg:
        return "rate_limit"
    if "auth" in msg or "api_key" in msg or "unauthorized" in msg:
        return "auth_error"
    if "overloaded" in msg or "529" in msg:
        return "server_overloaded"
    return f"unknown_{name}"


def _parse_json(raw: str) -> Any:
    """
    从Claude返回里提取JSON，修不好就抛异常
    先直接解析，再修复常见问题，最后兜底截断恢复
    """
    # --- 候选文本 ---
    candidates: list[str] = []

    # json代码块
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if m:
        candidates.append(m.group(1).strip())

    # 整串或找{...}
    stripped = raw.strip()
    if stripped.startswith(("{", "[")):
        candidates.append(stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(stripped[start:end + 1])

    # --- 直接试 ---
    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            pass

    # --- 修复后试 ---
    for c in candidates:
        try:
            return json.loads(_repair_json(c))
        except (json.JSONDecodeError, Exception):
            pass

    # --- 兜底：截断恢复 ---
    for c in candidates:
        recovered = _recover_truncated_json(c)
        if recovered is not None:
            logger.warning("[llm_json] JSON 被截断，已恢复部分字段")
            return recovered

    raise ValueError(f"无法从响应中提取 JSON (前200字符): {raw[:200]}")


def _repair_json(text: str) -> str:
    """修复常见JSON问题：嵌入式引号、尾随逗号、控制字符"""
    # 去非法控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Claude在中文字符串值里插ASCII引号的问题
    text = _fix_embedded_quotes(text)
    # 尾随逗号
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # 补全未关闭的括号
    text = _close_open_brackets(text)
    return text


def _fix_embedded_quotes(text: str) -> str:
    """修Claude在JSON字符串值里嵌入未转义引号的问题，看后面跟的是不是: , } ]来判断"""
    result: list[str] = []
    in_string = False
    escape_next = False
    i = 0
    while i < len(text):
        ch = text[i]
        if escape_next:
            result.append(ch)
            escape_next = False
            i += 1
            continue
        if ch == '\\' and in_string:
            result.append(ch)
            escape_next = True
            i += 1
            continue
        if ch == '"':
            if in_string:
                # 向前看，判断是不是合法关闭引号
                j = i + 1
                while j < len(text) and text[j] in ' \t\n\r':
                    j += 1
                next_ch = text[j] if j < len(text) else ''
                if next_ch in (':', ',', '}', ']', ''):
                    # 合法关闭引号
                    result.append(ch)
                    in_string = False
                else:
                    # 嵌入式引号，转义
                    result.append('\\"')
            else:
                result.append(ch)
                in_string = True
            i += 1
            continue
        result.append(ch)
        i += 1
    return ''.join(result)


def _close_open_brackets(text: str) -> str:
    """补全未关闭的{ [，处理token截断导致的不完整JSON"""
    stack: list[str] = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            stack.append('}' if ch == '{' else ']')
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()
    # 字符串中途截断就先关字符串
    if in_string:
        text += '"'
    # 去尾随逗号再关括号
    text = re.sub(r',\s*$', '', text.rstrip())
    # 依次关括号
    for closer in reversed(stack):
        text += closer
    return text


def _recover_truncated_json(text: str) -> Any | None:
    """JSON被token截断时，截到最后一个完整字段再补括号"""
    text = text.strip()
    if not text.startswith('{'):
        return None

    depth = 0
    in_string = False
    escape_next = False
    last_comma_pos = -1   # 顶层最后一个逗号位置

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            depth += 1
        elif ch in ('}', ']'):
            depth -= 1
            if depth == 0:
                # 整个JSON找到结束符了，直接试
                try:
                    return json.loads(text[:i + 1])
                except json.JSONDecodeError:
                    pass
        elif ch == ',' and depth == 1:
            last_comma_pos = i   # 记顶层字段分隔符

    if last_comma_pos < 1:
        return None

    # 截到最后一个顶层逗号前，补全未关闭的{ [
    partial = text[:last_comma_pos].rstrip()
    partial_closed = _close_open_brackets(partial)   # 自动补了}

    for attempt in (partial_closed, _repair_json(partial_closed)):
        try:
            return json.loads(attempt)
        except (json.JSONDecodeError, Exception):
            pass

    return None
