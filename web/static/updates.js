/** Shared update check + footer install button (index + projects pages). */
(function (global) {
    'use strict';

    function renderUpdateStatus(data) {
        const msg = document.getElementById('update-status-msg');
        const badge = document.getElementById('update-badge');
        const installBtn = document.getElementById('update-install-btn');
        const latestEl = document.getElementById('update-latest-version');
        const notes = document.getElementById('update-notes');
        const releaseLink = document.getElementById('update-release-link');
        const footerBtn = document.getElementById('footer-update-btn');
        if (!data) return;

        if (latestEl) {
            latestEl.textContent = data.latest_version
                ? `Latest: v${data.latest_version}`
                : 'Latest: —';
        }
        if (msg) {
            if (!data.success) {
                msg.textContent = data.error || 'Could not check for updates.';
            } else if (data.update_available) {
                msg.textContent = `v${data.current_version} → v${data.latest_version} available.`;
            } else {
                msg.textContent = `You are on the latest release (v${data.current_version}).`;
            }
        }
        if (badge) badge.classList.toggle('hidden', !data.update_available);
        if (installBtn) installBtn.classList.toggle('hidden', !data.update_available);
        if (notes) {
            const body = (data.release_notes || '').trim();
            if (body && data.update_available) {
                notes.textContent = body;
                notes.classList.remove('hidden');
            } else {
                notes.textContent = '';
                notes.classList.add('hidden');
            }
        }
        if (releaseLink && data.release_url) {
            releaseLink.href = data.release_url;
            releaseLink.classList.toggle('hidden', !data.update_available);
        }
        if (footerBtn) {
            footerBtn.classList.toggle('hidden', !data.update_available);
            if (data.update_available && data.latest_version) {
                footerBtn.textContent = `Update to v${data.latest_version}`;
                footerBtn.title = `Install v${data.latest_version}`;
            }
        }
    }

    function checkForUpdates(manual) {
        const btn = document.getElementById('update-check-btn');
        const msg = document.getElementById('update-status-msg');
        if (manual && btn) { btn.disabled = true; btn.textContent = 'Checking…'; }
        if (manual && msg) msg.textContent = 'Checking GitHub releases…';
        return fetch('/api/updates/check', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                renderUpdateStatus(data);
                if (typeof global.updateAiAccess === 'function' && data.features) {
                    global.updateAiAccess({
                        allowed: true,
                        premium_required: !!data.features.ai_premium_only,
                    });
                }
                return data;
            })
            .catch(() => {
                if (msg) msg.textContent = 'Update check failed.';
            })
            .finally(() => {
                if (btn) { btn.disabled = false; btn.textContent = 'Check for updates'; }
            });
    }

    function installAppUpdate() {
        if (!confirm('Download and install the latest AimSync.exe? The app will close and restart.')) return;
        const installBtn = document.getElementById('update-install-btn');
        const footerBtn = document.getElementById('footer-update-btn');
        const msg = document.getElementById('update-status-msg');
        if (installBtn) { installBtn.disabled = true; installBtn.textContent = 'Downloading…'; }
        if (footerBtn) { footerBtn.disabled = true; footerBtn.textContent = 'Downloading…'; }
        if (msg) msg.textContent = 'Downloading update…';
        return fetch('/api/updates/install', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (!data.success) {
                    alert(data.message || 'Update failed');
                    return;
                }
                if (msg) msg.textContent = data.message || 'Restarting…';
                if (footerBtn) footerBtn.textContent = 'Restarting…';
                setTimeout(() => fetch('/api/quit', { method: 'POST' }), 800);
            })
            .catch(() => alert('Update request failed'))
            .finally(() => {
                if (installBtn) { installBtn.disabled = false; installBtn.textContent = 'Install update'; }
                if (footerBtn) footerBtn.disabled = false; 
            });
    }

    function init(options) {
        const opts = options || {};
        if (opts.autoCheck !== false) {
            checkForUpdates(false);
        }
    }

    global.AimSyncUpdates = {
        init,
        check: checkForUpdates,
        install: installAppUpdate,
        render: renderUpdateStatus,
    };
})(window);
