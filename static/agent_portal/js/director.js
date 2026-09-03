(function () {
  "use strict";

  // Real in-app Director approval queue — Approve/Reject buttons wired
  // straight to views.api_review_sale, so a pending self-logged sale can be
  // resolved without leaving this page (the Sale admin's bulk actions still
  // work too, for anything beyond the top 8 shown here — see
  // insights.director_overview).

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

  const toastQueue = [];
  let toastBusy = false;

  function showToast(text) {
    toastQueue.push(text);
    processToastQueue();
  }

  function processToastQueue() {
    const toast = el("director-toast");
    if (!toast || toastBusy || toastQueue.length === 0) return;
    toastBusy = true;
    const text = toastQueue.shift();
    el("director-toast-text").textContent = text;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => {
        toastBusy = false;
        processToastQueue();
      }, 300);
    }, 2200);
  }

  const list = el("pending-review-list");
  if (!list) return;

  list.addEventListener("click", async (e) => {
    const btn = e.target.closest(".review-btn");
    if (!btn) return;

    const saleId = btn.dataset.saleId;
    const action = btn.dataset.action;
    if (!saleId || !action) return;

    const row = btn.closest(".pending-row");
    const rowButtons = row ? row.querySelectorAll(".review-btn") : [btn];
    rowButtons.forEach((b) => (b.disabled = true));
    btn.textContent = action === "approve" ? "Approving…" : "Rejecting…";

    try {
      const res = await fetch(`/api/review-sale/${saleId}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ action: action }),
      });
      const data = await res.json();

      if (!res.ok || data.error) {
        showToast(data.error || "Couldn't review that sale.");
        rowButtons.forEach((b) => (b.disabled = false));
        btn.textContent = action === "approve" ? "Approve" : "Reject";
        return;
      }

      if (row) {
        row.classList.add(action === "approve" ? "resolved-approve" : "resolved-reject");
        setTimeout(() => {
          row.remove();
          if (!list.querySelector(".pending-row")) {
            list.innerHTML = '<p class="muted">Nothing waiting on you right now.</p>';
          }
        }, 320);
      }

      const pendingEl = el("director-pending-count");
      if (pendingEl) pendingEl.textContent = data.pending_count;
      const chip = el("pending-stat-chip");
      if (chip) chip.classList.toggle("behind", data.pending_count > 0);

      const totalEl = el("director-total-points");
      if (totalEl && action === "approve") totalEl.textContent = data.total_points;

      showToast(action === "approve" ? "Sale approved ✓" : "Sale rejected");
    } catch (err) {
      showToast("Network error — try again.");
      rowButtons.forEach((b) => (b.disabled = false));
      btn.textContent = action === "approve" ? "Approve" : "Reject";
    }
  });
})();
