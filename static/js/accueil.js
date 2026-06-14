window.updateFormForRole = function (role) {
    const val = String(role).toLowerCase();

    const isAdmin = val === 'admin' || val === 'administrateur';
    const isProfessor = val === 'professor';
    const isStudent = val === 'student';

    const emailWrapper = document.getElementById('emailWrapper');
    const passwordWrapper = document.getElementById('passwordWrapper');
    const submitWrapper = document.getElementById('submitWrapper');
    const adminGoogleBtn = document.getElementById('adminGoogleBtn');

    const standardLoginForm = document.getElementById('standardLoginForm');
    const professorGoogleSection = document.getElementById('professorGoogleSection');
    const studentGoogleSection = document.getElementById('studentGoogleSection');

    const emailLabel = document.getElementById('emailLabel');
    const emailInput = document.getElementById('email');
    const codeLabel = document.getElementById('codeLabel');
    const codeInput = document.getElementById('code');
    const hiddenRole = document.getElementById('hiddenRole');
    const loginPanel = document.getElementById('loginPanel');

    if (loginPanel) {
        loginPanel.classList.remove('student-mode');
    }

    if (emailLabel) emailLabel.textContent = 'Gmail';
    if (emailInput) {
        emailInput.placeholder = 'exemple@gmail.com';
        emailInput.type = 'email';
        emailInput.required = false;
        emailInput.value = '';
        emailInput.autocomplete = 'email';
    }

    if (codeLabel) codeLabel.textContent = "Code d'accès";
    if (codeInput) {
        codeInput.type = 'password';
        codeInput.placeholder = '••••••••';
        codeInput.required = false;
        codeInput.value = '';
        codeInput.autocomplete = 'current-password';
    }

    if (standardLoginForm) standardLoginForm.style.display = 'block';
    if (professorGoogleSection) professorGoogleSection.style.display = 'none';
    if (studentGoogleSection) studentGoogleSection.style.display = 'none';
    if (adminGoogleBtn) adminGoogleBtn.style.display = 'none';

    if (emailWrapper) emailWrapper.style.display = 'block';
    if (passwordWrapper) passwordWrapper.style.display = 'block';
    if (submitWrapper) submitWrapper.style.display = 'block';

    if (isAdmin) {
        if (hiddenRole) hiddenRole.value = 'admin';

        if (emailWrapper) emailWrapper.style.display = 'none';
        if (passwordWrapper) passwordWrapper.style.display = 'none';
        if (submitWrapper) submitWrapper.style.display = 'none';
        if (adminGoogleBtn) adminGoogleBtn.style.display = 'block';
    }

    if (isProfessor) {
        if (standardLoginForm) standardLoginForm.style.display = 'none';
        if (professorGoogleSection) professorGoogleSection.style.display = 'block';
    }

    if (isStudent) {
        if (hiddenRole) hiddenRole.value = 'student';

        if (emailLabel) emailLabel.textContent = 'Code MASSAR';
        if (emailInput) {
            emailInput.placeholder = 'Ex: R123456789';
            emailInput.type = 'text';
            emailInput.required = true;
            emailInput.autocomplete = 'username';
        }

        if (codeLabel) codeLabel.textContent = 'Mot de passe';
        if (codeInput) {
            codeInput.required = true;
            codeInput.placeholder = '••••••••';
            codeInput.autocomplete = 'current-password';
        }

        if (studentGoogleSection) studentGoogleSection.style.display = 'block';
        if (loginPanel) loginPanel.classList.add('student-mode');
    }

    document.querySelectorAll('.role-option').forEach(opt => {
        const radio = opt.querySelector('input[type="radio"]');
        if (!radio) return;
        opt.classList.toggle('selected', radio.value.toLowerCase() === val);
        radio.checked = radio.value.toLowerCase() === val;
    });
};

document.addEventListener('DOMContentLoaded', () => {
    const setVH = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();
    window.addEventListener('resize', setVH);

    const heroSection = document.getElementById('heroSection');
    const loginSection = document.getElementById('loginSection');
    const btnShowLogin = document.getElementById('btnShowLogin');
    const btnBackToHero = document.getElementById('btnBackToHero');

    const toggleSections = (show, hide, focusEl = null) => {
        hide.classList.remove('active');
        hide.setAttribute('aria-hidden', 'true');

        setTimeout(() => {
            show.classList.add('active');
            show.setAttribute('aria-hidden', 'false');
            if (focusEl) focusEl.focus();
        }, 50);
    };

    if (btnShowLogin) {
        btnShowLogin.addEventListener('click', () => toggleSections(loginSection, heroSection));
    }

    if (btnBackToHero) {
        btnBackToHero.addEventListener('click', () => toggleSections(heroSection, loginSection));
    }

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && loginSection.classList.contains('active')) {
            toggleSections(heroSection, loginSection);
        }
    });

    const initialChecked = document.querySelector('input[name="role"]:checked');
    if (initialChecked) {
        window.updateFormForRole(initialChecked.value);
    }

    const bgVideo = document.getElementById('bgVideo');
    if (bgVideo) {
        bgVideo.play().catch(err => console.warn("Video autoplay failed", err));
    }

    const hasMessages = document.querySelector('.alert') !== null;
    if (hasMessages && heroSection && loginSection) {
        heroSection.classList.remove('active');
        heroSection.setAttribute('aria-hidden', 'true');
        loginSection.classList.add('active');
        loginSection.setAttribute('aria-hidden', 'false');
    }
});