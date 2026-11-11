/* Small progressive enhancements for the search / detail / booking pages.
   Everything also works without JavaScript. */
(function () {
  'use strict';

  // Swap the From / To text fields.
  document.querySelectorAll('[data-swap]').forEach(function (button) {
    button.addEventListener('animationend', function () { button.classList.remove('spin'); });
    button.addEventListener('click', function () {
      button.classList.remove('spin');
      void button.offsetWidth;
      button.classList.add('spin');
      var scope = button.closest('.route-fields, [data-route]');
      if (!scope) return;
      var fields = scope.querySelectorAll('input[type=text], input:not([type])');
      if (fields.length === 2) {
        var tmp = fields[0].value;
        fields[0].value = fields[1].value;
        fields[1].value = tmp;
      }
    });
  });


  // Round trip toggle: show the return date only for a round trip.
  document.querySelectorAll('[data-trip-form]').forEach(function (form) {
    var field = form.querySelector('[data-return-field]');
    var input = field && field.querySelector('input');
    var departure = form.querySelector('input[name=date]');
    var sync = function () {
      var round = form.querySelector('input[name=trip]:checked');
      var on = !!round && round.value === 'round';
      field.hidden = !on;
      if (input) { input.required = on; if (!on) input.value = ''; }
    };
    form.querySelectorAll('input[name=trip]').forEach(function (r) { r.addEventListener('change', sync); });
    if (departure && input) {
      var limit = function () { if (departure.value) { input.min = departure.value; if (input.value && input.value < departure.value) input.value = departure.value; } };
      departure.addEventListener('change', limit);
      limit();
    }
    if (field) sync();
  });

  // Filter drawer: opens from the right (pushing the page aside), and filters apply live
  // by swapping just the results, so the page doesn't reload or jump.
  var layout = document.querySelector('[data-search-layout]');
  var drawer = document.querySelector('[data-drawer]');
  var filterForm = document.getElementById('filter-form');
  if (layout && drawer && filterForm) {
    var openBtn = document.querySelector('[data-drawer-open]');
    var setOpen = function (open, instant) {
      if (instant) layout.classList.add('no-anim');
      layout.classList.toggle('filters-open', open);
      drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
      if (openBtn) openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open && !instant) {
        var close = drawer.querySelector('.icon-btn');
        if (close) setTimeout(function () { close.focus({ preventScroll: true }); }, 380);
      }
      if (instant) { void layout.offsetWidth; layout.classList.remove('no-anim'); }
    };
    if (openBtn) openBtn.addEventListener('click', function () { setOpen(!layout.classList.contains('filters-open')); });
    document.querySelectorAll('[data-drawer-close]').forEach(function (el) {
      el.addEventListener('click', function () { setOpen(false); if (openBtn) openBtn.focus({ preventScroll: true }); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && layout.classList.contains('filters-open')) { setOpen(false); if (openBtn) openBtn.focus({ preventScroll: true }); }
    });
    try {
      if (sessionStorage.getItem('wfFilters') === '1') { sessionStorage.removeItem('wfFilters'); setOpen(true, true); }
    } catch (err) { /* private mode: just stay closed */ }

    var currentUrl = function () {
      var params = new URLSearchParams(new FormData(filterForm));
      return window.location.pathname + '?' + params.toString();
    };
    var timer = null, request = 0;
    var apply = function () {
      var url = currentUrl(), mine = ++request;
      var results = document.querySelector('[data-results]');
      if (results) results.classList.add('loading');
      fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { if (!r.ok) throw new Error('bad'); return r.text(); })
        .then(function (html) {
          if (mine !== request) return;
          var doc = new DOMParser().parseFromString(html, 'text/html');
          var fresh = doc.querySelector('[data-results]');
          if (!fresh || !results) throw new Error('no results');
          results.innerHTML = fresh.innerHTML;
          results.classList.remove('loading');
          var badge = document.querySelector('[data-filter-count]');
          var newBadge = doc.querySelector('[data-filter-count]');
          if (badge && newBadge) { badge.textContent = newBadge.textContent; badge.hidden = newBadge.hidden; }
          var count = doc.querySelector('[data-count]'), plural = doc.querySelector('[data-plural]');
          if (count) filterForm.querySelector('[data-count]').textContent = count.textContent;
          if (plural) filterForm.querySelector('[data-plural]').textContent = plural.textContent;
          history.replaceState(null, '', url);
        })
        .catch(function () {
          // Fall back to a normal page load, keeping the drawer open afterwards.
          try { sessionStorage.setItem('wfFilters', '1'); } catch (err) { /* ignore */ }
          window.location.href = url;
        });
    };
    var later = function () { clearTimeout(timer); timer = setTimeout(apply, 120); };
    filterForm.addEventListener('change', later);
    var sort = document.querySelector('[data-sort]');
    if (sort) sort.addEventListener('change', later);
    filterForm.addEventListener('submit', function (e) {
      e.preventDefault();
      apply();
      if (window.matchMedia('(max-width: 1020px)').matches) setOpen(false);
    });
    var range = filterForm.querySelector('[data-price-range]');
    var out = filterForm.querySelector('[data-price-out]');
    if (range && out) {
      range.addEventListener('input', function () { out.textContent = 'up to \u20b9' + Number(range.value).toLocaleString('en-US'); });
    }
    var clear = filterForm.querySelector('[data-clear]');
    if (clear) clear.addEventListener('click', function (e) {
      e.preventDefault();
      filterForm.querySelectorAll('input[type=checkbox]').forEach(function (c) { c.checked = false; });
      if (range) { range.value = range.max; if (out) out.textContent = 'up to \u20b9' + Number(range.max).toLocaleString('en-US'); }
      apply();
    });
  }

  // Seat maps: you can't pick more seats than travellers; keep the "x of n" count in step.
  document.querySelectorAll('[data-seatmap]').forEach(function (map) {
    var max = parseInt(map.getAttribute('data-max'), 10) || 1;
    var box = map.closest('.box');
    var counter = box && box.querySelector('[data-seat-count]');
    var boxes = map.querySelectorAll('input[type=checkbox]:not(:disabled)');
    var refresh = function () {
      var picked = map.querySelectorAll('input:checked').length;
      if (counter) counter.textContent = picked;
      boxes.forEach(function (b) { if (!b.checked) b.disabled = picked >= max; });
    };
    boxes.forEach(function (b) { b.addEventListener('change', refresh); });
    refresh();
  });

  // Live total on the fare box: price x number of passengers/seats.
  var qty = document.querySelector('[data-fare-qty]');
  var total = document.querySelector('[data-fare-total]');
  if (qty && total) {
    var price = parseFloat(qty.getAttribute('data-price')) || 0;
    var count = document.querySelector('[data-fare-count]');
    var update = function () {
      var n = Math.max(1, parseInt(qty.value, 10) || 1);
      total.textContent = '₹' + Math.round(price * n).toLocaleString('en-US');
      if (count) count.textContent = n;
    };
    qty.addEventListener('input', update);
    qty.addEventListener('change', update);
  }

  // Forms marked data-once: disable the button after the first submit (no double payments).
  document.querySelectorAll('form[data-once]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var button = form.querySelector('button[type=submit]');
      if (!button) return;
      var label = button.getAttribute('data-busy');
      // Disable on the next tick so the form still submits normally.
      setTimeout(function () {
        button.disabled = true;
        if (label) button.textContent = label;
      }, 0);
    });
  });

  // Check-out can't be on or before check-in.
  document.querySelectorAll('[data-stay-in]').forEach(function (checkIn) {
    var form = checkIn.form || document;
    var checkOut = form.querySelector('[data-stay-out]');
    if (!checkOut) return;
    var iso = function (d) {
      return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    };
    if (!checkIn.min) checkIn.min = iso(new Date());
    var sync = function () {
      if (!checkIn.value) {
        var tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        if (!checkOut.min) checkOut.min = iso(tomorrow);
        return;
      }
      var next = new Date(checkIn.value + 'T00:00:00');
      next.setDate(next.getDate() + 1);
      var minOut = iso(next);
      checkOut.min = minOut;
      if (checkOut.value && checkOut.value < minOut) checkOut.value = minOut;
    };
    checkIn.addEventListener('change', sync);
    sync();
  });

  // Review form: star caption, quick-phrase chips and a character counter.
  var reviewForm = document.querySelector('[data-review-form]');
  if (reviewForm) {
    var captions = {1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very good', 5: 'Excellent'};
    var caption = reviewForm.querySelector('[data-star-label]');
    var showCaption = function () {
      var picked = reviewForm.querySelector('input[name=rating]:checked');
      caption.textContent = picked ? captions[picked.value] : 'Tap a star to rate';
    };
    reviewForm.querySelectorAll('input[name=rating]').forEach(function (r) { r.addEventListener('change', showCaption); });
    showCaption();

    var comment = reviewForm.querySelector('textarea');
    var counter = reviewForm.querySelector('[data-counter]');
    var count = function () { counter.textContent = comment.value.length; };
    comment.addEventListener('input', count);
    count();

    reviewForm.querySelectorAll('[data-chips] button').forEach(function (chip) {
      chip.addEventListener('click', function () {
        var text = chip.textContent + '. ';
        comment.value = comment.value && !/\s$/.test(comment.value) ? comment.value + ' ' + text : comment.value + text;
        comment.focus();
        count();
      });
    });
  }

  // Payment hold countdown. When it reaches zero the seats are released, so leave the page.
  var hold = document.querySelector('[data-hold-seconds]');
  if (hold) {
    var left = parseInt(hold.getAttribute('data-hold-seconds'), 10) || 0;
    var clock = hold.querySelector('[data-hold-clock]');
    var tick = function () {
      var m = Math.floor(left / 60), s = left % 60;
      clock.textContent = m + ':' + (s < 10 ? '0' : '') + s;
      hold.classList.toggle('low', left <= 120);
      if (left <= 0) { window.location.href = hold.getAttribute('data-hold-url'); return; }
      left -= 1;
      setTimeout(tick, 1000);
    };
    if (clock) tick();
  }

  // Grey out past days in every date picker that does not already set its own minimum.
  var d = new Date();
  var today = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  document.querySelectorAll('input[type=date]:not([min])').forEach(function (input) { input.min = today; });
})();
