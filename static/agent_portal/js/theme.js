(function () {
  "use strict";

  var root = document.documentElement;
  var THEME_KEY = "spectrum_theme";
  var MUTE_KEY = "spectrum_muted";

  function safeGet(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function safeSet(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
  }

  // ---------- theme ----------

  function currentTheme() {
    return root.dataset.theme === "light" ? "light" : "dark";
  }

  function applyThemeIcon() {
    var knob = document.getElementById("theme-toggle-knob");
    if (knob) knob.textContent = currentTheme() === "light" ? "☀️" : "🌙";
  }

  function setTheme(theme) {
    root.dataset.theme = theme;
    safeSet(THEME_KEY, theme);
    applyThemeIcon();
    document.dispatchEvent(new CustomEvent("spectrum:themechange", { detail: { theme: theme } }));
  }

  var themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      setTheme(currentTheme() === "light" ? "dark" : "light");
    });
  }
  applyThemeIcon();

  // ---------- mute ----------

  var muted = safeGet(MUTE_KEY) === "1";

  function applyMuteIcon() {
    var btn = document.getElementById("mute-toggle");
    if (btn) btn.textContent = muted ? "🔇" : "🔊";
  }

  var muteBtn = document.getElementById("mute-toggle");
  if (muteBtn) {
    muteBtn.addEventListener("click", function () {
      muted = !muted;
      safeSet(MUTE_KEY, muted ? "1" : "0");
      applyMuteIcon();
    });
  }
  applyMuteIcon();

  // Exposed so dashboard.js can check mute state without duplicating storage logic.
  window.SpectrumSound = {
    isMuted: function () { return muted; },
  };

  // ---------- splash intro (once per browser session) ----------

  (function () {
    var SPLASH_KEY = "spectrum_splash_shown";
    var splash = document.getElementById("splash");
    if (!splash) return;

    var alreadyShown = false;
    try { alreadyShown = sessionStorage.getItem(SPLASH_KEY) === "1"; } catch (e) {}

    if (alreadyShown) {
      splash.hidden = true;
      return;
    }

    try { sessionStorage.setItem(SPLASH_KEY, "1"); } catch (e) {}

    setTimeout(function () {
      splash.classList.add("hide");
      setTimeout(function () { splash.hidden = true; }, 400);
    }, 1000);
  })();

  // ---------- compact header on scroll ----------

  (function () {
    var topbar = document.getElementById("topbar");
    if (!topbar) return;
    var THRESHOLD = 40;

    function onScroll() {
      if (window.scrollY > THRESHOLD) {
        topbar.classList.add("compact");
      } else {
        topbar.classList.remove("compact");
      }
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  })();

  // ---------- avatar picker ----------

  (function () {
    function getCookie(name) {
      var value = "; " + document.cookie;
      var parts = value.split("; " + name + "=");
      if (parts.length === 2) return parts.pop().split(";").shift();
      return null;
    }

    var backdrop = document.getElementById("avatar-picker-backdrop");
    var openBtn = document.getElementById("open-avatar-picker");
    var closeBtn = document.getElementById("close-avatar-picker");
    if (!backdrop || !openBtn) return;

    openBtn.addEventListener("click", function () { backdrop.classList.add("open"); });
    if (closeBtn) closeBtn.addEventListener("click", function () { backdrop.classList.remove("open"); });
    backdrop.addEventListener("click", function (e) {
      if (e.target === backdrop) backdrop.classList.remove("open");
    });

    backdrop.querySelectorAll(".avatar-choice").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var avatar = btn.dataset.avatar;
        fetch("/api/set-avatar/", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
          body: JSON.stringify({ avatar: avatar }),
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (!data.ok) return;
            var topbarAvatar = document.getElementById("topbar-avatar");
            var greetingAvatar = document.getElementById("greeting-avatar");
            if (topbarAvatar) topbarAvatar.textContent = data.avatar;
            if (greetingAvatar) greetingAvatar.textContent = data.avatar;
            backdrop.classList.remove("open");
          })
          .catch(function () {});
      });
    });
  })();
})();
