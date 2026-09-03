(function () {
  "use strict";

  var prefersReducedMotion = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

  /* ---------- Nav shadow on scroll ---------- */
  (function () {
    var nav = document.getElementById("landing-nav");
    if (!nav) return;
    var onScroll = function () {
      nav.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  })();

  /* ---------- Mobile nav toggle ---------- */
  (function () {
    var toggle = document.getElementById("landing-nav-toggle");
    var links = document.getElementById("landing-nav-links");
    if (!toggle || !links) return;
    toggle.addEventListener("click", function () {
      var isOpen = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      toggle.textContent = isOpen ? "✕" : "☰";
    });
    links.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.textContent = "☰";
      });
    });
  })();

  /* ---------- Count-up stats, once they scroll into view ---------- */
  (function () {
    var targets = document.querySelectorAll("[data-count-to]");
    if (!targets.length) return;

    var animateCount = function (el) {
      var end = parseInt(el.getAttribute("data-count-to"), 10) || 0;
      if (prefersReducedMotion || end === 0) {
        el.textContent = end.toLocaleString();
        return;
      }
      var start = 0;
      var duration = 900;
      var startTime = null;
      var step = function (timestamp) {
        if (startTime === null) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(start + (end - start) * eased).toLocaleString();
        if (progress < 1) window.requestAnimationFrame(step);
      };
      window.requestAnimationFrame(step);
    };

    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              animateCount(entry.target);
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.4 }
      );
      targets.forEach(function (el) { observer.observe(el); });
    } else {
      targets.forEach(animateCount);
    }
  })();

  /* ---------- Hero preview card — subtle mouse tilt ---------- */
  (function () {
    if (prefersReducedMotion) return;
    var wrap = document.getElementById("landing-preview-wrap");
    var card = document.getElementById("landing-preview");
    if (!wrap || !card) return;

    var maxTilt = 7;

    wrap.addEventListener("mousemove", function (e) {
      var rect = wrap.getBoundingClientRect();
      var px = (e.clientX - rect.left) / rect.width - 0.5;
      var py = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform =
        "rotateY(" + (px * maxTilt * 2) + "deg) rotateX(" + (-py * maxTilt * 2) + "deg)";
    });
    wrap.addEventListener("mouseleave", function () {
      card.style.transform = "rotateY(0deg) rotateX(0deg)";
    });
  })();
})();
