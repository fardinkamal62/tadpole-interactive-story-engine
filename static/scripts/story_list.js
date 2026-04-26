(function () {
    const animatedNodes = document.querySelectorAll('[data-animate]');
    const searchInput = document.getElementById('story-search');
    const searchMeta = document.getElementById('story-search-meta');
    const cards = Array.from(document.querySelectorAll('[data-story-card]'));

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

    const applyFilter = () => {
        if (!searchInput || !searchMeta || !cards.length) {
            return;
        }

        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        cards.forEach((card) => {
            const title = card.querySelector('h2')?.textContent?.toLowerCase() || '';
            const description = card.querySelector('[data-story-description]')?.textContent?.toLowerCase() || '';
            const isMatch = !query || title.includes(query) || description.includes(query);
            card.classList.toggle('is-hidden', !isMatch);
            if (isMatch) {
                visibleCount += 1;
            }
        });

        if (!query) {
            searchMeta.textContent = 'Showing all stories';
            return;
        }

        searchMeta.textContent = visibleCount > 0
            ? `Showing ${visibleCount} matching stor${visibleCount === 1 ? 'y' : 'ies'}`
            : 'No matching stories';
    };

    revealElements();
    if (searchInput) {
        searchInput.addEventListener('input', applyFilter);
    }
})();

