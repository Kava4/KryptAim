/** Hub sidebar tab navigation — works with existing .tab-content panels. */
(function (global) {
    'use strict';

    function setActiveHubTab(tabId) {
        document.querySelectorAll('.hub-nav-btn, .tab-button.hub-nav-btn').forEach((btn) => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        document.querySelectorAll('.tab-content').forEach((panel) => panel.classList.add('hidden'));
        document.getElementById('tab-content-' + tabId)?.classList.remove('hidden');
        if (tabId === 'ai-engine') {
            if (typeof global.startAiPoll === 'function') global.startAiPoll();
            if (global.KryptAimVisionFeed) global.KryptAimVisionFeed.start();
        } else if (global.KryptAimVisionFeed) {
            global.KryptAimVisionFeed.stop();
        }
        closeHubSidebar();
    }

    function bindHubNav() {
        document.querySelectorAll('.hub-nav-btn[data-tab], .tab-button.hub-nav-btn[data-tab]').forEach((btn) => {
            btn.addEventListener('click', () => setActiveHubTab(btn.dataset.tab));
        });
    }

    function toggleHubSidebar(forceClose) {
        const sidebar = document.getElementById('hub-sidebar');
        const backdrop = document.getElementById('hub-sidebar-backdrop');
        if (!sidebar) return;
        const open = forceClose === true ? false : !sidebar.classList.contains('open');
        sidebar.classList.toggle('open', open);
        backdrop?.classList.toggle('open', open);
    }

    function closeHubSidebar() {
        toggleHubSidebar(true);
    }

    function toggleHubSupportMenu() {
        const menu = document.getElementById('hub-support-menu');
        const wrap = document.getElementById('hub-support-wrap');
        if (!menu) return;
        const open = menu.classList.contains('hidden');
        menu.classList.toggle('hidden', !open);
        wrap?.classList.toggle('is-open', open);
    }

    function closeHubSupportMenu() {
        document.getElementById('hub-support-menu')?.classList.add('hidden');
        document.getElementById('hub-support-wrap')?.classList.remove('is-open');
    }

    function bindHubSupportClickAway() {
        document.addEventListener('click', (e) => {
            const wrap = document.getElementById('hub-support-wrap');
            if (!wrap || wrap.contains(e.target)) return;
            closeHubSupportMenu();
        });
    }

    function bindMobileNoZoom() {
        if (!document.body.classList.contains('hub-theme')) return;
        ['gesturestart', 'gesturechange', 'gestureend'].forEach((evt) => {
            document.addEventListener(evt, (e) => e.preventDefault(), { passive: false });
        });
    }

    function initHubNav() {
        bindHubNav();
        bindHubSupportClickAway();
        bindMobileNoZoom();
        const tab = new URLSearchParams(window.location.search).get('tab') || 'global';
        if (document.querySelector('.hub-nav-btn[data-tab]')) {
            setActiveHubTab(tab);
        }
    }

    global.toggleHubSupportMenu = toggleHubSupportMenu;
    global.closeHubSupportMenu = closeHubSupportMenu;

    global.setActiveHubTab = setActiveHubTab;
    global.toggleHubSidebar = toggleHubSidebar;
    global.closeHubSidebar = closeHubSidebar;
    global.initHubNav = initHubNav;
})(window);
