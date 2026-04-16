# 简历评估与可视化项目

## 项目简介
本项目用于将简历内容转为结构化 JSON，并基于实验室画像进行多维度评分，最后通过本地网页展示结果，便于快速筛选候选人。

核心能力：
- 读取简历 Markdown，调用大模型完成结构化抽取
- 输出统一 JSON v1 格式，包含评分、结论、证据与面试问题
- 提供本地可视化页面，支持浏览、搜索、排序简历结果

## 目录结构
~~~text
.
├─ main.py                    # 主流程：读取简历、调用模型、写入 JSON
├─ viewer.py                  # 本地网页服务：展示 output/json 下的结果
├─ lab_profile.md             # 实验室画像
├─ io_Standardization.md      # 输入输出标准
├─ requirements.txt           # 依赖
├─ input/
│  └─ resume/                 # 原始简历（例如 PDF）
├─ output/
│  ├─ resume/                 # 简历 Markdown
│  └─ json/                   # 结构化评分结果
└─ tool/
   └─ pdf2md.py               # PDF 转 Markdown 工具（可选）
~~~

## 环境要求
- Windows 或 Linux/macOS
- Python 3.10 及以上
- 可访问的 OpenAI 兼容接口

## 安装依赖
在项目根目录执行：

~~~bash
pip install -r requirements.txt
~~~

## 配置环境变量
在项目根目录新建 .env 文件，至少包含以下字段：

~~~dotenv
API_KEY=你的密钥
BASE_URL=你的接口基础地址
MODEL=你的模型名
~~~

说明：
- BASE_URL 需要填写 API 根路径，不要填写到具体接口路径（例如不要写到 chat/completions）。
- main.py 启动时会检查这三个变量，缺失会直接报错。

## 数据处理流程
### 1. 准备简历
- 将待处理简历放入 input/resume。
- 如果你已有 Markdown，可直接放到 output/resume。

### 2. 生成结构化 JSON
在项目根目录执行：

~~~bash
python main.py
~~~

执行后会在 output/json 生成对应的 .json 文件。

## 网页查看结果
在项目根目录执行：

~~~bash
python viewer.py
~~~

启动成功后访问：
- http://127.0.0.1:8000

页面能力：
- 左侧简历列表
- 搜索（按文件名/摘要/学校/专业）
- 分数排序（高到低、低到高）
- 右侧卡片化展示完整字段
- 原始 JSON 查看

网页端独立说明见：`README_web.md`

## 输出说明（JSON v1）
主要字段包括：
- candidate_summary
- education
- research_interests
- skills
- experiences
- publications_awards
- highlights
- risks_unknowns
- pii_detected
- total_score
- dimension_scores
- decision
- rationale
- interview_questions
- confidence
- model_version
- prompt_version
- source_file

评分区间：
- total_score: 0-100
- match_score: 0-40
- engineering_score: 0-25
- research_potential_score: 0-25
- communication_score: 0-10

决策字段：
- recommend_interview
- need_review
- not_recommended

## 常见问题
### 1) 运行 main.py 报环境变量缺失
请检查 .env 是否存在，以及 API_KEY、BASE_URL、MODEL 是否填写正确。

### 2) viewer 页面为空
请先运行 main.py 生成 output/json 文件，或确认该目录下存在有效 JSON。

### 3) 模型返回无法解析
main.py 内已包含兜底修复与默认回填逻辑；若仍频繁发生，可降低 temperature 或缩短输入文本长度。

## 说明
- 当前 viewer.py 使用 Python 标准库 http.server，无需额外 Web 框架。
- 如需部署到服务器，可后续改造为 FastAPI 或 Flask 版本。
