(function () {
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

    function setStatus(text, isError) {
      status.textContent = text;
      status.className = `text-xs ${isError ? "text-red-300" : "text-white/40"}`;
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

    function applyDetectedPayload(data, sourceLabel, includeSuggested) {
      frameDataUrls = Array.isArray(data.frame_data_urls) && data.frame_data_urls.length
        ? data.frame_data_urls
        : [data.preview_data_url];
      activeFrameIndex = 0;
      if (includeSuggested) points = data.suggested_points || [];
      showFrame(0);
      renderPointsList();
      setStatus(`Loaded ${sourceLabel}. ${includeSuggested ? "Suggested points applied." : "Ready for manual marking."}`, false);
    }

    async function loadFromFile(includeSuggested) {
      const file = fileInput.files && fileInput.files[0];
      if (!file) throw new Error("Select an image or GIF first.");

      const form = new FormData();
      form.append("spray_file", file);
      const data = await jsonFetch("/api/pattern-generator/detect", { method: "POST", body: form });
      applyDetectedPayload(data, file.name, includeSuggested);
    }

    async function loadFromUrl(includeSuggested) {
      const mediaUrl = (urlInput.value || "").trim();
      if (!mediaUrl) throw new Error("Paste an image/GIF URL first.");
      const data = await jsonFetch("/api/pattern-generator/detect-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ media_url: mediaUrl }),
      });
      applyDetectedPayload(data, mediaUrl, includeSuggested);
    }

    fileInput.addEventListener("change", async () => {
      try {
        await loadFromFile(false);
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    detectBtn.addEventListener("click", async () => {
      try {
        await loadFromFile(true);
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
      const data = await jsonFetch("/api/pattern-generator/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          points,
          delay_ms: Math.round(toNumber(delayMsInput, 90)),
          scale_x: toNumber(scaleXInput, 1),
          scale_y: toNumber(scaleYInput, 1),
          invert_x: invertXInput.checked,
          invert_y: invertYInput.checked,
            export_mode: exportModeInput ? exportModeInput.value : "canonical",
        }),
      });
      output.value = data.pattern_text;
      setStatus(`Generated ${data.steps_ms.length} recoil steps.`, false);
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
        setStatus("Pattern copied. Paste it in Recoil Lab Pattern field.", false);
      } catch (err) {
        setStatus(err.message || "Clipboard copy failed.", true);
      }
    });

    sendLabBtn.addEventListener("click", async () => {
      try {
        if (!output.value.trim()) {
          await generatePattern();
        }
        const payload = { pattern: output.value, ts: Date.now() };
        localStorage.setItem("aimsync.pattern.import", JSON.stringify(payload));

        if (window.opener && !window.opener.closed) {
          try {
            window.opener.postMessage({ type: "aimsync_pattern_import", pattern: output.value }, window.location.origin);
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

    updateFrameUi();
    draw();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".pattern-generator-root").forEach(initGenerator);
  });
})();
