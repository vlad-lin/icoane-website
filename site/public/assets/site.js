(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };

  // ---------- menu (small screens) ----------
  var toggle = document.querySelector('.nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = $('nav').classList.toggle('open');
      toggle.setAttribute('aria-expanded', open);
    });
  }

  // ---------- gallery: search, themes, sorting, paging ----------
  // All cards are in the page (so it works without JavaScript and for search engines);
  // this only hides, reorders and pages them. The state lives in the address (#theme=…)
  // so the browser's Back button returns to the same view.
  var grid = $('grid');
  if (grid) {
    var PAGE = 36;
    var lang = grid.dataset.lang;
    var S = JSON.parse(grid.dataset.strings);
    var cards = Array.prototype.slice.call(grid.children);
    var index = window.SEARCH || {};
    var state = { theme: 'all', q: '', sort: 'new', shown: PAGE };

    var fold = function (s) {
      return String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    };
    var fmt = function (s, n) { return s.replace('{n}', n); };
    var matches = function (card) {
      if (!state.q) return true;
      var hay = index[card.dataset.id] || fold(card.dataset.title);
      return fold(state.q).split(/\s+/).every(function (w) { return hay.indexOf(w) !== -1; });
    };

    var readHash = function () {
      var p = new URLSearchParams(location.hash.slice(1));
      state.theme = p.get('theme') || 'all';
      state.q = p.get('q') || '';
      state.sort = p.get('sort') || 'new';
      state.shown = Math.max(PAGE, +p.get('shown') || 0);
      $('search').value = state.q;
      $('sort').value = state.sort;
    };
    var writeHash = function () {
      var p = new URLSearchParams();
      if (state.theme !== 'all') p.set('theme', state.theme);
      if (state.q) p.set('q', state.q);
      if (state.sort !== 'new') p.set('sort', state.sort);
      if (state.shown > PAGE) p.set('shown', state.shown);
      var h = p.toString();
      history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
    };

    var render = function () {
      var byQuery = cards.filter(matches);
      // Theme chips show how many works match the search in each theme.
      // "biserici" (icons for churches) is a filter across all themes.
      var counts = { all: byQuery.length, biserici: 0 };
      byQuery.forEach(function (c) {
        counts[c.dataset.theme] = (counts[c.dataset.theme] || 0) + 1;
        if (c.dataset.church) counts.biserici++;
      });
      Array.prototype.forEach.call($('theme-filter').children, function (b) {
        b.setAttribute('aria-pressed', b.dataset.theme === state.theme);
        b.querySelector('.count').textContent = counts[b.dataset.theme] || 0;
      });

      var list = byQuery.filter(function (c) {
        if (state.theme === 'biserici') return !!c.dataset.church;
        return state.theme === 'all' || c.dataset.theme === state.theme;
      });
      var order = cards.slice();
      if (state.sort === 'old') order.reverse();
      if (state.sort === 'az') order.sort(function (a, b) { return a.dataset.title.localeCompare(b.dataset.title, lang); });
      order.forEach(function (c) { grid.appendChild(c); });

      var visible = {};
      list.forEach(function (c) { visible[c.dataset.id] = true; });
      var shown = 0;
      order.forEach(function (c) {
        var show = visible[c.dataset.id] && shown < state.shown;
        if (show) shown++;
        c.hidden = !show;
      });
      $('empty').hidden = list.length > 0;
      $('more').hidden = list.length <= state.shown;
      $('result-count').textContent = (list.length === 1 ? S.count_one : fmt(S.count_many, list.length)) +
        (list.length > shown ? fmt(S.count_shown, shown) : '');
      writeHash();
    };

    $('theme-filter').addEventListener('click', function (ev) {
      var b = ev.target.closest('button');
      if (!b) return;
      state.theme = b.dataset.theme;
      state.shown = PAGE;
      render();
    });
    var timer;
    $('search').addEventListener('input', function (ev) {
      clearTimeout(timer);
      timer = setTimeout(function () {
        state.q = ev.target.value.trim();
        state.shown = PAGE;
        render();
      }, 150);
    });
    $('sort').addEventListener('change', function (ev) {
      state.sort = ev.target.value;
      state.shown = PAGE;
      render();
    });
    $('more').addEventListener('click', function () {
      state.shown += PAGE;
      render();
    });

    readHash();
    render();
  }

  // ---------- icon page: photos and drawings ----------
  var main = $('v-main');
  if (main) {
    var thumbs = document.querySelectorAll('.v-thumbs a');
    var show = function (i) {
      var t = thumbs[i];
      if (!t) return;
      $('v-img').src = t.href;
      main.href = t.href;
      $('v-caption').textContent = t.dataset.caption || '';
      Array.prototype.forEach.call(thumbs, function (x, j) { x.setAttribute('aria-current', j === i ? 'true' : 'false'); });
    };
    document.addEventListener('click', function (ev) {
      var a = ev.target.closest('.v-thumbs a, .stage a[data-index]');
      if (!a) return;
      ev.preventDefault();
      show(+a.dataset.index);
      if (a.closest('.stage')) main.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
    // Arrow keys move to the previous / next work.
    document.addEventListener('keydown', function (ev) {
      if (ev.target.closest('input, textarea, select') || ev.altKey || ev.ctrlKey || ev.metaKey) return;
      var link = document.querySelector(ev.key === 'ArrowLeft' ? '.pager-prev' : ev.key === 'ArrowRight' ? '.pager-next' : null);
      if (link) location.href = link.href;
    });
  }

  // ---------- statistics: Google Analytics, only after the visitor accepts ----------
  // Nothing is loaded from Google until "Accept" is pressed. The choice is remembered
  // in this browser; "Cookie settings" in the footer reopens the banner. Opened from
  // disk (file://), the banner works but Analytics is never loaded.
  var GA = document.body.dataset.ga;
  var banner = $('consent');
  if (GA && banner) {
    var KEY = 'icoane-consent';
    var loaded = false;
    var getChoice = function () { try { return localStorage.getItem(KEY); } catch (e) { return null; } };
    var setChoice = function (v) { try { localStorage.setItem(KEY, v); } catch (e) { /* private mode */ } };
    var loadAnalytics = function () {
      if (loaded || location.protocol === 'file:') return;
      loaded = true;
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () { window.dataLayer.push(arguments); };
      // Consent Mode: statistics allowed, everything advertising-related refused.
      window.gtag('consent', 'default', {
        analytics_storage: 'granted', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied'
      });
      window.gtag('js', new Date());
      window.gtag('config', GA);
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA);
      document.head.appendChild(s);
    };
    var removeCookies = function () {
      var host = location.hostname;
      document.cookie.split(';').forEach(function (c) {
        var name = c.split('=')[0].trim();
        if (name.indexOf('_ga') !== 0) return;
        ['', host, '.' + host, '.' + host.split('.').slice(-2).join('.')].forEach(function (d) {
          document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + (d ? '; domain=' + d : '');
        });
      });
    };
    var choose = function (v) {
      setChoice(v);
      banner.hidden = true;
      if (v === 'granted') {
        loadAnalytics();
      } else {
        if (loaded) window.gtag('consent', 'update', { analytics_storage: 'denied' });
        removeCookies();
      }
    };
    banner.addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-consent]');
      if (b) choose(b.dataset.consent);
    });
    var settings = $('cookie-settings');
    if (settings) settings.addEventListener('click', function () { banner.hidden = false; });
    var choice = getChoice();
    if (choice === 'granted') loadAnalytics();
    else if (choice !== 'denied') banner.hidden = false;
  }
})();
