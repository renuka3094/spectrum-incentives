(function () {
  "use strict";

  // ---------- helpers ----------

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  const csrftoken = getCookie("csrftoken");

  function el(id) {
    return document.getElementById(id);
  }

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#7c5cff";
  }

  // ---------- animated number count-up ----------
  // Generic helper: animates a number from `from` to `to`, calling `format`
  // on every frame's rounded value to build the displayed text. Used for
  // points, pace %, goal counts, and leaderboard scores so updates feel
  // alive instead of snapping.
  function animateNumber(elem, to, { from = 0, duration = 900, format = (v) => String(v) } = {}) {
    if (!elem) return;
    const start = performance.now();
    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const val = Math.round(from + (to - from) * eased);
      elem.textContent = format(val);
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  const dataTag = el("dashboard-data");
  const state = dataTag ? JSON.parse(dataTag.textContent) : { progress: {}, history: [] };
  let lastRingPct = 0;

  // ---------- tier progress ring (hand-drawn canvas, no chart library) ----------

  function drawRing(pct) {
    const canvas = el("tier-ring");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const size = canvas.width;
    const center = size / 2;
    const radius = center - 12;
    const start = -Math.PI / 2;

    ctx.clearRect(0, 0, size, size);

    // track
    ctx.beginPath();
    ctx.arc(center, center, radius, 0, Math.PI * 2);
    ctx.lineWidth = 14;
    ctx.strokeStyle = cssVar("--border");
    ctx.stroke();

    // progress arc
    const end = start + (Math.PI * 2 * Math.min(100, Math.max(0, pct))) / 100;
    ctx.beginPath();
    ctx.arc(center, center, radius, start, end);
    ctx.lineWidth = 14;
    ctx.lineCap = "round";
    const gradient = ctx.createLinearGradient(0, 0, size, size);
    gradient.addColorStop(0, cssVar("--accent"));
    gradient.addColorStop(1, cssVar("--accent-strong"));
    ctx.strokeStyle = gradient;
    ctx.stroke();
  }

  function animateRing(fromPct, toPct) {
    const durationMs = 600;
    const start = performance.now();
    function frame(now) {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      const pct = fromPct + (toPct - fromPct) * eased;
      drawRing(pct);
      lastRingPct = pct;
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  animateRing(0, state.progress.is_maxed ? 100 : state.progress.pct_to_next || 0);
  animateNumber(el("hero-points"), state.progress.points || 0, { duration: 1000 });

  // ---------- on-load count-ups elsewhere on the page ----------

  const paceEl = el("pace-pct");
  if (paceEl) {
    const target = parseInt(paceEl.dataset.value, 10) || 0;
    const mode = paceEl.dataset.mode;
    animateNumber(paceEl, target, {
      duration: 1100,
      format: (v) => (mode === "pct" ? `${v >= 0 ? "+" : ""}${v}%` : `${v} pts`),
    });
  }

  document.querySelectorAll(".goal-sold").forEach((elm) => {
    const target = parseInt(elm.textContent, 10) || 0;
    animateNumber(elm, target, { duration: 800 });
  });

  ["lifetime-points", "units-remaining"].forEach((id) => {
    const elm = el(id);
    if (!elm) return;
    const target = parseInt(elm.dataset.value, 10) || 0;
    animateNumber(elm, target, { duration: 1000 });
  });

  const cashEl = el("lifetime-cash");
  if (cashEl) {
    const target = parseInt(cashEl.dataset.value, 10) || 0;
    animateNumber(cashEl, target, { duration: 1100, format: (v) => `$${v.toLocaleString()}` });
  }

  // ---------- history bar chart ----------

  // The canvas's `width`/`height` attributes (720x180) set its internal
  // drawing resolution, while CSS stretches it to `width: 100%` for
  // responsiveness. On a narrow phone that stretch runs backwards — the
  // 720px-wide drawing gets squeezed into ~340 CSS px, shrinking every bar,
  // label, and number along with it until the point/month labels are
  // barely legible. Resizing the actual backing store to match the
  // canvas's real on-screen size (times devicePixelRatio, for crispness on
  // retina screens) keeps everything drawn at its true, readable size
  // no matter how narrow the screen is.
  function sizeCanvasForDisplay(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const cssW = rect.width || canvas.clientWidth || canvas.width;
    const cssH = rect.height || canvas.clientHeight || canvas.height;
    const pxW = Math.max(1, Math.round(cssW * dpr));
    const pxH = Math.max(1, Math.round(cssH * dpr));
    if (canvas.width !== pxW || canvas.height !== pxH) {
      canvas.width = pxW;
      canvas.height = pxH;
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w: cssW, h: cssH };
  }

  function drawHistory(history) {
    const canvas = el("history-chart");
    if (!canvas || !history || !history.length) return;
    const { ctx, w, h } = sizeCanvasForDisplay(canvas);
    ctx.clearRect(0, 0, w, h);

    const max = Math.max(...history.map((d) => d.points), 1);
    const padding = 28;
    const chartH = h - padding;
    const barGap = 18;
    const barW = (w - barGap * (history.length + 1)) / history.length;

    const trackColor = cssVar("--border");
    const accentColor = cssVar("--accent");
    const dimColor = cssVar("--text-dim");
    const textColor = cssVar("--text");

    ctx.font = "12px Inter, sans-serif";
    history.forEach((d, i) => {
      const barH = (d.points / max) * (chartH - 20);
      const x = barGap + i * (barW + barGap);
      const y = chartH - barH;

      ctx.fillStyle = i === history.length - 1 ? accentColor : trackColor;
      const r = 6;
      ctx.beginPath();
      ctx.moveTo(x, chartH);
      ctx.lineTo(x, y + r);
      ctx.arcTo(x, y, x + r, y, r);
      ctx.lineTo(x + barW - r, y);
      ctx.arcTo(x + barW, y, x + barW, y + r, r);
      ctx.lineTo(x + barW, chartH);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = dimColor;
      ctx.textAlign = "center";
      ctx.fillText(d.label, x + barW / 2, h - 8);
      ctx.fillStyle = textColor;
      ctx.fillText(String(d.points), x + barW / 2, y - 6 < 10 ? 10 : y - 6);
    });
  }

  drawHistory(state.history);

  // redraw canvases in the new palette when the theme flips, without
  // re-triggering the fill animation
  document.addEventListener("spectrum:themechange", () => {
    drawRing(lastRingPct);
    drawHistory(state.history);
  });

  // re-fit the chart's backing resolution when the viewport changes width
  // (window resize, or a phone rotating) — debounced since resize fires
  // continuously while dragging.
  let historyResizeTimer = null;
  window.addEventListener("resize", () => {
    clearTimeout(historyResizeTimer);
    historyResizeTimer = setTimeout(() => drawHistory(state.history), 150);
  });

  // ---------- hero card tilt (subtle 3D tilt on mouse move) ----------

  (function () {
    const card = document.querySelector(".hero-card");
    if (!card) return;
    const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) return;

    const MAX_TILT = 6; // degrees

    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width;
      const py = (e.clientY - rect.top) / rect.height;
      const rotateY = (px - 0.5) * MAX_TILT * 2;
      const rotateX = (0.5 - py) * MAX_TILT * 2;
      card.style.transform = `perspective(700px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(700px) rotateX(0deg) rotateY(0deg)";
    });
  })();

  // ---------- tabs ----------

  let leaderboardAnimated = false;

  function animateLeaderboardPoints() {
    if (leaderboardAnimated) return;
    leaderboardAnimated = true;
    document.querySelectorAll(".lb-points").forEach((elm) => {
      const target = parseInt(elm.dataset.value, 10) || 0;
      animateNumber(elm, target, { duration: 900, format: (v) => `${v} pts` });
    });
  }

  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const panel = el("panel-" + btn.dataset.tab);
      if (panel) panel.classList.add("active");
      if (btn.dataset.tab === "leaderboard") animateLeaderboardPoints();
    });
  });

  // ---------- subtabs (leaderboard: my region / company-wide) ----------

  const subtabButtons = document.querySelectorAll(".subtab-btn");
  subtabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      subtabButtons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".lb-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const panel = el("lb-" + btn.dataset.subtab);
      if (panel) panel.classList.add("active");
    });
  });

  // ---------- live countdown to incentive end ----------

  if (state.periodEnd) {
    // periodEnd is a date like "2026-09-30" — count down to the end of that day, local time.
    const target = new Date(state.periodEnd + "T23:59:59");
    const countdownEl = el("countdown");

    function tickCountdown() {
      if (!countdownEl) return;
      const diff = target.getTime() - Date.now();
      if (diff <= 0) {
        countdownEl.textContent = "Incentive ended";
        return;
      }
      const totalSeconds = Math.floor(diff / 1000);
      const days = Math.floor(totalSeconds / 86400);
      const hours = Math.floor((totalSeconds % 86400) / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      countdownEl.textContent = `${days}d ${String(hours).padStart(2, "0")}h ${String(minutes).padStart(2, "0")}m ${String(seconds).padStart(2, "0")}s`;
    }

    tickCountdown();
    setInterval(tickCountdown, 1000);
  }

  // ---------- live company-wide activity ticker ----------

  (function () {
    const track = el("ticker-track");
    if (!track) return;

    async function refreshTicker() {
      try {
        const res = await fetch("/api/activity/");
        const data = await res.json();
        if (!data.items || !data.items.length) return;
        const itemsHtml = data.items.map((t) => `<span class="ticker-item">${escapeHtml(t)}</span>`).join("");
        // duplicated back-to-back so the CSS translateX(-50%) loop is seamless
        track.innerHTML = itemsHtml + itemsHtml;
      } catch (e) {
        // keep showing whatever's already on screen
      }
    }

    setInterval(refreshTicker, 25000);
  })();

  // ---------- achievement share cards ----------

  function drawShareCard(name, emoji, earnedText) {
    const canvas = el("share-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    const bg = ctx.createLinearGradient(0, 0, w, h);
    bg.addColorStop(0, cssVar("--accent-strong"));
    bg.addColorStop(1, cssVar("--accent"));
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // soft corner glow
    ctx.save();
    ctx.globalAlpha = 0.18;
    ctx.beginPath();
    ctx.arc(w * 0.85, h * 0.1, 160, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.restore();

    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(255,255,255,0.85)";
    ctx.font = "600 15px Inter, sans-serif";
    ctx.fillText("SPECTRUM INCENTIVES", w / 2, 44);

    ctx.font = "80px sans-serif";
    ctx.fillText(emoji, w / 2, 190);

    ctx.fillStyle = "#ffffff";
    ctx.font = "700 30px 'Space Grotesk', sans-serif";
    ctx.fillText(name, w / 2, 250);

    ctx.font = "500 14px Inter, sans-serif";
    ctx.fillStyle = "rgba(255,255,255,0.75)";
    const who = state.agentName ? `${state.agentAvatar || ""} ${state.agentName}`.trim() : "";
    const when = earnedText && earnedText.trim() ? earnedText.trim() : new Date().toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
    ctx.fillText(`Unlocked by ${who} · ${when}`, w / 2, h - 34);

    const link = el("download-share-card");
    if (link) {
      const safeName = name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
      link.href = canvas.toDataURL("image/png");
      link.setAttribute("download", `spectrum-${safeName}.png`);
    }
  }

  const shareBackdrop = el("share-card-backdrop");
  const closeShareBtn = el("close-share-card");

  document.addEventListener("click", (e) => {
    const shareBtn = e.target.closest(".badge-share");
    if (!shareBtn) return;
    const { name, emoji, earned } = shareBtn.dataset;
    drawShareCard(name, emoji, earned);
    if (shareBackdrop) shareBackdrop.classList.add("open");
  });

  if (closeShareBtn) closeShareBtn.addEventListener("click", () => shareBackdrop.classList.remove("open"));
  if (shareBackdrop) {
    shareBackdrop.addEventListener("click", (e) => {
      if (e.target === shareBackdrop) shareBackdrop.classList.remove("open");
    });
  }

  // ---------- modal ----------

  const backdrop = el("log-sale-backdrop");
  const openBtn = el("open-log-sale");
  const closeBtn = el("close-log-sale");

  if (openBtn) {
    openBtn.addEventListener("click", () => backdrop.classList.add("open"));
  }
  if (closeBtn) {
    closeBtn.addEventListener("click", () => backdrop.classList.remove("open"));
  }
  if (backdrop) {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.classList.remove("open");
    });
  }

  // ---------- modal accessibility: focus trap + Escape to close ----------
  // Applies to every .modal-backdrop on the page (log-sale, share card,
  // mystery box) rather than just this one, so opening any of them keeps
  // keyboard/screen-reader focus inside the dialog, Tab wraps instead of
  // escaping to the page behind it, Escape closes it, and focus returns to
  // whatever triggered it on close — standard modal behavior that was
  // missing entirely before.

  (function () {
    const backdrops = document.querySelectorAll(".modal-backdrop");
    if (!backdrops.length) return;

    function getFocusable(container) {
      return Array.from(
        container.querySelectorAll(
          'a[href], button:not([disabled]), textarea, input:not([disabled]), select, [tabindex]:not([tabindex="-1"])'
        )
      ).filter((elm) => elm.offsetParent !== null);
    }

    const lastFocusedByBackdrop = new WeakMap();

    backdrops.forEach((bd) => {
      const modal = bd.querySelector(".modal");
      if (!modal) return;
      modal.setAttribute("tabindex", "-1");

      const observer = new MutationObserver(() => {
        if (bd.classList.contains("open")) {
          lastFocusedByBackdrop.set(bd, document.activeElement);
          const focusables = getFocusable(modal);
          (focusables[0] || modal).focus({ preventScroll: true });
        } else {
          const toRestore = lastFocusedByBackdrop.get(bd);
          if (toRestore && document.body.contains(toRestore)) {
            toRestore.focus({ preventScroll: true });
          }
          lastFocusedByBackdrop.delete(bd);
        }
      });
      observer.observe(bd, { attributes: true, attributeFilter: ["class"] });
    });

    // Bound to `document`, not the individual backdrop — content inside an
    // open modal (like the recent-submissions list) can get its innerHTML
    // swapped out from under a focused button, which the browser resolves
    // by quietly moving focus to <body>. A listener scoped to the backdrop
    // would go deaf at that exact moment since <body> isn't inside it;
    // listening on `document` and looking up whichever backdrop is
    // currently open keeps Escape/Tab working regardless of where focus
    // actually landed.
    document.addEventListener("keydown", (e) => {
      const openBackdrop = document.querySelector(".modal-backdrop.open");
      if (!openBackdrop) return;
      const modal = openBackdrop.querySelector(".modal");
      if (!modal) return;

      if (e.key === "Escape") {
        openBackdrop.classList.remove("open");
        return;
      }

      if (e.key !== "Tab") return;
      const focusables = getFocusable(modal);
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      } else if (!modal.contains(document.activeElement)) {
        // focus drifted outside the modal (e.g. onto <body> after a DOM
        // swap) — pull it back in rather than letting Tab continue from body
        e.preventDefault();
        first.focus();
      }
    });
  })();

  // quantity stepper
  const qtyInput = el("sale-qty");
  const qtyMinus = el("qty-minus");
  const qtyPlus = el("qty-plus");
  if (qtyMinus) qtyMinus.addEventListener("click", () => {
    qtyInput.value = Math.max(1, parseInt(qtyInput.value || "1", 10) - 1);
  });
  if (qtyPlus) qtyPlus.addEventListener("click", () => {
    qtyInput.value = Math.min(50, parseInt(qtyInput.value || "1", 10) + 1);
  });

  // ---------- log-sale live point-impact preview ----------
  // As the agent picks a product/quantity, show what it would be worth and
  // how close that gets them to their next tier — *before* they submit.
  // Nothing here is authoritative (the sale still goes in "pending" and the
  // real math happens server-side on approval, same as ever) — it's purely
  // a preview so the decision of what to log feels informed instead of a
  // guess. Also flags up front when a quantity would blow the daily cap,
  // since api_log_sale rejects the whole request rather than partially
  // logging it.

  const saleProductSelect = el("sale-product");
  const salePreviewPoints = el("sale-preview-points");
  const salePreviewNote = el("sale-preview-note");
  const capWarning = el("cap-warning");
  const logSaleSubmit = el("log-sale-submit");

  function currentDailyRemaining() {
    const capEl = el("daily-cap-remaining");
    if (!capEl) return state.dailyCap || 0;
    const n = parseInt(capEl.textContent, 10);
    return Number.isNaN(n) ? state.dailyCap || 0 : n;
  }

  function updateSalePreview() {
    if (!salePreviewPoints || !saleProductSelect || !qtyInput) return;
    const productId = saleProductSelect.value;
    const quantity = Math.max(1, parseInt(qtyInput.value || "1", 10));
    const perUnit = (state.productPoints && state.productPoints[productId]) || 0;
    const points = perUnit * quantity;

    salePreviewPoints.textContent = `+${points} pt${points === 1 ? "" : "s"}`;

    if (state.progress && state.progress.is_maxed) {
      salePreviewNote.textContent = "You're already at the top tier — nice going.";
    } else if (state.progress && state.progress.nextTierName) {
      const remaining = state.progress.pointsToNext - points;
      if (remaining <= 0) {
        salePreviewNote.textContent = `once approved, this is enough to reach ${state.progress.nextTierEmoji || ""} ${state.progress.nextTierName} 🎉`.trim();
      } else {
        salePreviewNote.textContent = `once approved, ${remaining} pt${remaining === 1 ? "" : "s"} short of ${state.progress.nextTierEmoji || ""} ${state.progress.nextTierName}`.trim();
      }
    } else {
      salePreviewNote.textContent = "once approved";
    }

    if (capWarning) {
      const remainingToday = currentDailyRemaining();
      if (quantity > remainingToday) {
        capWarning.textContent = remainingToday > 0
          ? `Only ${remainingToday} unit${remainingToday === 1 ? "" : "s"} left in today's logging cap — lower the quantity or it'll be rejected.`
          : "Today's logging cap is used up — try again tomorrow.";
        capWarning.hidden = false;
        if (logSaleSubmit) logSaleSubmit.disabled = true;
      } else {
        capWarning.hidden = true;
        if (logSaleSubmit) logSaleSubmit.disabled = false;
      }
    }
  }

  if (saleProductSelect) saleProductSelect.addEventListener("change", updateSalePreview);
  if (qtyInput) qtyInput.addEventListener("input", updateSalePreview);
  if (qtyMinus) qtyMinus.addEventListener("click", updateSalePreview);
  if (qtyPlus) qtyPlus.addEventListener("click", updateSalePreview);
  if (openBtn) openBtn.addEventListener("click", updateSalePreview);
  updateSalePreview();

  // ---------- toast (queued — a level-up + several badge unlocks can all
  // fire off one action, and they should show one at a time, not stomp
  // on each other) ----------

  const toastQueue = [];
  let toastBusy = false;

  function showToast(text) {
    toastQueue.push(text);
    processToastQueue();
  }

  function processToastQueue() {
    const toast = el("level-up-toast");
    if (!toast || toastBusy || toastQueue.length === 0) return;
    toastBusy = true;
    const text = toastQueue.shift();
    el("level-up-text").textContent = text;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => {
        toastBusy = false;
        processToastQueue();
      }, 300); // matches the CSS fade-out transition
    }, 2400);
  }

  // ---------- cancel a pending submission ----------
  // The "recent submissions" list is re-rendered wholesale (new HTML swapped
  // in) after every log/cancel action, so its Cancel buttons don't exist yet
  // when this script first runs — the click listener has to live on the
  // stable container (#recent-sales-list) and delegate down to whichever
  // button is actually on screen at click time.

  const recentSalesList = el("recent-sales-list");
  if (recentSalesList) {
    recentSalesList.addEventListener("click", async (e) => {
      const btn = e.target.closest(".recent-sale-cancel");
      if (!btn) return;
      const saleId = btn.dataset.saleId;
      if (!saleId) return;

      btn.disabled = true;
      btn.textContent = "Canceling…";

      try {
        const res = await fetch(`/api/cancel-sale/${saleId}/`, {
          method: "POST",
          headers: { "X-CSRFToken": csrftoken },
        });
        const data = await res.json();

        if (!res.ok || data.error) {
          showToast(data.error || "Couldn't cancel that submission.");
          btn.disabled = false;
          btn.textContent = "Cancel";
          return;
        }

        const capEl = el("daily-cap-remaining");
        if (capEl) capEl.textContent = data.daily_remaining;

        if (data.recent_sales_html) {
          recentSalesList.innerHTML = data.recent_sales_html;
        }
        showToast("Submission canceled.");
        updateSalePreview();
      } catch (err) {
        showToast("Network error — try again.");
        btn.disabled = false;
        btn.textContent = "Cancel";
      }
    });
  }

  // ---------- level-up sound (synthesized — no audio file, no network) ----------

  function playLevelUpSound() {
    if (window.SpectrumSound && window.SpectrumSound.isMuted()) return;
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      const ctx = new Ctx();
      const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6 — a quick triumphant arpeggio
      notes.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "triangle";
        osc.frequency.value = freq;
        const startAt = ctx.currentTime + i * 0.09;
        gain.gain.setValueAtTime(0, startAt);
        gain.gain.linearRampToValueAtTime(0.18, startAt + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, startAt + 0.35);
        osc.connect(gain).connect(ctx.destination);
        osc.start(startAt);
        osc.stop(startAt + 0.4);
      });
      setTimeout(() => ctx.close(), 1000);
    } catch (e) {
      // Web Audio unsupported/blocked — fail silently, the visual confetti still lands.
    }
  }

  // ---------- mystery-box sparkle (synthesized — no audio file) ----------

  function playMysteryChime() {
    if (window.SpectrumSound && window.SpectrumSound.isMuted()) return;
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      const ctx = new Ctx();
      const notes = [784, 1174.66]; // G5, D6 — a quick two-note sparkle, distinct from the level-up arpeggio
      notes.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;
        const startAt = ctx.currentTime + i * 0.12;
        gain.gain.setValueAtTime(0, startAt);
        gain.gain.linearRampToValueAtTime(0.16, startAt + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, startAt + 0.3);
        osc.connect(gain).connect(ctx.destination);
        osc.start(startAt);
        osc.stop(startAt + 0.35);
      });
      setTimeout(() => ctx.close(), 800);
    } catch (e) {
      // Web Audio unsupported/blocked — fail silently.
    }
  }

  // ---------- achievement unlocks ----------

  function unlockAchievements(achievements) {
    const countEl = el("ach-tab-count");
    let earned = 0;
    if (countEl) {
      const [have] = countEl.textContent.split("/").map((n) => parseInt(n, 10));
      earned = have;
    }

    achievements.forEach((ach) => {
      const card = document.querySelector(`.badge-card[data-key="${CSS.escape(ach.key)}"]`);
      if (card) {
        card.classList.remove("locked");
        card.classList.add("unlocked", "pop");
        const pill = card.querySelector(".pill");
        if (pill) {
          pill.textContent = "Unlocked";
          pill.classList.remove("pill-locked");
          pill.classList.add("pill-success");
        }
      }
      // the toast queue (see showToast) handles sequencing so this never
      // overlaps the level-up toast or another badge's toast
      showToast(`🏅 Achievement unlocked: ${ach.name}!`);
    });

    if (countEl) {
      const [, total] = countEl.textContent.split("/");
      countEl.textContent = `${earned + achievements.length}/${total}`;
    }
  }

  // ---------- bonus quest unlocks ----------

  function unlockTasks(tasks) {
    const countEl = el("tasks-tab-count");
    let earned = 0;
    if (countEl) {
      const [have] = countEl.textContent.split("/").map((n) => parseInt(n, 10));
      earned = have;
    }

    tasks.forEach((t) => {
      const card = document.querySelector(`.task-card[data-key="${CSS.escape(t.key)}"]`);
      if (card) {
        card.classList.add("done", "pop");
        const pill = card.querySelector(".pill");
        if (pill) {
          pill.textContent = `+${t.points} pts ✓`;
          pill.classList.remove("pill-locked");
          pill.classList.add("pill-success");
        }
      }
      // same toast queue as achievements/level-ups — never overlaps
      showToast(`✅ Quest complete: ${t.name} (+${t.points} pts)`);
    });

    if (countEl) {
      const [, total] = countEl.textContent.split("/");
      countEl.textContent = `${earned + tasks.length}/${total}`;
    }
  }

  // ---------- weekly challenge unlocks ----------
  // Same shape as unlockTasks (task-card, data-key, pill swap) — the weekly
  // challenge board deliberately reuses the exact task-card markup/CSS
  // (see _weekly_challenges.html), so the same DOM-update logic works
  // unchanged; only the container id and count element differ.

  function unlockWeeklyChallenges(challenges) {
    const countEl = el("weekly-tab-count");

    challenges.forEach((c) => {
      const card = document.querySelector(`#weekly-challenge-list .task-card[data-key="${CSS.escape(c.key)}"]`);
      if (card) {
        card.classList.add("done", "pop");
        const pill = card.querySelector(".pill");
        if (pill) {
          pill.textContent = `+${c.points} pts ✓`;
          pill.classList.remove("pill-locked");
          pill.classList.add("pill-success");
        }
      }
      showToast(`🗓️ Weekly challenge complete: ${c.name} (+${c.points} pts)`);
    });

    if (countEl) {
      const match = countEl.textContent.match(/(\d+) of (\d+)/);
      if (match) {
        const have = parseInt(match[1], 10) + challenges.length;
        countEl.textContent = countEl.textContent.replace(/^\d+ of \d+/, `${have} of ${match[2]}`);
      }
    }
  }

  // ---------- level up ----------

  function celebrateLevelUp(level) {
    if (!level) return;
    const emojiEl = el("level-badge-emoji");
    if (emojiEl) {
      emojiEl.textContent = level.emoji;
      emojiEl.classList.add("pop");
    }
    const numberEl = el("level-number");
    if (numberEl) numberEl.textContent = level.level;
    const titleEl = el("level-title");
    if (titleEl) titleEl.textContent = level.title;
    const tabBadgeEl = el("level-tab-badge");
    if (tabBadgeEl) tabBadgeEl.textContent = level.level;

    showToast(`⬆️ Level up! You're now Level ${level.level} — ${level.title}`);
    launchConfetti();
    playLevelUpSound();
  }

  // ---------- Clean Streak ----------
  // No wheel, no draw step, nothing to animate on click — the streak is
  // rendered straight from the server (clean_streak.current/progress_pct in
  // the template), since it's fully determined by real approval/rejection
  // history rather than anything the agent does in the browser. The only
  // thing JS does for this mechanic is celebrate milestone(s) newly crossed
  // since the last page load (state.newCleanStreaks, from
  // insights.sync_clean_streak), same "newly earned this call" pattern as
  // achievements/tasks/weekly challenges above.

  function celebrateCleanStreaks(awards) {
    if (!awards || !awards.length) return;

    awards.forEach((a) => {
      showToast(`🔥 Clean Streak milestone: ${a.streak_length} in a row! (+${a.points_awarded} pts)`);
    });

    const feed = el("clean-streak-feed");
    if (feed) {
      awards
        .slice()
        .reverse()
        .forEach((a) => {
          const row = document.createElement("div");
          row.className = "mini-row pop";
          row.innerHTML = `<span>🔥 ${a.streak_length}-streak</span><span class="muted small">+${a.points_awarded} pts</span>`;
          feed.insertBefore(row, feed.firstChild);
        });
    }

    launchConfetti();
    playMysteryChime();
  }

  // ---------- mystery box (surprise bonus when a goal is completed) ----------

  const mysteryQueue = [];
  let mysteryBusy = false;

  function queueMysteryBox(box) {
    mysteryQueue.push(box);
    processMysteryQueue();
  }

  function processMysteryQueue() {
    const backdrop = el("mystery-box-backdrop");
    if (!backdrop || mysteryBusy || mysteryQueue.length === 0) return;
    mysteryBusy = true;
    openMysteryBox(mysteryQueue.shift());
  }

  function openMysteryBox(box) {
    const backdrop = el("mystery-box-backdrop");
    const emojiEl = el("mystery-emoji");
    const revealEl = el("mystery-reveal");
    const titleEl = el("mystery-title");
    const subEl = el("mystery-sub");
    if (!backdrop || !emojiEl) return;

    emojiEl.textContent = "🎁";
    emojiEl.classList.remove("mystery-open");
    revealEl.hidden = true;
    backdrop.classList.add("open");
    emojiEl.classList.add("mystery-shake");

    setTimeout(() => {
      emojiEl.classList.remove("mystery-shake");
      emojiEl.textContent = "🎉";
      emojiEl.classList.add("mystery-open");
      titleEl.textContent = `+${box.points} pts`;
      subEl.textContent = `Surprise bonus for completing ${box.product}!`;
      revealEl.hidden = false;
      launchConfetti();
      playMysteryChime();
    }, 650);
  }

  function closeMysteryBox() {
    const backdrop = el("mystery-box-backdrop");
    if (backdrop) backdrop.classList.remove("open");
    mysteryBusy = false;
    processMysteryQueue();
  }

  const mysteryCloseBtn = el("close-mystery-box");
  const mysteryBackdrop = el("mystery-box-backdrop");
  if (mysteryCloseBtn) mysteryCloseBtn.addEventListener("click", closeMysteryBox);
  if (mysteryBackdrop) {
    mysteryBackdrop.addEventListener("click", (e) => {
      if (e.target === mysteryBackdrop) closeMysteryBox();
    });
  }

  // ---------- confetti burst (hand-rolled particle system, no library) ----------

  function launchConfetti() {
    const canvas = document.createElement("canvas");
    canvas.id = "confetti-canvas";
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");

    const colors = [
      cssVar("--accent"),
      cssVar("--accent-strong"),
      cssVar("--gold"),
      cssVar("--silver"),
      cssVar("--success"),
    ];

    const particles = Array.from({ length: 140 }, () => ({
      x: canvas.width / 2 + (Math.random() - 0.5) * 120,
      y: canvas.height * 0.35 + (Math.random() - 0.5) * 40,
      vx: (Math.random() - 0.5) * 12,
      vy: Math.random() * -12 - 4,
      size: Math.random() * 7 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * Math.PI * 2,
      spin: (Math.random() - 0.5) * 0.3,
      shape: Math.random() > 0.5 ? "rect" : "circle",
      gravity: 0.35 + Math.random() * 0.15,
      drag: 0.99,
    }));

    const startedAt = performance.now();
    const durationMs = 2600;

    function frame(now) {
      const elapsed = now - startedAt;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const fade = Math.max(0, 1 - elapsed / durationMs);

      particles.forEach((p) => {
        p.vx *= p.drag;
        p.vy = p.vy * p.drag + p.gravity;
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.spin;

        ctx.save();
        ctx.globalAlpha = fade;
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation);
        ctx.fillStyle = p.color;
        if (p.shape === "rect") {
          ctx.fillRect(-p.size / 2, -p.size / 3, p.size, p.size * 0.66);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      });

      if (elapsed < durationMs) {
        requestAnimationFrame(frame);
      } else {
        canvas.remove();
      }
    }
    requestAnimationFrame(frame);
  }

  // ---------- log sale submit ----------
  // A self-logged sale does NOT count instantly anymore — it's saved
  // "pending" and only affects points/tiers/goals/badges once an admin
  // approves it (see the README/views.py for the reasoning). So this handler
  // no longer animates the ring, goals, or triggers any celebration — it
  // just confirms the submission landed, shows the running daily cap, and
  // drops the new row into "Your recent submissions" right in the modal.
  // The celebration for anything that *does* get approved happens on the
  // next page load instead — see "on-load celebration" below.

  const form = el("log-sale-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = el("log-sale-msg");
      msg.textContent = "Logging…";

      const productId = el("sale-product").value;
      const quantity = el("sale-qty").value;

      try {
        const res = await fetch("/api/log-sale/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({ product_id: productId, quantity: quantity }),
        });
        const data = await res.json();

        if (!res.ok || data.error) {
          msg.textContent = data.error || "Something went wrong.";
          return;
        }

        msg.textContent = `Logged ✓ — pending review. ${data.daily_remaining} unit${data.daily_remaining === 1 ? "" : "s"} left today.`;

        const capEl = el("daily-cap-remaining");
        if (capEl) capEl.textContent = data.daily_remaining;

        const recentList = el("recent-sales-list");
        if (recentList && data.recent_sales_html) {
          recentList.innerHTML = data.recent_sales_html;
          const firstRow = recentList.querySelector(".recent-sale-row");
          if (firstRow) firstRow.classList.add("pop");
        }

        updateSalePreview();

        setTimeout(() => {
          msg.textContent = "";
        }, 3500);
      } catch (err) {
        msg.textContent = "Network error — try again.";
      }
    });
  }

  // ---------- on-load celebration ----------
  // Achievements/quests/mystery-boxes are synced fresh on every dashboard
  // load (see views.py) — most of the time nothing new comes back, but the
  // first load after an admin approves a backlog of pending sales, this is
  // where the "look what happened while you were away" moment fires.

  (function () {
    const hasAchievements = state.newAchievements && state.newAchievements.length;
    const hasTasks = state.newTasks && state.newTasks.length;
    const hasBoxes = state.newMysteryBoxes && state.newMysteryBoxes.length;
    const hasWeeklyChallenges = state.newWeeklyChallenges && state.newWeeklyChallenges.length;
    const hasCleanStreaks = state.newCleanStreaks && state.newCleanStreaks.length;
    const hasLevelUp = !!state.levelUp;
    if (!hasAchievements && !hasTasks && !hasBoxes && !hasWeeklyChallenges && !hasCleanStreaks && !hasLevelUp) return;

    setTimeout(() => {
      // Level-up first — it's the "biggest" moment, and celebrateLevelUp's
      // own confetti/toast shouldn't have to compete with a badge/quest
      // toast that's already mid-flight.
      if (hasLevelUp) celebrateLevelUp(state.levelUp);
      if (hasAchievements) unlockAchievements(state.newAchievements);
      if (hasTasks) unlockTasks(state.newTasks);
      if (hasWeeklyChallenges) unlockWeeklyChallenges(state.newWeeklyChallenges);
      if (hasCleanStreaks) celebrateCleanStreaks(state.newCleanStreaks);
      if (hasBoxes) state.newMysteryBoxes.forEach(queueMysteryBox);
    }, 1600); // wait out the splash screen (it fades until ~1.4s) so nothing pops behind it
  })();

  // ---------- refresh AI insights ----------

  const refreshBtn = el("refresh-insights");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = "Refreshing…";
      try {
        const res = await fetch("/api/insights/");
        const data = await res.json();
        renderInsights(data);
      } catch (err) {
        // silently keep old insights
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "Refresh";
      }
    });
  }

  function renderInsights(data) {
    const container = el("insights-content");
    if (!container) return;
    let html = "";

    if (data.tip) {
      html += `<div class="insight-row"><span class="insight-icon">🎯</span>
        <p><strong>Fastest path:</strong> sell <strong>${data.tip.units_needed}</strong> more ${escapeHtml(data.tip.product)} to reach your next tier.</p></div>`;
    }

    if (data.momentum) {
      const arrow = data.momentum.trend === "up" ? "📈" : data.momentum.trend === "down" ? "📉" : "➖";
      const deltaText = data.momentum.delta_pct !== null && data.momentum.delta_pct !== undefined
        ? ` (${data.momentum.delta_pct >= 0 ? "+" : ""}${data.momentum.delta_pct}% vs last week)`
        : "";
      html += `<div class="insight-row"><span class="insight-icon">${arrow}</span>
        <p><strong>This week:</strong> ${data.momentum.this_week} pts${deltaText}</p></div>`;
    }

    html += `<p class="eyebrow insight-subhead">Nearby, people are buying…</p>`;
    if (data.trending && data.trending.length) {
      data.trending.forEach((t) => {
        const youText = t.my_units === 0 ? "you haven't logged one yet" : `you: ${t.my_units}`;
        html += `<div class="insight-row trend-row"><span class="insight-icon">🔥</span>
          <p><strong>${escapeHtml(t.product_name)}</strong> — ${t.region_agents} agents near you sold ${t.region_units} this period, ${youText}.</p></div>`;
      });
    } else {
      html += `<p class="muted small">Not enough regional activity yet to spot a trend.</p>`;
    }

    container.innerHTML = html;
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
})();
