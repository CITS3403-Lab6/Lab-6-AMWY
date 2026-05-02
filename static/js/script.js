/**
 * HabitWise - Static JavaScript
 * Handles client-side interactions and RPG theme features
 */

// Set random background image on page load
document.addEventListener('DOMContentLoaded', function() {
    const backgroundImages = [
        '/static/img/backgrounds/origbig.png',
        '/static/img/backgrounds/origbig2.png',
        '/static/img/backgrounds/origbig3.png',
        '/static/img/backgrounds/origbig4.png'
    ];
    
    const bgLayer = document.getElementById('bgLayer');
    if (bgLayer) {
        const randomImage = backgroundImages[Math.floor(Math.random() * backgroundImages.length)];
        bgLayer.style.backgroundImage = `url('${randomImage}')`;
        // Fallback: if image fails to load, set a gradient
        bgLayer.onerror = function() {
            bgLayer.style.backgroundImage = 'linear-gradient(135deg, #1f2937 0%, #111827 100%)';
        };
    }
});

// Add ripple effect to buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('button')) {
        const button = e.target;
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        
        button.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }
});

// Add CSS animation for ripple effect
const style = document.createElement('style');
style.textContent = `
    .button {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Form validation enhancements
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', function(e) {
        // Add visual feedback during submission
        const buttons = form.querySelectorAll('button[type="submit"]');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.6';
        });
    });
});

// Console greeting
console.log('%c⚔️ HabitWise ⚔️', 'font-size: 24px; color: #22c55e; font-weight: bold; text-shadow: 2px 2px 0px rgba(0,0,0,0.5);');
console.log('%cMake the oath. Face the monsters. Build unbreakable habits.', 'font-size: 12px; color: #d1d5db;');
