/* Small progressive enhancements for the search / detail / booking pages.
   Everything also works without JavaScript. */
(function () {
  'use strict';

  // Swap the From / To text fields.
  document.querySelectorAll('[data-swap]').forEach(function (button) {
    button.addEventListener('click', function () {
      var scope = button.closest('.route-fields');
      if (!scope) return;
      var fields = scope.querySelectorAll('input[type=text]');
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
})();
