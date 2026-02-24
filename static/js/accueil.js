/**
 * Accueil JS: Handles transitions, role selection, and accessibility.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Viewport Height Fix
    const setVH = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    };
    setVH();
    window.addEventListener('resize', setVH);

    // 2. DOM Elements
    const heroSection = document.getElementById('heroSection');
    const loginSection = document.getElementById('loginSection');
    const btnShowLogin = document.getElementById('btnShowLogin');
    const btnBackToHero = document.getElementById('btnBackToHero');
    const emailInput = document.getElementById('email');
    const roleList = document.getElementById('roleList');

    // 3. Transition Logic
    const toggleSections = (show, hide, focusEl = null) => {
        hide.classList.remove('active');
        hide.setAttribute('aria-hidden', 'true');
        
        // Small delay to allow the "hide" transition to start before showing the next
        setTimeout(() => {
            show.classList.add('active');
            show.setAttribute('aria-hidden', 'false');
            if (focusEl) focusEl.focus();
        }, 50);
    };

    if (btnShowLogin) {
        btnShowLogin.addEventListener('click', () => {
            toggleSections(loginSection, heroSection, emailInput);
        });
    }

    if (btnBackToHero) {
        btnBackToHero.addEventListener('click', () => {
            toggleSections(heroSection, loginSection);
        });
    }

    // 4. Keyboard Accessibility (ESC to go back)
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && loginSection.classList.contains('active')) {
            toggleSections(heroSection, loginSection);
        }
    });

    // 5. Role Selection Logic
    if (roleList) {
        const options = roleList.querySelectorAll('.role-option');
        
        const updateSelected = () => {
            options.forEach(opt => {
                const radio = opt.querySelector('input[type="radio"]');
                if (radio.checked) {
                    opt.classList.add('selected');
                } else {
                    opt.classList.remove('selected');
                }
            });
        };

        options.forEach(opt => {
            opt.addEventListener('click', () => {
                const radio = opt.querySelector('input[type="radio"]');
                radio.checked = true;
                updateSelected();
            });
        });

        // Sync on direct radio change (keyboard nav)
        roleList.addEventListener('change', updateSelected);

        // Initial update
        updateSelected();
    }

    // 6. Video Fallback
    const bgVideo = document.getElementById('bgVideo');
    if (bgVideo) {
        bgVideo.play().catch(error => {
            console.warn("Video autoplay failed, showing background color fallback.", error);
        });
    }
});
