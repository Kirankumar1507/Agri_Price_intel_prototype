/* ============================================
   Agri Price Intel — Walkthrough Interactions
   ============================================ */

// --- Scroll Reveal ---
document.addEventListener('DOMContentLoaded', () => {
    const revealElements = document.querySelectorAll('[data-reveal]');

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

    revealElements.forEach(el => revealObserver.observe(el));

    // --- Counter Animation ---
    const counters = document.querySelectorAll('.stat-number[data-count]');
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(el => counterObserver.observe(el));

    function animateCounter(el) {
        const target = parseInt(el.dataset.count, 10);
        const duration = 1800;
        const startTime = performance.now();
        const suffix = target >= 100 ? '+' : '';

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(eased * target);
            el.textContent = current + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        requestAnimationFrame(update);
    }

    // --- Tab Switching ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;

            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const panel = document.getElementById('tab-' + tabId);
            if (panel) panel.classList.add('active');
        });
    });

    // --- Smooth scroll for anchor links ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // --- Map pin hover animations ---
    const mapPins = document.querySelectorAll('.map-pin');
    mapPins.forEach(pin => {
        pin.addEventListener('mouseenter', () => {
            pin.style.transform = 'scale(1.4)';
            pin.style.zIndex = '10';
            pin.style.transition = 'transform 0.2s ease';
        });
        pin.addEventListener('mouseleave', () => {
            pin.style.transform = 'scale(1)';
            pin.style.zIndex = '';
        });
    });

    // --- Verdict cards stagger animation ---
    const verdictCards = document.querySelectorAll('.verdict-card');
    const verdictObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const cards = entry.target.querySelectorAll ?
                    entry.target.parentElement.querySelectorAll('.verdict-card') :
                    [];
                verdictCards.forEach((card, i) => {
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, i * 120);
                });
                verdictObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    if (verdictCards.length > 0) {
        verdictCards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(10px)';
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        });
        verdictObserver.observe(verdictCards[0]);
    }

    // --- Pipeline step hover glow ---
    const pipeSteps = document.querySelectorAll('.pipe-step');
    pipeSteps.forEach(step => {
        step.addEventListener('mouseenter', () => {
            step.style.transform = 'translateY(-4px)';
            step.style.transition = 'transform 0.25s ease';
        });
        step.addEventListener('mouseleave', () => {
            step.style.transform = 'translateY(0)';
        });
    });

    // --- Tech card tilt effect ---
    const techCards = document.querySelectorAll('.tech-card');
    techCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            card.style.transform = `translateY(-3px) perspective(600px) rotateX(${-y * 4}deg) rotateY(${x * 4}deg)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) perspective(600px) rotateX(0) rotateY(0)';
            card.style.transition = 'transform 0.4s ease';
        });
    });

    // --- Interactive Demo Logic ---
    const demoState = document.getElementById('demo-state');
    const demoCrop = document.getElementById('demo-crop');
    const demoLocation = document.getElementById('demo-location');
    const demoBtn = document.getElementById('demo-btn');
    const demoPinTooltip = document.querySelector('.pin-best .pin-tooltip');
    const demoChartTitle = document.querySelector('.chart-title');
    const demoSchemeName = document.querySelector('.scheme-name');
    const demoSchemeTag = document.querySelector('.scheme-tag');

    const crops = {
        karnataka: ["Ragi", "Paddy", "Tur", "Jowar", "Maize", "Sugarcane", "Cotton", "Groundnut", "Bengal Gram", "Green Gram", "Onion", "Tomato", "Potato"],
        haryana: ["Wheat", "Paddy", "Mustard", "Bajra", "Cotton", "Sugarcane", "Bengal Gram", "Groundnut", "Onion", "Tomato", "Potato"]
    };

    function updateCrops() {
        const state = demoState.value;
        const currentCrops = crops[state] || [];
        
        demoCrop.innerHTML = '';
        currentCrops.forEach(crop => {
            const opt = document.createElement('option');
            opt.value = crop.toLowerCase().replace(/\s+/g, '-');
            opt.textContent = crop;
            demoCrop.appendChild(opt);
        });

        if (state === 'haryana' && demoLocation.value === 'Mandya, Karnataka') {
            demoLocation.value = 'Hisar, Haryana';
        } else if (state === 'karnataka' && demoLocation.value === 'Hisar, Haryana') {
            demoLocation.value = 'Mandya, Karnataka';
        }

        updateUI();
    }

    function updateUI() {
        const cropName = demoCrop.options[demoCrop.selectedIndex]?.text || '';
        const stateName = demoState.options[demoState.selectedIndex].text;
        const locName = demoLocation.value.split(',')[0].trim();

        if (demoPinTooltip) demoPinTooltip.textContent = `${locName} · ₹3,500/qtl`;
        if (demoChartTitle) demoChartTitle.textContent = `15-Day Price Trend — ${cropName} (₹/qtl)`;
        if (demoSchemeTag) demoSchemeTag.textContent = stateName;
        
        if (demoSchemeName) {
            if (cropName === 'Ragi' || cropName === 'Jowar') {
                demoSchemeName.textContent = 'Raitha Siri (Millet Incentive)';
            } else if (cropName === 'Wheat' || cropName === 'Paddy') {
                demoSchemeName.textContent = `MSP Procurement — ${cropName}`;
            } else {
                demoSchemeName.textContent = 'PM-KISAN';
            }
        }
    }

    if (demoState) {
        demoState.addEventListener('change', updateCrops);
        demoCrop.addEventListener('change', updateUI);
        demoLocation.addEventListener('input', updateUI);
        updateCrops();
        
        demoBtn.addEventListener('click', () => {
            demoBtn.textContent = 'Analyzing...';
            demoBtn.style.opacity = '0.7';
            setTimeout(() => {
                demoBtn.textContent = 'Get Market Intelligence';
                demoBtn.style.opacity = '1';
                document.getElementById('solution').scrollIntoView({ behavior: 'smooth' });
            }, 800);
        });
    }
});
