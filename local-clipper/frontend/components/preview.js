// Preview component: segment preview, thumbnails, gif
export default function Preview() {
    const container = document.createElement('div');
    container.style.margin = '16px 0';
    container.style.display = 'flex';
    container.style.flexWrap = 'wrap';
    container.style.gap = '12px';
    container.style.background = '#fff';
    container.style.borderRadius = '12px';
    container.style.boxShadow = '0 2px 8px #0001';
    container.style.padding = '16px';
    container.style.minHeight = '120px';
    container.show = async function(job_id, highlights) {
        container.innerHTML = `<b style='font-size:1.1em'>Предпросмотр клипов:</b><br>`;
        if (!highlights || !highlights.length) {
            container.innerHTML += '<i>Нет найденных сегментов</i>';
            return;
        }
        highlights.forEach(seg => {
            const card = document.createElement('div');
            card.style.display = 'flex';
            card.style.flexDirection = 'column';
            card.style.alignItems = 'center';
            card.style.background = '#f9f9f9';
            card.style.borderRadius = '8px';
            card.style.padding = '8px';
            card.style.boxShadow = '0 1px 4px #0001';
            card.style.width = '170px';
            card.style.margin = '0 4px';
            const img = document.createElement('img');
            img.src = `/media/work/${job_id}/${seg.id}_preview.jpg`;
            img.style.width = '160px';
            img.style.borderRadius = '6px';
            img.style.marginBottom = '6px';
            img.title = `${seg.start.toFixed(1)}–${seg.end.toFixed(1)}s`;
            card.appendChild(img);
            const meta = document.createElement('div');
            meta.style.fontSize = '0.95em';
            meta.style.color = '#444';
            meta.innerHTML = `<b>${seg.id}</b><br>${seg.start.toFixed(1)}–${seg.end.toFixed(1)}s<br>score: ${seg.score ? seg.score.toFixed(2) : ''}`;
            card.appendChild(meta);
            container.appendChild(card);
        });
    };
    return container;
}
