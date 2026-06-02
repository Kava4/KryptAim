// pattern_visualiser.js — full editor build
(function () {
    const canvas  = document.getElementById('vis-canvas');
    if (!canvas) return;
    const ctx     = canvas.getContext('2d');
    const tooltip = document.getElementById('vis-tooltip');

    // stat elements
    const elSteps = document.getElementById('vis-steps');
    const elTotX  = document.getElementById('vis-totx');
    const elTotY  = document.getElementById('vis-toty');
    const elDur   = document.getElementById('vis-dur');
    const elNums  = document.getElementById('vis-show-nums');

    // toolbar elements
    const elSnap      = document.getElementById('vis-snap');
    const elGrid      = document.getElementById('vis-grid');
    const elInspector = document.getElementById('vis-inspector');
    const elUndoBtn   = document.getElementById('vis-undo');
    const elRedoBtn   = document.getElementById('vis-redo');

    // inspector fields
    const elInspX     = document.getElementById('vis-insp-x');
    const elInspY     = document.getElementById('vis-insp-y');
    const elInspD     = document.getElementById('vis-insp-d');
    const elInspStep  = document.getElementById('vis-insp-step');
    const elInspClose = document.getElementById('vis-insp-close');
    const elInspPrev  = document.getElementById('vis-insp-prev');
    const elInspNext  = document.getElementById('vis-insp-next');
    const elInspDist  = document.getElementById('vis-insp-dist');
    const elInspDel   = document.getElementById('vis-insp-del');

    // step list
    const elStepList  = document.getElementById('vis-step-list');

    // context menu
    const elCtxMenu   = document.getElementById('vis-ctx-menu');

    const C = {
        bg:      '#0a0a0a',
        grid:    'rgba(255,255,255,0.04)',
        gridSub: 'rgba(255,255,255,0.02)',
        axis:    'rgba(255,255,255,0.08)',
        path:    '#00f0ff',
        dot:     '#00f0ff',
        dotHov:  '#fbbf24',
        dotDrag: '#f87171',
        dotOrig: '#38bdf8',
        num:     '#ffffff',
        empty:   'rgba(255,255,255,0.4)',
        select:  '#a78bfa',
        add:     '#00f0ff',
    };

    let steps       = [];
    let hoveredIdx  = -1;
    let dragIdx     = -1;
    let selectedIdx = -1;
    let dragStart   = null;
    let dragSnap    = null;
    let currentMode = 'advanced';

    // canvas add-step ghost (mouse pos in pattern space when hovering empty area)
    let addGhost = null;

    // animation
    let pathProgress = 1;
    let dotScales    = [];
    let gridAlpha    = 1;
    let animRaf      = null;
    let pulseT       = 0;

    // ── Playback ──────────────────────────────────────────────────────────────
    const PB = {
        active:    false,
        startTime: 0,
        segIdx:    0,
        raf:       null,
        timeline:  [],
        tail:      [],
        TAIL_MAX:  28,
    };

    function buildTimeline() {
        const { xCtrl, yCtrl } = getControlMultipliers();
        const STEPS = 20;
        const tl = [];
        let cx = 0, cy = 0;
        for (const s of steps) {
            const actual_x = s.x * xCtrl;
            const actual_y = s.y * yCtrl;
            let acc_x = 0.0, acc_y = 0.0;
            const subPts = [{ x: cx, y: cy }];
            for (let k = 0; k < STEPS; k++) {
                const eased = easeOutQuad((k + 1) / STEPS);
                const mv_x = Math.round(actual_x * eased - acc_x);
                const mv_y = Math.round(actual_y * eased - acc_y);
                acc_x += mv_x; acc_y += mv_y;
                subPts.push({ x: cx + acc_x, y: cy + acc_y });
            }
            tl.push({ dur: Math.max(1, s.d), x1: cx, y1: cy, x2: cx + acc_x, y2: cy + acc_y, subPts });
            cx += acc_x; cy += acc_y;
        }
        return tl;
    }

    function syncPlayBtn() {
        const btn = document.getElementById('vis-play-btn');
        if (!btn) return;
        btn.innerHTML = PB.active
            ? `<svg width="11" height="11" fill="currentColor" viewBox="0 0 24 24"><rect x="5" y="4" width="4" height="16" rx="1"/><rect x="15" y="4" width="4" height="16" rx="1"/></svg> STOP`
            : `<svg width="11" height="11" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4l15 8-15 8V4z"/></svg> PLAY`;
        btn.style.color = PB.active ? '#f87171' : '';
        btn.style.borderColor = PB.active ? 'rgba(248,113,113,0.3)' : '';
    }

    function startPlayback() {
        if (!steps.length) return;
        if (PB.raf) cancelAnimationFrame(PB.raf);
        PB.timeline = buildTimeline();
        PB.segIdx = 0;
        PB.startTime = performance.now();
        PB.active = true;
        PB.tail = [];
        PB.raf = requestAnimationFrame(tickPlayback);
        syncPlayBtn();
    }

    function stopPlayback() {
        PB.active = false;
        if (PB.raf) { cancelAnimationFrame(PB.raf); PB.raf = null; }
        PB.tail = [];
        syncPlayBtn();
        scheduleDraw();
    }

    function tickPlayback() {
        if (!PB.active || !PB.timeline.length) { stopPlayback(); return; }
        const now = performance.now();
        
        while (PB.active && PB.timeline[PB.segIdx] && (now - PB.startTime) >= PB.timeline[PB.segIdx].dur) {
            PB.startTime += PB.timeline[PB.segIdx].dur;
            PB.segIdx++;
        }

        if (PB.segIdx >= PB.timeline.length) { setTimeout(stopPlayback, 400); return; }

        const seg = PB.timeline[PB.segIdx];
        const elapsed = now - PB.startTime;
        const STEPS = seg.subPts.length - 1;
        const subF = (elapsed / seg.dur) * STEPS;
        const subLo = Math.floor(subF);
        const subHi = Math.min(subLo + 1, STEPS);
        const blend = subF - subLo;
        const lo = seg.subPts[subLo], hi = seg.subPts[subHi];
        PB.currentX = lo.x + (hi.x - lo.x) * blend;
        PB.currentY = lo.y + (hi.y - lo.y) * blend;
        const subDur = seg.dur / STEPS;
        PB.speed = Math.hypot(hi.x - lo.x, hi.y - lo.y) / Math.max(subDur, 1);
        PB.tail.push({ x: PB.currentX, y: PB.currentY, speed: PB.speed });
        if (PB.tail.length > PB.TAIL_MAX) PB.tail.shift();
        scheduleDraw();
        PB.raf = requestAnimationFrame(tickPlayback);
    }

    window.visPlay = function () { PB.active ? stopPlayback() : startPlayback(); };
    function stopPlaybackIfActive() { if (PB.active) stopPlayback(); }

    // ── Undo / Redo ───────────────────────────────────────────────────────────
    const undoStack = [], redoStack = [];
    const MAX_UNDO = 40;

    function pushUndo() {
        undoStack.push(steps.map(s => ({ ...s })));
        if (undoStack.length > MAX_UNDO) undoStack.shift();
        redoStack.length = 0;
        syncUndoButtons();
    }

    function undo() {
        if (!undoStack.length) return;
        redoStack.push(steps.map(s => ({ ...s })));
        steps = undoStack.pop();
        syncUndoButtons();
        writeStepsToTextarea(false);
        renderStepList();
        startEntrance();
    }

    function redo() {
        if (!redoStack.length) return;
        undoStack.push(steps.map(s => ({ ...s })));
        steps = redoStack.pop();
        syncUndoButtons();
        writeStepsToTextarea(false);
        renderStepList();
        startEntrance();
    }

    function syncUndoButtons() {
        if (elUndoBtn) elUndoBtn.disabled = undoStack.length === 0;
        if (elRedoBtn) elRedoBtn.disabled = redoStack.length === 0;
    }

    // ── Entrance animation ────────────────────────────────────────────────────
    function startEntrance() {
        stopPlaybackIfActive();
        pathProgress = 0; gridAlpha = 0;
        dotScales = steps.map(() => 0);
        if (animRaf) cancelAnimationFrame(animRaf);
        animRaf = requestAnimationFrame(animStep);
    }

    function animStep() {
        pathProgress = Math.min(1, pathProgress + 0.04);
        gridAlpha    = Math.min(1, gridAlpha    + 0.025);
        pulseT      += 0.05;
        const n = dotScales.length;
        dotScales = dotScales.map((s, i) => {
            const threshold = 0.08 + (i / Math.max(n, 1)) * 0.5;
            return pathProgress >= threshold ? Math.min(1, s + 0.13) : s;
        });
        draw();
        const done = pathProgress >= 1 && gridAlpha >= 1 && dotScales.every(v => v >= 1);
        animRaf = done ? null : requestAnimationFrame(animStep);
    }

    // ── Source readers ────────────────────────────────────────────────────────
    function stepsFromTextarea() {
        const ta = document.getElementById('pattern-textarea');
        if (!ta) return [];
        const out = [];
        for (const raw of ta.value.split('\n')) {
            const line = raw.trim();
            if (!line) continue;
            const parts = line.split(',');
            if (parts.length < 2) continue;
            const x = parseFloat(parts[0]), y = parseFloat(parts[1]);
            const d = parts.length >= 3 ? parseFloat(parts[2]) : 100;
            if (isNaN(x) || isNaN(y)) continue;
            out.push({ x, y, d: isNaN(d) ? 100 : d });
        }
        return out;
    }

    function stepsFromSimple() {
        const x = parseFloat(document.querySelector('[name="x"]')?.value ?? 0) || 0;
        const y = parseFloat(document.querySelector('[name="y"]')?.value ?? 0) || 0;
        const d = parseFloat(document.querySelector('[name="recoil_delay"]')?.value ?? 100) || 100;
        if (x === 0 && y === 0) return [];
        return [{ x, y, d }];
    }

    // ── Public API ────────────────────────────────────────────────────────────
    window.visRefresh = function (mode) {
        currentMode = mode || currentMode;
        hoveredIdx = -1; dragIdx = -1;
        tooltip.style.display = 'none';
        if (currentMode === 'advanced' || currentMode === 'CS2') steps = stepsFromTextarea();
        else if (currentMode === 'simple') steps = stepsFromSimple();
        
        if (selectedIdx >= steps.length) selectedIdx = -1;
        updateStats(steps);
        renderStepList();
        startEntrance();
    };
    window.visDrawFromTextarea = function () { window.visRefresh('advanced'); };

    // ── Stats ─────────────────────────────────────────────────────────────────
    let statT = { steps: 0, x: 0, y: 0, dur: 0 };
    let statC = { steps: 0, x: 0, y: 0, dur: 0 };
    let statRaf = null;

    function updateStats(s) {
        const { xCtrl, yCtrl } = getControlMultipliers();
        statT.steps = s.length;
        statT.x   = s.reduce((a, v) => a + v.x * xCtrl, 0);
        statT.y   = s.reduce((a, v) => a + v.y * yCtrl, 0);
        statT.dur = s.reduce((a, v) => a + v.d, 0);
        if (statRaf) cancelAnimationFrame(statRaf);
        statRaf = requestAnimationFrame(tickStats);
    }

    function tickStats() {
        const L = 0.16;
        statC.steps += (statT.steps - statC.steps) * L;
        statC.x     += (statT.x     - statC.x)     * L;
        statC.y     += (statT.y     - statC.y)     * L;
        statC.dur   += (statT.dur   - statC.dur)    * L;
        if (elSteps) elSteps.textContent = Math.round(statC.steps);
        if (elTotX)  elTotX.textContent  = statC.x.toFixed(1);
        if (elTotY)  elTotY.textContent  = statC.y.toFixed(1);
        if (elDur)   elDur.textContent   = Math.round(statC.dur) + 'ms';
        const done = Math.abs(statC.steps - statT.steps) < 0.4 && Math.abs(statC.dur - statT.dur) < 0.8;
        if (done) {
            if (elSteps) elSteps.textContent = statT.steps;
            if (elTotX)  elTotX.textContent  = statT.x.toFixed(1);
            if (elTotY)  elTotY.textContent  = statT.y.toFixed(1);
            if (elDur)   elDur.textContent   = statT.dur + 'ms';
        } else { statRaf = requestAnimationFrame(tickStats); }
    }

    // ── Canvas size ───────────────────────────────────────────────────────────
    function syncSize() {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        const w = Math.floor(rect.width * dpr), h = Math.floor(rect.height * dpr);
        if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
        return { W: rect.width, H: rect.height };
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    function easeOutQuad(t) { return t * (2 - t); }
    function r1(n) { return Math.round(n); }

    function getControlMultipliers() {
        const xCtrl = parseFloat(document.querySelector('[name="recoil_x_control"]')?.value ?? 100) / 100;
        const yCtrl = parseFloat(document.querySelector('[name="recoil_y_control"]')?.value ?? 100) / 100;
        return { xCtrl, yCtrl };
    }

    function getSnapSize() { return parseFloat(elSnap?.value) || 0; }
    function snapVal(v, snapSize) { return snapSize ? Math.round(v / snapSize) * snapSize : v; }

    function speedColor(t) {
        t = Math.max(0, Math.min(1, t));
        if (t < 0.5) {
            const f = t * 2;
            return `rgb(${r1(52+(251-52)*f)},${r1(211+(191-211)*f)},${r1(153+(36-153)*f)})`;
        } else {
            const f = (t - 0.5) * 2;
            return `rgb(${r1(251+(248-251)*f)},${r1(191+(113-191)*f)},${r1(36+(113-36)*f)})`;
        }
    }

    function getTransform(W, H) {
        const PAD = 40;
        const { xCtrl, yCtrl } = getControlMultipliers();
        const STEPS = 20;
        const pts = [{ px: 0, py: 0 }];
        let cx = 0, cy = 0;
        for (const s of steps) {
            let acc_x = 0, acc_y = 0;
            for (let k = 0; k < STEPS; k++) {
                const eased = easeOutQuad((k + 1) / STEPS);
                acc_x += Math.round(s.x * xCtrl * eased - acc_x);
                acc_y += Math.round(s.y * yCtrl * eased - acc_y);
            }
            cx += acc_x; cy += acc_y;
            pts.push({ px: cx, py: cy });
        }
        const allX = pts.map(p => p.px), allY = pts.map(p => p.py);
        const minX = Math.min(...allX, 0), maxX = Math.max(...allX, 0);
        const minY = Math.min(...allY, 0), maxY = Math.max(...allY, 0);
        const spanX = maxX - minX || 1, spanY = maxY - minY || 1;
        const scale = Math.min((W - 2*PAD)/spanX, (H - 2*PAD)/spanY) * 0.80;
        const offX  = W/2 - ((minX+maxX)/2)*scale;
        const offY  = H/2 - ((minY+maxY)/2)*scale;
        return { pts, scale, offX, offY, minX, maxX, minY, maxY, spanX, spanY, xCtrl, yCtrl };
    }

    // Convert canvas mouse coords → pattern-space raw step delta
    function canvasToPatternDelta(dx, dy, tf) {
        return { rx: dx / tf.scale / tf.xCtrl, ry: dy / tf.scale / tf.yCtrl };
    }

    // Convert canvas coords → absolute pattern-space position
    function canvasToPatternAbs(mx, my, tf) {
        return { px: (mx - tf.offX) / tf.scale, py: (my - tf.offY) / tf.scale };
    }

    function nearestStepIdx(mx, my, W, H) {
        if (!steps.length) return { idx: -1, dist: Infinity };
        const { pts, scale, offX, offY } = getTransform(W, H);
        let best = -1, bestD = Infinity;
        for (let i = 1; i < pts.length; i++) {
            const d = Math.hypot(mx - (offX + pts[i].px * scale), my - (offY + pts[i].py * scale));
            if (d < bestD) { bestD = d; best = i - 1; }
        }
        return { idx: best, dist: bestD };
    }

    function writeStepsToTextarea(triggerHtmx = true) {
        const ta = document.getElementById('pattern-textarea');
        if (!ta) return;
        ta.value = steps.map(s => `${r1(s.x)},${r1(s.y)},${s.d}`).join('\n');
        if (triggerHtmx) {
            ta.dispatchEvent(new Event('keyup',  { bubbles: true }));
            ta.dispatchEvent(new Event('change', { bubbles: true }));
        }
        updateStats(steps);
    }

    // ── Step operations ───────────────────────────────────────────────────────
    function addStepAt(idx, step) {
        // idx = position to insert (0 = before first, steps.length = append)
        pushUndo();
        steps.splice(idx, 0, step);
        dotScales.splice(idx, 0, 0);
        writeStepsToTextarea(true);
        renderStepList();
        updateStats(steps);
        scheduleDraw();
    }

    function deleteStep(idx) {
        if (idx < 0 || idx >= steps.length) return;
        pushUndo();
        steps.splice(idx, 1);
        dotScales.splice(idx, 1);
        if (selectedIdx === idx) { selectedIdx = -1; closeInspector(); }
        else if (selectedIdx > idx) selectedIdx--;
        writeStepsToTextarea(true);
        renderStepList();
        updateStats(steps);
        scheduleDraw();
    }

    function moveStep(fromIdx, toIdx) {
        if (fromIdx === toIdx) return;
        pushUndo();
        const [step] = steps.splice(fromIdx, 1);
        steps.splice(toIdx, 0, step);
        if (selectedIdx === fromIdx) selectedIdx = toIdx;
        writeStepsToTextarea(true);
        renderStepList();
        updateStats(steps);
        startEntrance();
    }

    // ── Bulk operations ───────────────────────────────────────────────────────
    window.visBulk = function(op) {
        if (!steps.length) return;
        pushUndo();
        switch (op) {
            case 'reverse':
                steps.reverse();
                break;
            case 'mirror-x':
                steps = steps.map(s => ({ ...s, x: -s.x }));
                break;
            case 'mirror-y':
                steps = steps.map(s => ({ ...s, y: -s.y }));
                break;
            case 'smooth': {
                const orig = steps.map(s => ({ ...s }));
                steps = steps.map((s, i) => {
                    if (i === 0 || i === steps.length - 1) return { ...s };
                    const p = orig[i - 1], n = orig[i + 1];
                    return { ...s, x: r1((p.x + s.x + n.x) / 3), y: r1((p.y + s.y + n.y) / 3) };
                });
                break;
            }
            case 'cs-scale':
                // Apply the 20x scaling (2*2*5) discovered for view-angle to pixel conversion
                steps = steps.map(s => ({ ...s, x: r1(s.x * 10), y: r1(s.y * 10) }));
                break;
            case 'scale-x': {
                const v = parseFloat(prompt('Scale X by factor (e.g. 1.5):', '1.0'));
                if (!isNaN(v)) steps = steps.map(s => ({ ...s, x: r1(s.x * v) }));
                break;
            }
            case 'scale-y': {
                const v = parseFloat(prompt('Scale Y by factor (e.g. 1.5):', '1.0'));
                if (!isNaN(v)) steps = steps.map(s => ({ ...s, y: r1(s.y * v) }));
                break;
            }
            case 'scale-delay': {
                const v = parseFloat(prompt('Scale all delays by factor (e.g. 0.8):', '1.0'));
                if (!isNaN(v)) steps = steps.map(s => ({ ...s, d: Math.max(1, r1(s.d * v)) }));
                break;
            }
            case 'set-delay': {
                const v = parseInt(prompt('Set all delays to (ms):', '100'));
                if (!isNaN(v) && v > 0) steps = steps.map(s => ({ ...s, d: v }));
                break;
            }
        }
        writeStepsToTextarea(true);
        renderStepList();
        updateStats(steps);
        startEntrance();
    };

    window.visAddStep = function() {
        const defaultD = steps.length ? steps[steps.length - 1].d : 100;
        addStepAt(steps.length, { x: 0, y: 5, d: defaultD });
        openInspector(steps.length - 1);
        renderStepList();
        // scroll step list to bottom
        if (elStepList) elStepList.scrollTop = elStepList.scrollHeight;
    };

    // ── Inspector ─────────────────────────────────────────────────────────────
    function openInspector(idx) {
        selectedIdx = idx;
        if (!elInspector) { scheduleDraw(); return; }
        const s = steps[idx];
        if (elInspStep) elInspStep.textContent = `step ${idx + 1} / ${steps.length}`;
        if (elInspX) elInspX.value = s.x;
        if (elInspY) elInspY.value = s.y;
        if (elInspD) elInspD.value = s.d;
        // cumulative distance
        if (elInspDist) {
            const { xCtrl, yCtrl } = getControlMultipliers();
            let cx = 0, cy = 0;
            for (let i = 0; i <= idx; i++) { cx += steps[i].x * xCtrl; cy += steps[i].y * yCtrl; }
            elInspDist.textContent = `Σ (${cx.toFixed(1)}, ${cy.toFixed(1)})`;
        }
        if (elInspPrev) elInspPrev.disabled = idx <= 0;
        if (elInspNext) elInspNext.disabled = idx >= steps.length - 1;
        elInspector.classList.remove('vis-insp-hidden');
        // highlight step list row
        highlightStepListRow(idx);
        scheduleDraw();
    }

    function closeInspector() {
        selectedIdx = -1;
        if (elInspector) elInspector.classList.add('vis-insp-hidden');
        scheduleDraw();
    }

    function commitInspector() {
        if (selectedIdx < 0 || selectedIdx >= steps.length) return;
        const x = parseFloat(elInspX?.value);
        const y = parseFloat(elInspY?.value);
        const d = parseFloat(elInspD?.value);
        if (isNaN(x) || isNaN(y) || isNaN(d)) return;
        pushUndo();
        steps[selectedIdx] = { x: r1(x), y: r1(y), d: Math.max(1, r1(d)) };
        updateStats(steps);
        writeStepsToTextarea(false);
        renderStepList();
        scheduleDraw();
    }

    if (elInspClose) elInspClose.addEventListener('click', closeInspector);
    if (elInspX)     elInspX.addEventListener('change', commitInspector);
    if (elInspY)     elInspY.addEventListener('change', commitInspector);
    if (elInspD)     elInspD.addEventListener('change', commitInspector);
    if (elInspPrev)  elInspPrev.addEventListener('click', () => { if (selectedIdx > 0) openInspector(selectedIdx - 1); });
    if (elInspNext)  elInspNext.addEventListener('click', () => { if (selectedIdx < steps.length - 1) openInspector(selectedIdx + 1); });
    if (elInspDel)   elInspDel.addEventListener('click', () => { const idx = selectedIdx; closeInspector(); deleteStep(idx); });
    if (elUndoBtn)   elUndoBtn.addEventListener('click', undo);
    if (elRedoBtn)   elRedoBtn.addEventListener('click', redo);

    // ── Step list panel ───────────────────────────────────────────────────────
    let dragListIdx = null;
    let dragListOver = null;

    function renderStepList() {
        if (!elStepList) return;
        const scrollTop = elStepList.scrollTop;
        elStepList.innerHTML = '';

        steps.forEach((s, i) => {
            const row = document.createElement('div');
            row.className = 'vis-sl-row' + (i === selectedIdx ? ' vis-sl-selected' : '');
            row.dataset.idx = i;
            row.draggable = true;

            row.innerHTML = `
                <span class="vis-sl-num">${i + 1}</span>
                <input class="vis-sl-input" type="number" step="1" value="${r1(s.x)}" data-field="x" title="X">
                <input class="vis-sl-input" type="number" step="1" value="${r1(s.y)}" data-field="y" title="Y">
                <input class="vis-sl-input vis-sl-ms" type="number" step="1" min="1" value="${s.d}" data-field="d" title="delay ms">
                <span class="vis-sl-ms-label">ms</span>
                <button class="vis-sl-del" title="Delete step" data-idx="${i}">
                    <svg width="10" height="10" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round"/>
                    </svg>
                </button>`;

            // input changes
            row.querySelectorAll('.vis-sl-input').forEach(inp => {
                inp.addEventListener('change', () => {
                    const field = inp.dataset.field;
                    const val = parseFloat(inp.value);
                    if (isNaN(val)) return;
                    pushUndo();
                    if (field === 'x') steps[i].x = r1(val);
                    else if (field === 'y') steps[i].y = r1(val);
                    else if (field === 'd') steps[i].d = Math.max(1, r1(val));
                    writeStepsToTextarea(true);
                    updateStats(steps);
                    if (selectedIdx === i) openInspector(i);
                    scheduleDraw();
                });
                inp.addEventListener('focus', () => { selectedIdx = i; openInspector(i); });
            });

            // delete button
            row.querySelector('.vis-sl-del').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteStep(i);
            });

            // click row → select
            row.addEventListener('click', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
                openInspector(i);
                scheduleDraw();
            });

            // drag reorder
            row.addEventListener('dragstart', (e) => {
                dragListIdx = i;
                e.dataTransfer.effectAllowed = 'move';
                row.classList.add('vis-sl-dragging');
            });
            row.addEventListener('dragend', () => {
                row.classList.remove('vis-sl-dragging');
                if (dragListIdx !== null && dragListOver !== null && dragListIdx !== dragListOver) {
                    moveStep(dragListIdx, dragListOver);
                }
                dragListIdx = null; dragListOver = null;
                elStepList.querySelectorAll('.vis-sl-row').forEach(r => r.classList.remove('vis-sl-drag-over'));
            });
            row.addEventListener('dragover', (e) => {
                e.preventDefault();
                dragListOver = i;
                elStepList.querySelectorAll('.vis-sl-row').forEach(r => r.classList.remove('vis-sl-drag-over'));
                row.classList.add('vis-sl-drag-over');
            });

            elStepList.appendChild(row);
        });

        elStepList.scrollTop = scrollTop;
    }

    function highlightStepListRow(idx) {
        if (!elStepList) return;
        elStepList.querySelectorAll('.vis-sl-row').forEach((r, i) => {
            r.classList.toggle('vis-sl-selected', i === idx);
        });
        const row = elStepList.children[idx];
        if (row) row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }

    // ── Context menu ──────────────────────────────────────────────────────────
    let ctxTargetIdx = -1;
    let ctxCanvasPos = null;

    function showCtxMenu(x, y, nearIdx) {
        if (!elCtxMenu) return;
        ctxTargetIdx = nearIdx;
        elCtxMenu.style.left = x + 'px';
        elCtxMenu.style.top  = y + 'px';
        elCtxMenu.classList.remove('vis-ctx-hidden');

        // update item visibility
        elCtxMenu.querySelector('[data-action="insert-before"]').style.display = nearIdx >= 0 ? '' : 'none';
        elCtxMenu.querySelector('[data-action="insert-after"]').style.display  = nearIdx >= 0 ? '' : 'none';
        elCtxMenu.querySelector('[data-action="delete"]').style.display        = nearIdx >= 0 ? '' : 'none';
        elCtxMenu.querySelector('[data-action="inspect"]').style.display       = nearIdx >= 0 ? '' : 'none';
    }

    function hideCtxMenu() {
        if (elCtxMenu) elCtxMenu.classList.add('vis-ctx-hidden');
    }

    document.addEventListener('click', hideCtxMenu);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') hideCtxMenu();
    });

    if (elCtxMenu) {
        elCtxMenu.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            const action = btn.dataset.action;
            hideCtxMenu();
            const defaultD = steps.length ? (steps[ctxTargetIdx]?.d ?? steps[steps.length-1].d) : 100;

            if (action === 'add-end') {
                addStepAt(steps.length, { x: 0, y: 5, d: defaultD });
                openInspector(steps.length - 1);
            } else if (action === 'insert-before' && ctxTargetIdx >= 0) {
                addStepAt(ctxTargetIdx, { x: 0, y: 5, d: defaultD });
                openInspector(ctxTargetIdx);
            } else if (action === 'insert-after' && ctxTargetIdx >= 0) {
                addStepAt(ctxTargetIdx + 1, { x: 0, y: 5, d: defaultD });
                openInspector(ctxTargetIdx + 1);
            } else if (action === 'delete' && ctxTargetIdx >= 0) {
                deleteStep(ctxTargetIdx);
            } else if (action === 'inspect' && ctxTargetIdx >= 0) {
                openInspector(ctxTargetIdx);
            } else if (action === 'add-here' && ctxCanvasPos) {
                // add step at the clicked canvas position
                const rect = canvas.getBoundingClientRect();
                const W = rect.width, H = rect.height;
                const tf = getTransform(W, H);
                const abs = canvasToPatternAbs(ctxCanvasPos.x, ctxCanvasPos.y, tf);
                // compute cumulative position up to last step
                let cx = 0, cy = 0;
                for (const s of steps) { cx += s.x * tf.xCtrl; cy += s.y * tf.yCtrl; }
                const dx = r1((abs.px - cx) / tf.xCtrl);
                const dy = r1((abs.py - cy) / tf.yCtrl);
                addStepAt(steps.length, { x: dx, y: dy, d: defaultD });
                openInspector(steps.length - 1);
            }
        });
    }

    // ── Draw ──────────────────────────────────────────────────────────────────
    function draw() {
        const { W, H } = syncSize();
        const dpr = window.devicePixelRatio || 1;
        ctx.save();
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, W, H);

        if (!steps.length) { drawEmpty(W, H); ctx.restore(); return; }

        const PAD = 40;
        const showNums = elNums && elNums.checked;
        const showGrid = !elGrid || elGrid.checked;
        const tf = getTransform(W, H);
        const { pts, scale, offX, offY, minX, maxX, minY, maxY, spanX, spanY } = tf;

        function sx(px) { return offX + px * scale; }
        function sy(py) { return offY + py * scale; }

        // scanlines
        ctx.globalAlpha = 0.018 * gridAlpha;
        ctx.strokeStyle = 'rgba(255,255,255,0.6)';
        ctx.lineWidth = 0.5;
        for (let row = 0; row < H; row += 3) {
            ctx.beginPath(); ctx.moveTo(0, row); ctx.lineTo(W, row); ctx.stroke();
        }
        ctx.globalAlpha = 1;

        // grid
        if (showGrid) {
            const gridStep = Math.ceil(Math.max(spanX, spanY) / 6) || 1;
            const sub = gridStep / 4;
            ctx.strokeStyle = C.gridSub; ctx.lineWidth = 0.4; ctx.globalAlpha = gridAlpha * 0.6;
            for (let g = Math.floor(minX/sub)*sub; g <= maxX+sub; g += sub) { ctx.beginPath(); ctx.moveTo(sx(g),PAD); ctx.lineTo(sx(g),H-PAD); ctx.stroke(); }
            for (let g = Math.floor(minY/sub)*sub; g <= maxY+sub; g += sub) { ctx.beginPath(); ctx.moveTo(PAD,sy(g)); ctx.lineTo(W-PAD,sy(g)); ctx.stroke(); }
            ctx.strokeStyle = C.grid; ctx.lineWidth = 0.5; ctx.globalAlpha = gridAlpha;
            for (let g = Math.floor(minX/gridStep)*gridStep; g <= maxX+gridStep; g += gridStep) { ctx.beginPath(); ctx.moveTo(sx(g),PAD); ctx.lineTo(sx(g),H-PAD); ctx.stroke(); }
            for (let g = Math.floor(minY/gridStep)*gridStep; g <= maxY+gridStep; g += gridStep) { ctx.beginPath(); ctx.moveTo(PAD,sy(g)); ctx.lineTo(W-PAD,sy(g)); ctx.stroke(); }
        }

        // axes
        const ox = sx(0), oy = sy(0);
        ctx.strokeStyle = C.axis; ctx.lineWidth = 0.75; ctx.globalAlpha = gridAlpha;
        if (ox > PAD && ox < W-PAD) { ctx.beginPath(); ctx.moveTo(ox,PAD); ctx.lineTo(ox,H-PAD); ctx.stroke(); }
        if (oy > PAD && oy < H-PAD) { ctx.beginPath(); ctx.moveTo(PAD,oy); ctx.lineTo(W-PAD,oy); ctx.stroke(); }
        ctx.globalAlpha = 1;

        // path
        if (pts.length > 1) {
            let totalLen = 0;
            const segLens = [];
            for (let i = 1; i < pts.length; i++) {
                const l = Math.hypot(sx(pts[i].px)-sx(pts[i-1].px), sy(pts[i].py)-sy(pts[i-1].py));
                segLens.push(l); totalLen += l;
            }
            const drawLen = pathProgress * totalLen;
            let travelled = 0;
            ctx.lineCap = 'round';
            const N_EASE = 12;
            for (let i = 1; i < pts.length; i++) {
                if (travelled >= drawLen) break;
                const segLen = segLens[i-1];
                const segFrac = Math.min(1, (drawLen-travelled)/segLen);
                const t = pts.length > 2 ? i/(pts.length-1) : 1;
                const x1=sx(pts[i-1].px),y1=sy(pts[i-1].py),x2=sx(pts[i].px),y2=sy(pts[i].py);
                const subPts=[];
                const subCount=Math.max(2,Math.round(N_EASE*segFrac));
                for (let k=0;k<=subCount;k++){const raw=(k/subCount)*segFrac;const eased=easeOutQuad(raw);subPts.push({x:x1+(x2-x1)*eased,y:y1+(y2-y1)*eased});}

                const drawLine = (lw, alpha) => {
                    ctx.lineWidth=lw; ctx.globalAlpha=alpha;
                    ctx.beginPath(); ctx.moveTo(subPts[0].x,subPts[0].y);
                    for(let k=1;k<subPts.length;k++) ctx.lineTo(subPts[k].x,subPts[k].y);
                    ctx.stroke();
                };
                ctx.strokeStyle = C.path;
                ctx.shadowBlur = 10; ctx.shadowColor = C.path;
                drawLine(10, 0.06+0.08*t);
                drawLine(4, 0.12+0.15*t);
                ctx.shadowBlur = 0;
                drawLine(2, 0.40+0.60*t);

                if (segFrac>=1 && pts.length>2) {
                    const every=Math.max(1,Math.floor(pts.length/8));
                    if (i%every===0) {
                        const mid=Math.floor(subPts.length/2);
                        const nx=subPts[Math.min(mid+1,subPts.length-1)];
                        const angle=Math.atan2(nx.y-subPts[mid].y,nx.x-subPts[mid].x);
                        ctx.save(); ctx.translate(subPts[mid].x,subPts[mid].y); ctx.rotate(angle);
                        ctx.globalAlpha=0.25+0.4*t; ctx.lineWidth=1; ctx.strokeStyle=C.path;
                        ctx.beginPath(); ctx.moveTo(-5,-3.5); ctx.lineTo(0,0); ctx.lineTo(-5,3.5); ctx.stroke();
                        ctx.restore();
                    }
                }
                travelled += segLen;
            }

            // leading bullet
            if (pathProgress < 1) {
                let tip={x:sx(pts[0].px),y:sy(pts[0].py)},walked=0;
                for(let i=1;i<pts.length;i++){const sl=segLens[i-1];if(walked+sl>=drawLen){const f=(drawLen-walked)/sl;const e=easeOutQuad(f);tip={x:sx(pts[i-1].px)+(sx(pts[i].px)-sx(pts[i-1].px))*e,y:sy(pts[i-1].py)+(sy(pts[i].py)-sy(pts[i-1].py))*e};break;}walked+=sl;}
                ctx.globalAlpha=0.9; ctx.beginPath(); ctx.arc(tip.x,tip.y,3.5,0,Math.PI*2); ctx.fillStyle='#fff'; ctx.fill();
                ctx.globalAlpha=0.3; ctx.beginPath(); ctx.arc(tip.x,tip.y,8,0,Math.PI*2); ctx.fillStyle=C.path; ctx.fill();
            }
            ctx.globalAlpha=1; ctx.lineCap='butt';
        }

        // simple mode arrow
        if (currentMode === 'simple' && pts.length === 2) {
            const x1=sx(pts[0].px),y1=sy(pts[0].py),x2=sx(pts[1].px),y2=sy(pts[1].py);
            const angle=Math.atan2(y2-y1,x2-x1);
            ctx.save(); ctx.translate(x2,y2); ctx.rotate(angle);
            ctx.fillStyle=C.path; ctx.globalAlpha=0.9*pathProgress;
            ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(-11,-5); ctx.lineTo(-11,5); ctx.closePath(); ctx.fill();
            ctx.restore(); ctx.globalAlpha=1;
        } else {
            // dots
            for (let i = 0; i < pts.length; i++) {
                const px=sx(pts[i].px), py=sy(pts[i].py);
                const isOrigin=i===0, sIdx=i-1;
                const isDrag=sIdx===dragIdx, isHov=sIdx===hoveredIdx&&!isDrag, isSel=sIdx===selectedIdx&&!isDrag;
                const sc_dot=isOrigin?1:(dotScales[sIdx]??1);
                if(sc_dot<=0.01) continue;
                const baseR=isOrigin?7:isDrag?8:isHov?7:isSel?7:5.5;
                const r=baseR*sc_dot;
                ctx.save(); ctx.translate(px,py);
                if(isDrag){for(let ring=0;ring<2;ring++){const p=0.5+0.5*Math.sin(pulseT*3.5+ring*Math.PI);ctx.beginPath();ctx.arc(0,0,r+6+p*5+ring*4,0,Math.PI*2);ctx.strokeStyle=C.dotDrag;ctx.lineWidth=1;ctx.globalAlpha=(0.15+0.15*p)/(ring+1);ctx.stroke();}}
                if(isSel){const p=0.5+0.5*Math.sin(pulseT*2);ctx.beginPath();ctx.arc(0,0,r+5+p*2,0,Math.PI*2);ctx.strokeStyle=C.select;ctx.lineWidth=1.5;ctx.globalAlpha=0.4+0.2*p;ctx.stroke();}
                if(isHov||isDrag||isOrigin||isSel){ctx.beginPath();ctx.arc(0,0,r+7,0,Math.PI*2);ctx.fillStyle=isOrigin?'rgba(56,189,248,0.15)':isDrag?'rgba(248,113,113,0.2)':isSel?'rgba(167,139,250,0.18)':'rgba(251,191,36,0.18)';ctx.globalAlpha=1;ctx.fill();}
                ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);
                ctx.fillStyle=isOrigin?C.dotOrig:isDrag?C.dotDrag:isSel?C.select:isHov?C.dotHov:C.dot;
                ctx.globalAlpha=(isHov||isOrigin||isDrag||isSel)?1:0.8;ctx.fill();
                ctx.beginPath();ctx.arc(0,-r*0.25,r*0.3,0,Math.PI*2);ctx.fillStyle='rgba(255,255,255,0.25)';ctx.globalAlpha=sc_dot*0.6;ctx.fill();
                ctx.globalAlpha=1;ctx.restore();
                if(showNums&&i>0&&sc_dot>0.5){ctx.fillStyle=isSel?C.select:C.num;ctx.font='9px ui-monospace,monospace';ctx.textAlign='center';ctx.globalAlpha=sc_dot*(isSel?1:0.7);ctx.fillText(i,px,py-r-5);ctx.globalAlpha=1;}
            }
        }

        // origin crosshair
        ctx.strokeStyle=C.dotOrig;ctx.lineWidth=1;ctx.globalAlpha=0.35*gridAlpha;ctx.lineCap='round';ctx.setLineDash([2,3]);
        ctx.beginPath();ctx.moveTo(ox-9,oy);ctx.lineTo(ox+9,oy);ctx.stroke();
        ctx.beginPath();ctx.moveTo(ox,oy-9);ctx.lineTo(ox,oy+9);ctx.stroke();
        ctx.setLineDash([]);ctx.globalAlpha=1;ctx.lineCap='butt';

        // snap ghost
        if(dragSnap&&dragIdx!==-1){ctx.strokeStyle=C.dotDrag;ctx.lineWidth=0.75;ctx.globalAlpha=0.3;ctx.setLineDash([3,3]);ctx.beginPath();ctx.arc(sx(dragSnap.px),sy(dragSnap.py),6,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);ctx.globalAlpha=1;}

        // add ghost (double-click preview)
        if (addGhost && currentMode === 'advanced') {
            ctx.save();
            ctx.strokeStyle = C.add;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.5;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.arc(addGhost.cx, addGhost.cy, 7, 0, Math.PI * 2);
            ctx.stroke();
            ctx.setLineDash([]);
            // line from last step to ghost
            if (pts.length > 0) {
                const lastPt = pts[pts.length - 1];
                ctx.beginPath();
                ctx.moveTo(sx(lastPt.px), sy(lastPt.py));
                ctx.lineTo(addGhost.cx, addGhost.cy);
                ctx.globalAlpha = 0.2;
                ctx.stroke();
            }
            ctx.globalAlpha = 0.7;
            ctx.fillStyle = C.add;
            ctx.font = '9px ui-monospace,monospace';
            ctx.textAlign = 'center';
            ctx.fillText('+', addGhost.cx, addGhost.cy + 3.5);
            ctx.restore();
        }

        // playback dot + trail
        if(PB.active&&PB.currentX!==undefined){
            const maxSpeed=PB.timeline.reduce((m,seg)=>Math.max(m,Math.hypot(seg.x2-seg.x1,seg.y2-seg.y1)/Math.max(seg.dur,1)),0.001);
            for(let i=0;i<PB.tail.length;i++){const pt=PB.tail[i];const age=(i+1)/PB.tail.length;const col=speedColor(Math.min(1,pt.speed/maxSpeed));ctx.beginPath();ctx.arc(sx(pt.x),sy(pt.y),2.5*age,0,Math.PI*2);ctx.fillStyle=col;ctx.globalAlpha=age*0.55;ctx.fill();}
            const normSpeed=Math.min(1,PB.speed/maxSpeed);const dotCol=speedColor(normSpeed);
            const cx_dot=sx(PB.currentX),cy_dot=sy(PB.currentY);
            const pulse=0.5+0.5*Math.sin(pulseT*5);
            ctx.beginPath();ctx.arc(cx_dot,cy_dot,10+pulse*3,0,Math.PI*2);ctx.strokeStyle=dotCol;ctx.lineWidth=1;ctx.globalAlpha=0.2+0.15*pulse;ctx.stroke();
            ctx.beginPath();ctx.arc(cx_dot,cy_dot,7,0,Math.PI*2);ctx.fillStyle=dotCol;ctx.globalAlpha=0.18;ctx.fill();
            ctx.beginPath();ctx.arc(cx_dot,cy_dot,4.5,0,Math.PI*2);ctx.fillStyle=dotCol;ctx.globalAlpha=1;ctx.fill();
            ctx.beginPath();ctx.arc(cx_dot,cy_dot,1.8,0,Math.PI*2);ctx.fillStyle='#fff';ctx.globalAlpha=0.85;ctx.fill();
            ctx.globalAlpha=1;
        }

        ctx.restore();
    }

    function drawEmpty(W, H) {
        ctx.fillStyle = 'rgba(255,255,255,0.04)';
        const ds = 24;
        for(let x=ds;x<W;x+=ds) for(let y=ds;y<H;y+=ds){ctx.beginPath();ctx.arc(x,y,0.75,0,Math.PI*2);ctx.fill();}
        ctx.fillStyle = C.empty; ctx.font='13px ui-monospace,monospace'; ctx.textAlign='center'; ctx.globalAlpha=1;
        ctx.fillText(currentMode==='simple'?'set x or y to preview':'no steps — right-click or use + below',W/2,H/2);
        ctx.font='11px ui-monospace,monospace'; ctx.fillStyle='rgba(255,255,255,0.2)';
        ctx.fillText('pattern visualiser',W/2,H/2+22);
    }

    // ── scheduleDraw ──────────────────────────────────────────────────────────
    let _pending = false;
    function scheduleDraw() {
        if(_pending) return; _pending=true;
        requestAnimationFrame(()=>{_pending=false;pulseT+=0.04;draw();if(dragIdx!==-1||selectedIdx!==-1||PB.active)scheduleDraw();});
    }

    // ── Mouse ─────────────────────────────────────────────────────────────────
    let dragStartSteps=null, hasDragged=false;

    canvas.addEventListener('mousedown', function(e){
        if(e.button!==0) return;
        if(currentMode!=='advanced') return;
        if(!steps.length) return;
        hideCtxMenu();
        const rect=canvas.getBoundingClientRect();
        const mx=e.clientX-rect.left, my=e.clientY-rect.top;
        const {idx,dist}=nearestStepIdx(mx,my,rect.width,rect.height);
        if(dist>22){closeInspector();return;}
        pushUndo();
        dragIdx=idx; dragStart={x:mx,y:my}; dragStartSteps=steps.map(s=>({...s})); hasDragged=false;
        canvas.style.cursor='grabbing'; tooltip.style.display='none';
        e.preventDefault(); scheduleDraw();
    });

    canvas.addEventListener('dblclick', function(e){
        if(currentMode!=='advanced') return;
        const rect=canvas.getBoundingClientRect();
        const mx=e.clientX-rect.left, my=e.clientY-rect.top;
        const {dist}=nearestStepIdx(mx,my,rect.width,rect.height);
        if(dist<=22) return; // clicked near existing step — don't add
        const tf=getTransform(rect.width,rect.height);
        const abs=canvasToPatternAbs(mx,my,tf);
        let cx=0,cy=0;
        for(const s of steps){cx+=s.x*tf.xCtrl;cy+=s.y*tf.yCtrl;}
        const dx=r1((abs.px-cx)/tf.xCtrl);
        const dy=r1((abs.py-cy)/tf.yCtrl);
        const defaultD=steps.length?steps[steps.length-1].d:100;
        addStepAt(steps.length,{x:dx,y:dy,d:defaultD});
        openInspector(steps.length-1);
    });

    canvas.addEventListener('contextmenu', function(e){
        e.preventDefault();
        if(currentMode!=='advanced') return;
        const rect=canvas.getBoundingClientRect();
        const mx=e.clientX-rect.left, my=e.clientY-rect.top;
        const {idx,dist}=nearestStepIdx(mx,my,rect.width,rect.height);
        ctxCanvasPos={x:mx,y:my};
        // offset menu so it doesn't go off-screen
        const menuX=Math.min(e.clientX,window.innerWidth-180);
        const menuY=Math.min(e.clientY,window.innerHeight-220);
        showCtxMenu(menuX,menuY,dist<=22?idx:-1);
    });

    canvas.addEventListener('mousemove', function(e){
        const rect=canvas.getBoundingClientRect();
        const mx=e.clientX-rect.left, my=e.clientY-rect.top;

        if(dragIdx!==-1&&dragStart){
            hasDragged=true;
            const tf=getTransform(rect.width,rect.height);
            const {rx,ry}=canvasToPatternDelta(mx-dragStart.x,my-dragStart.y,tf);
            const snap=getSnapSize();
            steps=dragStartSteps.map((s,i)=>{
                if(i!==dragIdx) return {...s};
                return {...s,x:snapVal(r1(s.x+rx),snap),y:snapVal(r1(s.y+ry),snap)};
            });
            if(snap){let cx=0,cy=0;for(let j=0;j<=dragIdx;j++){cx+=steps[j].x;cy+=steps[j].y;}dragSnap={px:cx,py:cy};}else dragSnap=null;
            updateStats(steps);
            const ta=document.getElementById('pattern-textarea');
            if(ta) ta.value=steps.map(s=>`${r1(s.x)},${r1(s.y)},${s.d}`).join('\n');
            if(selectedIdx===dragIdx&&elInspX){elInspX.value=steps[dragIdx].x;elInspY.value=steps[dragIdx].y;}
            // update step list row live
            if(elStepList){
                const row=elStepList.children[dragIdx];
                if(row){const ins=row.querySelectorAll('.vis-sl-input');if(ins[0])ins[0].value=steps[dragIdx].x;if(ins[1])ins[1].value=steps[dragIdx].y;}
            }
            scheduleDraw(); return;
        }

        if(currentMode==='simple'){addGhost=null;return;}
        const {idx,dist}=nearestStepIdx(mx,my,rect.width,rect.height);
        if(dist<22){
            hoveredIdx=idx; addGhost=null;
            const s=steps[idx];
            tooltip.innerHTML=`<span class="vis-tt-step">step ${idx+1}</span><span class="vis-tt-val"><span class="vis-tt-label">x</span>${s.x}</span><span class="vis-tt-val"><span class="vis-tt-label">y</span>${s.y}</span><span class="vis-tt-val"><span class="vis-tt-label">ms</span>${s.d}</span>`;
            tooltip.style.left=Math.min(mx+14,rect.width-180)+'px'; tooltip.style.top=Math.max(my-14,4)+'px'; tooltip.style.display='flex';
            canvas.style.cursor=currentMode==='advanced'?'grab':'default';
        } else {
            hoveredIdx=-1; tooltip.style.display='none';
            if(currentMode==='advanced'){
                canvas.style.cursor='crosshair';
                // show add ghost only when no steps nearby
                if(steps.length>0){
                    const tf=getTransform(rect.width,rect.height);
                    addGhost={cx:mx,cy:my,tf};
                }
            } else { canvas.style.cursor='default'; addGhost=null; }
        }
        scheduleDraw();
    });

    canvas.addEventListener('mouseup', function(){
        if(dragIdx===-1) return;
        const wasDrag=hasDragged, idx=dragIdx;
        dragIdx=-1; dragStart=null; dragStartSteps=null; dragSnap=null; hasDragged=false;
        canvas.style.cursor='default';
        if(!wasDrag) openInspector(idx);
        else writeStepsToTextarea(true);
        scheduleDraw();
    });

    canvas.addEventListener('mouseleave', function(){
        hoveredIdx=-1; tooltip.style.display='none'; addGhost=null;
        if(dragIdx!==-1){
            dragIdx=-1; dragStart=null; dragStartSteps=null; dragSnap=null; hasDragged=false;
            canvas.style.cursor='default';
            writeStepsToTextarea(true);
        }
        scheduleDraw();
    });

    // ── Touch Events (Mobile Support) ─────────────────────────────────────────
    function getTouchPos(e) {
        const rect = canvas.getBoundingClientRect();
        const touch = e.touches[0];
        return {
            x: touch.clientX - rect.left,
            y: touch.clientY - rect.top,
            clientX: touch.clientX,
            clientY: touch.clientY
        };
    }

    canvas.addEventListener('touchstart', function(e) {
        if (e.touches.length > 1) return;
        const pos = getTouchPos(e);
        
        const mousedownEvent = new MouseEvent('mousedown', {
            clientX: pos.clientX,
            clientY: pos.clientY,
            button: 0
        });
        canvas.dispatchEvent(mousedownEvent);
        
        // Prevent scrolling if we are interacting with a point
        if (dragIdx !== -1) e.preventDefault();
    }, { passive: false });

    canvas.addEventListener('touchmove', function(e) {
        if (e.touches.length > 1) return;
        const pos = getTouchPos(e);
        
        const mousemoveEvent = new MouseEvent('mousemove', {
            clientX: pos.clientX,
            clientY: pos.clientY
        });
        canvas.dispatchEvent(mousemoveEvent);
        
        if (dragIdx !== -1) e.preventDefault();
    }, { passive: false });

    canvas.addEventListener('touchend', function(e) {
        const mouseupEvent = new MouseEvent('mouseup', {});
        canvas.dispatchEvent(mouseupEvent);
    }, { passive: false });

    // ── Keyboard ──────────────────────────────────────────────────────────────
    document.addEventListener('keydown', function(e){
        // Undo/redo
        if((e.ctrlKey||e.metaKey)&&e.key==='z'&&!e.shiftKey){e.preventDefault();undo();return;}
        if((e.ctrlKey||e.metaKey)&&(e.key==='y'||(e.key==='z'&&e.shiftKey))){e.preventDefault();redo();return;}

        if(selectedIdx<0||selectedIdx>=steps.length) return;
        if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;

        // Delete selected step
        if(e.key==='Delete'||e.key==='Backspace'){
            e.preventDefault();
            const idx=selectedIdx;
            closeInspector();
            deleteStep(idx);
            return;
        }

        // Arrow nudge
        const nudge=e.shiftKey?5:1;
        let dx=0,dy=0;
        if(e.key==='ArrowLeft') dx=-nudge;
        if(e.key==='ArrowRight') dx=nudge;
        if(e.key==='ArrowUp') dy=-nudge;
        if(e.key==='ArrowDown') dy=nudge;
        if(!dx&&!dy) return;
        e.preventDefault();
        pushUndo();
        steps[selectedIdx]={...steps[selectedIdx],x:r1(steps[selectedIdx].x+dx),y:r1(steps[selectedIdx].y+dy)};
        openInspector(selectedIdx);
        writeStepsToTextarea(true);
        scheduleDraw();
    });

    // ── Live inputs ───────────────────────────────────────────────────────────
    const ta=document.getElementById('pattern-textarea');
    if(ta) ta.addEventListener('input',()=>{
        steps=stepsFromTextarea();
        if(selectedIdx>=steps.length) selectedIdx=-1;
        updateStats(steps); renderStepList(); startEntrance();
    });

    document.querySelectorAll('[name="x"],[name="y"],[name="recoil_delay"]').forEach(el=>{
        el.addEventListener('input',()=>{if(currentMode==='simple') window.visRefresh('simple');});
    });
    if(elNums) elNums.addEventListener('change',scheduleDraw);
    if(elGrid) elGrid.addEventListener('change',scheduleDraw);
    if(elSnap) elSnap.addEventListener('change',scheduleDraw);
    document.querySelectorAll('[name="recoil_x_control"],[name="recoil_y_control"]').forEach(el=>{
        el.addEventListener('input',scheduleDraw);
    });

    // mode select
    const modeEl=document.getElementById('recoil-mode');
    if(modeEl){currentMode=modeEl.value;modeEl.addEventListener('change',()=>{currentMode=modeEl.value;});}

    // resize
    new ResizeObserver(()=>{
        const dpr=window.devicePixelRatio||1;
        const rect=canvas.getBoundingClientRect();
        canvas.width=Math.floor(rect.width*dpr);
        canvas.height=Math.floor(rect.height*dpr);
        scheduleDraw();
    }).observe(canvas.parentElement);

    syncUndoButtons();
    window.visRefresh(currentMode);
})();