// Jobs list component: show jobs, progress, errors
export default function JobsList({ jobs, onSelect }) {
    const container = document.createElement('div');
    container.style.margin = '16px 0';
    container.update = jobs => {
        container.innerHTML = '<b>Задачи:</b><br>';
        Object.entries(jobs).forEach(([id, job]) => {
            const div = document.createElement('div');
            div.style.margin = '4px 0';
            div.style.padding = '4px';
            div.style.border = '1px solid #ccc';
            div.style.background = job.status === 'error' ? '#ffe0e0' : (job.status === 'ready' ? '#e0ffe0' : '#f7f7f7');
            div.textContent = `${id.slice(0,8)}... | ${job.status}`;
            if (job.error) {
                div.textContent += ` | Ошибка: ${job.error}`;
            }
            div.onclick = () => onSelect && onSelect(id);
            // Прогресс по шагам
            if (job.steps && job.steps.length) {
                const ul = document.createElement('ul');
                job.steps.forEach(s => {
                    const li = document.createElement('li');
                    li.textContent = `${s.step || ''} ${s.status || ''}`;
                    // --- Новый: отображение прогресса загрузки ---
                    if (s.step === 'download' && typeof s.progress === 'number') {
                        li.textContent += ` (${s.progress}%)`;
                        // Прогресс-бар
                        const bar = document.createElement('div');
                        bar.style.height = '8px';
                        bar.style.width = '100%';
                        bar.style.background = '#eee';
                        bar.style.borderRadius = '4px';
                        bar.style.margin = '4px 0';
                        const fill = document.createElement('div');
                        fill.style.height = '8px';
                        fill.style.width = `${s.progress}%`;
                        fill.style.background = '#1976d2';
                        fill.style.borderRadius = '4px';
                        bar.appendChild(fill);
                        li.appendChild(bar);
                    }
                    ul.appendChild(li);
                });
                div.appendChild(ul);
            }
            container.appendChild(div);
        });
    };
    container.update(jobs);
    return container;
}
