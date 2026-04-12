(function () {
  function setDeviceClass() {
    var sw = window.screen ? window.screen.width : 0;
    var iw = window.innerWidth || 0;
    // Real phones: screen.width is small even when layout viewport is forced wide (meta width=1280).
    // Firefox/Chrome responsive mode: screen.width often stays desktop-sized; innerWidth matches the emulated device.
    var narrow = (sw > 0 && sw < 1024) || iw < 1024;
    document.documentElement.classList.toggle("livia-narrow", narrow);
    document.documentElement.classList.toggle("livia-wide", !narrow);
  }

  setDeviceClass();
  window.addEventListener("resize", setDeviceClass);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", setDeviceClass);
  }

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

  function init() {
    if (window.sessionStorage) {
      sessionStorage.removeItem("livia_fly_nav");
    }
    highlightActiveNav();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  window.setTimeout(highlightActiveNav, 500);
  window.setTimeout(highlightActiveNav, 1500);
})();
