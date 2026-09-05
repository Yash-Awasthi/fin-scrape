"""
事件抽象prompt，从新闻簇提炼结构化IRGEvent，只输出核心字段控token
"""

ABSTRACTION_SYSTEM_PROMPT = """
你是国际关系分析师，从新闻事件簇中提炼结构化国际关系事件。

事件类型只能从以下7种选一：
military_escalation / diplomatic_negotiation / economic_coercion /
energy_shipping_risk / alliance_realignment / domestic_political_spillover /
information_psychological_operations

危机阶段只能从以下7种选一：
latent / emergence / escalation / crisis / de_escalation / resolution / post_crisis

输出严格 JSON，用 ```json ... ``` 包裹，不要任何解释。
"""

ABSTRACTION_USER_TEMPLATE = """
事件簇：{cluster_title}
主体：{key_actors}
地点：{key_locations}
核心议题：{primary_issue}
升级信号：{escalation_signals}
缓和信号：{deescalation_signals}
证据：{evidence_summary}
新闻：{news_summaries}

返回 JSON：

```json
{{
  "event_title": "精确标题（主体+行动+背景，15-30字）",
  "event_type": "military_escalation",
  "stage_of_crisis": "escalation",
  "key_actors": ["主体A", "主体B"],
  "actor_roles": {{
    "主体A": "角色描述",
    "主体B": "角色描述"
  }},
  "key_locations": ["地点1", "地点2"],
  "strategic_dimensions": ["维度1", "维度2"],
  "driving_forces": ["驱动力1", "驱动力2", "驱动力3"],
  "constraints": ["约束1", "约束2"],
  "immediate_triggers": ["触发器1"],
  "current_balance": "当前力量对比（2-3句）",
  "major_risks": ["风险1", "风险2"],
  "current_opportunities": ["机会1"],
  "event_confidence": 0.8,
  "geo_coordinates": {{"lat": 35.0, "lng": 45.0}},
  "region": "Middle East"
}}
```
"""
