// Im using JavaScript instead of a form to avoid page reloads and to provide a smoother user experience when managing recoil patterns.

async function savePattern() {
    const name = document.getElementById('save-pattern-name').value.trim();
    const pattern = document.getElementById('pattern-textarea').value;
    if (!name) return;
    const form = new FormData();
    form.append('pattern_name', name);
    form.append('advanced_pattern', pattern);

    const response = await fetch('/api/recoil/pattern/save', { method: 'POST', body: form });
    if (response.ok) {
        const html = await response.text();
        document.getElementById('pattern-select').innerHTML = html;
        document.getElementById('save-pattern-name').value = '';
    }
}

async function loadPattern() {
    const name = document.getElementById('pattern-select').value;
    if (!name) return;
    const form = new FormData();
    form.append('pattern_name', name);

    const response = await fetch('/api/recoil/pattern/load', { method: 'POST', body: form });
    if (response.ok) {
        const text = await response.text();
        document.getElementById('pattern-textarea').value = text;
        // Refresh visualizer if it exists
        if (window.visRefresh) window.visRefresh('advanced');
    }
}

async function deletePattern() {
    const name = document.getElementById('pattern-select').value;
    if (!name) return;
    const form = new FormData();
    form.append('pattern_name', name);

    const response = await fetch('/api/recoil/pattern/delete', { method: 'POST', body: form });
    if (response.ok) {
        const html = await response.text();
        document.getElementById('pattern-select').innerHTML = html;
        document.getElementById('pattern-textarea').value = '';
    }
}