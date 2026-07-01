document.addEventListener('DOMContentLoaded', function() {
    // Scroll Reveal Observer
    const revealOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const revealObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            }
            entry.target.classList.add('visible');
            // Optional: stop observing once revealed
            // observer.unobserve(entry.target);
        });
    }, revealOptions);

    const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale, .scroll-fade, .scroll-animate');
    revealElements.forEach(el => {
        revealObserver.observe(el);
    });

    // Also observe counter stats if any
    const counterElements = document.querySelectorAll('.num, .stat-num');
    const counterObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // If there's counter logic, trigger it here.
                // For now, we just ensure it's visible.
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    });
    counterElements.forEach(el => counterObserver.observe(el));
});
