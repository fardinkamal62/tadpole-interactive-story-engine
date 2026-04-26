(function () {
    const animatedNodes = document.querySelectorAll('[data-animate]');

    const revealElements = () => {
        if (!animatedNodes.length) {
            return;
        }

        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) {
            animatedNodes.forEach((node) => node.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });

        animatedNodes.forEach((node) => observer.observe(node));
    };

    revealElements();

    const loginBtn = document.getElementById('home-login-btn');
    const profileMenu = document.getElementById('home-profile-menu');
    const dashboardBtn = document.getElementById('home-dashboard-btn');
    const profileDashboardLink = document.getElementById('home-profile-dashboard-link');
    const logoutBtn = document.getElementById('home-profile-logout-btn');
    const userNameEl = document.getElementById('home-user-name');
    const userAvatarEl = document.getElementById('home-user-avatar');

    if (!loginBtn || !profileMenu || !dashboardBtn || !profileDashboardLink || !logoutBtn || !userNameEl || !userAvatarEl) {
        return;
    }

    const token = localStorage.getItem('auth_token');
    if (!token) {
        return;
    }

    loginBtn.classList.add('d-none');
    profileMenu.classList.remove('d-none');
    dashboardBtn.setAttribute('href', '/story/');
    profileDashboardLink.setAttribute('href', '/story/');

    logoutBtn.addEventListener('click', async function () {
        try {
            await fetch('/api/auth/logout/', {
                method: 'POST',
                headers: {
                    Authorization: `Token ${token}`,
                },
            });
        } catch (error) {
            // Always clear client auth state even if the API request fails.
        } finally {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            window.location.replace('/');
        }
    });

    let username = 'User';
    try {
        const rawUser = localStorage.getItem('auth_user');
        const parsedUser = rawUser ? JSON.parse(rawUser) : null;
        username = parsedUser?.username || 'User';
    } catch (error) {
        username = 'User';
    }

    userNameEl.textContent = username;
    userAvatarEl.textContent = username.charAt(0).toUpperCase();
})();
