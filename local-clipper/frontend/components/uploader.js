// Uploader component: file input, drag-n-drop, progress

export default function Uploader({ onUpload }) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*';
    input.style.display = 'none';

    const label = document.createElement('label');
    label.textContent = 'Загрузить видео';
    label.style.display = 'inline-block';
    label.style.padding = '8px 16px';
    label.style.background = '#eee';
    label.style.cursor = 'pointer';
    label.onclick = () => input.click();

    input.onchange = () => {
        if (input.files.length > 0) {
            onUpload(input.files[0]);
        }
    };

    // Drag-n-drop
    label.ondragover = e => { e.preventDefault(); label.style.background = '#ddd'; };
    label.ondragleave = e => { e.preventDefault(); label.style.background = '#eee'; };
    label.ondrop = e => {
        e.preventDefault();
        label.style.background = '#eee';
        if (e.dataTransfer.files.length > 0) {
            onUpload(e.dataTransfer.files[0]);
        }
    };

    const container = document.createElement('div');
    container.appendChild(label);
    container.appendChild(input);
    return container;
}
