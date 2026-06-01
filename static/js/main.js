/* ================================================================
   WanderSphere – main.js
   Global utilities: toasts, star-widget helpers, CSRF token.
   ================================================================ */

'use strict';

// ── CSRF helper (works with Django's cookie-based CSRF) ──────────
function getCookie(name) {
  const val = `; ${document.cookie}`;
  const parts = val.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
const CSRF = getCookie('csrftoken');

// ── Generic AJAX POST helper ─────────────────────────────────────
async function apiPost(url, data) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': CSRF,
    },
    body: JSON.stringify(data),
  });
  return { ok: resp.ok, data: await resp.json() };
}

// ── Toast helper ─────────────────────────────────────────────────
function showToast(message, type = 'primary') {
  const container = document.getElementById('toast-container')
                  || (() => {
                      const el = document.createElement('div');
                      el.id = 'toast-container';
                      document.body.appendChild(el);
                      return el;
                    })();

  const el = document.createElement('div');
  el.className = `toast align-items-center text-bg-${type} border-0 mb-2`;
  el.setAttribute('role', 'alert');
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(el);
  const t = new bootstrap.Toast(el, { delay: 4000 });
  t.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

// ── Auto-dismiss toasts on page load ────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toast').forEach(el => {
    const t = new bootstrap.Toast(el, { delay: 4000 });
    t.show();
  });
});
