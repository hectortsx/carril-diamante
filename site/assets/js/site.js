/* Carril Diamante · site behaviour. Loaded with defer; no inline scripts anywhere (CSP). */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------- header background after scroll ---------- */
  var header = document.querySelector("[data-header]");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 24); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------- mobile menu: Esc closes, focus returns, page locked while open ---------- */
  var menu = document.querySelector("[data-menu]");
  var openBtn = document.querySelector("[data-menu-open]");
  var closeBtn = document.querySelector("[data-menu-close]");
  function setMenu(open) {
    if (!menu || !openBtn) return;
    openBtn.setAttribute("aria-expanded", String(open));
    if (open) {
      menu.hidden = false;
      document.body.classList.add("menu-open");
      requestAnimationFrame(function () { menu.classList.add("is-open"); });
      (closeBtn || menu).focus();
    } else {
      menu.classList.remove("is-open");
      menu.hidden = true;
      document.body.classList.remove("menu-open");
      openBtn.focus();
    }
  }
  if (menu && openBtn) {
    openBtn.addEventListener("click", function () { setMenu(true); });
    if (closeBtn) closeBtn.addEventListener("click", function () { setMenu(false); });
    menu.addEventListener("click", function (ev) {
      if (ev.target.closest("a")) { menu.classList.remove("is-open"); menu.hidden = true; document.body.classList.remove("menu-open"); openBtn.setAttribute("aria-expanded", "false"); }
    });
    document.addEventListener("keydown", function (ev) {
      if (menu.hidden) return;
      if (ev.key === "Escape") { setMenu(false); return; }
      if (ev.key === "Tab") {
        var f = menu.querySelectorAll("a[href], button");
        var first = f[0], last = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
        else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
      }
    });
    window.addEventListener("resize", function () { if (!menu.hidden && window.innerWidth > 1080) setMenu(false); });
  }

  /* ---------- toggle buttons (video + gallery share the same pattern) ---------- */
  function setToggle(btn, paused) {
    btn.setAttribute("aria-pressed", String(paused));
    var label = btn.querySelector("[data-label]");
    if (label) label.textContent = paused ? btn.getAttribute("data-label-play") : btn.getAttribute("data-label-pause");
  }

  /* ---------- hero video: plays only on screen, fades over the loop seam, user can pause ---------- */
  var video = document.querySelector("[data-hero-video]");
  var vBtn = document.querySelector("[data-video-toggle]");
  if (video && vBtn) {
    var userPaused = reduce.matches;   // reduced motion: start paused, the visitor can still press play
    var onScreen = true;
    vBtn.hidden = false;
    setToggle(vBtn, userPaused);
    var sync = function () {
      if (!userPaused && onScreen) {
        var p = video.play();
        // Only a real autoplay block (e.g. iOS Low Power Mode) flips the button to "play".
        // AbortError just means a pause() interrupted play(), which is harmless.
        if (p && p.catch) p.catch(function (err) { if (err && err.name === "NotAllowedError") { userPaused = true; setToggle(vBtn, true); } });
      }
      else video.pause();
    };
    vBtn.addEventListener("click", function () { userPaused = !userPaused; setToggle(vBtn, userPaused); sync(); });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) { onScreen = entries[0].isIntersecting; sync(); }, { threshold: 0.15 }).observe(video);
    }
    var fading = false;
    video.addEventListener("timeupdate", function () {
      if (fading || !video.duration) return;
      if (video.duration - video.currentTime < 0.6) {
        fading = true;
        video.classList.add("is-fading");
        setTimeout(function () {
          video.currentTime = 0;
          video.classList.remove("is-fading");
          fading = false;
          sync();
        }, 500);
      }
    });
    video.addEventListener("ended", function () { video.currentTime = 0; sync(); });
    sync();
  }

  /* ---------- gallery marquee pause (WCAG 2.2.2: moving content can be paused) ---------- */
  var marquee = document.querySelector("[data-marquee]");
  var mBtn = document.querySelector("[data-marquee-toggle]");
  // On touch screens and phones the gallery is a swipeable strip (site.css): nothing moves, nothing to pause.
  var swipe = window.matchMedia("(hover: none), (max-width: 760px)");
  if (marquee && mBtn && !reduce.matches && !swipe.matches) {
    mBtn.hidden = false;
    setToggle(mBtn, false);
    mBtn.addEventListener("click", function () {
      var paused = !marquee.classList.contains("is-paused");
      marquee.classList.toggle("is-paused", paused);
      setToggle(mBtn, paused);
    });
  }

  /* ---------- scroll reveals ---------- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduce.matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); } });
    }, { threshold: 0.15, rootMargin: "0px 0px -6% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  }
  // Fail-safe: never leave anything hidden if the observer misbehaves.
  setTimeout(function () {
    reveals.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) el.classList.add("is-in");
    });
  }, 2500);

  /* ---------- fact numbers count up once, like a scoreboard ----------
     The real value stays in a visually-hidden span for screen readers; the width is locked first so
     nothing shifts. The numbers only reset to 0 as their section starts fading in, so if this never
     runs, the real numbers simply stay. */
  var counts = document.querySelectorAll("[data-count]");
  if (counts.length && "IntersectionObserver" in window && !reduce.matches && window.requestAnimationFrame) {
    var runCount = function (el) {
      if (el.getAttribute("data-counted")) return;
      el.setAttribute("data-counted", "1");
      var finalText = el.textContent;
      el.style.minWidth = el.getBoundingClientRect().width + "px";
      el.textContent = "";
      var shown = document.createElement("span");
      shown.setAttribute("aria-hidden", "true");
      var real = document.createElement("span");
      real.className = "visually-hidden";
      real.textContent = finalText;
      el.appendChild(shown);
      el.appendChild(real);
      var t0 = null, DURATION = 1400;
      var step = function (t) {
        if (t0 === null) t0 = t;
        var p = Math.min(1, (t - t0) / DURATION);
        var eased = 1 - Math.pow(1 - p, 3);
        shown.textContent = finalText.replace(/\d+/g, function (n) { return String(Math.round(Number(n) * eased)); });
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { runCount(en.target); cio.unobserve(en.target); } });
    }, { threshold: 0.15, rootMargin: "0px 0px -6% 0px" });
    counts.forEach(function (el) { cio.observe(el); });
  }

  /* ---------- analytics consent (active only when <body data-ga-id> is set) ---------- */
  var gaId = document.body.getAttribute("data-ga-id");
  var banner = document.querySelector("[data-consent]");
  if (!gaId || !banner) return;

  var COOKIE = "cd_consent";
  var MAX_AGE = 60 * 60 * 24 * 182; // ~6 months
  function readChoice() {
    var m = document.cookie.match(/(?:^|; )cd_consent=(granted|rejected)/);
    return m ? m[1] : null;
  }
  function writeChoice(v) {
    document.cookie = COOKIE + "=" + v + "; Max-Age=" + MAX_AGE + "; Path=/; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : "");
  }
  function deleteGaCookies() {
    var host = location.hostname.replace(/^www\./, "");
    document.cookie.split("; ").forEach(function (c) {
      var name = c.split("=")[0];
      if (name === "_ga" || name.indexOf("_ga_") === 0 || name === "_gid") {
        ["", "; Domain=" + host, "; Domain=." + host].forEach(function (d) {
          document.cookie = name + "=; Max-Age=0; Path=/" + d;
        });
      }
    });
  }
  var loaded = false;
  function loadGa() {
    if (loaded) return;
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", gaId, {
      page_location: location.origin + location.pathname, // no query strings or fragments
      allow_google_signals: false,
      allow_ad_personalization_signals: false
    });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(gaId);
    document.head.appendChild(s);
  }
  function show() { banner.hidden = false; var b = banner.querySelector("button"); if (b) b.focus(); }
  function hide() { banner.hidden = true; }

  banner.addEventListener("click", function (ev) {
    var btn = ev.target.closest("[data-consent-choice]");
    if (!btn) return;
    var v = btn.getAttribute("data-consent-choice");
    writeChoice(v);
    hide();
    if (v === "granted") loadGa();
    else { deleteGaCookies(); if (loaded) location.reload(); }
  });
  document.querySelectorAll("[data-consent-open]").forEach(function (b) { b.addEventListener("click", show); });

  var choice = readChoice();
  var gpc = navigator.globalPrivacyControl === true;
  if (choice === "granted" && !gpc) loadGa();
  else if (!choice && !gpc) banner.hidden = false; // GPC counts as a rejection: no banner, nothing loads
})();
