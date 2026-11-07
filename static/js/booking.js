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
})();
