import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT_DIR = Path(__file__).resolve().parent
JSON_DIR = ROOT_DIR / "output" / "json"


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>简历 JSON 展示页</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111f;
      --bg-2: #0b1b32;
      --panel: rgba(12, 24, 44, 0.82);
      --panel-strong: rgba(17, 31, 58, 0.96);
      --border: rgba(151, 174, 216, 0.18);
      --text: #ecf4ff;
      --muted: #9db0d1;
      --accent: #7dd3fc;
      --accent-2: #a78bfa;
      --good: #34d399;
      --warn: #fbbf24;
      --bad: #fb7185;
      --shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(125, 211, 252, 0.18), transparent 34%),
        radial-gradient(circle at 80% 10%, rgba(167, 139, 250, 0.16), transparent 28%),
        linear-gradient(180deg, var(--bg), var(--bg-2));
      color: var(--text);
      min-height: 100vh;
    }

    .app {
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: 100vh;
    }

    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 24px;
      border-right: 1px solid var(--border);
      background: rgba(5, 12, 23, 0.72);
      backdrop-filter: blur(16px);
    }

    .brand {
      padding: 18px;
      border: 1px solid var(--border);
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(125, 211, 252, 0.12), rgba(167, 139, 250, 0.12));
      box-shadow: var(--shadow);
      margin-bottom: 18px;
    }

    .brand h1 {
      margin: 0 0 8px;
      font-size: 22px;
      line-height: 1.2;
    }

    .brand p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    .sidebar-tools {
      display: grid;
      gap: 12px;
      margin-bottom: 18px;
    }

    .search-box,
    .select-box {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.04);
      color: var(--text);
      padding: 12px 14px;
      outline: none;
    }

    .resume-list {
      display: grid;
      gap: 10px;
    }

    .resume-item {
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.04);
      cursor: pointer;
      transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }

    .resume-item:hover {
      transform: translateY(-1px);
      border-color: rgba(125, 211, 252, 0.42);
      background: rgba(125, 211, 252, 0.08);
    }

    .resume-item.active {
      border-color: rgba(125, 211, 252, 0.65);
      background: linear-gradient(135deg, rgba(125, 211, 252, 0.15), rgba(167, 139, 250, 0.14));
      box-shadow: 0 0 0 1px rgba(125, 211, 252, 0.14) inset;
    }

    .resume-item .name {
      margin: 0 0 6px;
      font-weight: 700;
      font-size: 15px;
    }

    .resume-item .meta {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }

    .main {
      padding: 28px;
    }

    .hero {
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1fr) 300px;
      margin-bottom: 22px;
      animation: fadeUp 0.5s ease both;
    }

    .hero-panel,
    .card {
      border: 1px solid var(--border);
      border-radius: 24px;
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
    }

    .hero-panel {
      padding: 24px;
    }

    .hero-title {
      margin: 0 0 10px;
      font-size: 30px;
      line-height: 1.15;
    }

    .hero-subtitle {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      max-width: 64ch;
    }

    .hero-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--text);
      font-size: 13px;
    }

    .score-panel {
      padding: 24px;
      display: grid;
      gap: 16px;
      align-content: start;
    }

    .score-ring {
      width: 180px;
      height: 180px;
      margin: 0 auto;
      border-radius: 50%;
      background: conic-gradient(var(--accent) 0deg, var(--accent-2) 180deg, rgba(255,255,255,0.1) 180deg 360deg);
      display: grid;
      place-items: center;
      position: relative;
    }

    .score-ring::after {
      content: "";
      position: absolute;
      inset: 14px;
      border-radius: 50%;
      background: linear-gradient(180deg, rgba(7, 17, 31, 0.98), rgba(12, 24, 44, 0.98));
      border: 1px solid var(--border);
    }

    .score-inner {
      position: relative;
      z-index: 1;
      text-align: center;
    }

    .score-number {
      display: block;
      font-size: 48px;
      font-weight: 800;
      letter-spacing: -0.05em;
      line-height: 1;
    }

    .score-label {
      display: block;
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }

    .score-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .stat {
      padding: 12px;
      border-radius: 16px;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
    }

    .stat .k {
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }

    .stat .v {
      font-size: 18px;
      font-weight: 700;
    }

    .content-grid {
      display: grid;
      gap: 18px;
      grid-template-columns: repeat(12, minmax(0, 1fr));
    }

    .card {
      padding: 20px;
    }

    .span-12 { grid-column: span 12; }
    .span-8 { grid-column: span 8; }
    .span-6 { grid-column: span 6; }
    .span-4 { grid-column: span 4; }

    .card h2 {
      margin: 0 0 14px;
      font-size: 18px;
    }

    .section-meta {
      margin-top: -8px;
      margin-bottom: 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    .definition-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .definition-item,
    .list-item {
      padding: 14px;
      border-radius: 16px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.07);
    }

    .definition-item .label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }

    .definition-item .value {
      font-size: 15px;
      line-height: 1.7;
      word-break: break-word;
    }

    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(125, 211, 252, 0.1);
      border: 1px solid rgba(125, 211, 252, 0.18);
      color: var(--text);
      font-size: 13px;
    }

    .list-stack {
      display: grid;
      gap: 12px;
    }

    .list-item {
      display: grid;
      gap: 8px;
    }

    .list-item strong {
      font-size: 15px;
    }

    .list-item p {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      word-break: break-word;
    }

    .score-row {
      display: grid;
      gap: 12px;
    }

    .score-line {
      display: grid;
      gap: 6px;
    }

    .score-line-head {
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 12px;
    }

    .bar {
      height: 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.07);
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.06);
    }

    .bar > span {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
    }

    .raw-json {
      width: 100%;
      min-height: 340px;
      resize: vertical;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.28);
      color: #dceaff;
      padding: 16px;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre;
    }

    .empty {
      padding: 32px;
      border: 1px dashed var(--border);
      border-radius: 24px;
      color: var(--muted);
      text-align: center;
      background: rgba(255,255,255,0.03);
    }

    .hidden { display: none !important; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 1100px) {
      .app { grid-template-columns: 1fr; }
      .sidebar {
        position: relative;
        height: auto;
        border-right: none;
        border-bottom: 1px solid var(--border);
      }
      .hero { grid-template-columns: 1fr; }
      .span-8, .span-6, .span-4 { grid-column: span 12; }
    }

    @media (max-width: 720px) {
      .main { padding: 16px; }
      .sidebar { padding: 16px; }
      .definition-grid { grid-template-columns: 1fr; }
      .score-stats { grid-template-columns: 1fr; }
      .hero-title { font-size: 24px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <h1>简历 JSON 展示页</h1>
        <p>自动读取 output/json 目录下的文件。点击左侧条目即可查看对应简历的结构化结果。</p>
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
      <section class="hero">
        <div class="hero-panel">
          <h2 id="heroTitle" class="hero-title">正在加载简历数据</h2>
          <p id="heroSubtitle" class="hero-subtitle">页面会把 JSON 内容拆成摘要、分数、技能、经历和风险等模块展示，便于快速浏览与对比。</p>
          <div id="heroBadges" class="hero-badges"></div>
        </div>

        <div class="hero-panel score-panel">
          <div class="score-ring">
            <div class="score-inner">
              <span id="scoreNumber" class="score-number">--</span>
              <span class="score-label">综合评分</span>
            </div>
          </div>
          <div class="score-stats">
            <div class="stat"><span class="k">判断</span><span id="decisionValue" class="v">--</span></div>
            <div class="stat"><span class="k">置信度</span><span id="confidenceValue" class="v">--</span></div>
            <div class="stat"><span class="k">模型</span><span id="modelValue" class="v">--</span></div>
            <div class="stat"><span class="k">PII</span><span id="piiValue" class="v">--</span></div>
          </div>
        </div>
      </section>

      <section class="content-grid">
        <article class="card span-12">
          <h2>候选人概览</h2>
          <p id="summaryText" class="section-meta"></p>
          <div id="overviewGrid" class="definition-grid"></div>
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
          <h2>分项评分</h2>
          <div id="scoresArea" class="score-row"></div>
        </article>

        <article class="card span-6">
          <h2>亮点</h2>
          <div id="highlightsArea" class="list-stack"></div>
        </article>

        <article class="card span-6">
          <h2>风险与未知</h2>
          <div id="risksArea" class="list-stack"></div>
        </article>

        <article class="card span-12">
          <h2>评估依据</h2>
          <div id="rationaleArea" class="list-stack"></div>
        </article>

        <article class="card span-12">
          <h2>面试问题</h2>
          <div id="questionsArea" class="chips"></div>
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
    server = ThreadingHTTPServer((host, port), ResumeViewerHandler)
    print(f"简历 JSON 展示页已启动：http://{host}:{port}")
    print(f"正在读取目录：{JSON_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()