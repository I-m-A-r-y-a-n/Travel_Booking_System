/* Notification dropdown under the bell. Without JavaScript the bell is just a button,
   and the full list is still reachable at /notifications/. */
(function () {
  'use strict';
  var wrap = document.querySelector('[data-bell]');
  if (!wrap) return;

  var button = wrap.querySelector('.bell');
  var panel = wrap.querySelector('[data-panel]');
  var badge = wrap.querySelector('[data-bell-badge]');
  var url = wrap.getAttribute('data-panel-url');
  var loaded = false;

  function csrf() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function setBadge(n) {
    if (!badge) return;
    badge.textContent = n;
    badge.hidden = !n;
  }

  function load() {
    panel.innerHTML = '<div class="np-loading"><i></i><i></i><i></i></div>';
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (html) {
        panel.innerHTML = html;
        loaded = true;
        var count = panel.querySelector('.np-count');
        setBadge(count ? parseInt(count.textContent, 10) || 0 : 0);
      })
      .catch(function () {
        panel.innerHTML = '<div class="np-empty"><b>Could not load notifications</b><a href="' + url.replace('panel/', '') + '">Open the full list</a></div>';
      });
  }

  function open() {
    panel.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    load();
  }
  function close() {
    panel.hidden = true;
    button.setAttribute('aria-expanded', 'false');
  }

  button.addEventListener('click', function (e) {
    e.stopPropagation();
    if (panel.hidden) open(); else close();
  });
  document.addEventListener('click', function (e) { if (!panel.hidden && !wrap.contains(e.target)) close(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) { close(); button.focus(); } });

  panel.addEventListener('click', function (e) {
    var all = e.target.closest('[data-mark-all]');
    if (!all) return;
    fetch(all.getAttribute('data-url'), {
      method: 'POST', credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf() }
    }).then(function () { setBadge(0); load(); });
  });
})();
