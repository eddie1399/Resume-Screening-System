# 网页端使用说明（viewer）

## 1. 页面简介
本页面用于展示 `output/json` 下的简历结构化结果，支持快速筛选与查看候选人评估信息。

当前页面包含：
- 候选人列表（左侧）
- 搜索与排序（按分数）
- KPI 概览（当前评分、总数、筛选数、平均分）
- 详情卡片（概览、技能、经历、亮点、风险、依据、面试问题）
- 原始 JSON 查看

---

## 2. 运行方式

### 方式 A：Python 启动（开发调试）
在项目根目录执行：

```bash
python viewer.py
```

启动后访问：
- `http://127.0.0.1:8000`

说明：
- 此方式默认读取目录：`output/json`

### 方式 B：GUI 可执行文件启动（给业务同学使用）
直接双击：
- `dist/resume_viewer_gui.exe`

说明：
- 该版本为无控制台窗口模式（不显示黑框）
- 启动后会自动打开浏览器
- 默认读取目录：`dist/output/json`

---

## 3. 数据准备
页面依赖 JSON 文件，文件需放在对应目录：

- Python 运行：`output/json`
- GUI EXE 运行：`dist/output/json`

你可以把 `output/json/*.json` 复制到 `dist/output/json/`，让 GUI 版直接可用。

---

## 4. JSON 基本字段（示例）
至少建议包含以下字段，以获得完整展示效果：

- `candidate_summary`
- `education`
- `skills`
- `experiences`
- `highlights`
- `risks_unknowns`
- `dimension_scores`
- `total_score`
- `decision`
- `confidence`
- `rationale`
- `interview_questions`
- `model_version`
- `prompt_version`
- `source_file`

---

## 5. 重新打包网页 EXE
如果修改了 `viewer.py` 前端模板，需要重新打包：

```bash
pyinstaller --noconfirm resume_viewer_gui.spec
```

产物位置：
- `dist/resume_viewer_gui.exe`

---

## 6. 常见问题

### Q1：双击 EXE 后页面显示为空
先确认 `dist/output/json` 下有有效 `.json` 文件。

### Q2：端口被占用（8000）
关闭占用 8000 端口的进程后再启动，或改 `viewer.py` 中端口。

### Q3：页面还是旧样式
请确认你启动的是最新打包产物，必要时重新执行打包命令。

---

## 7. 开发入口
- 页面与接口都在：`viewer.py`
- 前端模板变量：`HTML_TEMPLATE`
- 接口：
  - `/api/resumes`
  - `/api/resume?file=...`
  - `/api/resume/<file_name>`
