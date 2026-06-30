(function () {
  const CS2PULSE_PRESETS = {
    famas: {
      label: "FAMAS",
      media_url: "https://cs2pulse.com/wp-content/uploads/2024/10/Famas.gif",
      weapon: "famas",
      reference_weapon: "m4a1s",
      horizontal_strength: 0.45,
      delay_ms: 100,
    },
    ak47: {
      label: "AK-47",
      media_url: "https://cs2pulse.com/wp-content/uploads/2024/10/Ak47.gif",
      weapon: "ak47",
      reference_weapon: "ak47",
      delay_ms: 100,
    },
    m4a1s: {
      label: "M4A1-S",
      media_url: "https://cs2pulse.com/wp-content/uploads/2024/02/M4A1-S-Spray-Pattern.gif",
      weapon: "m4a1s",
      reference_weapon: "m4a1s",
      delay_ms: 100,
    },
  };

  function q(root, selector) {
    return root.querySelector(selector);
  }

  function toNumber(el, fallback) {
    const v = parseFloat(el.value);
    return Number.isFinite(v) ? v : fallback;
  }

  async function jsonFetch(url, opts) {
    const resp = await fetch(url, opts);
    const data = await resp.json();
    if (!resp.ok || !data.ok) {
      throw new Error(data.error || `Request failed: ${resp.status}`);
    }
    return data;
  }

  function initGenerator(root) {
    const canvas = q(root, '[data-pg="canvas"]');
    const ctx = canvas.getContext("2d");
    const presetSelect = q(root, '[data-pg="preset-select"]');
    const loadPresetBtn = q(root, '[data-pg="load-preset-btn"]');
    const detectStyleInput = q(root, '[data-pg="detect-style"]');
    const fileInput = q(root, '[data-pg="file-input"]');
    const urlInput = q(root, '[data-pg="url-input"]');
    const loadUrlBtn = q(root, '[data-pg="load-url-btn"]');
    const detectBtn = q(root, '[data-pg="detect-btn"]');
    const pointsList = q(root, '[data-pg="points-list"]');
    const clearPointsBtn = q(root, '[data-pg="clear-points"]');
    const delayMsInput = q(root, '[data-pg="delay-ms"]');
    const scaleXInput = q(root, '[data-pg="scale-x"]');
    const scaleYInput = q(root, '[data-pg="scale-y"]');
    const invertXInput = q(root, '[data-pg="invert-x"]');
    const invertYInput = q(root, '[data-pg="invert-y"]');
    const exportModeInput = q(root, '[data-pg="export-mode"]');
    const referenceWeaponInput = q(root, '[data-pg="reference-weapon"]');
    const horizontalStrengthInput = q(root, '[data-pg="horizontal-strength"]');
    const referenceWrap = q(root, '[data-pg="reference-wrap"]');
    const horizontalWrap = q(root, '[data-pg="horizontal-wrap"]');
    const exportHint = q(root, '[data-pg="export-hint"]');
    const autoGenerateInput = q(root, '[data-pg="auto-generate"]');
    const gameIdInput = q(root, '[data-pg="game-id"]');
    const weaponNameInput = q(root, '[data-pg="weapon-name"]');
    const applyGameBtn = q(root, '[data-pg="apply-game-btn"]');
    const generateBtn = q(root, '[data-pg="generate-btn"]');
    const copyBtn = q(root, '[data-pg="copy-btn"]');
    const sendLabBtn = q(root, '[data-pg="send-lab-btn"]');
    const output = q(root, '[data-pg="output"]');
    const status = q(root, '[data-pg="status"]');
    const frameControls = q(root, '[data-pg="frame-controls"]');
    const frameSlider = q(root, '[data-pg="frame-slider"]');
    const frameLabel = q(root, '[data-pg="frame-label"]');

    let points = [];
    let image = null;
    let imageWidth = 0;
    let imageHeight = 0;
    let frameDataUrls = [];
    let activeFrameIndex = 0;
    let canvasDisplayWidth = 0;
    let canvasDisplayHeight = 0;
    let generateTimer = null;

    function setStatus(text, isError) {
      status.textContent = text;
      status.className = `text-xs ${isError ? "text-red-300" : "text-white/40"}`;
    }

    function detectStyle() {
      return detectStyleInput ? detectStyleInput.value : "generic";
    }

    function shouldAutoGenerate() {
      return autoGenerateInput ? autoGenerateInput.checked : false;
    }

    function patternPayload() {
      const exportMode = exportModeInput ? exportModeInput.value : "laser_fit";
      const payload = {
        points,
        game_id: gameIdInput ? gameIdInput.value || "cs2" : "cs2",
        delay_ms: Math.round(toNumber(delayMsInput, 100)),
        scale_x: toNumber(scaleXInput, 1),
        scale_y: toNumber(scaleYInput, 1),
        invert_x: invertXInput.checked,
        invert_y: invertYInput.checked,
        export_mode: exportMode,
      };
      if (exportMode === "laser_fit" && referenceWeaponInput) {
        payload.reference_weapon = referenceWeaponInput.value || weaponNameInput.value || "m4a1s";
        payload.horizontal_strength = toNumber(horizontalStrengthInput, 1);
      }
      return payload;
    }

    function updateExportUi() {
      const laserMode = exportModeInput && exportModeInput.value === "laser_fit";
      if (referenceWrap) referenceWrap.classList.toggle("opacity-50", !laserMode);
      if (horizontalWrap) horizontalWrap.classList.toggle("opacity-50", !laserMode);
      if (referenceWeaponInput) referenceWeaponInput.disabled = !laserMode;
      if (horizontalStrengthInput) horizontalStrengthInput.disabled = !laserMode;
      if (exportHint) {
        exportHint.textContent = laserMode
          ? "Laser fit: lower Horizontal strength (try 0.5–0.7) if bullets drift left at end of spray."
          : "Raw deltas: manual Scale X/Y tuning required. Use Laser fit for CS2 Pulse GIFs.";
      }
    }

    async function loadReferenceWeapons() {
      if (!referenceWeaponInput || !gameIdInput) return;
      const gameId = gameIdInput.value || "cs2";
      const data = await jsonFetch(`/api/pattern-generator/weapons/${gameId}`);
      const current = referenceWeaponInput.value;
      referenceWeaponInput.innerHTML = "";
      data.weapons.forEach((weapon) => {
        const opt = document.createElement("option");
        opt.value = weapon;
        opt.textContent = weapon;
        referenceWeaponInput.appendChild(opt);
      });
      if (current && data.weapons.includes(current)) {
        referenceWeaponInput.value = current;
      }
    }

    async function copyText(text) {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return;
      }
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(ta);
      if (!ok) throw new Error("Clipboard copy failed.");
    }

    function resizeCanvasForImage(img) {
      const maxWidth = Math.min(900, root.clientWidth - 40);
      const ratio = img.width / img.height;
      canvasDisplayWidth = Math.max(300, Math.round(maxWidth));
      canvasDisplayHeight = Math.max(180, Math.round(canvasDisplayWidth / ratio));
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(canvasDisplayWidth * dpr);
      canvas.height = Math.round(canvasDisplayHeight * dpr);
      canvas.style.width = `${canvasDisplayWidth}px`;
      canvas.style.height = `${canvasDisplayHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      imageWidth = img.width;
      imageHeight = img.height;
    }

    function canvasToImagePoint(clientX, clientY) {
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return { x: 0, y: 0 };
      const relX = (clientX - rect.left) / rect.width;
      const relY = (clientY - rect.top) / rect.height;
      const x = Math.max(0, Math.min(imageWidth, relX * imageWidth));
      const y = Math.max(0, Math.min(imageHeight, relY * imageHeight));
      return { x: Math.round(x), y: Math.round(y) };
    }

    function draw() {
      ctx.clearRect(0, 0, canvasDisplayWidth, canvasDisplayHeight);
      ctx.fillStyle = "#111827";
      ctx.fillRect(0, 0, canvasDisplayWidth, canvasDisplayHeight);
      if (image) {
        ctx.drawImage(image, 0, 0, canvasDisplayWidth, canvasDisplayHeight);
      }
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#22d3ee";
      ctx.fillStyle = "#60a5fa";

      points.forEach((pt, idx) => {
        const x = (pt.x / imageWidth) * canvasDisplayWidth;
        const y = (pt.y / imageHeight) * canvasDisplayHeight;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#ffffff";
        ctx.font = "11px sans-serif";
        ctx.fillText(String(idx + 1), x + 6, y - 6);
        ctx.fillStyle = "#60a5fa";
        if (idx > 0) {
          const prev = points[idx - 1];
          const px = (prev.x / imageWidth) * canvasDisplayWidth;
          const py = (prev.y / imageHeight) * canvasDisplayHeight;
          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(x, y);
          ctx.stroke();
        }
      });
    }

    function updateFrameUi() {
      const hasMultipleFrames = frameDataUrls.length > 1;
      frameControls.classList.toggle("hidden", !hasMultipleFrames);
      if (!frameDataUrls.length) {
        frameSlider.value = "0";
        frameSlider.min = "0";
        frameSlider.max = "0";
        frameLabel.textContent = "Frame 1/1";
        return;
      }
      frameSlider.min = "0";
      frameSlider.max = String(frameDataUrls.length - 1);
      frameSlider.value = String(activeFrameIndex);
      frameLabel.textContent = `Frame ${activeFrameIndex + 1}/${frameDataUrls.length}`;
    }

    function showFrame(index) {
      if (!frameDataUrls.length) return;
      activeFrameIndex = Math.max(0, Math.min(index, frameDataUrls.length - 1));
      const src = frameDataUrls[activeFrameIndex];
      image = new Image();
      image.onload = () => {
        resizeCanvasForImage(image);
        draw();
      };
      image.src = src;
      updateFrameUi();
    }

    function renderPointsList() {
      pointsList.innerHTML = "";
      points.forEach((pt, idx) => {
        const row = document.createElement("div");
        row.className = "flex items-center justify-between bg-white/5 rounded px-2 py-1 text-[11px]";
        row.innerHTML = `
          <span>#${idx + 1} (${pt.x}, ${pt.y})</span>
          <span class="space-x-1">
            <button data-act="up" data-idx="${idx}" class="text-white/60 hover:text-white">↑</button>
            <button data-act="down" data-idx="${idx}" class="text-white/60 hover:text-white">↓</button>
            <button data-act="del" data-idx="${idx}" class="text-red-300 hover:text-red-200">x</button>
          </span>`;
        pointsList.appendChild(row);
      });
      draw();
      scheduleAutoGenerate();
    }

    function scheduleAutoGenerate() {
      if (!shouldAutoGenerate() || points.length < 2) return;
      clearTimeout(generateTimer);
      generateTimer = setTimeout(() => {
        generatePattern().catch((err) => setStatus(err.message, true));
      }, 250);
    }

    pointsList.addEventListener("click", (evt) => {
      const btn = evt.target.closest("button[data-act]");
      if (!btn) return;
      const idx = parseInt(btn.dataset.idx, 10);
      const act = btn.dataset.act;
      if (act === "del") points.splice(idx, 1);
      if (act === "up" && idx > 0) [points[idx - 1], points[idx]] = [points[idx], points[idx - 1]];
      if (act === "down" && idx < points.length - 1) [points[idx + 1], points[idx]] = [points[idx], points[idx + 1]];
      renderPointsList();
    });

    canvas.addEventListener("click", (evt) => {
      if (!image) return;
      points.push(canvasToImagePoint(evt.clientX, evt.clientY));
      renderPointsList();
    });

    canvas.addEventListener("contextmenu", (evt) => {
      evt.preventDefault();
      if (points.length) {
        points.pop();
        renderPointsList();
      }
    });

    clearPointsBtn.addEventListener("click", () => {
      points = [];
      renderPointsList();
      output.value = "";
    });

    function applyPresetFields(presetId) {
      const preset = CS2PULSE_PRESETS[presetId];
      if (!preset) return;
      urlInput.value = preset.media_url;
      weaponNameInput.value = preset.weapon;
      delayMsInput.value = String(preset.delay_ms);
      scaleXInput.value = "1";
      scaleYInput.value = "1";
      if (detectStyleInput) detectStyleInput.value = "cs2pulse";
      if (exportModeInput) exportModeInput.value = "laser_fit";
      if (referenceWeaponInput && preset.reference_weapon) {
        referenceWeaponInput.value = preset.reference_weapon;
      }
      if (horizontalStrengthInput && preset.horizontal_strength != null) {
        horizontalStrengthInput.value = String(preset.horizontal_strength);
      }
      updateExportUi();
    }

    function applyDetectedPayload(data, sourceLabel, includeSuggested) {
      frameDataUrls = Array.isArray(data.frame_data_urls) && data.frame_data_urls.length
        ? data.frame_data_urls
        : [data.preview_data_url];
      activeFrameIndex = Number.isInteger(data.recommended_frame_index)
        ? data.recommended_frame_index
        : Math.max(0, frameDataUrls.length - 1);
      if (includeSuggested) points = data.suggested_points || [];
      showFrame(activeFrameIndex);
      renderPointsList();
      const pointMsg = includeSuggested
        ? `${points.length} bullet points detected.`
        : "Ready for manual marking.";
      setStatus(`Loaded ${sourceLabel}. ${pointMsg}`, false);
      if (includeSuggested && shouldAutoGenerate() && points.length >= 2) {
        generatePattern().catch((err) => setStatus(err.message, true));
      }
    }

    async function loadFromFile(includeSuggested) {
      const file = fileInput.files && fileInput.files[0];
      if (!file) throw new Error("Select an image or GIF first.");

      const form = new FormData();
      form.append("spray_file", file);
      form.append("detect_style", detectStyle());
      const data = await jsonFetch("/api/pattern-generator/detect", { method: "POST", body: form });
      applyDetectedPayload(data, file.name, includeSuggested);
    }

    async function loadFromUrl(includeSuggested) {
      const mediaUrl = (urlInput.value || "").trim();
      if (!mediaUrl) throw new Error("Paste an image/GIF URL first.");
      const data = await jsonFetch("/api/pattern-generator/detect-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ media_url: mediaUrl, detect_style: detectStyle() }),
      });
      applyDetectedPayload(data, mediaUrl, includeSuggested);
    }

    presetSelect.addEventListener("change", () => {
      applyPresetFields(presetSelect.value);
    });

    loadPresetBtn.addEventListener("click", async () => {
      try {
        const presetId = presetSelect.value;
        if (!presetId) throw new Error("Select a CS2 Pulse preset first.");
        applyPresetFields(presetId);
        await loadFromUrl(true);
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    fileInput.addEventListener("change", async () => {
      try {
        await loadFromFile(false);
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    detectBtn.addEventListener("click", async () => {
      try {
        if (fileInput.files && fileInput.files[0]) {
          await loadFromFile(true);
          return;
        }
        await loadFromUrl(true);
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    loadUrlBtn.addEventListener("click", async () => {
      try {
        await loadFromUrl(true);
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    frameSlider.addEventListener("input", () => {
      const idx = parseInt(frameSlider.value, 10) || 0;
      showFrame(idx);
    });

    async function generatePattern() {
      if (points.length < 2) throw new Error("Add at least 2 bullet points.");
      const data = await jsonFetch("/api/pattern-generator/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patternPayload()),
      });
      output.value = data.pattern_text;
      const modeLabel = data.export_mode === "laser_fit" ? "laser fit" : data.export_mode;
      setStatus(`Generated ${data.steps_ms.length} ${modeLabel} steps. Fine-tune X/Y if needed.`, false);
      return data;
    }

    generateBtn.addEventListener("click", async () => {
      try {
        await generatePattern();
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    copyBtn.addEventListener("click", async () => {
      try {
        if (!output.value.trim()) {
          await generatePattern();
        }
        await copyText(output.value);
        setStatus("Pattern copied.", false);
      } catch (err) {
        setStatus(err.message || "Clipboard copy failed.", true);
      }
    });

    applyGameBtn.addEventListener("click", async () => {
      try {
        if (points.length < 2) throw new Error("Add at least 2 bullet points.");
        const weaponName = (weaponNameInput.value || "").trim();
        if (!weaponName) throw new Error("Weapon name is required.");
        const data = await jsonFetch("/api/pattern-generator/append", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...patternPayload(),
            game_id: gameIdInput.value || "cs2",
            weapon_name: weaponName,
            overwrite: true,
          }),
        });
        setStatus(
          `Updated ${weaponName} in cs2.py (${data.steps} steps). Backup: ${data.backup_path}`,
          false,
        );
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    sendLabBtn.addEventListener("click", async () => {
      try {
        if (!output.value.trim()) {
          await generatePattern();
        }
        const payload = { pattern: output.value, ts: Date.now() };
        localStorage.setItem("kryptaim.pattern.import", JSON.stringify(payload));

        if (window.opener && !window.opener.closed) {
          try {
            window.opener.postMessage({ type: "kryptaim_pattern_import", pattern: output.value }, window.location.origin);
            window.opener.focus();
            setStatus("Pattern sent to Recoil Lab.", false);
            return;
          } catch (_) {
            // fallback below
          }
        }

        window.open("/", "_blank");
        setStatus("Opened AimSync tab. Pattern is queued for import.", false);
      } catch (err) {
        setStatus(err.message || "Failed to send pattern to Recoil Lab.", true);
      }
    });

    if (exportModeInput) {
      exportModeInput.addEventListener("change", () => {
        updateExportUi();
        scheduleAutoGenerate();
      });
    }

    applyPresetFields("famas");
    presetSelect.value = "famas";
    loadReferenceWeapons()
      .then(() => applyPresetFields("famas"))
      .catch((err) => setStatus(err.message, true));
    updateExportUi();
    updateFrameUi();
    draw();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".pattern-generator-root").forEach(initGenerator);
  });
})();
