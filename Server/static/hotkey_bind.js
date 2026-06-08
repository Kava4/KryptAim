(function () {
    const MODIFIER_ONLY = new Set(['Control', 'Alt', 'Shift', 'Meta']);
    const MOUSE_BUTTONS = { 0: 'LMB', 1: 'MMB', 2: 'RMB', 3: 'M4', 4: 'M5' };

    function codeToToken(code, key) {
        if (key === 'Alt') return 'alt';
        if (key === 'Control') return 'ctrl';
        if (key === 'Shift') return 'shift';
        if (key === ' ') return 'space';
        if (key === 'Escape') return 'esc';
        if (key === 'Enter') return 'enter';
        if (key === 'Tab') return 'tab';
        if (key === 'Delete') return 'delete';
        if (key === 'Insert') return 'insert';
        if (key === 'Home') return 'home';
        if (key === 'End') return 'end';
        if (key === 'PageUp') return 'pageup';
        if (key === 'PageDown') return 'pagedown';
        if (key.startsWith('Arrow')) return key.slice(5).toLowerCase();
        if (/^F\d+$/.test(key)) return key.toLowerCase();
        if (code && code.startsWith('Key')) return code.slice(3).toLowerCase();
        if (code && code.startsWith('Digit')) return code.slice(5);
        if (code && code.startsWith('Numpad')) return code.slice(6).toLowerCase();
        return null;
    }

    function formatHotkeyLabel(value) {
        const raw = (value || 'None').trim();
        if (!raw || raw.toLowerCase() === 'none') return 'None';
        return raw.split('+').map(part => {
            const token = part.trim();
            if (!token) return '';
            if (token === 'ctrl') return 'Ctrl';
            if (token === 'alt') return 'Alt';
            if (token === 'shift') return 'Shift';
            if (['LMB', 'RMB', 'MMB', 'M4', 'M5'].includes(token.toUpperCase())) return token.toUpperCase();
            if (/^f\d+$/i.test(token)) return token.toUpperCase();
            if (token.length === 1) return token.toUpperCase();
            return token.charAt(0).toUpperCase() + token.slice(1);
        }).filter(Boolean).join(' + ');
    }

    function eventToHotkeyString(event) {
        if (event.type === 'mousedown') {
            return MOUSE_BUTTONS[event.button] || null;
        }
        if (MODIFIER_ONLY.has(event.key)) return null;
        const parts = [];
        if (event.ctrlKey) parts.push('ctrl');
        if (event.altKey) parts.push('alt');
        if (event.shiftKey) parts.push('shift');
        const primary = codeToToken(event.code, event.key);
        if (!primary) return null;
        parts.push(primary);
        return parts.join('+');
    }

    let activeBtn = null;

    async function setHotkeyBindingActive(active) {
        try {
            await fetch('/api/recoil/hotkey-binding', {
                method: 'POST',
                body: new URLSearchParams({ active: active ? 'on' : 'off' }),
            });
        } catch (_) {
            /* non-fatal; recoil loop may still see a stray edge */
        }
    }

    function stopCapture() {
        if (activeBtn) {
            activeBtn.classList.remove('ring-2', 'ring-amber-400/60', 'border-amber-400/50');
            const label = activeBtn.querySelector('.hotkey-bind-label');
            if (label) label.textContent = formatHotkeyLabel(activeBtn.dataset.hotkeyValue || 'None');
            if (typeof activeBtn._hkCleanup === 'function') activeBtn._hkCleanup();
            activeBtn._hkCleanup = null;
            activeBtn = null;
        }
        void setHotkeyBindingActive(false);
    }

    function startCapture(btn, callback) {
        stopCapture();
        void setHotkeyBindingActive(true);
        activeBtn = btn;
        btn.classList.add('ring-2', 'ring-amber-400/60', 'border-amber-400/50');
        const label = btn.querySelector('.hotkey-bind-label');
        if (label) label.textContent = 'Press any key…';

        function onKeyDown(e) {
            if (e.key === 'Escape') {
                stopCapture();
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            const hotkey = eventToHotkeyString(e);
            if (hotkey) callback(hotkey);
        }

        function onMouseDown(e) {
            if (e.button > 4) return;
            e.preventDefault();
            e.stopPropagation();
            const hotkey = eventToHotkeyString(e);
            if (hotkey) callback(hotkey);
        }

        window.addEventListener('keydown', onKeyDown, true);
        window.addEventListener('mousedown', onMouseDown, true);
        btn._hkCleanup = () => {
            window.removeEventListener('keydown', onKeyDown, true);
            window.removeEventListener('mousedown', onMouseDown, true);
        };
    }

    async function saveHotkeyField(field, value) {
        const body = new FormData();
        body.append('field', field);
        body.append('value', value || 'None');
        const response = await fetch('/api/recoil/hotkey', { method: 'POST', body });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.message || 'Failed to save hotkey.');
        }
        return data;
    }

    function setButtonValue(btn, value) {
        btn.dataset.hotkeyValue = value;
        const label = btn.querySelector('.hotkey-bind-label');
        if (label) label.textContent = formatHotkeyLabel(value);
    }

    function showError(btn, message) {
        const errorEl = btn.closest('[data-hotkey-row]')?.querySelector('.hotkey-bind-error')
            || btn.parentElement?.querySelector('.hotkey-bind-error');
        if (!errorEl) return;
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
        setTimeout(() => errorEl.classList.add('hidden'), 4000);
    }

    function initHotkeyButtons(root) {
        (root || document).querySelectorAll('[data-hotkey-field]').forEach(btn => {
            if (btn.dataset.hotkeyInit === '1') return;
            btn.dataset.hotkeyInit = '1';
            setButtonValue(btn, btn.dataset.hotkeyValue || 'None');

            btn.addEventListener('click', () => {
                startCapture(btn, async (value) => {
                    stopCapture();
                    const field = btn.dataset.hotkeyField;
                    try {
                        const data = await saveHotkeyField(field, value);
                        setButtonValue(btn, data.value);
                        document.dispatchEvent(new CustomEvent('hotkey:saved', { detail: data }));
                    } catch (error) {
                        showError(btn, error.message);
                        setButtonValue(btn, btn.dataset.hotkeyValue || 'None');
                    }
                });
            });
        });

        (root || document).querySelectorAll('[data-hotkey-clear]').forEach(link => {
            if (link.dataset.hotkeyInit === '1') return;
            link.dataset.hotkeyInit = '1';
            link.addEventListener('click', async (event) => {
                event.preventDefault();
                const targetId = link.dataset.hotkeyClear;
                const btn = document.getElementById(targetId);
                if (!btn) return;
                try {
                    const data = await saveHotkeyField(btn.dataset.hotkeyField, 'None');
                    setButtonValue(btn, data.value);
                    document.dispatchEvent(new CustomEvent('hotkey:saved', { detail: data }));
                } catch (error) {
                    showError(btn, error.message);
                }
            });
        });
    }

    window.HotkeyBind = {
        init: initHotkeyButtons,
        format: formatHotkeyLabel,
        save: saveHotkeyField,
        stop: stopCapture,
    };

    document.addEventListener('DOMContentLoaded', () => initHotkeyButtons());
})();
