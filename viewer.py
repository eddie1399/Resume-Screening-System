import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
JSON_DIR = ROOT_DIR / "output" / "json"


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>智能简历分析系统</title>
  <style>
    :root {
      --bg: #f8fbff;
      --surface: #ffffff;
      --line: #e5eaf5;
      --text: #0f172a;
      --muted: #64748b;
      --brand: #2563eb;
      --brand-2: #4f46e5;
      --good: #16a34a;
      --warn: #d97706;
      --bad: #dc2626;
      --shadow: 0 10px 30px rgba(37, 99, 235, 0.08);
      --shadow-soft: 0 6px 20px rgba(15, 23, 42, 0.06);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Noto Sans SC", "PingFang SC", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 0% 0%, rgba(59, 130, 246, 0.14), transparent 36%),
        radial-gradient(circle at 92% 0%, rgba(79, 70, 229, 0.12), transparent 30%),
        linear-gradient(180deg, #f8fbff, #f1f6ff 40%, #f9fbff);
      color: var(--text);
      min-height: 100vh;
    }

    .navbar {
      position: sticky;
      top: 0;
      z-index: 10;
      height: 64px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.92);
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow-soft);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
    }

    .nav-brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      color: #1d4ed8;
      letter-spacing: 0.01em;
    }

    .brand-mark {
      width: 30px;
      height: 30px;
      border-radius: 9px;
      background: linear-gradient(135deg, var(--brand), var(--brand-2));
      box-shadow: 0 8px 16px rgba(37, 99, 235, 0.28);
    }

    .nav-meta {
      color: var(--muted);
      font-size: 13px;
    }

    .app {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: calc(100vh - 64px);
      max-width: 1440px;
      margin: 0 auto;
      padding: 18px;
      gap: 16px;
    }

    .sidebar {
      position: sticky;
      top: 82px;
      height: calc(100vh - 100px);
      overflow: auto;
      background: var(--surface);
      color: var(--text);
      border: 1px solid var(--line);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 16px;
    }

    .brand {
      padding: 16px;
      border-radius: 14px;
      background: linear-gradient(135deg, #eff6ff, #eef2ff);
      border: 1px solid #dbeafe;
      margin-bottom: 14px;
    }

    .brand h1 {
      margin: 0;
      font-size: 17px;
      font-weight: 800;
      letter-spacing: 0.02em;
      color: #1d4ed8;
    }

    .brand p {
      margin: 8px 0 0;
      line-height: 1.6;
      font-size: 12px;
      color: #5b6f94;
    }

    .sidebar-tools {
      display: grid;
      gap: 10px;
      margin-bottom: 14px;
    }

    .search-box,
    .select-box {
      border: 1px solid #dbe5f6;
      border-radius: 10px;
      background: #ffffff;
      color: var(--text);
      padding: 10px 12px;
      font-size: 13px;
      outline: none;
      width: 100%;
    }

    .search-box:focus,
    .select-box:focus {
      border-color: #93c5fd;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
    }

    .resume-list {
      display: grid;
      gap: 8px;
    }

    .resume-item {
      border: 1px solid #e2e8f3;
      border-radius: 12px;
      background: #ffffff;
      padding: 12px;
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.2s ease, background 0.2s ease;
    }

    .resume-item:hover {
      transform: translateY(-1px);
      border-color: #93c5fd;
      background: #f8fbff;
    }

    .resume-item.active {
      border-color: #60a5fa;
      background: linear-gradient(130deg, #eff6ff, #eef2ff);
      box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.2) inset;
    }

    .resume-item .name {
      margin: 0 0 6px;
      font-size: 14px;
      font-weight: 700;
      color: #111827;
    }

    .resume-item .meta {
      margin: 0;
      font-size: 12px;
      color: #64748b;
      line-height: 1.5;
    }

    .main {
      padding: 0;
    }

    .hero-head {
      border: 1px solid var(--line);
      border-radius: 16px;
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(79, 70, 229, 0.9));
      box-shadow: var(--shadow);
      padding: 20px;
      margin-bottom: 16px;
      animation: panelIn 0.35s ease;
      color: #f8fbff;
    }

    .hero-head .caption {
      margin: 0 0 8px;
      font-size: 12px;
      color: rgba(237, 242, 255, 0.9);
      letter-spacing: 0.07em;
      text-transform: uppercase;
      font-weight: 700;
    }

    .hero-head h2 {
      margin: 0;
      font-size: 28px;
      line-height: 1.25;
      letter-spacing: 0.01em;
    }

    .hero-head p {
      margin: 10px 0 0;
      max-width: 70ch;
      color: rgba(232, 238, 255, 0.95);
      font-size: 14px;
    }

    .kpi-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-bottom: 14px;
      animation: panelIn 0.45s ease both;
    }

    .kpi-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--surface);
      box-shadow: var(--shadow);
      padding: 14px;
      position: relative;
      overflow: hidden;
    }

    .kpi-card::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 3px;
      background: linear-gradient(90deg, #3b82f6, #6366f1);
    }

    .kpi-label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }

    .kpi-value {
      font-size: 26px;
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.03em;
      color: #13203a;
    }

    .hero {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--surface);
      box-shadow: var(--shadow);
      padding: 18px;
      margin-bottom: 14px;
      animation: panelIn 0.55s ease both;
    }

    .hero-title {
      margin: 0;
      font-size: 23px;
      line-height: 1.35;
    }

    .hero-subtitle {
      margin: 10px 0 0;
      color: var(--muted);
      line-height: 1.8;
      max-width: 72ch;
    }

    .hero-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .badge,
    .chip {
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid #dbeafe;
      background: #eff6ff;
      color: #1e3a8a;
      font-size: 12px;
      font-weight: 600;
    }

    .content-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      animation: panelIn 0.65s ease both;
    }

    .card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--surface);
      box-shadow: var(--shadow);
      padding: 16px;
    }

    .card h2 {
      margin: 0 0 12px;
      font-size: 16px;
      color: #1b335a;
    }

    .section-meta {
      margin: -4px 0 12px;
      color: var(--muted);
      line-height: 1.6;
      font-size: 13px;
    }

    .span-12 { grid-column: span 12; }
    .span-8 { grid-column: span 8; }
    .span-6 { grid-column: span 6; }
    .span-4 { grid-column: span 4; }

    .definition-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .definition-item,
    .list-item {
      border: 1px solid #e2e8f0;
      background: #f9fbff;
      border-radius: 10px;
      padding: 12px;
    }

    .definition-item .label {
      font-size: 11px;
      color: var(--muted);
      display: block;
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .definition-item .value {
      font-size: 14px;
      line-height: 1.7;
      word-break: break-word;
      color: #16243b;
    }

    .chips,
    .list-stack,
    .score-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .list-stack,
    .score-row {
      display: grid;
      gap: 9px;
    }

    .list-item {
      display: grid;
      gap: 7px;
    }

    .list-item strong {
      color: #132746;
      font-size: 14px;
    }

    .list-item p {
      margin: 0;
      color: #4d5d77;
      line-height: 1.65;
      word-break: break-word;
      font-size: 13px;
    }

    .score-line {
      display: grid;
      gap: 4px;
    }

    .score-line-head {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #4f6281;
    }

    .bar {
      height: 8px;
      border-radius: 999px;
      background: #e8eef9;
      overflow: hidden;
      border: 1px solid #dce5f4;
    }

    .bar > span {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #3b82f6, #6366f1);
    }

    .raw-json {
      width: 100%;
      min-height: 320px;
      resize: vertical;
      border-radius: 10px;
      border: 1px solid #cfdced;
      background: #0f1728;
      color: #e5f0ff;
      padding: 14px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre;
    }

    .empty {
      margin-top: 14px;
      padding: 20px;
      border-radius: 10px;
      border: 1px dashed #b9c9e4;
      color: #557094;
      background: #f4f8ff;
      text-align: center;
    }

    .hidden { display: none !important; }

    @keyframes panelIn {
      from {
        opacity: 0;
        transform: translateY(6px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @media (max-width: 1120px) {
      .app { grid-template-columns: 1fr; }
      .sidebar {
        position: relative;
        height: auto;
        top: 0;
      }
      .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .definition-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .span-8, .span-6, .span-4 { grid-column: span 12; }
    }

    @media (max-width: 760px) {
      .navbar { padding: 0 12px; }
      .app { padding: 10px; }
      .sidebar { padding: 12px; }
      .kpi-grid { grid-template-columns: 1fr; }
      .definition-grid { grid-template-columns: 1fr; }
      .hero-head h2 { font-size: 22px; }
      .hero-title { font-size: 19px; }
    }
  </style>
</head>
<body>
  <header class="navbar">
    <div class="nav-brand"><span class="brand-mark"></span>智能简历分析系统</div>
    <div class="nav-meta">AI 驱动招聘决策面板</div>
  </header>

  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <h1>候选人列表</h1>
        <p>参考 example/frontend 视觉风格重写：蓝靛渐变、浅色卡片、清晰层级与高可读性。</p>
      </div>

      <div class="sidebar-tools">
        <input id="search" class="search-box" type="search" placeholder="搜索姓名、学校、文件名" />
        <select id="sort" class="select-box">
          <option value="default">默认顺序</option>
          <option value="score-desc">分数从高到低</option>
          <option value="score-asc">分数从低到高</option>
        </select>
      </div>

      <div id="resumeList" class="resume-list"></div>
    </aside>

    <main class="main">
      <header class="hero-head">
        <p class="caption">AI Resume Review Workspace</p>
        <h2>让招聘评估更快、更清晰</h2>
        <p>从候选人摘要到评分依据、亮点风险与面试问题，一屏聚合，支持检索和排序快速对比。</p>
      </header>

      <section class="kpi-grid">
        <article class="kpi-card"><span class="kpi-label">当前候选人评分</span><div id="scoreNumber" class="kpi-value">--</div></article>
        <article class="kpi-card"><span class="kpi-label">总简历数</span><div id="totalCount" class="kpi-value">0</div></article>
        <article class="kpi-card"><span class="kpi-label">筛选结果数</span><div id="filteredCount" class="kpi-value">0</div></article>
        <article class="kpi-card"><span class="kpi-label">平均分</span><div id="averageScore" class="kpi-value">0</div></article>
      </section>

      <section class="hero">
        <h2 id="heroTitle" class="hero-title">正在加载简历数据</h2>
        <p id="heroSubtitle" class="hero-subtitle">页面将按照候选人摘要、评分、维度依据、经历亮点和风险项进行结构化展示。</p>
        <div id="heroBadges" class="hero-badges"></div>
      </section>

      <section class="content-grid">
        <article class="card span-12">
          <h2>候选人概览</h2>
          <p id="summaryText" class="section-meta"></p>
          <div id="overviewGrid" class="definition-grid"></div>
        </article>

        <article class="card span-4">
          <h2>评估状态</h2>
          <div class="list-stack">
            <div class="list-item"><strong>判断</strong><p id="decisionValue">--</p></div>
            <div class="list-item"><strong>置信度</strong><p id="confidenceValue">--</p></div>
            <div class="list-item"><strong>模型版本</strong><p id="modelValue">--</p></div>
            <div class="list-item"><strong>PII 检测</strong><p id="piiValue">--</p></div>
          </div>
        </article>

        <article class="card span-8">
          <h2>分项评分</h2>
          <div id="scoresArea" class="score-row"></div>
        </article>

        <article class="card span-6">
          <h2>技能栈</h2>
          <div id="skillsArea" class="list-stack"></div>
        </article>

        <article class="card span-6">
          <h2>研究方向</h2>
          <div id="interestsArea" class="chips"></div>
        </article>

        <article class="card span-8">
          <h2>经历与成果</h2>
          <div id="experiencesArea" class="list-stack"></div>
        </article>

        <article class="card span-4">
          <h2>亮点</h2>
          <div id="highlightsArea" class="list-stack"></div>
        </article>

        <article class="card span-6">
          <h2>风险与未知</h2>
          <div id="risksArea" class="list-stack"></div>
        </article>

        <article class="card span-6">
          <h2>面试问题</h2>
          <div id="questionsArea" class="chips"></div>
        </article>

        <article class="card span-12">
          <h2>评估依据</h2>
          <div id="rationaleArea" class="list-stack"></div>
        </article>

        <article class="card span-12">
          <h2>原始 JSON</h2>
          <textarea id="rawJson" class="raw-json" readonly></textarea>
        </article>
      </section>

      <div id="emptyState" class="empty hidden">未找到 JSON 文件。请确认 output/json 目录下已有简历结果。</div>
    </main>
  </div>

  <script>
    const state = {
      resumes: [],
      filtered: [],
      selected: null,
    };

    const elements = {
      search: document.getElementById('search'),
      sort: document.getElementById('sort'),
      resumeList: document.getElementById('resumeList'),
      totalCount: document.getElementById('totalCount'),
      filteredCount: document.getElementById('filteredCount'),
      averageScore: document.getElementById('averageScore'),
      heroTitle: document.getElementById('heroTitle'),
      heroSubtitle: document.getElementById('heroSubtitle'),
      heroBadges: document.getElementById('heroBadges'),
      scoreNumber: document.getElementById('scoreNumber'),
      decisionValue: document.getElementById('decisionValue'),
      confidenceValue: document.getElementById('confidenceValue'),
      modelValue: document.getElementById('modelValue'),
      piiValue: document.getElementById('piiValue'),
      summaryText: document.getElementById('summaryText'),
      overviewGrid: document.getElementById('overviewGrid'),
      skillsArea: document.getElementById('skillsArea'),
      interestsArea: document.getElementById('interestsArea'),
      experiencesArea: document.getElementById('experiencesArea'),
      scoresArea: document.getElementById('scoresArea'),
      highlightsArea: document.getElementById('highlightsArea'),
      risksArea: document.getElementById('risksArea'),
      rationaleArea: document.getElementById('rationaleArea'),
      questionsArea: document.getElementById('questionsArea'),
      rawJson: document.getElementById('rawJson'),
      emptyState: document.getElementById('emptyState'),
    };

    function text(value, fallback = '未填写') {
      return String(value ?? '').trim() || fallback;
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function toArray(value) {
      return Array.isArray(value) ? value : [];
    }

    function statusLabel(decision) {
      if (decision === 'recommend_interview') return '推荐面试';
      if (decision === 'not_recommended') return '不推荐';
      return '待复核';
    }

    function scoreColor(score) {
      if (score >= 80) return 'var(--good)';
      if (score >= 60) return 'var(--warn)';
      return 'var(--bad)';
    }

    function renderBadgeList(items, target) {
      target.innerHTML = items.map(item => `<span class="badge">${escapeHtml(item)}</span>`).join('');
    }

    function renderDefinitionGrid(items) {
      elements.overviewGrid.innerHTML = items.map(item => `
        <div class="definition-item">
          <span class="label">${escapeHtml(item.label)}</span>
          <div class="value">${escapeHtml(item.value)}</div>
        </div>
      `).join('');
    }

    function renderListItems(items, target, emptyText) {
      if (!items.length) {
        target.innerHTML = `<div class="list-item"><p>${escapeHtml(emptyText)}</p></div>`;
        return;
      }
      target.innerHTML = items.join('');
    }

    function renderSelected(resume) {
      if (!resume) return;
      const data = resume.data || {};
      const summary = text(data.candidate_summary, '暂无摘要');
      const school = text(data.education && data.education.school);
      const major = text(data.education && data.education.major);
      const degree = text(data.education && data.education.degree);
      const graduation = text(data.education && data.education.graduation_time);
      const score = Number(data.total_score || 0);
      const dim = data.dimension_scores || {};

      elements.heroTitle.textContent = resume.label;
      elements.heroSubtitle.textContent = summary;
      renderBadgeList([
        resume.file_name,
        text(data.decision, 'need_review'),
        `评分 ${score}`,
        `置信度 ${text(data.confidence, '低')}`,
      ], elements.heroBadges);

      elements.scoreNumber.textContent = score;
      elements.scoreNumber.style.color = scoreColor(score);
      elements.decisionValue.textContent = statusLabel(data.decision);
      elements.confidenceValue.textContent = text(data.confidence, '低');
      elements.modelValue.textContent = text(data.model_version, '未知');
      elements.piiValue.textContent = data.pii_detected ? '已检测' : '未检测';

      elements.summaryText.textContent = `来源文件：${resume.file_name}。${data.prompt_version ? `提示词版本：${data.prompt_version}。` : ''}${data.model_version ? `模型版本：${data.model_version}。` : ''}`;

      renderDefinitionGrid([
        { label: '学校', value: school },
        { label: '专业', value: major },
        { label: '学历', value: degree },
        { label: '毕业时间', value: graduation },
        { label: '来源文件', value: text(data.source_file, resume.file_name) },
        { label: '是否检测到 PII', value: data.pii_detected ? '是' : '否' },
      ]);

      const skills = data.skills || {};
      elements.skillsArea.innerHTML = [
        { title: '编程语言', value: toArray(skills.programming) },
        { title: '框架/库', value: toArray(skills.frameworks) },
        { title: '工程工具', value: toArray(skills.engineering_tools) },
        { title: '算法基础', value: [text(skills.algorithm_fundamentals)] },
        { title: '英语', value: [text(skills.english)] },
      ].map(group => `
        <div class="list-item">
          <strong>${escapeHtml(group.title)}</strong>
          <div class="chips">${group.value.map(item => `<span class="chip">${escapeHtml(item)}</span>`).join('')}</div>
        </div>
      `).join('');

      const interests = toArray(data.research_interests);
      renderBadgeList(interests.length ? interests : ['暂无研究方向'], elements.interestsArea);

      const experiences = toArray(data.experiences).map(item => `
        <div class="list-item">
          <strong>${escapeHtml(text(item.role, '项目经历'))}</strong>
          <p><strong>做了什么：</strong>${escapeHtml(text(item.what))}</p>
          <p><strong>怎么做的：</strong>${escapeHtml(text(item.how))}</p>
          <p><strong>结果：</strong>${escapeHtml(text(item.result))}</p>
          <p><strong>证据：</strong>${escapeHtml(text(item.evidence, '未找到'))}</p>
        </div>
      `);
      renderListItems(experiences, elements.experiencesArea, '暂无经历信息');

      const scoreItems = [
        ['匹配度', dim.match_score ?? 0, 40],
        ['工程能力', dim.engineering_score ?? 0, 25],
        ['科研潜力', dim.research_potential_score ?? 0, 25],
        ['沟通能力', dim.communication_score ?? 0, 10],
      ].map(([name, value, max]) => `
        <div class="score-line">
          <div class="score-line-head"><span>${escapeHtml(name)}</span><span>${Number(value)} / ${max}</span></div>
          <div class="bar"><span style="width:${Math.max(0, Math.min(100, Number(value) / max * 100))}%;"></span></div>
        </div>
      `);
      elements.scoresArea.innerHTML = scoreItems.join('');

      const highlights = toArray(data.highlights).map(item => `
        <div class="list-item">
          <strong>${escapeHtml(text(item.point, '亮点'))}</strong>
          <p>${escapeHtml(text(item.evidence, '未找到'))}</p>
        </div>
      `);
      renderListItems(highlights, elements.highlightsArea, '暂无亮点');

      const risks = toArray(data.risks_unknowns).map(item => `
        <div class="list-item">
          <strong>${escapeHtml(text(item.point, '风险'))}</strong>
          <p>${escapeHtml(text(item.evidence, '未找到'))}</p>
        </div>
      `);
      renderListItems(risks, elements.risksArea, '暂无风险信息');

      const rationale = toArray(data.rationale).map(item => `
        <div class="list-item">
          <strong>${escapeHtml(text(item.dimension, '维度说明'))}</strong>
          <p><strong>原因：</strong>${escapeHtml(text(item.reason))}</p>
          <p><strong>证据：</strong>${escapeHtml(text(item.evidence, '未找到'))}</p>
        </div>
      `);
      renderListItems(rationale, elements.rationaleArea, '暂无评估依据');

      const questions = toArray(data.interview_questions);
      renderBadgeList(questions.length ? questions : ['暂无面试问题'], elements.questionsArea);

      elements.rawJson.value = JSON.stringify(data, null, 2);
      highlightActive(resume.file_name);
    }

    function highlightActive(fileName) {
      document.querySelectorAll('.resume-item').forEach(node => {
        node.classList.toggle('active', node.dataset.file === fileName);
      });
    }

    function renderList() {
      const query = elements.search.value.trim().toLowerCase();
      let items = state.resumes.filter(item => {
        const haystack = [item.label, item.file_name, item.summary, item.school, item.major]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return !query || haystack.includes(query);
      });

      const sortMode = elements.sort.value;
      if (sortMode === 'score-desc') {
        items = items.slice().sort((a, b) => b.score - a.score);
      } else if (sortMode === 'score-asc') {
        items = items.slice().sort((a, b) => a.score - b.score);
      }

      const total = state.resumes.length;
      const avg = total ? Math.round(state.resumes.reduce((sum, item) => sum + Number(item.score || 0), 0) / total) : 0;
      elements.totalCount.textContent = String(total);
      elements.filteredCount.textContent = String(items.length);
      elements.averageScore.textContent = String(avg);

      state.filtered = items;
      elements.resumeList.innerHTML = items.map(item => `
        <div class="resume-item ${state.selected && state.selected.file_name === item.file_name ? 'active' : ''}" data-file="${escapeHtml(item.file_name)}">
          <p class="name">${escapeHtml(item.label)}</p>
          <p class="meta">${escapeHtml(item.summary || '暂无摘要')}</p>
          <p class="meta">分数 ${item.score} · ${escapeHtml(item.decision_label)} · ${escapeHtml(item.confidence)}</p>
        </div>
      `).join('');

      elements.resumeList.querySelectorAll('.resume-item').forEach(node => {
        node.addEventListener('click', () => {
          const fileName = node.dataset.file;
          const next = state.resumes.find(item => item.file_name === fileName);
          if (next) {
            state.selected = next;
            renderSelected(next);
          }
        });
      });

      if (!items.length) {
        elements.emptyState.classList.remove('hidden');
      } else {
        elements.emptyState.classList.add('hidden');
      }
    }

    async function loadResumes() {
      const response = await fetch('/api/resumes');
      if (!response.ok) {
        throw new Error('无法获取 JSON 列表');
      }
      const payload = await response.json();
      state.resumes = payload.resumes || [];
      if (!state.resumes.length) {
        elements.emptyState.classList.remove('hidden');
        elements.heroTitle.textContent = '未找到 JSON 文件';
        elements.heroSubtitle.textContent = '请先运行数据生成脚本，确认 output/json 目录里有结果文件。';
        return;
      }
      state.selected = state.resumes[0];
      renderList();
      renderSelected(state.selected);
    }

    elements.search.addEventListener('input', renderList);
    elements.sort.addEventListener('change', renderList);

    loadResumes().catch(error => {
      elements.heroTitle.textContent = '加载失败';
      elements.heroSubtitle.textContent = error.message || String(error);
      elements.emptyState.classList.remove('hidden');
      elements.emptyState.textContent = '网页启动正常，但无法读取 JSON 数据，请检查服务端日志。';
    });
  </script>
</body>
</html>
"""


def load_json_resumes() -> list[dict]:
    resumes = []
    if not JSON_DIR.exists():
        return resumes

    for path in sorted(JSON_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue

        label = data.get("candidate_summary") or data.get("source_file") or path.stem
        source_file = data.get("source_file") or path.stem
        resumes.append(
            {
                "file_name": path.name,
                "label": label,
                "summary": data.get("candidate_summary", ""),
                "school": (data.get("education") or {}).get("school", ""),
                "major": (data.get("education") or {}).get("major", ""),
                "score": int(data.get("total_score", 0) or 0),
                "decision": data.get("decision", "need_review"),
                "decision_label": {"recommend_interview": "推荐面试", "need_review": "待复核", "not_recommended": "不推荐"}.get(data.get("decision", "need_review"), "待复核"),
                "confidence": data.get("confidence", "低"),
                "source_file": source_file,
                "data": data,
            }
        )

    return resumes


def serve_json(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


class ResumeViewerHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            content = HTML_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if path == "/api/resumes":
            serve_json(self, {"resumes": load_json_resumes()})
            return

        if path == "/api/resume":
            query = parse_qs(parsed.query)
            file_name = query.get("file", [""])[0]
            self._serve_resume_file(file_name)
            return

        if path.startswith("/api/resume/"):
            file_name = unquote(path.split("/api/resume/", 1)[1])
            self._serve_resume_file(file_name)
            return

        self.send_error(404, "Not Found")

    def _serve_resume_file(self, file_name: str) -> None:
        if not file_name:
            serve_json(self, {"error": "missing file"}, 400)
            return

        safe_name = os.path.basename(file_name)
        target = JSON_DIR / safe_name
        if not target.exists() or target.suffix.lower() != ".json":
            serve_json(self, {"error": "file not found"}, 404)
            return

        try:
            with target.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            serve_json(self, {"error": f"failed to read file: {exc}"}, 500)
            return

        serve_json(self, {"file_name": target.name, "data": data})


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}"
    server = ThreadingHTTPServer((host, port), ResumeViewerHandler)
    print(f"简历 JSON 展示页已启动：{url}")
    print(f"正在读取目录：{JSON_DIR}")

    # Delay opening slightly to avoid browser race with server readiness.
    threading.Timer(0.35, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()