---
hide:
  - navigation
  - toc
---

<style>
  /* 隐藏默认的标题层级，让Hero区域独占 */
  .md-content__inner { margin-top: 0; padding-top: 0; }
  .md-typeset h1 { display: none; }

  /* Hero 容器 */
  .hero-container {
    position: relative;
    height: 85vh; /* 占据85%视口高度 */
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    overflow: hidden;
    margin-bottom: 4rem;
  }

  /* 背景 Canvas */
  #hero-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    opacity: 0.6; /* 稍微淡一点，不抢文字 */
  }

  /* 内容层 */
  .hero-content {
    z-index: 10;
    text-align: center;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05); /* 极淡的背景 */
    backdrop-filter: blur(2px);
    border-radius: 20px;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
  }

  /* 渐变流光标题 */
  .gradient-text {
    font-size: 4.5rem;
    font-weight: 800;
    background: linear-gradient(45deg, #4051b5, #ff4081, #4051b5);
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 3s linear infinite;
    margin-bottom: 1rem;
    line-height: 1.2;
  }

  @keyframes shine {
    to { background-position: 200% center; }
  }

  /* 打字机光标 */
  .typing-cursor::after {
    content: '|';
    animation: blink 1s step-end infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }

  /* 按钮组优化 */
  .hero-buttons {
    margin-top: 2rem;
    display: flex;
    gap: 20px;
    justify-content: center;
  }
  .hero-btn {
    padding: 12px 30px;
    border-radius: 30px;
    font-weight: bold;
    transition: all 0.3s ease;
    text-decoration: none !important;
  }
  .hero-btn-primary {
    background: linear-gradient(90deg, #5c6bc0, #3949ab);
    color: white !important;
    box-shadow: 0 4px 15px rgba(63, 81, 181, 0.4);
  }
  .hero-btn-primary:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(63, 81, 181, 0.6);
  }
  .hero-btn-secondary {
    background: rgba(255,255,255,0.8);
    color: #333 !important;
    border: 1px solid #ddd;
  }
  .hero-btn-secondary:hover {
    background: #fff;
    transform: translateY(-3px);
  }

  /* 移动端适配 */
  @media screen and (max-width: 768px) {
    .gradient-text { font-size: 2.5rem; }
    .hero-container { height: 60vh; }
  }
</style>

<div class="hero-container">
    <canvas id="hero-canvas"></canvas>
    <div class="hero-content">
        <div class="gradient-text">Tele Communication</div>
        <p style="font-size: 1.5em; color: var(--md-default-fg-color--light); max-width: 600px; margin: 0 auto;">
            <span id="typing-text"></span><span class="typing-cursor"></span>
        </p>
        <div class="hero-buttons">
            <a href="电子通信/" class="hero-btn hero-btn-primary">探索知识库</a>      
        </div>
    </div>
</div>



<script>
// --- 打字机特效 ---
const textToType = "探索原理，构建未来。";
const typeSpeed = 100;
let charIndex = 0;
function typeWriter() {
    if (charIndex < textToType.length) {
        document.getElementById("typing-text").innerHTML += textToType.charAt(charIndex);
        charIndex++;
        setTimeout(typeWriter, typeSpeed);
    }
}
// 延迟一点开始打字
setTimeout(typeWriter, 1000);


// --- 粒子连线动画 (无需Three.js) ---
const canvas = document.getElementById('hero-canvas');
const ctx = canvas.getContext('2d');
let width, height;
let particles = [];

// 粒子配置
const particleCount = window.innerWidth < 768 ? 40 : 100; // 移动端少一点
const connectionDistance = 150;
const moveSpeed = 0.5;

function resize() {
    width = canvas.width = canvas.parentElement.offsetWidth;
    height = canvas.height = canvas.parentElement.offsetHeight;
}

class Particle {
    constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * moveSpeed;
        this.vy = (Math.random() - 0.5) * moveSpeed;
        this.size = Math.random() * 2 + 1;
    }
    update() {
        this.x += this.vx;
        this.y += this.vy;
        // 边界反弹
        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;
    }
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--md-primary-fg-color') || '#5c6bc0';
        ctx.fill();
    }
}

function init() {
    resize();
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    animate();
}

function animate() {
    ctx.clearRect(0, 0, width, height);
    
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
            
            if (dist < connectionDistance) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(92, 107, 192, ${1 - dist/connectionDistance})`; // 距离越近越不透明
                ctx.lineWidth = 1;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }
    }
    requestAnimationFrame(animate);
}

window.addEventListener('resize', () => {
    resize();
    particles = [];
    init(); // 重置以防变形
});

// 启动
init();
</script>