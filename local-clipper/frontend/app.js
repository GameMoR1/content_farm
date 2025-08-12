// Vanilla JS: fetch API, polling, segment display, render requests, meta generation
// TODO: implement uploader, link-input, settings, jobs-list, preview, clip-editor

import LinkInput from './components/link-input.js';
import Uploader from './components/uploader.js';
import Settings from './components/settings.js';
import JobsList from './components/jobs-list.js';
import Preview from './components/preview.js';
import ClipEditor from './components/clip-editor.js';

const app = document.getElementById('app');
const uiSections = document.getElementById('ui-sections');

// --- UI секции с описанием ---
function section(title, desc, node) {
    const s = document.createElement('div');
    s.className = 'section card';
    const h = document.createElement('div');
    h.className = 'section-title';
    h.textContent = title;
    const d = document.createElement('div');
    d.className = 'section-desc';
    d.innerHTML = desc;
    s.appendChild(h);
    s.appendChild(d);
    if (node) s.appendChild(node);
    return s;
}

// State
let jobs = {};
let presets = {};

// UI Elements
const linkInput = LinkInput({ onSubmit: handleUrl });
const uploader = Uploader({ onUpload: handleFile });
const settings = Settings({ onChange: handleSettings });
const jobsList = JobsList({ jobs, onSelect: handleJobSelect });
const preview = Preview();
const clipEditor = ClipEditor();

uiSections.appendChild(section(
    '1. Загрузка видео',
    'Вставьте ссылку на YouTube или загрузите свой файл. <br><i>Поддерживаются только публичные ролики YouTube и локальные видеофайлы.</i>',
    (() => { const c = document.createElement('div'); c.appendChild(linkInput); c.appendChild(uploader); return c; })()
));
uiSections.appendChild(section(
    '2. Настройки',
    'Выберите язык, стиль, длительность клипов и другие параметры.',
    settings
));
uiSections.appendChild(section(
    '3. Очередь задач',
    'Здесь отображаются все ваши задачи, их статус и прогресс обработки.',
    jobsList
));
uiSections.appendChild(section(
    '4. Предпросмотр клипов',
    'Автоматически найденные лучшие моменты. Можно просмотреть и выбрать для рендера.',
    preview
));
uiSections.appendChild(section(
    '5. Редактор и рендер',
    'Выберите сегменты, сгенерируйте мету, запустите рендер. Готовые клипы появятся в папке <b>media/outputs</b>.',
    clipEditor
));

let currentSettings = {}

// --- Сохранение po_token в localStorage ---
function handleSettings(newSettings) {
    if (newSettings.po_token !== undefined) {
        if (newSettings.po_token) {
            localStorage.setItem('po_token', newSettings.po_token);
        } else {
            localStorage.removeItem('po_token');
        }
    }
    currentSettings = newSettings;
}

// При инициализации — подставить po_token из localStorage
if (localStorage.getItem('po_token')) {
    currentSettings.po_token = localStorage.getItem('po_token');
    // Автоматически заполнить поле в UI
    setTimeout(() => {
        const poInput = document.querySelector('input[name=po_token]');
        if (poInput) poInput.value = currentSettings.po_token;
    }, 0);
}

async function handleUrl(url) {
    const body = { url, ...currentSettings };
    const res = await fetch('/api/job/from_url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await res.json();
    addJob(data.job_id);
}

async function handleFile(file) {
    const form = new FormData();
    form.append('file', file);
    for (const k in currentSettings) {
        form.append(k, currentSettings[k]);
    }
    const res = await fetch('/api/job/from_file', {
        method: 'POST',
        body: form
    });
    const data = await res.json();
    addJob(data.job_id);
}

function addJob(job_id) {
    jobs[job_id] = { status: 'queued', steps: [] };
    updateJobsList();
    pollJob(job_id);
}

function updateJobsList() {
    jobsList.update(jobs);
}

async function pollJob(job_id) {
    let done = false;
    while (!done) {
        const res = await fetch(`/api/job/${job_id}`);
        const data = await res.json();
        jobs[job_id] = data;
        updateJobsList();
        if (data.status === 'ready' || data.status === 'error') done = true;
        await new Promise(r => setTimeout(r, 2000));
    }
    if (jobs[job_id].status === 'ready') {
        // Автозагрузка сегментов и предпросмотра
        // Новый: получаем highlights через API
        const highlightsRes = await fetch(`/api/job/${job_id}/highlights`);
        const highlights = await highlightsRes.json();
        preview.show(job_id, highlights);
        clipEditor.show(job_id, highlights);
    }
}

function handleJobSelect(job_id) {
    // При выборе задачи показываем предпросмотр и редактор для выбранного job_id
    fetch(`/api/job/${job_id}/highlights`).then(r => r.json()).then(highlights => {
        preview.show(job_id, highlights);
        clipEditor.show(job_id, highlights);
    });
}

// Инициализация пресетов
(async function loadPresets() {
    const res = await fetch('/api/presets');
    presets = await res.json();
    settings.setPresets(presets);
})();
