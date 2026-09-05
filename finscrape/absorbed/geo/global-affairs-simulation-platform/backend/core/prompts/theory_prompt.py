"""
多理论视角分析prompt，每个理论生成结构化分析
"""

THEORY_SYSTEM_PROMPT = """
你是一位顶尖国际关系学者，精通现实主义、自由制度主义、建构主义、地缘政治学和国际政治经济学。

你的任务是：从指定的理论视角对国际关系事件进行深度分析。

要求：
1. 每个理论必须有独特的分析切入点，不能千篇一律
2. 必须说明该理论的核心假设在此事件中的体现
3. 必须指出每个主体在该理论框架下的预期行为
4. 必须指出该理论的局限性（哪些现象它解释不了）
5. 必须提出反驳论点

输出必须是严格的 JSON 格式。
"""

THEORY_USER_TEMPLATE = """
事件：{event_title}
事件类型：{event_type}
危机阶段：{stage_of_crisis}
主要行为主体：{key_actors}
主体角色：{actor_roles}
驱动力：{driving_forces}
约束条件：{constraints}
直接触发器：{immediate_triggers}

请从【{theory_name}】视角对此事件进行分析。

该理论基本信息：
{theory_description}

返回如下 JSON：

```json
{{
  "theory_name": "{theory_name}",
  "core_assumption": "该理论在此事件中体现的核心假设",
  "interpretation": "对当前事件的完整理论解读（150-300字）",
  "main_drivers": [
    "该理论视角下的主要驱动力1",
    "主要驱动力2"
  ],
  "likely_actor_responses": {{
    "美国": "该理论预测的行为逻辑",
    "伊朗": "该理论预测的行为逻辑"
  }},
  "escalation_implications": [
    "该理论视角下升级的含义1",
    "含义2"
  ],
  "deescalation_implications": [
    "该理论视角下缓和的含义1"
  ],
  "weaknesses": [
    "该理论无法很好解释的现象1",
    "局限2"
  ],
  "counterarguments": [
    "反驳该理论解读的论点1",
    "反驳论点2"
  ],
  "confidence_note": "该理论分析的适用程度说明"
}}
```
"""

THEORY_DESCRIPTIONS = {
    "realism": "现实主义认为国家是主要行为体，在无政府状态下追求权力和安全。国家行为由物质能力和战略利益决定，道德和制度作用有限。",
    "liberal_institutionalism": "自由制度主义强调国际制度、规则和多边合作的作用。认为重复博弈、信息共享和制度约束可以促进合作，降低冲突。",
    "constructivism": "建构主义认为国际关系中的利益和身份是社会建构的，规范、认知和话语塑造国家行为。物质因素必须通过社会意义才能发挥作用。",
    "geopolitics": "地缘政治学关注地理因素（资源、战略位置、缓冲区、通道控制）对国家战略的决定性影响。分析心脏地带、边缘地带和关键节点。",
    "international_political_economy": "国际政治经济学分析经济利益、贸易依存、资本流动和经济制裁等如何影响国家行为和国际关系。关注经济与政治的交叉互动。",
}
