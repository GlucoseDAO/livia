(function () {
  /** Narrow layout: prefer CSS media query (matches real layout width), then screen width, then inner width. */
  function setDeviceClass() {
    var sw = window.screen ? window.screen.width : 0;
    var iw = window.innerWidth || 0;
    var mq = window.matchMedia("(max-width: 1023px)");
    var narrow =
      mq.matches ||
      (sw > 0 && sw < 1024) ||
      (iw > 0 && iw < 1024);
    document.documentElement.classList.toggle("livia-narrow", narrow);
    document.documentElement.classList.toggle("livia-wide", !narrow);
  }

  setDeviceClass();
  window.addEventListener("resize", setDeviceClass);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", setDeviceClass);
  }
  try {
    var mq = window.matchMedia("(max-width: 1023px)");
    if (mq.addEventListener) {
      mq.addEventListener("change", setDeviceClass);
    } else if (mq.addListener) {
      mq.addListener(setDeviceClass);
    }
  } catch (e) {}

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

  function initSequenceCyclers() {
    document.querySelectorAll(".livia-sequence:not([data-livia-seq-init])").forEach(function (seq) {
      seq.setAttribute("data-livia-seq-init", "1");
      var imgs = seq.querySelectorAll("img");
      if (imgs.length < 2) return;
      var i = 0;
      function tick() {
        imgs.forEach(function (img, j) {
          img.style.opacity = j === i ? "1" : "0";
        });
        i = (i + 1) % imgs.length;
      }
      tick();
      window.setInterval(tick, 400);
    });
  }

  function init() {
    if (window.sessionStorage) {
      sessionStorage.removeItem("livia_fly_nav");
    }
    highlightActiveNav();
    initSequenceCyclers();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  var seqObserverTimer = null;
  try {
    var seqObserver = new MutationObserver(function () {
      if (seqObserverTimer) window.clearTimeout(seqObserverTimer);
      seqObserverTimer = window.setTimeout(function () {
        initSequenceCyclers();
      }, 120);
    });
    if (document.body) {
      seqObserver.observe(document.body, { childList: true, subtree: true });
    }
  } catch (e) {}
  window.setTimeout(highlightActiveNav, 500);
  window.setTimeout(highlightActiveNav, 1500);

  /* Delegated lightbox for .livia-lightbox-thumb (markdown HTML + Reflex gallery/artifact). */
  function ensureLightbox() {
    var id = "livia-image-lightbox";
    var root = document.getElementById(id);
    if (root) return root;
    root = document.createElement("div");
    root.id = id;
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    root.setAttribute("aria-label", "Image");
    root.style.cssText =
      "display:none;position:fixed;inset:0;z-index:400;background:rgba(0,0,0,0.88);backdrop-filter:blur(8px);align-items:center;justify-content:center;padding:1rem;box-sizing:border-box;";
    root.innerHTML =
      '<div class="livia-lightbox-inner" style="position:relative;max-width:min(96vw,1400px);max-height:100%;display:flex;flex-direction:column;align-items:center;gap:0.75rem;">' +
      '<div style="display:flex;width:100%;justify-content:space-between;align-items:center;flex-shrink:0;">' +
      '<button type="button" class="livia-lightbox-close-btn" style="background:transparent;border:none;color:#f5f0e8;font:600 1rem Manrope,sans-serif;cursor:pointer;letter-spacing:0.06em;">Close</button>' +
      '<button type="button" class="livia-lightbox-x-btn" style="background:transparent;border:none;color:#f5f0e8;font-size:1.75rem;line-height:1;cursor:pointer;" aria-label="Close">&times;</button></div>' +
      '<img class="livia-lightbox-full" alt="" style="max-width:100%;max-height:min(85vh,1200px);width:auto;height:auto;object-fit:contain;border-radius:0.8rem;"/>' +
      "</div>";
    document.body.appendChild(root);

    function close() {
      root.style.display = "none";
      var img = root.querySelector(".livia-lightbox-full");
      if (img) img.removeAttribute("src");
      document.body.style.overflow = "";
    }

    root.addEventListener("click", function (e) {
      if (e.target === root) close();
    });
    root.querySelector(".livia-lightbox-close-btn").addEventListener("click", close);
    root.querySelector(".livia-lightbox-x-btn").addEventListener("click", close);
    root.querySelector(".livia-lightbox-inner").addEventListener("click", function (e) {
      e.stopPropagation();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && root.style.display === "flex") close();
    });

    return root;
  }

  function openLightbox(src) {
    if (!src) return;
    var root = ensureLightbox();
    var full = root.querySelector(".livia-lightbox-full");
    if (full) {
      full.src = src;
    }
    root.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  document.addEventListener(
    "click",
    function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      var thumb = t.closest(".livia-lightbox-thumb-wrap") || t.closest(".livia-lightbox-thumb");
      if (!thumb) return;
      var img = thumb.classList.contains("livia-lightbox-thumb") ? thumb : thumb.querySelector("img.livia-lightbox-thumb");
      if (!img) img = thumb.querySelector("img");
      if (!img) return;
      var fullSrc = img.getAttribute("data-full-src") || img.getAttribute("src");
      if (!fullSrc) return;
      e.preventDefault();
      e.stopPropagation();
      openLightbox(fullSrc);
    },
    true
  );
})();
