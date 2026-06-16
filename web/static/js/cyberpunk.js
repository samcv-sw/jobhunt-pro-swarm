// ==========================================
// Cyberpunk UI God-Tier Effects - JobHunt Pro
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Particles.js (Tactile Brutalism Node Network)
    if (window.particlesJS) {
        particlesJS('particles-js', {
            "particles": {
                "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
                "color": { "value": "#3b82f6" },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.5, "random": true },
                "size": { "value": 3, "random": true },
                "line_linked": {
                    "enable": true,
                    "distance": 150,
                    "color": "#3b82f6",
                    "opacity": 0.4,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 2,
                    "direction": "none",
                    "random": false,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": false,
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": { "enable": true, "mode": "grab" },
                    "onclick": { "enable": true, "mode": "push" },
                    "resize": true
                },
                "modes": {
                    "grab": { "distance": 140, "line_linked": { "opacity": 1 } },
                    "push": { "particles_nb": 4 }
                }
            },
            "retina_detect": true
        });
    }

    // 2. Cryptographic Decryption Typing Effect (Scrambler)
    class TextScrambler {
        constructor() {
            this.chars = '!<>-_\\\\/[]{}—=+*^?#________';
        }
        scramble(element) {
            const originalText = element.dataset.original || element.innerText || element.textContent;
            if (!element.dataset.original) {
                element.dataset.original = originalText; // Save original
            }
            
            // Prevent re-scrambling if it's already running
            if (element.hasAttribute('data-scrambling')) return;
            element.setAttribute('data-scrambling', 'true');
            
            let frame = 0;
            const length = originalText.length;
            const queue = [];
            
            for (let i = 0; i < length; i++) {
                const char = originalText[i];
                if (char === ' ' || char === '\\n') {
                    queue.push({ char, isSpace: true, start: 0, end: 0 });
                } else {
                    const start = Math.floor(Math.random() * 40);
                    const end = start + Math.floor(Math.random() * 40);
                    queue.push({ char, start, end, isSpace: false });
                }
            }
            
            const update = () => {
                let output = '';
                let complete = 0;
                
                for (let i = 0; i < length; i++) {
                    let { char, start, end, isSpace } = queue[i];
                    
                    if (isSpace) {
                        output += char;
                        complete++;
                        continue;
                    }
                    
                    if (frame >= end) {
                        complete++;
                        output += char;
                    } else if (frame >= start) {
                        output += this.chars[Math.floor(Math.random() * this.chars.length)];
                    } else {
                        output += '';
                    }
                }
                
                element.innerText = output;
                
                if (complete === length) {
                    element.removeAttribute('data-scrambling');
                } else {
                    frame++;
                    requestAnimationFrame(update);
                }
            };
            
            update();
        }
    }

    const scrambler = new TextScrambler();
    const scrambleElements = document.querySelectorAll('.scramble-text');
    
    // Scramble on load
    scrambleElements.forEach(el => {
        scrambler.scramble(el);
        // Also scramble on hover for tactile feel
        el.addEventListener('mouseenter', () => scrambler.scramble(el));
    });
});
