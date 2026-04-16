import sys
from pathlib import Path
sys.path.append("tool")  # 把文件夹加入路径
import tool.pdf2md as pdf2md
import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

PROMPT_VERSION = "json_v1_2026-04-02"

BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def resource_path(relative_path: str) -> Path:
  if getattr(sys, "frozen", False):
    return Path(sys._MEIPASS) / relative_path
  return BASE_DIR / relative_path

## 遍历文件夹中的pdf文件，批量转换成markdown文件
## 改成相对路径，方便在不同环境运行
pdf_path = BASE_DIR / "input" / "resume"
output_path = BASE_DIR / "output" / "resume"
json_output_path = BASE_DIR / "output" / "json"

for filename in os.listdir(pdf_path):
    if filename.endswith(".pdf"):
        pdf_file = os.path.join(pdf_path, filename)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        markdown_file = os.path.join(output_path, filename.replace(".pdf", ".md"))
        pdf2md.convert_pdf_to_markdown(pdf_file, markdown_file)

##大模型llm api 调用
load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key:
  raise ValueError("API_KEY 未配置。请在 .env 文件中设置 API_KEY=你的密钥")
base_url = os.getenv("BASE_URL");
if not base_url:
  raise ValueError("BASE_URL 未配置。请在 .env 文件中设置 BASE_URL=你的基础URL")
model = os.getenv("MODEL");
if not model:
  raise ValueError("MODEL 未配置。请在 .env 文件中设置 MODEL=你的模型名称")

client = OpenAI(api_key=api_key, base_url=base_url)


def extract_json_text(text):
  """Extract the first JSON object substring from model text."""
  if not text:
    return ""
  stripped = text.strip()
  if stripped.startswith("{") and stripped.endswith("}"):
    return stripped

  match = re.search(r"\{[\s\S]*\}", stripped)
  if match:
    return match.group(0)
  return stripped


def get_message_text(message):
  """Return assistant text with fallback for providers that use non-standard fields."""
  content = message.content or ""
  if isinstance(content, list):
    parts = []
    for item in content:
      if isinstance(item, dict) and item.get("type") == "text":
        parts.append(item.get("text", ""))
    content = "\n".join([p for p in parts if p])
  if content:
    return content

  reasoning = getattr(message, "reasoning_content", "") or ""
  # Some compatible providers may place answer-like text in reasoning_content.
  return reasoning


def normalize_result(data, source_file, model_name):
  """Normalize model output to the required JSON v1 schema."""
  if not isinstance(data, dict):
    data = {}

  result = {
    "candidate_summary": data.get("candidate_summary", ""),
    "education": data.get("education", {}),
    "research_interests": data.get("research_interests", []),
    "skills": data.get("skills", {}),
    "experiences": data.get("experiences", []),
    "publications_awards": data.get("publications_awards", []),
    "highlights": data.get("highlights", []),
    "risks_unknowns": data.get("risks_unknowns", []),
    "pii_detected": data.get("pii_detected", False),
    "total_score": data.get("total_score", 0),
    "dimension_scores": data.get("dimension_scores", {}),
    "decision": data.get("decision", "need_review"),
    "rationale": data.get("rationale", []),
    "interview_questions": data.get("interview_questions", []),
    "confidence": data.get("confidence", "低"),
    "model_version": data.get("model_version", model_name),
    "prompt_version": PROMPT_VERSION,
    "source_file": source_file,
  }

  # Ensure dimension score fields exist and stay in expected ranges.
  dim = result["dimension_scores"] if isinstance(result["dimension_scores"], dict) else {}
  result["dimension_scores"] = {
    "match_score": max(0, min(40, int(dim.get("match_score", 0) or 0))),
    "engineering_score": max(0, min(25, int(dim.get("engineering_score", 0) or 0))),
    "research_potential_score": max(0, min(25, int(dim.get("research_potential_score", 0) or 0))),
    "communication_score": max(0, min(10, int(dim.get("communication_score", 0) or 0))),
  }

  result["total_score"] = max(0, min(100, int(result.get("total_score", 0) or 0)))
  if result["decision"] not in ["recommend_interview", "need_review", "not_recommended"]:
    result["decision"] = "need_review"
  if result["confidence"] not in ["高", "中", "低"]:
    result["confidence"] = "低"

  if not isinstance(result["education"], dict):
    result["education"] = {}
  if not isinstance(result["skills"], dict):
    result["skills"] = {}
  if not isinstance(result["research_interests"], list):
    result["research_interests"] = []
  if not isinstance(result["experiences"], list):
    result["experiences"] = []
  if not isinstance(result["publications_awards"], list):
    result["publications_awards"] = []
  if not isinstance(result["highlights"], list):
    result["highlights"] = []
  if not isinstance(result["risks_unknowns"], list):
    result["risks_unknowns"] = []
  if not isinstance(result["rationale"], list):
    result["rationale"] = []
  if not isinstance(result["interview_questions"], list):
    result["interview_questions"] = []

  # Normalize nested list item shapes.
  norm_experiences = []
  for item in result["experiences"]:
    if isinstance(item, dict):
      norm_experiences.append({
        "role": item.get("role", ""),
        "what": item.get("what", ""),
        "how": item.get("how", ""),
        "result": item.get("result", ""),
        "evidence": item.get("evidence", "未找到"),
      })
  result["experiences"] = norm_experiences

  norm_highlights = []
  for item in result["highlights"]:
    if isinstance(item, dict):
      norm_highlights.append({
        "point": item.get("point", ""),
        "evidence": item.get("evidence", "未找到"),
      })
  result["highlights"] = norm_highlights

  norm_risks = []
  for item in result["risks_unknowns"]:
    if isinstance(item, dict):
      norm_risks.append({
        "point": item.get("point", ""),
        "evidence": item.get("evidence", "未找到"),
      })
  result["risks_unknowns"] = norm_risks

  norm_rationale = []
  for item in result["rationale"]:
    if isinstance(item, dict):
      norm_rationale.append({
        "dimension": item.get("dimension", ""),
        "reason": item.get("reason", ""),
        "evidence": item.get("evidence", "未找到"),
      })
  result["rationale"] = norm_rationale

  # Ensure interview questions are present (3-6 expected by spec).
  valid_questions = [q for q in result["interview_questions"] if isinstance(q, str) and q.strip()]
  if len(valid_questions) < 3:
    valid_questions.extend([
      "请结合一个最有代表性的项目说明你的技术选型与取舍。",
      "如果进入实验室，你希望优先参与哪个研究方向，为什么？",
      "请举例说明你如何定位并解决一次复杂技术问题。",
    ])
  result["interview_questions"] = valid_questions[:6]

  return result


def has_missing_scores(result):
  dim = result.get("dimension_scores", {}) if isinstance(result, dict) else {}
  total = int(result.get("total_score", 0) or 0) if isinstance(result, dict) else 0
  score_sum = int(dim.get("match_score", 0) or 0) + int(dim.get("engineering_score", 0) or 0) + int(dim.get("research_potential_score", 0) or 0) + int(dim.get("communication_score", 0) or 0)
  return total == 0 and score_sum == 0


def merge_score_fields(result, score_patch):
  if not isinstance(result, dict) or not isinstance(score_patch, dict):
    return result

  if "total_score" in score_patch:
    result["total_score"] = score_patch.get("total_score", result.get("total_score", 0))
  if "dimension_scores" in score_patch and isinstance(score_patch["dimension_scores"], dict):
    result["dimension_scores"] = score_patch["dimension_scores"]
  if "decision" in score_patch:
    result["decision"] = score_patch.get("decision", result.get("decision", "need_review"))
  if "rationale" in score_patch:
    result["rationale"] = score_patch.get("rationale", result.get("rationale", []))
  if "confidence" in score_patch:
    result["confidence"] = score_patch.get("confidence", result.get("confidence", "低"))
  if "interview_questions" in score_patch:
    result["interview_questions"] = score_patch.get("interview_questions", result.get("interview_questions", []))

  return result


## 导入实验室画像文件 lab_profile.md和简历，读取内容并发送给大模型
## 根据实验室画像和简历内容，生成一个匹配度评分，范围是0-100，分数越高表示匹配度越高
with open(resource_path("lab_profile.md"), "r", encoding="utf-8") as f:
    lab_profile = f.read()
## 打开io_Standardization.md文件，读取内容并发送给大模型
with open(resource_path("io_Standardization.md"), "r", encoding="utf-8") as f:
    io_standardization = f.read()
os.makedirs(json_output_path, exist_ok=True)
## 遍历output文件夹中找到markdown文件，读取内容并发送给大模型
markdown_files = sorted(
  [name for name in os.listdir(output_path) if name.lower().endswith(".md")]
)
print(f"检测到 {len(markdown_files)} 个简历文件")

for index, filename in enumerate(markdown_files, start=1):
  markdown_file = os.path.join(output_path, filename)
  print(f"\n[{index}/{len(markdown_files)}] 正在处理: {filename}")
  with open(markdown_file, "r", encoding="utf-8") as f:
    resume = f.read()

  ## 构造提示语，发送给大模型
  system_prompt = f"""你是一个科研招聘评估专家。
请严格输出 JSON 对象（response_format=json_object）。
不要输出任何 JSON 以外的文字。
输出字段必须完整，且遵循 JSON v1：
{{
  "candidate_summary": "",
  "education": {{"school": "", "major": "", "degree": "", "graduation_time": ""}},
  "research_interests": [],
  "skills": {{"programming": [], "frameworks": [], "engineering_tools": [], "algorithm_fundamentals": "", "english": ""}},
  "experiences": [{{"role": "", "what": "", "how": "", "result": "", "evidence": ""}}],
  "publications_awards": [],
  "highlights": [{{"point": "", "evidence": ""}}],
  "risks_unknowns": [{{"point": "", "evidence": "未找到"}}],
  "pii_detected": false,
  "total_score": 0,
  "dimension_scores": {{"match_score": 0, "engineering_score": 0, "research_potential_score": 0, "communication_score": 0}},
  "decision": "need_review",
  "rationale": [{{"dimension": "", "reason": "", "evidence": ""}}],
  "interview_questions": [""],
  "confidence": "低",
  "model_version": "{model}",
  "prompt_version": "{PROMPT_VERSION}"
}}

评分必须给出非空数值：
- total_score: 0-100
- match_score: 0-40
- engineering_score: 0-25
- research_potential_score: 0-25
- communication_score: 0-10
- decision: recommend_interview / need_review / not_recommended

规则：
- 每条结论附 evidence 原文引用。
- 禁止使用敏感属性评分。
- 信息缺失或置信度不足时，decision 设为 need_review。
"""

  user_prompt = f"""请根据以下材料完成结构化抽取和评分：

实验室画像：
{lab_profile}

简历内容：
{resume}

输入输出标准参考：
{io_standardization}
"""

  prompt = f"""你是一名资深的招聘专家，负责评估求职者与实验室的匹配度。

请严格按 JSON v1 输出，仅输出一个 JSON 对象，不要输出任何解释、注释或 Markdown 代码块。
每条结论都需要 evidence（原文引用）。禁止使用敏感属性评分。
若信息缺失或置信度不足，decision 必须为 need_review。

输出字段必须完整包含以下结构：
{{
  "candidate_summary": "",
  "education": {{
    "school": "",
    "major": "",
    "degree": "",
    "graduation_time": ""
  }},
  "research_interests": ["", ""],
  "skills": {{
    "programming": [],
    "frameworks": [],
    "engineering_tools": [],
    "algorithm_fundamentals": "",
    "english": ""
  }},
  "experiences": [
    {{"role": "", "what": "", "how": "", "result": "", "evidence": ""}}
  ],
  "publications_awards": [],
  "highlights": [{{"point": "", "evidence": ""}}],
  "risks_unknowns": [{{"point": "", "evidence": "未找到"}}],
  "pii_detected": false,
  "total_score": 0,
  "dimension_scores": {{
    "match_score": 0,
    "engineering_score": 0,
    "research_potential_score": 0,
    "communication_score": 0
  }},
  "decision": "need_review",
  "rationale": [{{"dimension": "", "reason": "", "evidence": ""}}],
  "interview_questions": [""],
  "confidence": "低",
  "model_version": "{model}",
  "prompt_version": "{PROMPT_VERSION}"
}}

评分规则：
- total_score: 0-100
- match_score: 0-40
- engineering_score: 0-25
- research_potential_score: 0-25
- communication_score: 0-10
- decision: recommend_interview / need_review / not_recommended

生成约束：
- 输出紧凑，避免冗长叙述。
- interview_questions 输出 3-6 条。
- 每个 evidence 保持 1-2 句短引用。

实验室画像：
{lab_profile}

简历内容：
{resume}
"""
  try:
    request_payload = {
      "model": model,
      "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
      ],
      "max_tokens": 10240,
      "temperature": 0.2,
    }

    # Prefer JSON mode when the provider supports OpenAI-compatible response_format.
    try:
      response = client.chat.completions.create(
        **request_payload,
        response_format={"type": "json_object"}
      )
    except Exception:
      response = client.chat.completions.create(**request_payload)

    finish_reason = response.choices[0].finish_reason
    output_text = get_message_text(response.choices[0].message)
    if not output_text.strip():
      # Retry once with lower temperature if the first attempt returns empty text.
      retry_payload = dict(request_payload)
      retry_payload["temperature"] = 0
      response = client.chat.completions.create(
        **retry_payload
      )
      finish_reason = response.choices[0].finish_reason
      output_text = get_message_text(response.choices[0].message)

    print(f"finish_reason: {finish_reason}")
    print(f"模型响应长度: {len(output_text)}")
    json_text = extract_json_text(output_text)
    output_file = os.path.join(json_output_path, filename.replace(".md", ".json"))

    result_obj = None
    try:
      result_obj = json.loads(json_text)
      result_obj = normalize_result(result_obj, filename, model)

      if has_missing_scores(result_obj):
        score_system_prompt = """你是评分专家。仅输出 JSON 对象，且只包含这些字段：total_score, dimension_scores, decision, rationale, confidence, interview_questions。
要求：所有分数字段必须为数字，不能留空；decision 仅可取 recommend_interview/need_review/not_recommended；confidence 仅可取 高/中/低。"""
        score_user_prompt = f"""请基于以下候选人结构化信息补全评分字段：
{json.dumps(result_obj, ensure_ascii=False)}

评分维度范围：match_score(0-40), engineering_score(0-25), research_potential_score(0-25), communication_score(0-10), total_score(0-100)。
并给出 3-6 条 interview_questions。"""
        try:
          score_resp = client.chat.completions.create(
            model=model,
            messages=[
              {"role": "system", "content": score_system_prompt},
              {"role": "user", "content": score_user_prompt}
            ],
            max_tokens=1024,
            temperature=0.2,
            response_format={"type": "json_object"}
          )
          score_text = get_message_text(score_resp.choices[0].message)
          score_patch = json.loads(extract_json_text(score_text))
          result_obj = merge_score_fields(result_obj, score_patch)
          result_obj = normalize_result(result_obj, filename, model)
        except Exception:
          pass
    except json.JSONDecodeError:
      # Retry once to repair non-JSON or truncated output into required JSON v1 schema.
      repair_prompt = f"""请将下面内容修复为严格 JSON 对象，只输出 JSON，不要输出其他文字。
必须包含这些字段：candidate_summary, education, research_interests, skills, experiences, publications_awards, highlights, risks_unknowns, pii_detected, total_score, dimension_scores(match_score/engineering_score/research_potential_score/communication_score), decision, rationale, interview_questions, confidence, model_version, prompt_version。
decision 只能是 recommend_interview/need_review/not_recommended。
confidence 只能是 高/中/低。

待修复内容：
{output_text}
"""
      try:
        repaired = client.chat.completions.create(
          model=model,
          messages=[{"role": "user", "content": repair_prompt}],
          max_tokens=2048,
          temperature=0,
          response_format={"type": "json_object"}
        )
        repaired_text = get_message_text(repaired.choices[0].message)
        repaired_json = extract_json_text(repaired_text)
        result_obj = normalize_result(json.loads(repaired_json), filename, model)
      except Exception:
        # Fallback: keep parse-error record but maintain full required schema.
        pass

    if not isinstance(result_obj, dict):
      result_obj = {
        "source_file": filename,
        "candidate_summary": "",
        "education": {},
        "research_interests": [],
        "skills": {},
        "experiences": [],
        "publications_awards": [],
        "highlights": [],
        "risks_unknowns": [{"point": "输出解析失败", "evidence": "未找到"}],
        "pii_detected": False,
        "total_score": 0,
        "dimension_scores": {
          "match_score": 0,
          "engineering_score": 0,
          "research_potential_score": 0,
          "communication_score": 0
        },
        "decision": "need_review",
        "rationale": [],
        "interview_questions": [],
        "confidence": "低",
        "model_version": model,
        "prompt_version": PROMPT_VERSION,
        "parse_error": "模型输出不是合法JSON，已保留原文",
        "finish_reason": finish_reason,
        "usage": response.usage.model_dump() if response.usage else None,
        "raw_output": output_text
      }

    with open(output_file, "w", encoding="utf-8") as jf:
      json.dump(result_obj, jf, ensure_ascii=False, indent=2)

    print(f"已保存JSON: {output_file}")
  except Exception as e:
    print(f"调用失败: {filename} -> {e}")


