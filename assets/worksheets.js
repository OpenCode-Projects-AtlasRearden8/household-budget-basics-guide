/* Household Budget Basics — worksheet helper.
   Saves every input to this browser's localStorage (device-only, no network).
   Page key = current filename, field key = field index. */
(function () {
  'use strict';

  var key = 'hbbg:' + (window.location.pathname.split('/').pop() || 'unknown');
  var fields = Array.prototype.slice.call(
    document.querySelectorAll('table.fill input, table.fill textarea, body.worksheet textarea, header input')
  );

  function load() {
    try {
      var saved = JSON.parse(window.localStorage.getItem(key) || '{}');
      fields.forEach(function (f) {
        if (saved[f.id] !== undefined) { f.value = saved[f.id]; }
      });
    } catch (e) { /* storage unavailable; worksheet still works unsaved */ }
  }

  function save() {
    var data = {};
    fields.forEach(function (f) { data[f.id] = f.value; });
    try {
      window.localStorage.setItem(key, JSON.stringify(data));
    } catch (e) { /* ignore */ }
  }

  // Give every field a stable id.
  fields.forEach(function (f, i) { if (!f.id) { f.id = 'f' + i; } });

  load();

  fields.forEach(function (f) {
    f.addEventListener('input', function () {
      save();
      if (f.hasAttribute('data-median')) { updateMedian(); }
    });
  });

  // Buttons: Print / Clear.
  document.querySelectorAll('button[data-action]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var action = btn.getAttribute('data-action');
      if (action === 'print') { window.print(); }
      if (action === 'clear') {
        fields.forEach(function (f) { f.value = f.value === undefined ? '' : ''; });
        try { window.localStorage.removeItem(key); } catch (e) { /* ignore */ }
        updateMedian();
      }
    });
  });

  // Media helpers: the median calculator on the variable-income worksheet.
  function updateMedian() {
    var inputs = Array.prototype.slice.call(document.querySelectorAll('input[data-median]'));
    var out = document.querySelector('[data-median-output]');
    if (!out) { return; }
    var nums = inputs.map(function (i) { return parseFloat(i.value); })
      .filter(function (n) { return isFinite(n); })
      .sort(function (a, b) { return a - b; });
    var mid = Math.floor(nums.length / 2);
    var shown;
    if (nums.length === 0) {
      shown = '\u2014';
    } else if (nums.length % 2 === 1) {
      shown = nums[mid];
    } else {
      shown = (nums[mid - 1] + nums[mid]) / 2;
    }
    out.textContent = shown;
  }

  updateMedian();
})();
