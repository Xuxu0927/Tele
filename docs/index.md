hide:
  - navigation
  - toc

<style>
  /* === 1. 全局布局与背景优化 === */
  .md-content__inner { margin-top: 0; padding-top: 0; }
  .md-typeset h1 { display: none; }

  .hero-container {
    position: relative;
    height: 90vh; /*稍微增加高度*/
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    overflow: hidden;
    /* 动态深色渐变背景 */
    background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #1a1a2e);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    color: white;
    border-radius: 0 0 20px 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  }

  @keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  /* Canvas 必须在最底层 */
  #hero-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1; 
  }

  /* === 2. 内容卡片：磨砂玻璃特效 === */
  .hero-content {
    z-index: 10;
    text-align: center;
    padding: 40px 60px;
    background: rgba(255, 255, 255, 0.03); /* 极低透明度 */
    backdrop-filter: blur(10px); /* 磨砂效果 */
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    transition: transform 0.3s ease;
  }

  .hero-content:hover {
    transform: translateY(-5px);
    border-color: rgba(255, 255, 255, 0.3);
  }

  /* === 3. 字体特效 === */
  .main-title {
    font-size: 5rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
    letter-spacing: -2px;
    /* 霓虹发光文字 */
    color: #fff;
    text-shadow: 0 0 10px rgba(64, 224, 208, 0.7),
                 0 0 20px rgba(64, 224, 208, 0.5),
                 0 0 40px rgba(64, 224, 208, 0.3);
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  }

  .subtitle {
    font-size: 1.5rem;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 2rem;
    font-weight: 300;
    min-height: 1.5em; /* 防止打字时跳动 */
  }

  /* 光标闪烁 */
  .typing-cursor {
    display: inline-block;
    width: 3px;
    height: 1.2em;
    background-color: #00f2ff;
    margin-left: 5px;
    vertical-align: middle;
    animation: blink 1s step-end infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }

  /* === 4. 按钮组 === */
  .hero-buttons {
    display: flex;
    gap: 20px;
    justify-content: center;
  }

  .hero-btn {
    padding: 14px 36px;
    border-radius: 50px;
    font-weight: 600;
    font-size: 1.1rem;
    text-decoration: none !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }

  /* 主要按钮：渐变流光 */
  .hero-btn-primary {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white !important;
    box-shadow: 0 0 20px rgba(0, 198, 255, 0.4);
    border: none;
  }

  .hero-btn-primary:hover {
    box-shadow: 0 0 30px rgba(0, 198, 255, 0.7);
    transform: scale(1.05);
  }

  /* 次要按钮：透明描边 */
  .hero-btn-secondary {
    background: transparent;
    color: #fff !important;
    border: 2px solid rgba(255, 255, 255, 0.3);
  }

  .hero-btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #fff;
  }

  /* 移动端适配 */
  @media screen and (max-width: 768px) {
    .main-title { font-size: 2.8rem; }
    .hero-content { padding: 20px; width: 90%; }
    .hero-container { height: 70vh; }
  }
</style>

<div class="hero-container">
  <canvas id="hero-canvas"></canvas>

  <div class="hero-content">
    <div class="main-title">TeleComm</div>
    <div class="subtitle">
      <span id="typing-text"></span><span class="typing-cursor"></span>
    </div>

    <div class="hero-buttons">
      <a href="./docs/" class="hero-btn hero-btn-primary">开始探索</a>
      <a href="https://github.com/Xuxu0927" target="_blank" class="hero-btn hero-btn-secondary">GitHub</a>
    </div>
  </div>
</div>

<script>
// --- 配置参数 ---
const config = {
  text: "连接世界，感知未来。", // 打字机文字
  typingSpeed: 120,
  particleCount: window.innerWidth < 768 ? 45 : 110, // 粒子数量
  connectionDist: 140, // 连线距离
  mouseDist: 200, // 鼠标吸附距离
  color: '255, 255, 255' // 粒子颜色 (RGB)
};

// --- 打字机逻辑 ---
const typeEl = document.getElementById("typing-text");
let charIndex = 0;
function typeWriter() {
    if (charIndex < config.text.length) {
        typeEl.innerHTML += config.text.charAt(charIndex);
        charIndex++;
        setTimeout(typeWriter, config.typingSpeed);
    }
}
setTimeout(typeWriter, 800);

// --- 炫酷粒子系统 ---
const canvas = document.getElementById('hero-canvas');
const ctx = canvas.getContext('2d');
let w, h;
let particles = [];

// 鼠标位置对象
let mouse = { x: null, y: null };

// 监听鼠标移动
window.addEventListener('mousemove', (e) => {
    // 修正 Canvas 在页面中的偏移
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
});

window.addEventListener('mouseout', () => {
    mouse.x = null;
    mouse.y = null;
});

function resize() {
    w = canvas.width = canvas.parentElement.offsetWidth;
    h = canvas.height = canvas.parentElement.offsetHeight;
}

class Particle {
    constructor() {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        // 随机速度，稍微慢一点更有“漂浮感”
        this.vx = (Math.random() - 0.5) * 0.8; 
        this.vy = (Math.random() - 0.5) * 0.8;
        this.size = Math.random() * 2;
        // 随机透明度，制造闪烁感
        this.baseAlpha = Math.random() * 0.5 + 0.2; 
        this.alpha = this.baseAlpha;
        this.phase = Math.random() * Math.PI * 2; // 呼吸相位
    }

    update() {
        // 1. 基础移动
        this.x += this.vx;
        this.y += this.vy;
    
        // 2. 边界反弹
        if (this.x < 0 || this.x > w) this.vx *= -1;
        if (this.y < 0 || this.y > h) this.vy *= -1;
    
        // 3. 鼠标交互 (核心炫酷点)
        if (mouse.x != null) {
            let dx = mouse.x - this.x;
            let dy = mouse.y - this.y;
            let distance = Math.sqrt(dx * dx + dy * dy);
    
            if (distance < config.mouseDist) {
                // 吸引力：粒子会稍微向鼠标靠近
                const forceDirectionX = dx / distance;
                const forceDirectionY = dy / distance;
                const force = (config.mouseDist - distance) / config.mouseDist;
                const directionX = forceDirectionX * force * 2; // 2是力度
                const directionY = forceDirectionY * force * 2;
                
                this.x += directionX;
                this.y += directionY;
            }
        }
        
        // 4. 呼吸闪烁效果
        this.phase += 0.05;
        this.alpha = this.baseAlpha + Math.sin(this.phase) * 0.2;
    }
    
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${config.color}, ${this.alpha})`;
        ctx.fill();
    }
}

function init() {
    resize();
    particles = [];
    for (let i = 0; i < config.particleCount; i++) {
        particles.push(new Particle());
    }
    animate();
}

function animate() {
    ctx.clearRect(0, 0, w, h);
    
    for (let i = 0; i < particles.length; i++) {
        let p = particles[i];
        p.update();
        p.draw();
    
        // 粒子间连线
        for (let j = i + 1; j < particles.length; j++) {
            let p2 = particles[j];
            let dx = p.x - p2.x;
            let dy = p.y - p2.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
    
            if (dist < config.connectionDist) {
                ctx.beginPath();
                // 线条透明度基于距离
                let opacity = 1 - (dist / config.connectionDist);
                ctx.strokeStyle = `rgba(${config.color}, ${opacity * 0.3})`; 
                ctx.lineWidth = 0.5;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }
    
        // 鼠标连线 (高亮显示)
        if (mouse.x != null) {
            let dx = mouse.x - p.x;
            let dy = mouse.y - p.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < config.mouseDist) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(0, 242, 255, ${1 - dist / config.mouseDist})`; // 青色高亮连线
                ctx.lineWidth = 1;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(mouse.x, mouse.y);
                ctx.stroke();
            }
        }
    }
    requestAnimationFrame(animate);
}

window.addEventListener('resize', () => {
    resize();
    particles = [];
    for (let i = 0; i < config.particleCount; i++) {
        particles.push(new Particle());
    }
});

init();
</script>