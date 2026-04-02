基于实验室岗位画像进行多维度评分与推荐（面试  / 复核/ 暂不建议）

## 提示词要点

- 强制 JSON 输出
- 每条结论必须引用 evidence
- 明确禁止使用敏感属性评分
- 低置信度/信息缺失必须标注 need_review

## 规则与配置

可配置项（建议 YAML/JSON）：

- 必须项（hard requirements）：如 Python、相关方向关键词、项目经历至少 1 条
- 加分项：论文/开源/比赛/工程化
- 维度权重：40/25/25/10（可调）
- 决策阈值：
  - total >= 75 且置信度高 → recommend_interview
  - 55–74 或置信度中 → need_review
  - <55 且证据充分 → not_recommended

## 结构化抽取输出（JSON v1）

字段建议：

- candidate_summary：一句话概括
- education：学校/专业/学历/毕业时间
- research_interests：关键词数组（5–10）
- skills：编程/框架/工程工具/算法基础/英语
- experiences：数组，每项包含 role、what、how、result、evidence（原文引用）
- publications_awards：论文/专利/竞赛
- highlights：亮点（含 evidence）
- risks_unknowns：风险/信息缺失点（含 evidence 或“未找到”）
- pii_detected：是否检测到手机号/邮箱等（用于脱敏检查）

## 评分输出（JSON v1）

- total_score（0–100）
- dimension_scores：
  - match_score（0–40）：研究方向与岗位匹配
  - engineering_score（0–25）：工程实现/代码能力
  - research_potential_score（0–25）：科研潜力/论文与问题抽象能力
  - communication_score（0–10）：表达与条理
- decision：recommend_interview / need_review / not_recommended
- rationale：每个维度的评分依据与引用证据
- interview_questions：建议追问点 3–6 条（对齐风险/亮点）
- confidence：高/中/低（基于证据充分性与解析质量）
- model_version / prompt_version