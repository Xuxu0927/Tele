/**
 * Tele 主题增强脚本
 * - 密码保护（首次输入后记住）
 * - 阅读进度条
 * - 平滑滚动
 */

(function () {
  'use strict';

  // ================= 0. 密码保护 =================
  var PASSWORD_HASH = 'b3a8e0e1f9ab1bfe3a36f231f676f78bb30a519d2b21e6c530c0eee8ebb4a5d0';
  var AUTH_KEY = '_tele_auth_v2';

  function injectPasswordStyles() {
    var style = document.createElement('style');
    style.textContent = [
      '#password-overlay {',
      '  position: fixed; top: 0; left: 0; width: 100%; height: 100%;',
      '  background: var(--md-default-bg-color, #fff);',
      '  z-index: 9999; display: flex; align-items: center; justify-content: center;',
      '}',
      '.password-box {',
      '  text-align: center; padding: 40px; border-radius: 12px;',
      '  box-shadow: 0 4px 24px rgba(0,0,0,0.12);',
      '  background: var(--md-default-bg-color, #fff);',
      '  max-width: 360px; width: 90%;',
      '}',
      '.password-box h2 { margin-bottom: 20px; font-size: 1.3rem; }',
      '.password-box input {',
      '  width: 100%; padding: 10px 14px; border: 2px solid #ddd;',
      '  border-radius: 8px; font-size: 1rem; outline: none;',
      '  transition: border-color 0.2s;',
      '}',
      '.password-box input:focus { border-color: #5c6bc0; }',
      '.password-box button {',
      '  margin-top: 14px; padding: 10px 36px;',
      '  background: #5c6bc0; color: #fff; border: none;',
      '  border-radius: 8px; font-size: 1rem; cursor: pointer;',
      '  transition: background 0.2s;',
      '}',
      '.password-box button:hover { background: #3f51b5; }',
    ].join('\n');
    document.head.appendChild(style);
  }

  function sha256(message) {
    var encoder = new TextEncoder();
    var data = encoder.encode(message);
    return crypto.subtle.digest('SHA-256', data).then(function (buffer) {
      return Array.prototype.map.call(new Uint8Array(buffer), function (b) {
        return ('00' + b.toString(16)).slice(-2);
      }).join('');
    });
  }

  function showOverlay() {
    var overlay = document.getElementById('password-overlay');
    if (overlay) overlay.style.display = 'flex';
  }

  function hideOverlay() {
    var overlay = document.getElementById('password-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  function initPasswordProtection() {
    injectPasswordStyles();

    if (localStorage.getItem(AUTH_KEY) === '1') {
      hideOverlay();
      return;
    }

    showOverlay();

    var input = document.getElementById('password-input');
    var btn = document.getElementById('password-submit');
    var error = document.getElementById('password-error');

    function tryLogin() {
      var pw = input.value.trim();
      if (!pw) return;

      sha256(pw).then(function (hash) {
        if (hash === PASSWORD_HASH) {
          localStorage.setItem(AUTH_KEY, '1');
          hideOverlay();
          error.style.display = 'none';
        } else {
          error.style.display = 'block';
          input.value = '';
          input.focus();
        }
      });
    }

    btn.addEventListener('click', tryLogin);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') tryLogin();
    });
  }

  // ================= 1. 阅读进度条 =================
  function createProgressBar() {
    var bar = document.createElement('div');
    bar.className = 'reading-progress';
    document.body.prepend(bar);

    function update() {
      var scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
      var scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      if (scrollHeight > 0) {
        var pct = Math.min((scrollTop / scrollHeight) * 100, 100);
        bar.style.width = pct + '%';
      }
    }

    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update, { passive: true });
  }

  // ================= 2. 初始化和页面切换 =================
  function init() {
    initPasswordProtection();
    createProgressBar();
  }

  // DOM 加载完后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // 支持 MkDocs Material 的 instant navigation（如果启用）
  // 页面切换时重新同步进度条
  if (typeof document$ !== 'undefined') {
    document$.subscribe(function () {
      var bar = document.querySelector('.reading-progress');
      if (bar) {
        bar.style.width = '0';
      }
    });
  }
})();
