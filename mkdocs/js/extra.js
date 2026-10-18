/**
 * Tele 主题增强脚本
 * - 阅读进度条
 * - 平滑滚动
 */

(function () {
  'use strict';

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
