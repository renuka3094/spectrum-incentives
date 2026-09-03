(function () {
  "use strict";

  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- role tabs (Agent / Incentive Analyst / Director) ----------
  // The tab picked here is a real assertion of which account type you're
  // logging in as, not just decoration — its value is kept in the hidden
  // #selected-role field submitted with the form, and the server (see
  // views.SpectrumLoginView.form_valid) rejects the login outright if the
  // credentials entered belong to a different role than whichever tab is
  // active. This also swaps the headline/demo-credentials copy to match,
  // same as before.

  const tabs = document.querySelectorAll(".role-tab");
  const heading = document.getElementById("auth-heading");
  const subtext = document.getElementById("auth-subtext");
  const demoUser = document.getElementById("auth-demo-user");
  const demoRole = document.getElementById("auth-demo-role");
  const selectedRoleField = document.getElementById("selected-role");
  const copyBlocks = [document.getElementById("auth-copy"), document.getElementById("auth-copy-demo")].filter(Boolean);

  function applyTabCopy(tab) {
    if (heading) heading.textContent = tab.dataset.heading;
    if (subtext) subtext.textContent = tab.dataset.subtext;
    if (demoUser) demoUser.textContent = tab.dataset.demoUser;
    if (demoRole) demoRole.textContent = tab.dataset.demoRole;
    if (selectedRoleField) selectedRoleField.value = tab.dataset.role;
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
      });
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");

      if (reduceMotion || !copyBlocks.length) {
        // No fade to wait on — swap immediately.
        applyTabCopy(tab);
        return;
      }

      // Fade the copy out, swap the text once it's invisible, fade back in.
      copyBlocks.forEach((el) => el.classList.add("is-swapping"));
      window.setTimeout(() => {
        applyTabCopy(tab);
        copyBlocks.forEach((el) => el.classList.remove("is-swapping"));
      }, 150);
    });
  });

  // ---------- password visibility toggle ----------

  (function () {
    const toggle = document.getElementById("toggle-password");
    const passwordInput = document.getElementById("id_password");
    if (!toggle || !passwordInput) return;

    toggle.addEventListener("click", () => {
      const showing = passwordInput.type === "text";
      passwordInput.type = showing ? "password" : "text";
      toggle.textContent = showing ? "👁" : "🙈";
      toggle.setAttribute("aria-label", showing ? "Show password" : "Hide password");
    });
  })();

  // ---------- Caps Lock warning on the password field ----------

  (function () {
    const passwordInput = document.getElementById("id_password");
    const warning = document.getElementById("caps-lock-warning");
    if (!passwordInput || !warning) return;

    const checkCapsLock = (e) => {
      const isOn = typeof e.getModifierState === "function" && e.getModifierState("CapsLock");
      warning.hidden = !isOn;
    };

    passwordInput.addEventListener("keydown", checkCapsLock);
    passwordInput.addEventListener("keyup", checkCapsLock);
    passwordInput.addEventListener("blur", () => { warning.hidden = true; });
  })();
})();
