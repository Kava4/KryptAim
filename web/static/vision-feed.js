/** Live Vision Feed — canvas preview + detection overlay. */
(function (global) {
    'use strict';

    const GOLD = '#E5A93B';
    const GREEN = '#00E676';
    let pollTimer = null;
    const img = new Image();

    function canvas() {
        return document.getElementById('vision-feed-canvas');
    }

    function placeholder() {
        return document.getElementById('vision-feed-placeholder');
    }

    function fovRadius() {
        const el = document.getElementById('ai-fov-radius');
        return el ? parseInt(el.value, 10) || 120 : 120;
    }

    function drawFrame(data) {
        const c = canvas();
        if (!c) return;
        const ctx = c.getContext('2d');
        const wrap = c.parentElement;
        const w = wrap.clientWidth || 640;
        const h = wrap.clientHeight || 360;
        if (c.width !== w || c.height !== h) {
            c.width = w;
            c.height = h;
        }

        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, w, h);

        const hasImage = data && data.image;
        if (hasImage) {
            placeholder()?.classList.add('hidden');
            if (img.src !== data.image) {
                img.onload = () => drawFrame(data);
                img.src = data.image;
                return;
            }
            const scale = Math.min(w / img.width, h / img.height);
            const dw = img.width * scale;
            const dh = img.height * scale;
            const ox = (w - dw) / 2;
            const oy = (h - dh) / 2;
            ctx.drawImage(img, ox, oy, dw, dh);

            (data.boxes || []).forEach((box) => {
                const color = box.target ? GREEN : GOLD;
                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.strokeRect(
                    ox + (box.x || 0) * scale,
                    oy + (box.y || 0) * scale,
                    (box.w || 0) * scale,
                    (box.h || 0) * scale,
                );
            });
        } else {
            placeholder()?.classList.remove('hidden');
        }

        const fw = data?.frame_width || 1920;
        const fh = data?.frame_height || 1080;
        const scaleFov = hasImage ? Math.min(w / fw, h / fh) : Math.min(w, h) / 1920;
        const cx = w / 2;
        const cy = h / 2;
        const r = Math.max(fovRadius() * scaleFov, 20);
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = GOLD;
        ctx.lineWidth = 1;
        ctx.setLineDash([6, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    function pollPreview() {
        fetch('/api/ai/preview')
            .then((r) => r.json())
            .then((data) => {
                if (data.success) drawFrame(data);
            })
            .catch(() => {});
    }

    function start() {
        if (pollTimer) return;
        pollPreview();
        pollTimer = setInterval(pollPreview, 500);
    }

    function stop() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function bindFovSlider() {
        const el = document.getElementById('ai-fov-radius');
        const label = document.getElementById('ai-fov-radius-label');
        if (!el) return;
        el.addEventListener('input', () => {
            if (label) label.textContent = `${el.value}px`;
            pollPreview();
        });
        el.addEventListener('change', () => {
            fetch('/api/ai/detection', {
                method: 'POST',
                body: new URLSearchParams({ fov_radius: el.value }),
            });
        });
    }

    function bindConfSlider() {
        const el = document.getElementById('ai-vision-conf');
        const label = document.getElementById('ai-vision-conf-label');
        if (!el) return;
        el.addEventListener('input', () => {
            if (label) label.textContent = `${el.value}%`;
        });
        el.addEventListener('change', () => {
            if (typeof global.saveAiDetection === 'function') global.saveAiDetection();
        });
    }

    function init() {
        bindFovSlider();
        bindConfSlider();
        global.addEventListener('resize', pollPreview);
    }

    global.AimSyncVisionFeed = { start, stop, init, pollPreview };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(window);
