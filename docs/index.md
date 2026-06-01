<style>
/* 隐藏首页 git 日期和作者信息 */
.md-source-file { display: none !important; }
/* 隐藏首页一级标题 */
.md-typeset h1 { display: none !important; }

/* ==========================================
   首页星图 — 星座特效
   ========================================== */
.starmap {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 640px;
    margin: 20px 0;
    overflow: visible;
}

/* ---------- 背景星场粒子 ---------- */
.star-particle {
    position: absolute;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    animation: particleTwinkle var(--dur) ease-in-out infinite;
    animation-delay: var(--delay);
    pointer-events: none;
}

@keyframes particleTwinkle {
    0%, 100% { opacity: 0.15; transform: scale(1); }
    50%      { opacity: 0.9;  transform: scale(1.8); }
}

/* ---------- 旋转轨道 ---------- */
.star-orbit {
    position: absolute;
    top: 50%; left: 50%;
    width: 0; height: 0;
    animation: orbitSpin 90s linear infinite;
}

@keyframes orbitSpin {
    to { transform: rotate(360deg); }
}

/* ---------- SVG 连线 ---------- */
.starmap svg.lines-layer {
    position: absolute;
    top: -360px; left: -425px;
    width: 850px; height: 720px;
    pointer-events: none;
    z-index: 1;
}

.star-line {
    stroke: var(--md-primary-fg-color);
    stroke-width: 1.2;
    stroke-dasharray: 6 4;
    opacity: 0.55;
    animation: lineFlow 2.5s linear infinite;
    filter: url(#starGlow);
}

.star-line:nth-child(odd)  { animation-duration: 2.5s; animation-delay: 0s; }
.star-line:nth-child(even) { animation-duration: 3.2s; animation-delay: -1s; }

@keyframes lineFlow {
    to { stroke-dashoffset: -20; }
}

/* ---------- 光晕轨道环 ---------- */
.center-aura {
    position: absolute;
    width: 140px; height: 140px;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    border: 1.5px solid transparent;
    border-top-color: var(--md-primary-fg-color);
    border-right-color: color-mix(in srgb, var(--md-primary-fg-color) 40%, transparent);
    opacity: 0.35;
    animation: auraSpin 6s linear infinite;
    pointer-events: none;
    z-index: 5;
}

.center-aura::after {
    content: "";
    position: absolute;
    inset: 8px;
    border-radius: 50%;
    border: 1px solid transparent;
    border-bottom-color: var(--md-accent-fg-color);
    border-left-color: color-mix(in srgb, var(--md-accent-fg-color) 30%, transparent);
    animation: auraSpin 4s linear infinite reverse;
}

@keyframes auraSpin {
    to { transform: translate(-50%, -50%) rotate(360deg); }
}

/* ---------- 中心节点 ---------- */
.center-node {
    position: relative;
    z-index: 10;
    text-align: center;
    cursor: default;
}

.center-icon {
    display: block;
    font-size: 3rem;
    filter: drop-shadow(0 0 12px var(--md-primary-fg-color));
    animation: centerFloat 3s ease-in-out infinite;
}

@keyframes centerFloat {
    0%, 100% { transform: translateY(0) scale(1);   filter: drop-shadow(0 0 12px var(--md-primary-fg-color)); }
    50%      { transform: translateY(-10px) scale(1.05); filter: drop-shadow(0 0 22px var(--md-primary-fg-color)); }
}

.center-text {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    color: var(--md-primary-fg-color);
    text-shadow: 0 0 18px color-mix(in srgb, var(--md-primary-fg-color) 50%, transparent);
    animation: textGlow 3s ease-in-out infinite;
}

@keyframes textGlow {
    0%, 100% { text-shadow: 0 0 12px color-mix(in srgb, var(--md-primary-fg-color) 40%, transparent); }
    50%      { text-shadow: 0 0 28px color-mix(in srgb, var(--md-primary-fg-color) 80%, transparent); }
}

/* ---------- 环绕节点 ---------- */
.star-node {
    position: absolute;
    top: 0; left: 0;
    z-index: 10;
    transform: rotate(var(--a)) translateY(calc(-1 * var(--r)));
    cursor: pointer;
}

.star-node-fix {
    transform: rotate(calc(-1 * var(--a)));
}

.star-node-spin {
    animation: orbitSpin 90s linear infinite reverse;
}

.star-node a {
    display: block;
    text-decoration: none !important;
    background-image: none !important;
    color: var(--md-default-fg-color) !important;
    padding: 8px 14px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
    white-space: nowrap;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
    background: transparent;
}

.star-node a:hover {
    color: #fff !important;
    border-color: var(--md-primary-fg-color);
    background: var(--md-primary-fg-color);
    transform: scale(1.12);
    box-shadow: 0 0 24px color-mix(in srgb, var(--md-primary-fg-color) 50%, transparent),
                0 0 48px color-mix(in srgb, var(--md-primary-fg-color) 25%, transparent);
}

/* ---------- 节点小圆点（脉冲星） ---------- */
.star-dot {
    display: block;
    width: 8px;
    height: 8px;
    margin: 0 auto 5px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    animation: dotPulse 2s ease-in-out infinite;
    animation-delay: var(--dot-delay, 0s);
}

@keyframes dotPulse {
    0%, 100% { box-shadow: 0 0 6px  var(--md-primary-fg-color),
                           0 0 14px color-mix(in srgb, var(--md-primary-fg-color) 40%, transparent); }
    50%      { box-shadow: 0 0 12px var(--md-primary-fg-color),
                           0 0 28px color-mix(in srgb, var(--md-primary-fg-color) 60%, transparent),
                           0 0 44px color-mix(in srgb, var(--md-primary-fg-color) 25%, transparent); }
}

/* ---------- 移动端 ---------- */
@media (max-width: 600px) {
    .starmap { min-height: 520px; }
    .starmap svg.lines-layer { top: -260px; left: -310px; width: 620px; height: 520px; }
    .center-text { font-size: 1.6rem; }
    .center-icon { font-size: 2.2rem; }
    .star-node a { font-size: 0.78rem; padding: 4px 8px; }
    .center-aura { width: 100px; height: 100px; }
}
</style>

<div class="starmap">

<!-- 背景星场粒子 -->
<div class="star-particle" style="top:8%;  left:12%; width:3px; height:3px; --dur: 2.4s; --delay: 0s;"></div>
<div class="star-particle" style="top:15%; left:78%; width:2px; height:2px; --dur: 3.1s; --delay: -0.7s;"></div>
<div class="star-particle" style="top:22%; left:35%; width:2px; height:2px; --dur: 2.8s; --delay: -1.4s;"></div>
<div class="star-particle" style="top:30%; left:88%; width:3px; height:3px; --dur: 3.5s; --delay: -2.1s;"></div>
<div class="star-particle" style="top:38%; left:8%;  width:2px; height:2px; --dur: 2.2s; --delay: -0.3s;"></div>
<div class="star-particle" style="top:45%; left:72%; width:3px; height:3px; --dur: 3.0s; --delay: -1.8s;"></div>
<div class="star-particle" style="top:55%; left:18%; width:2px; height:2px; --dur: 2.6s; --delay: -0.9s;"></div>
<div class="star-particle" style="top:60%; left:92%; width:2px; height:2px; --dur: 3.3s; --delay: -2.5s;"></div>
<div class="star-particle" style="top:68%; left:42%; width:3px; height:3px; --dur: 2.9s; --delay: -1.1s;"></div>
<div class="star-particle" style="top:75%; left:82%; width:2px; height:2px; --dur: 3.7s; --delay: -0.5s;"></div>
<div class="star-particle" style="top:82%; left:22%; width:3px; height:3px; --dur: 2.4s; --delay: -1.7s;"></div>
<div class="star-particle" style="top:88%; left:68%; width:2px; height:2px; --dur: 3.1s; --delay: -2.8s;"></div>
<div class="star-particle" style="top:10%; left:55%; width:2px; height:2px; --dur: 2.7s; --delay: -0.2s;"></div>
<div class="star-particle" style="top:78%; left:52%; width:2px; height:2px; --dur: 2.7s; --delay: -1.9s;"></div>

<!-- 旋转轨道：连线 + 环绕节点 -->
<div class="star-orbit">

<!-- SVG 连线层 -->
<svg class="lines-layer" viewBox="0 0 850 720" preserveAspectRatio="xMidYMid meet">
    <defs>
        <filter id="starGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur" />
            <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
            </feMerge>
        </filter>
    </defs>
    <line class="star-line" x1="425" y1="360" x2="451.1"  y2="61.1" />
    <line class="star-line" x1="425" y1="360" x2="601.2"  y2="212.2" />
    <line class="star-line" x1="425" y1="360" x2="697.5"  y2="459.2" />
    <line class="star-line" x1="425" y1="360" x2="513.9"  y2="604.3" />
    <line class="star-line" x1="425" y1="360" x2="310.9"  y2="604.7" />
    <line class="star-line" x1="425" y1="360" x2="212.5"  y2="416.9" />
    <line class="star-line" x1="425" y1="360" x2="179.3"  y2="187.9" />
</svg>

<!-- 7 个环绕节点（距离不一，非正圆） -->
<div class="star-node" style="--a: 5deg;    --r: 300px;">
    <div class="star-node-fix" style="--a: 5deg;">
        <div class="star-node-spin">
            <span class="star-dot" style="--dot-delay: 0s;"></span>
            <a href="电子通信/">电子通信</a>
        </div>
    </div>
</div>

<div class="star-node" style="--a: 50deg;   --r: 230px;">
    <div class="star-node-fix" style="--a: 50deg;">
        <div class="star-node-spin">
            <span class="star-dot" style="--dot-delay: -0.3s;"></span>
            <a href="数学/">数学</a>
        </div>
    </div>
</div>

<div class="star-node" style="--a: 110deg;  --r: 290px;">
    <div class="star-node-fix" style="--a: 110deg;">
        <div class="star-node-spin">
            <span class="star-dot" style="--dot-delay: -0.6s;"></span>
            <a href="物理/">物理</a>
        </div>
    </div>
</div>

<div class="star-node" style="--a: 160deg;  --r: 260px;">
    <div class="star-node-fix" style="--a: 160deg;">
        <div class="star-node-spin">
            <span class="star-dot" style="--dot-delay: -0.9s;"></span>
            <a href="计算机/">计算机</a>
        </div>
    </div>
</div>

<div class="star-node" style="--a: 205deg;  --r: 270px;">
    <div class="star-node-fix" style="--a: 205deg;">
        <div class="star-node-spin">
            <span class="star-dot" style="--dot-delay: -1.2s;"></span>
            <a href="英语/">英语</a>
        </div>
    </div>
</div>

<div class="star-node" style="--a: 255deg;  --r: 220px;">
    <div class="star-node-fix" style="--a: 255deg;">
        <div class="star-node-spin">
            <span class="star-dot" style="--dot-delay: -1.5s;"></span>
            <a href="运动/">运动</a>
        </div>
    </div>
</div>

<div class="star-node" style="--a: 305deg;  --r: 300px;">
    <div class="star-node-fix" style="--a: 305deg;">
        <div class="star-node-spin">
            <span class="star-dot" style="--dot-delay: -1.8s;"></span>
            <a href="娱乐/">娱乐</a>
        </div>
    </div>
</div>

</div><!-- .star-orbit -->

<!-- 中心光晕环 -->
<div class="center-aura"></div>

<!-- 中心（固定不旋转） -->
<div class="center-node">
    <span class="center-icon">📡</span>
    <span class="center-text">Tele</span>
</div>

</div>
