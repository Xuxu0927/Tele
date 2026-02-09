hide:
  - navigation
  - toc

<style>
  /* === 1. 基础重置与全屏容器 === */
  .md-content__inner { margin-top: 0; padding-top: 0; }
  .md-typeset h1 { display: none; } /* 隐藏默认标题 */

  body, html {
    margin: 0;
    padding: 0;
    overflow-x: hidden;
    background-color: #050505; /* 纯黑底色 */
  }

  .hero-container {
    position: relative;
    width: 100vw;
    height: 100vh; /* 占满全屏 */
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    overflow: hidden;
    color: white;
  }

  /* Canvas 背景层 */
  #hero-canvas {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 1;
    /* 轻微的径向渐变，营造深空感 */
    background: radial-gradient(circle at center, #1a1f35 0%, #050505 80%);
  }

  /* === 2. 内容层：居中展示 === */
  .hero-content {
    z-index: 10;
    text-align: center;
    pointer-events: none; /* 让鼠标事件穿透文字，直接作用于粒子 */
    user-select: none;
  }

  /* === 3. 故障风格标题 (Glitch Title) === */
  .glitch-wrapper {
    position: relative;
    margin-bottom: 20px;
  }

  .main-title {
    font-size: 7rem;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -5px;
    color: #fff;
    font-family: 'Segoe UI', Impact, sans-serif;
    position: relative;
    text-transform: uppercase;
  }

  /* 故障残影层 1 */
  .main-title::before {
    content: attr(data-text);
    position: absolute;
    left: -2px;
    text-shadow: 1px 0 #ff00c1;
    top: 0;
    color: white;
    background: #050505;
    overflow: hidden;
    clip: rect(0, 900px, 0, 0); 
    animation: glitch-anim-1 2s infinite linear alternate-reverse;
  }

  /* 故障残影层 2 */
  .main-title::after {
    content: attr(data-text);
    position: absolute;
    left: 2px;
    text-shadow: -1px 0 #00fff9;
    top: 0;
    color: white;
    background: #050505;
    overflow: hidden;
    clip: rect(0, 900px, 0, 0); 
    animation: glitch-anim-2 3s infinite linear alternate-reverse;
  }

  @keyframes glitch-anim-1 {
    0% { clip: rect(20px, 9999px, 15px, 0); }
    20% { clip: rect(70px, 9999px, 90px, 0); }
    40% { clip: rect(30px, 9999px, 5px, 0); }
    60% { clip: rect(80px, 9999px, 55px, 0); }
    80% { clip: rect(10px, 9999px, 40px, 0); }
    100% { clip: rect(60px, 9999px, 75px, 0); }
  }

  @keyframes glitch-anim-2 {
    0% { clip: rect(65px, 9999px, 100px, 0); }
    20% { clip: rect(10px, 9999px, 50px, 0); }
    40% { clip: rect(90px, 9999px, 20px, 0); }
    60% { clip: rect(15px, 9999px, 60px, 0); }
    80% { clip: rect(55px, 9999px, 35px, 0); }
    100% { clip: rect(40px, 9999px, 80px, 0); }
  }

  /* === 4. 副标题与打字机 === */
  .subtitle {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.6);
    font-family: monospace;
    letter-spacing: 2px;
    text-transform: uppercase;
    display: inline-block;
    padding: 5px 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    border: 1px solid rgba(255,255,255,0.1);
  }

  .typing-cursor {
    display: inline-block;
    width: 8px;
    height: 10px;
    background-color: #00fff9;
    animation: blink 0.8s step-end infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }

  /* 底部装饰：滚动提示 */
  .scroll-indicator {
    position: absolute;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    color: rgba(255,255,255,0.3);
    font-size: 0.8rem;
    letter-spacing: 2px;
    animation: float 2s ease-in-out infinite;
  }
  @keyframes float { 0%, 100% { transform: translate(-50%, 0); } 50% { transform: translate(-50%, 10px); } }

  /* 移动端适配 */
  @media screen and (max-width: 768px) {
    .main-title { font-size: 3.5rem; letter-spacing: -2px; }
    .subtitle { font-size: 0.9rem; }
  }
</style>

<div class="hero-container">
  <canvas id="hero-canvas"></canvas>

  <div class="hero-content">
    <div class="glitch-wrapper">
      <div class="main-title" data-text="Tele">TeleComm</div>
    </div>

    <div class="subtitle">
      <span style="color: #00fff9;">SYSTEM:</span> <span id="typing-text"></span><span class="typing-cursor"></span>
    </div>
  </div>

  <div class="scroll-indicator">SCROLL TO EXPLORE</div>
</div>

<script>
// --- 配置参数 ---
const config = {
  text: "communication",
  typingSpeed: 60,
  particleCount: window.innerWidth < 768 ? 60 : 150, // 增加粒子密度
  connectionDist: 120,
  mouseDist: 250, // 增大鼠标吸附范围
  colors: ['#00fff9', '#ffffff', '#4d4d4d'] // 青色、白色、灰色混合
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
setTimeout(typeWriter, 500);

// --- 粒子网络系统 ---
const canvas = document.getElementById('hero-canvas');
const ctx = canvas.getContext('2d');
let w, h;
let particles = [];
let mouse = { x: null, y: null };

// 鼠标监听
window.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
});
window.addEventListener('mouseout', () => { mouse.x = null; mouse.y = null; });

function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
}

class Particle {
    constructor() {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        // 随机速度
        this.vx = (Math.random() - 0.5) * 1.5; 
        this.vy = (Math.random() - 0.5) * 1.5;
        this.size = Math.random() * 2;
        // 随机颜色
        this.color = config.colors[Math.floor(Math.random() * config.colors.length)];
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
    
        // 边界反弹
        if (this.x < 0 || this.x > w) this.vx *= -1;
        if (this.y < 0 || this.y > h) this.vy *= -1;
    
        // 强力鼠标吸附
        if (mouse.x != null) {
            let dx = mouse.x - this.x;
            let dy = mouse.y - this.y;
            let distance = Math.sqrt(dx * dx + dy * dy);
    
            if (distance < config.mouseDist) {
                const forceDirectionX = dx / distance;
                const forceDirectionY = dy / distance;
                const force = (config.mouseDist - distance) / config.mouseDist;
                // 更加顺滑的牵引力
                const directionX = forceDirectionX * force * 3; 
                const directionY = forceDirectionY * force * 3;
                this.x += directionX;
                this.y += directionY;
            }
        }
    }
    
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
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
    
        // 连线逻辑
        for (let j = i + 1; j < particles.length; j++) {
            let p2 = particles[j];
            let dx = p.x - p2.x;
            let dy = p.y - p2.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
    
            if (dist < config.connectionDist) {
                ctx.beginPath();
                // 只有近距离才连线，且线条更细更科幻
                let opacity = 1 - (dist / config.connectionDist);
                ctx.strokeStyle = `rgba(0, 255, 249, ${opacity * 0.2})`; // 统一使用青色连线
                ctx.lineWidth = 0.4;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }
    
        // 鼠标高亮连线
        if (mouse.x != null) {
            let dx = mouse.x - p.x;
            let dy = mouse.y - p.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < config.mouseDist) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(255, 255, 255, ${1 - dist / config.mouseDist})`; // 鼠标连线为白色
                ctx.lineWidth = 0.8;
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