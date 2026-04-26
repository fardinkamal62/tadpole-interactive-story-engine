(function () {
    const form = document.getElementById('login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const btnText = document.getElementById('btn-text');
    const spinner = document.getElementById('btn-spinner');
    const errorAlert = document.getElementById('error-alert');
    const loginBtn = document.getElementById('login-btn');
    const loggedInAlert = document.getElementById('already-logged-in');
    const loggedInText = document.getElementById('already-logged-in-text');
    const formWrap = document.getElementById('login-form-wrap');
    const loginCard = document.querySelector('.login-card');
    const togglePassword = document.getElementById('toggle-password');
    const logoutBtn = document.getElementById('logout-btn');

    document.querySelectorAll('[data-animate]').forEach((node) => {
        node.classList.add('is-visible');
    });

    if (!form || !usernameInput || !passwordInput || !btnText || !spinner || !errorAlert || !loginBtn) {
        return;
    }

    const showAlreadyLoggedIn = () => {
        const rawUser = localStorage.getItem('auth_user');
        let name;

        try {
            const parsed = rawUser ? JSON.parse(rawUser) : null;
            name = parsed?.username || '';
        } catch (err) {
            name = '';
        }

        if (name && loggedInText) {
            loggedInText.textContent = `You are already signed in as ${name}.`;
        }
        loggedInAlert?.classList.remove('d-none');
        formWrap?.classList.add('d-none');
        errorAlert.classList.add('d-none');
        errorAlert.textContent = '';
    };

    const showError = (message) => {
        if (loginCard) {
            loginCard.classList.remove('shake');
            // Restart animation so consecutive invalid submits still provide feedback.
            void loginCard.offsetWidth;
            loginCard.classList.add('shake');
        }
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
    };

    const hideError = () => {
        errorAlert.classList.add('d-none');
        errorAlert.textContent = '';
    };

    const setLoading = (isLoading) => {
        loginBtn.disabled = isLoading;
        btnText.textContent = isLoading ? 'Signing in...' : 'Sign in';
        spinner.classList.toggle('d-none', !isLoading);
    };

    if (togglePassword) {
        togglePassword.addEventListener('click', () => {
            const isHidden = passwordInput.type === 'password';
            passwordInput.type = isHidden ? 'text' : 'password';
            togglePassword.textContent = isHidden ? 'Hide' : 'Show';
            togglePassword.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
        });
    }

    if (localStorage.getItem('auth_token')) {
        showAlreadyLoggedIn();
    }

    logoutBtn?.addEventListener('click', () => {
        const token = localStorage.getItem('auth_token');

        const finalizeLogout = () => {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            window.location.reload();
        };

        if (!token) {
            finalizeLogout();
            return;
        }

        fetch('/api/auth/logout/', {
            method: 'POST',
            headers: {
                Authorization: `Token ${token}`,
            },
        }).finally(finalizeLogout);
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        hideError();

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            showError('Please enter both username and password.');
            return;
        }

        setLoading(true);
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            const response = await fetch('/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                const message = data?.errors?.non_field_errors?.[0]
                    || data?.message
                    || 'Invalid username or password.';
                showError(message);
                return;
            }

            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('auth_user', JSON.stringify(data.user));

            const next = new URLSearchParams(window.location.search).get('next') || '/';
            window.location.replace(next);
        } catch (err) {
            console.error('Login error:', err);
            showError('Something went wrong. Please try again.');
        } finally {
            setLoading(false);
        }
    });
})();

