// Link input component: YouTube URL, validation

export default function LinkInput({ onSubmit }) {
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'YouTube URL';
    input.style.width = '80%';
    input.style.marginRight = '8px';

    const button = document.createElement('button');
    button.textContent = 'Добавить';
    button.onclick = () => {
        const url = input.value.trim();
        if (!validateYouTubeUrl(url)) {
            alert('Некорректная ссылка на YouTube');
            return;
        }
        onSubmit(url);
        input.value = '';
    };

    const container = document.createElement('div');
    container.appendChild(input);
    container.appendChild(button);
    return container;
}

function validateYouTubeUrl(url) {
    return /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/.test(url);
}
