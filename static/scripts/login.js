const $form     = $('#login-form');
const $username = $('#username');
const $password = $('#password');
const $btnText  = $('#btn-text');
const $spinner  = $('#btn-spinner');
const $error    = $('#error-alert');
const $btn      = $('#login-btn');
const $loggedIn = $('#already-logged-in');
const $loggedInText = $('#already-logged-in-text');
const $formWrap = $('#login-form-wrap');

function showAlreadyLoggedIn() {
    const rawUser = localStorage.getItem('auth_user');
    let name = '';
    try {
        const parsed = rawUser ? JSON.parse(rawUser) : null;
        name = parsed?.username || '';
    } catch (err) {
        name = '';
    }

    if (name) {
        $loggedInText.text(`You are already signed in as ${name}.`);
    }
    $loggedIn.removeClass('d-none');
    $formWrap.addClass('d-none');
    $error.addClass('d-none').text('');
}

function showError(msg) {
    $error.text(msg).removeClass('d-none');
}

function hideError() {
    $error.addClass('d-none').text('');
}

function setLoading(on) {
    $btn.prop('disabled', on);
    $btnText.text(on ? 'Signing in…' : 'Sign in');
    $spinner.toggleClass('d-none', !on);
}

if (localStorage.getItem('auth_token')) {
    showAlreadyLoggedIn();
}

$('#logout-btn').on('click', function () {
    const token = localStorage.getItem('auth_token');

    const finalizeLogout = function () {
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

$form.on('submit', async function (e) {
    e.preventDefault();
    hideError();

    const username = $username.val().trim();
    const password = $password.val();

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
            const msg = data?.errors?.non_field_errors?.[0]
                || data?.message
                || 'Invalid username or password.';
            showError(msg);
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

