<style>
/* 隐藏首页 git 日期和作者信息 */
.md-source-file { display: none !important; }
/* ===== 首页星图 ===== */
.starmap {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 520px;
    margin: 20px 0;
    overflow: visible;
}

.starmap svg {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
}

/* 连线动画 */
.star-line {
    stroke: var(--md-default-fg-color--lighter, #ccc);
    stroke-width: 1;
    stroke-dasharray: 4 3;
    animation: lineFlow 3s linear infinite;
}

@keyframes lineFlow {
    to { stroke-dashoffset: -14; }
}

/* 中心节点 */
.center-node {
    position: relative;
    z-index: 10;
    text-align: center;
    cursor: default;
}

.center-icon {
    display: block;
    font-size: 3rem;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

.center-text {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    color: var(--md-primary-fg-color);
}

/* 环绕节点 */
.star-node {
    position: absolute;
    z-index: 10;
    text-align: center;
    transition: transform 0.3s ease;
}

.star-node:hover {
    transform: scale(1.15);
}

.star-node a {
    display: block;
    text-decoration: none !important;
    background-image: none !important;
    color: var(--md-default-fg-color) !important;
    padding: 6px 10px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
    white-space: nowrap;
    transition: all 0.3s ease;
    border: 1px solid transparent;
}

.star-node a:hover {
    color: var(--md-primary-fg-color) !important;
    border-color: var(--md-primary-fg-color);
}

/* 节点小圆点 */
.star-dot {
    display: block;
    width: 6px;
    height: 6px;
    margin: 0 auto 4px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    animation: dotPulse 2s ease-in-out infinite;
}

@keyframes dotPulse {
    0%, 100% { box-shadow: 0 0 4px var(--md-primary-fg-color); }
    50% { box-shadow: 0 0 12px var(--md-primary-fg-color); }
}

/* 移动端 */
@media (max-width: 600px) {
    .starmap { min-height: 420px; }
    .center-text { font-size: 1.6rem; }
    .center-icon { font-size: 2.2rem; }
    .star-node a { font-size: 0.78rem; padding: 4px 8px; }
}
</style>

<div class="starmap">

<!-- SVG 连线层 -->
<svg viewBox="0 0 600 520" preserveAspectRatio="xMidYMid meet">
    <line class="star-line" x1="300" y1="230" x2="300" y2="70" />
    <line class="star-line" x1="300" y1="230" x2="470" y2="110" />
    <line class="star-line" x1="300" y1="230" x2="530" y2="260" />
    <line class="star-line" x1="300" y1="230" x2="470" y2="400" />
    <line class="star-line" x1="300" y1="230" x2="300" y2="440" />
    <line class="star-line" x1="300" y1="230" x2="130" y2="400" />
    <line class="star-line" x1="300" y1="230" x2="70" y2="260"  />
    <line class="star-line" x1="300" y1="230" x2="130" y2="110" />
</svg>

<!-- 中心 -->
<div class="center-node">
    <span class="center-icon">📡</span>
    <span class="center-text">Tele</span>
</div>

<!-- 环绕节点 -->
<div class="star-node" style="top:36px; left:50%; transform:translateX(-50%);">
    <span class="star-dot"></span>
    <a href="电子通信/index.md">电子通信</a>
</div>

<div class="star-node" style="top:78px; right:32px;">
    <span class="star-dot"></span>
    <a href="数学/index.md">数学</a>
</div>

<div class="star-node" style="top:228px; right:2px;">
    <span class="star-dot"></span>
    <a href="物理/index.md">物理</a>
</div>

<div class="star-node" style="bottom:100px; right:32px;">
    <span class="star-dot"></span>
    <a href="计算机/index.md">计算机</a>
</div>

<div class="star-node" style="bottom:32px; left:50%; transform:translateX(-50%);">
    <span class="star-dot"></span>
    <a href="英语/index.md">英语</a>
</div>

<div class="star-node" style="bottom:100px; left:44px;">
    <span class="star-dot"></span>
    <a href="运动/index.md">运动</a>
</div>

<div class="star-node" style="top:228px; left:12px;">
    <span class="star-dot"></span>
    <a href="娱乐/index.md">娱乐</a>
</div>

</div>
