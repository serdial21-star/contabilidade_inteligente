/* T-0010 — tema claro/escuro do S21 Contábil. Só preferência visual no navegador; nenhum dado de negócio.
   Carregado no <head> sem defer para aplicar o tema antes da primeira pintura. */
(function (root) {
  'use strict';
  const KEY = 's21.theme';
  const html = root.document.documentElement;
  function stored() {
    try { const value = root.localStorage.getItem(KEY); return value === 'dark' || value === 'light' ? value : null; }
    catch (_) { return null; }
  }
  function preferred() {
    try { return root.matchMedia && root.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }
    catch (_) { return 'light'; }
  }
  function apply(theme) { html.setAttribute('data-theme', theme === 'dark' ? 'dark' : 'light'); }
  function current() { return html.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }
  function toggle() {
    const next = current() === 'dark' ? 'light' : 'dark';
    apply(next);
    try { root.localStorage.setItem(KEY, next); } catch (_) { /* preferência não persiste; a tela continua funcionando */ }
    return next;
  }
  apply(stored() || preferred());
  root.S21Theme = Object.freeze({current, toggle});
}(globalThis));
