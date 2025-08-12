// Settings component: lang, max_clips, clip_len, style, aspect, emojis
export default function Settings({ onChange }) {
    const lang = createInput('Язык распознавания (ru/en, опционально)', 'lang', '', 'text', 'Язык для транскрипции (например, ru или en). Оставьте пустым для автоопределения.');
    const maxClips = createInput('Максимум клипов', 'max_clips', '15', 'number', 'Сколько клипов максимум нарезать из видео.');
    const clipLen = createInput('Длина клипа (сек)', 'clip_len', '30', 'number', 'Желаемая длительность одного клипа в секундах.');
    const style = createStyleEditor();
    const aspect = createInput('Аспект (напр. 9:16)', 'aspect', '9:16', 'text', 'Соотношение сторон итогового клипа, например 9:16 или 16:9.');
    const emojis = createCheckbox('Добавлять эмодзи в субтитры', 'emojis', true, 'Включить автоматическое добавление эмодзи в субтитры.');
    const poToken = createInput('YouTube po_token', 'po_token', '', 'text', 'po_token для скачивания YouTube. Получить: https://github.com/YunzheZJU/youtube-po-token-generator');

    const container = document.createElement('div');
    container.className = 'settings-section card';
    [lang, maxClips, clipLen, style, aspect, emojis, poToken].forEach(el => container.appendChild(el));

    container.oninput = () => {
        onChange({
            lang: lang.querySelector('input')?.value || '',
            max_clips: maxClips.querySelector('input')?.value || '',
            clip_len: clipLen.querySelector('input')?.value || '',
            style: getStyleValues(style),
            aspect: aspect.querySelector('input')?.value || '',
            emojis: emojis.querySelector('input')?.checked || false,
            po_token: poToken.querySelector('input')?.value || ''
        });
    };

    container.setPresets = () => {};

    return container;
}

function createInput(label, name, value = '', type = 'text', desc = '') {
    const wrap = document.createElement('div');
    wrap.className = 'settings-field';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    lbl.htmlFor = name;
    const input = document.createElement('input');
    input.type = type;
    input.name = name;
    input.value = value;
    input.id = name;
    input.className = 'settings-input';
    if (desc) {
        const d = document.createElement('div');
        d.className = 'settings-desc';
        d.textContent = desc;
        wrap.appendChild(d);
    }
    wrap.appendChild(lbl);
    wrap.appendChild(input);
    return wrap;
}

function createCheckbox(label, name, checked = false, desc = '') {
    const wrap = document.createElement('div');
    wrap.className = 'settings-field';
    const box = document.createElement('input');
    box.type = 'checkbox';
    box.name = name;
    box.checked = checked;
    box.id = name;
    box.className = 'settings-input';
    const lbl = document.createElement('label');
    lbl.appendChild(box);
    lbl.appendChild(document.createTextNode(label));
    lbl.htmlFor = name;
    if (desc) {
        const d = document.createElement('div');
        d.className = 'settings-desc';
        d.textContent = desc;
        wrap.appendChild(d);
    }
    wrap.appendChild(lbl);
    return wrap;
}

function createStyleEditor() {
    const wrap = document.createElement('div');
    wrap.className = 'settings-field';
    const lbl = document.createElement('label');
    lbl.textContent = 'Настройки оформления';
    lbl.style.fontWeight = 'bold';
    wrap.appendChild(lbl);
    // Выпадающие списки для шрифта, стиля субтитров, палитры
    const fontField = createSelectField('Шрифт', 'font', [
        'Arial', 'Roboto', 'Impact', 'Montserrat', 'Comic Sans MS', 'Times New Roman', 'Georgia', 'Tahoma', 'Verdana'
    ], 'Arial', 'Название шрифта для субтитров.');
    const fontSizeField = createInput('Размер шрифта', 'font_size', '48', 'number', 'Размер субтитров в px.');
    const captionStyleField = createSelectField('Стиль субтитров', 'caption_style', [
        'white-outline', 'bold', 'karaoke', 'minimal', 'colorful', 'shadowed', 'high-contrast'
    ], 'white-outline', 'Вариант оформления субтитров.');
    const bgField = createInput('Цвет фона', 'background', '#000000', 'color', 'Фоновый цвет клипа.');
    const paletteField = createSelectField('Палитра', 'palette', [
        'default', 'tiktok', 'shorts', 'mrbeast', 'emoji-pop', 'minimal', 'high-contrast', 'shadowed'
    ], 'default', 'Цветовая палитра для оформления.');
    // Пример субтитра
    const prev = document.createElement('div');
    prev.className = 'style-preview';
    prev.textContent = 'Это пример субтитра!';
    prev.id = 'style-preview';
    prev.style.margin = '8px 0 0 0';
    prev.style.padding = '8px 16px';
    prev.style.background = '#222';
    prev.style.color = '#fff';
    prev.style.fontFamily = 'Arial';
    prev.style.fontSize = '48px';
    prev.style.borderRadius = '6px';
    prev.style.boxShadow = '0 1px 4px #0002';
    [fontField, fontSizeField, captionStyleField, bgField, paletteField, prev].forEach(f => {
        if (f) wrap.appendChild(f);
    });
    // Обновление превью при изменении
    wrap.oninput = () => updatePreview(wrap);
    return wrap;
}

function createSelectField(label, name, options, value, desc = '') {
    const wrap = document.createElement('div');
    wrap.className = 'settings-field';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    lbl.htmlFor = name;
    const select = document.createElement('select');
    select.name = name;
    select.id = name;
    select.className = 'settings-input';
    options.forEach(opt => {
        const o = document.createElement('option');
        o.value = opt;
        o.textContent = opt;
        if (opt === value) o.selected = true;
        select.appendChild(o);
    });
    if (desc) {
        const d = document.createElement('div');
        d.className = 'settings-desc';
        d.textContent = desc;
        wrap.appendChild(d);
    }
    wrap.appendChild(lbl);
    wrap.appendChild(select);
    return wrap;
}

function getStyleValues(styleWrap) {
    const style = {};
    styleWrap.querySelectorAll('input,select').forEach(input => {
        if (input.type === 'checkbox') style[input.name] = input.checked;
        else style[input.name] = input.value;
    });
    return style;
}

function updatePreview(wrap) {
    const prev = wrap.querySelector('#style-preview');
    if (!prev) return;
    const font = wrap.querySelector('select[name=font]')?.value || 'Arial';
    const fontSize = wrap.querySelector('input[name=font_size]')?.value || '48';
    const bg = wrap.querySelector('input[name=background]')?.value || '#000';
    prev.style.fontFamily = font;
    prev.style.fontSize = fontSize + 'px';
    prev.style.background = bg;
}
