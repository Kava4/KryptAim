/** Shared header shell — modals, mobile menu, quit (index + projects). */
(function (global) {
    'use strict';

    const cfg = () => global.KRYPTAIM_SHELL || global.AIMSYNC_SHELL || { localIp: '127.0.0.1', port: 5000 };
    const FEEDBACK_COOLDOWN_MS = 5 * 60 * 1000;
    let activeSupportProvider = '';

    function cooldownRemaining(key) {
        const last = Number(global.localStorage?.getItem(key) || 0);
        if (!last) return 0;
        return Math.max(0, FEEDBACK_COOLDOWN_MS - (Date.now() - last));
    }

    function enforceCooldown(key, label) {
        const remaining = cooldownRemaining(key);
        if (!remaining) return true;
        alert(`Please wait ${Math.ceil(remaining / 60000)} minute(s) before sending another ${label}.`);
        return false;
    }

    function markCooldown(key) {
        try {
            global.localStorage.setItem(key, String(Date.now()));
        } catch (_err) {
            /* ignore */
        }
    }

    function postForm(url, fields) {
        const fd = new FormData();
        Object.entries(fields).forEach(([key, value]) => fd.append(key, value));
        return fetch(url, { method: 'POST', body: fd }).then(async (response) => {
            const data = await response.json().catch(() => ({}));
            if (!response.ok || data.success === false) {
                throw new Error(data.message || data.error || 'Request failed');
            }
            return data;
        });
    }

    function toggleMobileMenu(forceClose) {
        const drawer = document.getElementById('mobile-menu-drawer');
        const overlay = document.getElementById('mobile-menu-overlay');
        if (!drawer || !overlay) return;

        const opening = forceClose === true
            ? false
            : drawer.classList.contains('translate-x-full');

        if (opening) {
            overlay.classList.remove('hidden');
            setTimeout(() => {
                overlay.classList.add('opacity-100');
                drawer.classList.remove('translate-x-full');
            }, 10);
            return;
        }

        overlay.classList.remove('opacity-100');
        drawer.classList.add('translate-x-full');
        setTimeout(() => overlay.classList.add('hidden'), 300);
    }

    function toggleQRModal() {
        const modal = document.getElementById('qr-modal');
        const container = document.getElementById('qrcode-container');
        if (!modal || !container) return;

        if (modal.classList.contains('hidden')) {
            if (typeof global.QRCode === 'undefined') {
                alert('QR library not loaded.');
                return;
            }
            modal.classList.remove('hidden');
            container.innerHTML = '';
            const shell = cfg();
            const url = `http://${shell.localIp}:${shell.port || 5000}`;
            new global.QRCode(container, {
                text: url,
                width: 200,
                height: 200,
                colorDark: '#171717',
                colorLight: '#ffffff',
                correctLevel: global.QRCode.CorrectLevel.H,
            });
        } else {
            modal.classList.add('hidden');
        }
    }

    function toggleFeedbackModal() {
        document.getElementById('feedback-modal')?.classList.toggle('hidden');
    }

    function toggleSupportDropdown() {
        const menu = document.getElementById('support-dropdown');
        const arrow = document.getElementById('support-arrow');
        if (!menu) return;
        const open = menu.classList.contains('hidden');
        menu.classList.toggle('hidden', !open);
        if (arrow) arrow.style.transform = open ? 'rotate(180deg)' : 'rotate(0deg)';
    }

    function sendFeedback(event) {
        const message = document.getElementById('feedback-message-input')?.value || '';
        const contact = document.getElementById('contact-info-input')?.value || '';
        const bugType = document.getElementById('feedback-type-input')?.value || '';
        if (!message.trim()) {
            alert('Please enter a message.');
            return;
        }
        if (!enforceCooldown('lastFeedbackSubmission', 'feedback')) return;

        const btn = event.currentTarget;
        btn.disabled = true;
        postForm('/api/feedback', {
            feedback_message: message,
            contact_info: contact,
            bug_type: bugType,
        })
            .then(() => {
                alert('Thank you! Your feedback was sent to Discord.');
                markCooldown('lastFeedbackSubmission');
                toggleFeedbackModal();
                const msg = document.getElementById('feedback-message-input');
                if (msg) msg.value = '';
            })
            .catch((err) => alert(err.message || 'Could not send feedback.'))
            .finally(() => { btn.disabled = false; });
    }

    function openSupportCodeModal(provider) {
        activeSupportProvider = provider;
        const modal = document.getElementById('support-code-modal');
        const title = document.getElementById('support-code-title');
        const hint = document.getElementById('support-code-hint');
        const input = document.getElementById('support-code-input');
        const contact = document.getElementById('support-code-contact-input');
        const labels = {
            giftmecrypto: 'GiftMeCrypto',
            paysafe: 'Paysafe',
        };
        const label = labels[provider] || 'Support';
        if (title) title.textContent = `Submit ${label} code`;
        if (hint) hint.textContent = `Paste your ${label} code below — we will receive it on Discord for manual verification.`;
        if (input) input.value = '';
        if (contact) contact.value = '';
        modal?.classList.remove('hidden');
        document.getElementById('support-dropdown')?.classList.add('hidden');
        const arrow = document.getElementById('support-arrow');
        if (arrow) arrow.style.transform = 'rotate(0deg)';
        setTimeout(() => input?.focus(), 50);
    }

    function closeSupportCodeModal() {
        document.getElementById('support-code-modal')?.classList.add('hidden');
        activeSupportProvider = '';
    }

    function sendSupportCode(event) {
        const code = document.getElementById('support-code-input')?.value || '';
        const contact = document.getElementById('support-code-contact-input')?.value || '';
        if (!code.trim()) {
            alert('Enter your code first.');
            return;
        }
        if (!activeSupportProvider) return;
        const cooldownKey = `lastSupportCode_${activeSupportProvider}`;
        if (!enforceCooldown(cooldownKey, 'code')) return;

        const btn = event.currentTarget;
        btn.disabled = true;
        postForm('/api/support/code', {
            provider: activeSupportProvider,
            code,
            contact_info: contact,
        })
            .then(() => {
                alert('Code sent — thank you!');
                markCooldown(cooldownKey);
                closeSupportCodeModal();
            })
            .catch((err) => alert(err.message || 'Could not send code.'))
            .finally(() => { btn.disabled = false; });
    }

    function openStopAppModal() {
        const note = document.getElementById('stop-app-shutdown-note');
        const willShutdownPC = document.querySelector('[name="shutdown_on_app_stop"]')?.checked;
        if (note) note.classList.toggle('hidden', !willShutdownPC);
        toggleMobileMenu(true);
        document.getElementById('stop-app-modal')?.classList.remove('hidden');
    }

    function closeStopAppModal() {
        document.getElementById('stop-app-modal')?.classList.add('hidden');
    }

    function showStoppedScreen(willShutdownPC) {
        const closeDelayMs = 3500;
        const logoUrl = cfg().logoUrl || '/static/KryptAim_logo.png';
        document.body.innerHTML = `
            <div class="min-h-screen bg-neutral-950 flex items-center justify-center text-center p-6">
                <div class="flex flex-col items-center gap-4 max-w-sm">
                    <img src="${logoUrl}" alt="KryptAim" class="h-36 md:h-44 w-auto max-w-[320px] object-contain mb-2 opacity-95">
                    <h1 class="text-2xl font-bold text-white mb-2">KryptAim Stopped</h1>
                    <p class="text-white/40 text-sm">The hardware connection has been released.</p>
                    ${willShutdownPC
                        ? '<p class="text-white/60 text-sm mt-2 font-semibold">System shutdown initiated...</p>'
                        : `<p id="stop-close-countdown" class="text-white/30 text-xs mt-3">Closing window in 4s…</p>`}
                </div>
            </div>
        `;

        if (willShutdownPC) return;

        let secondsLeft = 4;
        const countdownEl = document.getElementById('stop-close-countdown');
        const tick = global.setInterval(() => {
            secondsLeft -= 1;
            if (countdownEl && secondsLeft > 0) {
                countdownEl.textContent = `Closing window in ${secondsLeft}s…`;
            }
        }, 1000);

        global.setTimeout(() => {
            global.clearInterval(tick);
            try { global.close(); } catch (_err) { /* ignore */ }
            if (countdownEl) {
                countdownEl.textContent = 'You can close this tab manually.';
            }
        }, closeDelayMs);
    }

    function confirmStopApplication() {
        const btn = document.getElementById('stop-app-confirm-btn');
        const willShutdownPC = document.querySelector('[name="shutdown_on_app_stop"]')?.checked;
        closeStopAppModal();
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Stopping…';
        }
        fetch('/api/quit', { method: 'POST' })
            .finally(() => showStoppedScreen(!!willShutdownPC));
    }

    function quitApplication() {
        openStopAppModal();
    }

    function navigateToTab(tab) {
        const onDashboard = window.location.pathname === '/' || window.location.pathname === '';
        if (!onDashboard) {
            window.location.href = `/?tab=${encodeURIComponent(tab)}`;
            return;
        }
        document.querySelector(`.tab-button[data-tab="${tab}"]`)?.click();
        toggleMobileMenu(true);
    }

    function bindSupportClickAway() {
        global.addEventListener('click', (e) => {
            const container = document.getElementById('support-dropdown-container');
            if (container && !container.contains(e.target)) {
                document.getElementById('support-dropdown')?.classList.add('hidden');
                const arrow = document.getElementById('support-arrow');
                if (arrow) arrow.style.transform = 'rotate(0deg)';
            }
        });
    }

    function initShell() {
        bindSupportClickAway();
    }

    global.toggleMobileMenu = toggleMobileMenu;
    global.toggleQRModal = toggleQRModal;
    global.toggleFeedbackModal = toggleFeedbackModal;
    global.toggleSupportDropdown = toggleSupportDropdown;
    global.sendFeedback = sendFeedback;
    global.openSupportCodeModal = openSupportCodeModal;
    global.closeSupportCodeModal = closeSupportCodeModal;
    global.sendSupportCode = sendSupportCode;
    global.openStopAppModal = openStopAppModal;
    global.closeStopAppModal = closeStopAppModal;
    global.confirmStopApplication = confirmStopApplication;
    global.quitApplication = quitApplication;
    global.navigateToTab = navigateToTab;
    global.KryptAimShell = { init: initShell };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initShell);
    } else {
        initShell();
    }
})(window);
