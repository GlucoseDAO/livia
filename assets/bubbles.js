(function () {
  "use strict";

  function computeArcRadius() {
    var vw = window.innerWidth * 0.42;
    var vh = window.innerHeight * 0.38;
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

      el.style.setProperty("--offset-x", ox + "px");
      el.style.setProperty("--offset-y", oy + "px");
    });
  }

  function scheduleShiver(bubble) {
    var delay = 3000 + Math.random() * 5000;
    setTimeout(function () {
      bubble.classList.add("shiver");
      setTimeout(function () {
        bubble.classList.remove("shiver");
      }, 400);
      scheduleShiver(bubble);
    }, delay);
  }

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
    });

    window.addEventListener("resize", positionBubbles);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    setTimeout(init, 100);
  }
})();
