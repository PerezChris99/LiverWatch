/**
 * LiverWatch - Main Application Module
 * =====================================
 * 
 * Main application initialization and global functionality.
 */

(function() {
    'use strict';

    const { $, $$, on, debounce, throttle, isInViewport, storage, eventBus } = LiverWatch;

    // =========================================
    // Theme Management
    // =========================================

    const Theme = {
        STORAGE_KEY: 'liverwatch-theme',
        
        init() {
            // Load saved theme or detect system preference
            const savedTheme = storage.get(this.STORAGE_KEY);
            const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
                this.setDark();
            }

            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!storage.get(this.STORAGE_KEY)) {
                    e.matches ? this.setDark() : this.setLight();
                }
            });

            // Theme toggle buttons
            on(document, 'click', '.theme-toggle', () => this.toggle());
        },

        setDark() {
            document.body.classList.add('dark-mode');
            this.updateIcon('moon');
            eventBus.emit('theme:change', 'dark');
        },

        setLight() {
            document.body.classList.remove('dark-mode');
            this.updateIcon('sun');
            eventBus.emit('theme:change', 'light');
        },

        toggle() {
            const isDark = document.body.classList.contains('dark-mode');
            isDark ? this.setLight() : this.setDark();
            storage.set(this.STORAGE_KEY, isDark ? 'light' : 'dark');
        },

        updateIcon(type) {
            $$('.theme-toggle i').forEach(icon => {
                icon.className = type === 'moon' ? 'fas fa-moon' : 'fas fa-sun';
            });
        }
    };

    // =========================================
    // Navbar Functionality
    // =========================================

    const Navbar = {
        element: null,
        scrollThreshold: 50,

        init() {
            this.element = $('.navbar');
            if (!this.element) return;

            // Scroll handler
            window.addEventListener('scroll', throttle(() => this.onScroll(), 100));
            this.onScroll();

            // Mobile menu toggle
            const toggler = $('.navbar-toggler');
            const nav = $('.navbar-nav');

            if (toggler && nav) {
                on(toggler, 'click', () => {
                    toggler.classList.toggle('active');
                    nav.classList.toggle('show');
                    document.body.classList.toggle('nav-open');
                });

                // Close on link click (mobile)
                on(nav, 'click', '.nav-link:not(.dropdown-toggle)', () => {
                    toggler.classList.remove('active');
                    nav.classList.remove('show');
                    document.body.classList.remove('nav-open');
                });
            }
        },

        onScroll() {
            if (!this.element) return;

            if (window.scrollY > this.scrollThreshold) {
                this.element.classList.add('navbar-scrolled');
            } else {
                this.element.classList.remove('navbar-scrolled');
            }
        }
    };

    // =========================================
    // Scroll Animations
    // =========================================

    const ScrollAnimations = {
        observer: null,

        init() {
            if (!('IntersectionObserver' in window)) {
                // Fallback: show all elements
                $$('[data-animate]').forEach(el => el.classList.add('animated'));
                return;
            }

            this.observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add('animated');
                            this.observer.unobserve(entry.target);
                        }
                    });
                },
                {
                    threshold: 0.1,
                    rootMargin: '0px 0px -50px 0px'
                }
            );

            $$('[data-animate]').forEach(el => this.observer.observe(el));
            $$('[data-animate-children]').forEach(el => this.observer.observe(el));
        },

        refresh() {
            $$('[data-animate]:not(.animated)').forEach(el => {
                this.observer.observe(el);
            });
        }
    };

    // =========================================
    // Smooth Scroll
    // =========================================

    const SmoothScroll = {
        init() {
            on(document, 'click', 'a[href^="#"]', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;

                const target = $(targetId);
                if (!target) return;

                e.preventDefault();

                const navbarHeight = $('.navbar')?.offsetHeight || 0;
                const targetPosition = target.getBoundingClientRect().top + window.scrollY - navbarHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });

                // Update URL
                history.pushState(null, null, targetId);
            });
        }
    };

    // =========================================
    // Back to Top Button
    // =========================================

    const BackToTop = {
        button: null,
        threshold: 300,

        init() {
            this.button = $('#back-to-top');
            if (!this.button) {
                this.create();
            }

            window.addEventListener('scroll', throttle(() => this.onScroll(), 100));
            on(this.button, 'click', () => this.scrollToTop());
        },

        create() {
            this.button = LiverWatch.createElement('button', {
                id: 'back-to-top',
                className: 'btn btn-primary btn-icon back-to-top',
                'aria-label': 'Back to top',
                title: 'Back to top'
            }, [
                LiverWatch.createElement('i', { className: 'fas fa-arrow-up' })
            ]);
            document.body.appendChild(this.button);
        },

        onScroll() {
            if (window.scrollY > this.threshold) {
                this.button.classList.add('visible');
            } else {
                this.button.classList.remove('visible');
            }
        },

        scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
    };

    // =========================================
    // Form Enhancements
    // =========================================

    const FormEnhancements = {
        init() {
            // Float labels
            $$('.form-group.floating input, .form-group.floating textarea').forEach(input => {
                this.checkFloatLabel(input);
                on(input, 'focus', () => this.checkFloatLabel(input));
                on(input, 'blur', () => this.checkFloatLabel(input));
                on(input, 'input', () => this.checkFloatLabel(input));
            });

            // Character counter
            $$('[data-maxlength]').forEach(input => {
                const max = parseInt(input.dataset.maxlength);
                const counter = LiverWatch.createElement('span', {
                    className: 'char-counter text-sm text-muted'
                });
                input.parentNode.appendChild(counter);

                const updateCounter = () => {
                    const current = input.value.length;
                    counter.textContent = `${current}/${max}`;
                    counter.classList.toggle('text-danger', current > max);
                };

                updateCounter();
                on(input, 'input', updateCounter);
            });

            // Password visibility toggle
            $$('.password-toggle').forEach(toggle => {
                on(toggle, 'click', function() {
                    const input = this.previousElementSibling;
                    const icon = $('i', this);
                    
                    if (input.type === 'password') {
                        input.type = 'text';
                        icon.className = 'fas fa-eye-slash';
                    } else {
                        input.type = 'password';
                        icon.className = 'fas fa-eye';
                    }
                });
            });

            // Form validation styling
            on(document, 'submit', 'form[data-validate]', function(e) {
                if (!this.checkValidity()) {
                    e.preventDefault();
                    this.classList.add('was-validated');
                    
                    // Focus first invalid field
                    const invalid = $(':invalid', this);
                    if (invalid) invalid.focus();
                }
            });
        },

        checkFloatLabel(input) {
            const group = input.closest('.form-group');
            if (!group) return;

            if (input.value || document.activeElement === input) {
                group.classList.add('has-value');
            } else {
                group.classList.remove('has-value');
            }
        }
    };

    // =========================================
    // Lazy Loading Images
    // =========================================

    const LazyLoad = {
        init() {
            if ('loading' in HTMLImageElement.prototype) {
                // Native lazy loading supported
                $$('img[data-src]').forEach(img => {
                    img.src = img.dataset.src;
                    img.loading = 'lazy';
                });
            } else {
                // Fallback with IntersectionObserver
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.add('loaded');
                            observer.unobserve(img);
                        }
                    });
                });

                $$('img[data-src]').forEach(img => observer.observe(img));
            }
        }
    };

    // =========================================
    // Ripple Effect for Buttons
    // =========================================

    const RippleEffect = {
        init() {
            on(document, 'click', '.btn, .ripple', function(e) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const ripple = LiverWatch.createElement('span', {
                    className: 'ripple-effect'
                });

                ripple.style.left = `${x}px`;
                ripple.style.top = `${y}px`;

                this.appendChild(ripple);

                setTimeout(() => ripple.remove(), 600);
            });
        }
    };

    // =========================================
    // Counter Animation
    // =========================================

    const CounterAnimation = {
        init() {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.animate(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.5 });

            $$('[data-counter]').forEach(el => observer.observe(el));
        },

        animate(element) {
            const target = parseInt(element.dataset.counter);
            const duration = parseInt(element.dataset.duration) || 2000;
            const start = 0;
            const startTime = performance.now();

            const step = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // Ease out
                const easeProgress = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(start + (target - start) * easeProgress);

                element.textContent = LiverWatch.formatNumber(current);

                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    element.textContent = LiverWatch.formatNumber(target);
                }
            };

            requestAnimationFrame(step);
        }
    };

    // =========================================
    // Flash Messages
    // =========================================

    const FlashMessages = {
        init() {
            // Auto-dismiss flash messages
            $$('.alert[data-dismiss="auto"]').forEach(alert => {
                const delay = parseInt(alert.dataset.delay) || 5000;
                setTimeout(() => {
                    alert.style.animation = 'fadeOutUp 0.3s ease forwards';
                    setTimeout(() => alert.remove(), 300);
                }, delay);
            });

            // Dismiss buttons
            on(document, 'click', '.alert .btn-close', function() {
                const alert = this.closest('.alert');
                alert.style.animation = 'fadeOut 0.3s ease forwards';
                setTimeout(() => alert.remove(), 300);
            });
        }
    };

    // =========================================
    // Keyboard Navigation
    // =========================================

    const KeyboardNav = {
        init() {
            // Add visible focus indicators for keyboard users
            document.body.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-nav');
                }
            });

            document.body.addEventListener('mousedown', () => {
                document.body.classList.remove('keyboard-nav');
            });
        }
    };

    // =========================================
    // Page Transition Effects
    // =========================================

    const PageTransitions = {
        init() {
            // Add page transition class on load
            document.body.classList.add('page-transition');
            
            // Intercept navigation links for smooth transitions
            on(document, 'click', 'a:not([target="_blank"]):not([href^="#"]):not(.no-transition)', (e) => {
                const link = e.target.closest('a');
                if (!link || !link.href) return;
                
                // Check if it's an internal link
                const url = new URL(link.href);
                if (url.origin !== window.location.origin) return;
                
                e.preventDefault();
                this.navigateTo(link.href);
            });
        },

        navigateTo(url) {
            document.body.classList.add('page-transitioning');
            
            setTimeout(() => {
                window.location.href = url;
            }, 300);
        }
    };

    // =========================================
    // Loading Skeleton Manager
    // =========================================

    const SkeletonLoader = {
        create(type = 'card', count = 3) {
            const container = document.createElement('div');
            container.className = 'skeleton-container';
            
            for (let i = 0; i < count; i++) {
                const skeleton = this.createSkeleton(type);
                container.appendChild(skeleton);
            }
            
            return container;
        },

        createSkeleton(type) {
            const skeleton = document.createElement('div');
            skeleton.className = 'skeleton-card';
            
            switch(type) {
                case 'card':
                    skeleton.innerHTML = `
                        <div class="skeleton-wave skeleton-circle" style="margin-bottom: 16px;"></div>
                        <div class="skeleton-wave skeleton-line long"></div>
                        <div class="skeleton-wave skeleton-line medium"></div>
                        <div class="skeleton-wave skeleton-line short"></div>
                    `;
                    break;
                case 'list':
                    skeleton.innerHTML = `
                        <div class="skeleton-wave skeleton-line long"></div>
                        <div class="skeleton-wave skeleton-line medium"></div>
                    `;
                    break;
                case 'profile':
                    skeleton.innerHTML = `
                        <div style="display: flex; gap: 16px;">
                            <div class="skeleton-wave skeleton-circle"></div>
                            <div style="flex: 1;">
                                <div class="skeleton-wave skeleton-line long"></div>
                                <div class="skeleton-wave skeleton-line short"></div>
                            </div>
                        </div>
                    `;
                    break;
            }
            
            return skeleton;
        },

        replace(container, content) {
            const skeletons = container.querySelectorAll('.skeleton-container');
            skeletons.forEach(skeleton => {
                skeleton.style.opacity = '0';
                setTimeout(() => {
                    skeleton.remove();
                    if (content) {
                        container.innerHTML = content;
                        this.animateIn(container);
                    }
                }, 300);
            });
        },

        animateIn(container) {
            const children = container.children;
            Array.from(children).forEach((child, index) => {
                child.style.opacity = '0';
                child.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    child.style.transition = 'all 0.4s ease';
                    child.style.opacity = '1';
                    child.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
    };

    // =========================================
    // Pull to Refresh
    // =========================================

    const PullToRefresh = {
        threshold: 80,
        startY: 0,
        pulling: false,
        indicator: null,

        init() {
            if (!('ontouchstart' in window)) return;
            
            this.createIndicator();
            
            window.addEventListener('touchstart', (e) => this.onTouchStart(e), { passive: true });
            window.addEventListener('touchmove', (e) => this.onTouchMove(e), { passive: false });
            window.addEventListener('touchend', () => this.onTouchEnd());
        },

        createIndicator() {
            this.indicator = document.createElement('div');
            this.indicator.className = 'pull-refresh';
            this.indicator.innerHTML = '<i class="fas fa-sync-alt"></i>';
            document.body.appendChild(this.indicator);
        },

        onTouchStart(e) {
            if (window.scrollY === 0) {
                this.startY = e.touches[0].clientY;
                this.pulling = true;
            }
        },

        onTouchMove(e) {
            if (!this.pulling) return;
            
            const currentY = e.touches[0].clientY;
            const pullDistance = currentY - this.startY;
            
            if (pullDistance > 0 && window.scrollY === 0) {
                e.preventDefault();
                
                if (pullDistance > this.threshold) {
                    this.indicator.classList.add('active');
                } else {
                    this.indicator.classList.remove('active');
                }
            }
        },

        onTouchEnd() {
            if (!this.pulling) return;
            this.pulling = false;
            
            if (this.indicator.classList.contains('active')) {
                window.location.reload();
            } else {
                this.indicator.classList.remove('active');
            }
        }
    };

    // =========================================
    // Interactive Card Enhancements
    // =========================================

    const CardInteractions = {
        init() {
            // Add interactive behaviors to priority cards
            $$('.priority-card').forEach(card => {
                this.enhanceCard(card);
            });

            // Add ripple effect to buttons
            $$('.btn, .card-link').forEach(el => {
                if (!el.classList.contains('ripple')) {
                    el.classList.add('ripple');
                }
            });
        },

        enhanceCard(card) {
            // Add tilt effect on mouse move
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 20;
                const rotateY = (centerX - x) / 20;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        }
    };

    // =========================================
    // Progress Indicators
    // =========================================

    const ProgressIndicators = {
        init() {
            this.observeProgressRings();
        },

        observeProgressRings() {
            const rings = $$('.progress-ring-circle');
            if (rings.length === 0) return;

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.animateProgress(entry.target);
                    }
                });
            }, { threshold: 0.5 });

            rings.forEach(ring => observer.observe(ring));
        },

        animateProgress(circle) {
            const percent = parseFloat(circle.getAttribute('data-percent') || 0);
            const circumference = 283;
            const offset = circumference - (percent / 100) * circumference;
            
            setTimeout(() => {
                circle.style.strokeDashoffset = offset;
            }, 100);
        }
    };

    // =========================================
    // Floating Action Button
    // =========================================

    const FAB = {
        init() {
            const fab = $('.fab');
            if (!fab) return;

            // Hide FAB when scrolling down, show when scrolling up
            let lastScroll = 0;
            
            window.addEventListener('scroll', throttle(() => {
                const currentScroll = window.scrollY;
                
                if (currentScroll > lastScroll && currentScroll > 200) {
                    fab.style.transform = 'translateY(100px)';
                } else {
                    fab.style.transform = 'translateY(0)';
                }
                
                lastScroll = currentScroll;
            }, 100));
        }
    };

    // =========================================
    // Toast Notifications
    // =========================================

    const Toast = {
        show(message, type = 'info', duration = 3000) {
            const toast = this.create(message, type);
            document.body.appendChild(toast);
            
            // Trigger enter animation
            setTimeout(() => toast.classList.add('toast-enter'), 10);
            
            // Auto dismiss
            setTimeout(() => this.dismiss(toast), duration);
        },

        create(message, type) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 16px 24px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 12px;
                max-width: 400px;
            `;
            
            const icon = this.getIcon(type);
            toast.innerHTML = `
                <i class="fas fa-${icon}" style="font-size: 20px; color: var(--${type === 'info' ? 'primary' : type}-500);"></i>
                <span style="flex: 1;">${message}</span>
                <button class="toast-close" style="background: none; border: none; cursor: pointer; font-size: 18px; color: var(--gray-500);">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            const closeBtn = toast.querySelector('.toast-close');
            closeBtn.addEventListener('click', () => this.dismiss(toast));
            
            return toast;
        },

        getIcon(type) {
            const icons = {
                'info': 'info-circle',
                'success': 'check-circle',
                'warning': 'exclamation-triangle',
                'error': 'times-circle'
            };
            return icons[type] || icons.info;
        },

        dismiss(toast) {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-exit');
            
            setTimeout(() => toast.remove(), 300);
        }
    };

    // =========================================
    // Initialize Application
    // =========================================

    function init() {
        Theme.init();
        Navbar.init();
        ScrollAnimations.init();
        SmoothScroll.init();
        BackToTop.init();
        FormEnhancements.init();
        LazyLoad.init();
        RippleEffect.init();
        CounterAnimation.init();
        FlashMessages.init();
        KeyboardNav.init();

        // New app-like features
        PageTransitions.init();
        PullToRefresh.init();
        CardInteractions.init();
        ProgressIndicators.init();
        FAB.init();

        // Page loaded
        document.body.classList.add('page-loaded');

        // Emit ready event
        eventBus.emit('app:ready');
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // =========================================
    // Export Modules
    // =========================================

    LiverWatch.Theme = Theme;
    LiverWatch.Navbar = Navbar;
    LiverWatch.ScrollAnimations = ScrollAnimations;
    LiverWatch.PageTransitions = PageTransitions;
    LiverWatch.SkeletonLoader = SkeletonLoader;
    LiverWatch.Toast = Toast;
    LiverWatch.init = init;

})();
