// Clip editor component: select segments, style, overlays
export default function ClipEditor() {
    const container = document.createElement('div');
    container.style.margin = '16px 0';
    container.style.background = '#fff';
    container.style.borderRadius = '12px';
    container.style.boxShadow = '0 2px 8px #0001';
    container.style.padding = '16px';
    container.style.minHeight = '120px';
    container.show = function(job_id, highlights) {
        container.innerHTML = '<b style="font-size:1.1em">Редактор клипов:</b><br>';
        if (!highlights || !highlights.length) {
            container.innerHTML += '<i>Нет найденных сегментов</i>';
            return;
        }
        highlights.forEach(seg => {
            const div = document.createElement('div');
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.margin = '8px 0';
            div.style.background = '#f9f9f9';
            div.style.borderRadius = '8px';
            div.style.padding = '8px';
            div.style.boxShadow = '0 1px 4px #0001';
            const chk = document.createElement('input');
            chk.type = 'checkbox';
            chk.checked = true;
            chk.style.marginRight = '8px';
            div.appendChild(chk);
            div.appendChild(document.createTextNode(` ${seg.id} | ${seg.start.toFixed(1)}–${seg.end.toFixed(1)}s | score: ${seg.score ? seg.score.toFixed(2) : ''}`));
            const metaBtn = document.createElement('button');
            metaBtn.textContent = 'Генерировать мету';
            metaBtn.style.marginLeft = '12px';
            metaBtn.onclick = async () => {
                metaBtn.disabled = true;
                const res = await fetch(`/api/job/${job_id}/meta/${seg.id}`, { method: 'POST' });
                const data = await res.json();
                alert(`Title: ${data.titles?.[0] || ''}\nHook: ${data.hooks?.[0] || ''}\n#${data.hashtags?.join(' #')}`);
                metaBtn.disabled = false;
            };
            div.appendChild(metaBtn);
            container.appendChild(div);
        });
        // Кнопка рендера
        const renderBtn = document.createElement('button');
        renderBtn.textContent = 'Рендер выбранные';
        renderBtn.style.marginTop = '16px';
        renderBtn.style.fontWeight = 'bold';
        renderBtn.style.background = '#4caf50';
        renderBtn.style.color = '#fff';
        renderBtn.style.border = 'none';
        renderBtn.style.borderRadius = '6px';
        renderBtn.style.padding = '10px 24px';
        renderBtn.style.fontSize = '1.1em';
        renderBtn.style.cursor = 'pointer';
        renderBtn.onclick = async () => {
            renderBtn.disabled = true;
            // Собрать выбранные сегменты
            const segs = [];
            container.querySelectorAll('input[type=checkbox]').forEach((chk, i) => {
                if (chk.checked) segs.push(highlights[i]);
            });
            const res = await fetch(`/api/job/${job_id}/render`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ segments: segs, resolution: 720, format: 'mp4' })
            });
            const data = await res.json();
            alert('Рендер запущен!');
            renderBtn.disabled = false;
        };
        container.appendChild(renderBtn);
    };
    return container;
}
