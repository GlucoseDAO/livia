(function () {
  "use strict";

  function computeArcRadius() {
    var vw = window.innerWidth * 0.30;
    var vh = window.innerHeight * 0.32;
    return Math.min(vw, vh);
  }

  function positionBubbles() {
    var radius = computeArcRadius();
    var bubbles = document.querySelectorAll(".bubble[data-angle]");
    bubbles.forEach(function (el) {
      var angleDeg = parseFloat(el.getAttribute("data-angle"));
      var rad = (angleDeg * Math.PI) / 180;
      var ox = Math.cos(rad) * radius;
      var oy = Math.sin(rad) * radius;

      var expandFactor = 0.35;
      var ex = Math.cos(rad) * radius * expandFactor;
      var ey = Math.sin(rad) * radius * expandFactor;

      el.style.setProperty("--offset-x", ox + "px");
      el.style.setProperty("--offset-y", oy + "px");
      el.style.setProperty("--expand-x", ex + "px");
      el.style.setProperty("--expand-y", ey + "px");
    });
  }

  function scheduleShiver(bubble) {
    var delay = 3000 + Math.random() * 5000;
    setTimeout(function () {
      if (!bubble.classList.contains("expanded")) {
        bubble.classList.add("shiver");
        setTimeout(function () {
          bubble.classList.remove("shiver");
        }, 400);
      }
      scheduleShiver(bubble);
    }, delay);
  }

  function collapseAll() {
    document.querySelectorAll(".bubble.expanded").forEach(function (b) {
      b.classList.remove("expanded");
    });
    document.querySelectorAll(".bubble.touch-hover").forEach(function (b) {
      b.classList.remove("touch-hover");
    });
  }

  var isTouchDevice = false;

  function init() {
    positionBubbles();

    var bubbles = document.querySelectorAll(".bubble[data-angle]");

    bubbles.forEach(function (bubble) {
      var floatDur = 4 + Math.random() * 3;
      var floatDelay = Math.random() * -6;
      var floatAmp = 6 + Math.random() * 6;
      bubble.style.setProperty("--float-dur", floatDur + "s");
      bubble.style.setProperty("--float-delay", floatDelay + "s");
      bubble.style.setProperty("--float-amp", floatAmp + "px");

      scheduleShiver(bubble);

      bubble.addEventListener("click", function (e) {
        e.stopPropagation();
        var wasExpanded = bubble.classList.contains("expanded");
        collapseAll();
        if (!wasExpanded) {
          bubble.classList.add("expanded");
        }
      });

      bubble.addEventListener("touchstart", function () {
        isTouchDevice = true;
      }, { passive: true });

      bubble.addEventListener("touchend", function (e) {
        if (!bubble.classList.contains("expanded") && !bubble.classList.contains("touch-hover")) {
          e.preventDefault();
          collapseAll();
          bubble.classList.add("touch-hover");
        }
      });
    });

    document.addEventListener("click", function (e) {
      if (!e.target.closest(".bubble")) {
        collapseAll();
      }
    });

    window.addEventListener("resize", positionBubbles);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    setTimeout(init, 100);
  }
})();
