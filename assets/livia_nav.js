(function () {
  function setDeviceClass() {
    var narrow = window.screen && window.screen.width < 1024;
    document.documentElement.classList.toggle("livia-narrow", narrow);
    document.documentElement.classList.toggle("livia-wide", !narrow);
  }

  setDeviceClass();
  window.addEventListener("resize", setDeviceClass);

  function highlightActiveNav() {
    var path = window.location.pathname;
    if (path === "" || path === "/index") {
      path = "/";
    }
    var links = document.querySelectorAll(".livia-bottom-nav a[data-href]");
    links.forEach(function (a) {
      var href = a.getAttribute("data-href");
      var isActive = href === path;
      a.style.color = isActive ? "#f5f0e8" : "";
      a.style.fontWeight = isActive ? "700" : "";
      var bar = a.querySelector(".livia-nav-indicator");
      if (bar) {
        bar.style.width = isActive ? "100%" : "";
      }
    });
  }

  function runFlyFromSession() {
    if (document.documentElement.classList.contains("livia-narrow")) {
      return;
    }
    var raw = sessionStorage.getItem("livia_fly_nav");
    if (!raw) {
      return;
    }
    var data;
    try {
      data = JSON.parse(raw);
    } catch (err) {
      sessionStorage.removeItem("livia_fly_nav");
      return;
    }
    if (typeof data.nx !== "number") {
      sessionStorage.removeItem("livia_fly_nav");
      return;
    }

    var startMs = Date.now();
    var maxWaitMs = 2800;

    function fadeOutAndRemove(overlay, ghost) {
      var cleaned = false;
      function removeBoth() {
        if (cleaned) {
          return;
        }
        cleaned = true;
        ghost.remove();
        overlay.remove();
      }
      if (typeof overlay.animate === "function") {
        var animOverlay = overlay.animate(
          [{ opacity: 1 }, { opacity: 0 }],
          { duration: 520, easing: "ease-out", fill: "forwards" }
        );
        var animGhost = ghost.animate(
          [{ opacity: 1 }, { opacity: 0 }],
          { duration: 480, easing: "ease-out", fill: "forwards" }
        );
        Promise.all([animOverlay.finished, animGhost.finished])
          .then(removeBoth)
          .catch(removeBoth);
        window.setTimeout(removeBoth, 900);
      } else {
        overlay.style.transition = "opacity 0.52s ease-out";
        ghost.style.transition = "opacity 0.48s ease-out";
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            overlay.style.opacity = "0";
            ghost.style.opacity = "0";
          });
        });
        window.setTimeout(removeBoth, 600);
      }
    }

    function runWithTarget(target) {
      sessionStorage.removeItem("livia_fly_nav");

      var overlay = document.createElement("div");
      overlay.className = "livia-fly-overlay";
      document.body.appendChild(overlay);

      var ghost = document.createElement("div");
      ghost.className = "livia-fly-ghost";
      ghost.textContent = data.text || "";
      ghost.style.opacity = "1";
      document.body.appendChild(ghost);

      var vw = window.innerWidth;
      var vh = window.innerHeight;
      var gw = data.nw * vw;
      var gh = data.nh * vh;
      var gsx = data.nx * vw - gw / 2;
      var gsy = data.ny * vh - gh / 2;
      ghost.style.left = gsx + "px";
      ghost.style.top = gsy + "px";
      ghost.style.width = gw + "px";
      ghost.style.height = gh + "px";

      var tr = target.getBoundingClientRect();

      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          ghost.style.transition =
            "left 0.55s cubic-bezier(0.34, 1.56, 0.64, 1), top 0.55s cubic-bezier(0.34, 1.56, 0.64, 1), width 0.55s ease, height 0.55s ease";
          ghost.style.left = tr.left + "px";
          ghost.style.top = tr.top + "px";
          ghost.style.width = tr.width + "px";
          ghost.style.height = tr.height + "px";
        });
      });

      var moveMs = 620;
      window.setTimeout(function () {
        ghost.style.transition = "";
        fadeOutAndRemove(overlay, ghost);
      }, moveMs);
    }

    function waitForTarget() {
      var target = document.querySelector(".livia-heading-target");
      if (target) {
        runWithTarget(target);
        return;
      }
      if (Date.now() - startMs > maxWaitMs) {
        sessionStorage.removeItem("livia_fly_nav");
        return;
      }
      requestAnimationFrame(waitForTarget);
    }

    waitForTarget();
  }

  function attachNavClick() {
    document.addEventListener(
      "click",
      function (e) {
        if (e.defaultPrevented) {
          return;
        }
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
          return;
        }
        var a = e.target.closest(".livia-bottom-nav a[data-href]");
        if (!a) {
          return;
        }
        var href = a.getAttribute("data-href");
        if (!href || href.charAt(0) !== "/") {
          return;
        }
        var path = window.location.pathname;
        if (path === "" || path === "/index") {
          path = "/";
        }
        if (href === path) {
          return;
        }
        if (document.documentElement.classList.contains("livia-wide")) {
          var label = a.querySelector(".livia-nav-label");
          var rectSource = label || a;
          var lr = rectSource.getBoundingClientRect();
          var vw = window.innerWidth;
          var vh = window.innerHeight;
          var text = (label || a).textContent.trim();
          sessionStorage.setItem(
            "livia_fly_nav",
            JSON.stringify({
              nx: (lr.left + lr.width / 2) / vw,
              ny: (lr.top + lr.height / 2) / vh,
              nw: lr.width / vw,
              nh: lr.height / vh,
              text: text,
            })
          );
        }
        e.preventDefault();
        window.location.assign(href);
      },
      true
    );
  }

  function narrowNavAutoHide() {
    if (!document.documentElement.classList.contains("livia-narrow")) {
      return;
    }
    var nav = null;
    function ensureNav() {
      if (!nav) {
        nav = document.querySelector(".livia-bottom-nav");
      }
      return nav;
    }
    var hideTimer = null;
    function bump() {
      var n = ensureNav();
      if (!n) {
        return;
      }
      n.classList.remove("livia-nav-auto-hidden");
      if (hideTimer) {
        clearTimeout(hideTimer);
      }
      hideTimer = window.setTimeout(function () {
        if (ensureNav()) {
          n.classList.add("livia-nav-auto-hidden");
        }
      }, 2600);
    }
    document.addEventListener("touchstart", bump, { passive: true });
    document.addEventListener("scroll", bump, { passive: true });
    window.addEventListener("resize", bump);
    bump();
  }

  attachNavClick();

  function init() {
    highlightActiveNav();
    runFlyFromSession();
    narrowNavAutoHide();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  window.setTimeout(highlightActiveNav, 500);
  window.setTimeout(highlightActiveNav, 1500);
})();
