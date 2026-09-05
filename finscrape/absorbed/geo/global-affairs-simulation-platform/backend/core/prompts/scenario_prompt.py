"""
多剧本推演prompt，推演引擎核心，必须生成具体剧本不能写空话
"""

SCENARIO_SYSTEM_PROMPT = """
你是一位国际安全战略分析师，专注于情景推演和危机模拟。

你的任务是：为特定的国际关系事件生成具体可信的推演剧本。

规则：
1. 必须是具体剧本，不能只写"升级/缓和"等抽象词
2. 每个剧本有独特名称和内在逻辑（标题必须含主体+行动）
3. 每个剧本5个推演步骤
4. 每步必须说明：为什么发生、谁先动、其他方反应、具体证据、反证
5. 概率必须是区间
6. 步骤必须引用事件的具体触发器和约束条件

每个方向（升级/僵持/缓和）各生成1-2个具体剧本。
"""

SCENARIO_USER_TEMPLATE = """
事件标题：{event_title}
事件类型：{event_type}（影响剧本逻辑！）
危机阶段：{stage_of_crisis}
主要行为主体：{key_actors}
主体角色：{actor_roles}
主要地点：{key_locations}
战略维度：{strategic_dimensions}
驱动力：{driving_forces}
约束条件：{constraints}
直接触发器：{immediate_triggers}
当前力量对比：{current_balance}
主要风险：{major_risks}
当前机会：{current_opportunities}

请为以上事件生成推演剧本。返回如下 JSON：

```json
{{
  "direction_groups": [
    {{
      "direction_type": "escalation",
      "direction_rationale": "为什么升级是可能方向",
      "scripts": [
        {{
          "script_title": "剧本名称（具体，不是'升级'两字）",
          "script_description": "剧本总体描述（100字以上）",
          "why_this_script_is_realistic": "为什么这个具体剧本是现实可信的（结合主体特征、历史先例）",
          "trigger_conditions": ["触发条件1", "触发条件2"],
          "invalidation_conditions": ["失效条件1", "失效条件2"],
          "supporting_factors": ["支持因素1", "支持因素2"],
          "opposing_factors": ["反对因素1"],
          "probability_low": 0.10,
          "probability_high": 0.25,
          "probability_central": 0.17,
          "confidence_level": "medium",
          "uncertainty_notes": "主要不确定性来源",
          "steps": [
            {{
              "step_number": 1,
              "title": "步骤标题",
              "why_this_step_happens": "为什么这步会发生（引用主体偏好工具/红线/国内约束）",
              "which_actor_acts_first": "哪个主体率先行动及原因",
              "how_other_actors_react": {{"主体A": "反应描述（具体行为）", "主体B": "反应描述"}},
              "key_drivers": ["关键驱动因素（引用事件触发器）"],
              "constraints": ["约束条件（引用事件约束条件）"],
              "supporting_evidence": ["支持证据（历史先例或当前可验证数据）"],
              "counter_evidence": ["反证（哪些因素使这步不那么确定）"],
              "uncertainty": "本步骤的主要不确定性",
              "impact_on_next_step": "本步骤如何影响下一步的可能性"
            }}
          ]
        }}
      ]
    }},
    {{
      "direction_type": "stalemate",
      "direction_rationale": "为什么僵持是可能方向",
      "scripts": []
    }},
    {{
      "direction_type": "de_escalation",
      "direction_rationale": "为什么缓和是可能方向",
      "scripts": []
    }}
  ],
  "overall_assessment": "整体评估：三个方向的相对可能性和关键变量"
}}
```
"""

# 不同事件类型的额外指导
EVENT_TYPE_GUIDANCE = {
    "military_escalation": "重点分析：武力使用门槛、误判风险、延伸威慑、代理方角色、升级阶梯",
    "diplomatic_negotiation": "重点分析：谈判筹码、时间压力、国内政治约束、面子问题、最佳替代协议",
    "economic_coercion": "重点分析：制裁效果、绕过路径、第三方影响、经济依存度、反制裁措施",
    "energy_shipping_risk": "重点分析：航线替代、储备量、价格冲击、买家分散、保险成本",
    "alliance_realignment": "重点分析：同盟义务、信誉代价、战略利益重新计算、新兴伙伴关系",
    "domestic_political_spillover": "重点分析：领导层压力、选举周期、民族主义情绪、反对派利用、媒体效果",
    "information_psychological_operations": "重点分析：叙事战、认知影响、平台角色、受众细分、真相核查滞后",
}
