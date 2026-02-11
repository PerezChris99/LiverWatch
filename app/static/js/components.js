/**
 * LiverWatch - UI Components Module
 * ==================================
 * 
 * Reusable UI components: Toast, Modal, Loader, etc.
 */

(function() {
    'use strict';

    const { $, $$, createElement, on, removeElement, generateId, config } = LiverWatch;

    // =========================================
    // Toast Notifications
    // =========================================

    const Toast = {
        container: null,

        init() {
            if (!this.container) {
                this.container = createElement('div', {
                    className: 'toast-container',
                    id: 'toast-container'
                });
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info', duration = config.toastDuration) {
            this.init();

            const icons = {
                success: 'fas fa-check-circle',
                error: 'fas fa-exclamation-circle',
                warning: 'fas fa-exclamation-triangle',
                info: 'fas fa-info-circle'
            };

            const toast = createElement('div', {
                className: `toast toast-${type} animate-slide-up`,
                role: 'alert',
                'aria-live': 'polite'
            }, [
                createElement('i', { className: `toast-icon ${icons[type]}` }),
                createElement('div', { className: 'toast-content' }, [
                    createElement('p', { className: 'toast-message' }, [message])
                ]),
                createElement('button', {
                    className: 'toast-close',
                    'aria-label': 'Close notification',
                    onClick: () => this.dismiss(toast)
                }, [
                    createElement('i', { className: 'fas fa-times' })
                ])
            ]);

            this.container.appendChild(toast);

            // Auto dismiss
            if (duration > 0) {
                setTimeout(() => this.dismiss(toast), duration);
            }

            return toast;
        },

        dismiss(toast) {
            if (toast && toast.parentNode) {
                removeElement(toast, 'slideOutRight');
            }
        },

        success(message, duration) {
            return this.show(message, 'success', duration);
        },

        error(message, duration) {
            return this.show(message, 'error', duration);
        },

        warning(message, duration) {
            return this.show(message, 'warning', duration);
        },

        info(message, duration) {
            return this.show(message, 'info', duration);
        }
    };

    // =========================================
    // Modal Component
    // =========================================

    const Modal = {
        activeModals: [],

        create(options = {}) {
            const {
                id = generateId(),
                title = '',
                content = '',
                footer = null,
                size = 'medium',
                closable = true,
                onClose = null,
                onConfirm = null
            } = options;

            // Build footer if confirm callback provided
            let footerContent = footer;
            if (!footer && onConfirm) {
                footerContent = createElement('div', { className: 'modal-footer-buttons' }, [
                    createElement('button', {
                        className: 'btn btn-secondary',
                        onClick: () => this.close(id)
                    }, ['Cancel']),
                    createElement('button', {
                        className: 'btn btn-primary',
                        onClick: () => {
                            onConfirm();
                            this.close(id);
                        }
                    }, ['Confirm'])
                ]);
            }

            const modal = createElement('div', {
                className: 'modal-overlay',
                id: id,
                role: 'dialog',
                'aria-modal': 'true',
                'aria-labelledby': `${id}-title`
            }, [
                createElement('div', { className: `modal modal-${size} animate-scale-in` }, [
                    createElement('div', { className: 'modal-header' }, [
                        createElement('h3', {
                            className: 'modal-title',
                            id: `${id}-title`
                        }, [title]),
                        closable ? createElement('button', {
                            className: 'modal-close',
                            'aria-label': 'Close modal',
                            onClick: () => this.close(id)
                        }, [
                            createElement('i', { className: 'fas fa-times' })
                        ]) : null
                    ].filter(Boolean)),
                    createElement('div', { className: 'modal-body' }, [
                        typeof content === 'string' ? content : content
                    ]),
                    footerContent ? createElement('div', { className: 'modal-footer' }, [
                        footerContent
                    ]) : null
                ].filter(Boolean))
            ]);

            // Close on backdrop click
            if (closable) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) this.close(id);
                });
            }

            // Store reference
            modal._onClose = onClose;

            document.body.appendChild(modal);
            document.body.style.overflow = 'hidden';
            this.activeModals.push(id);

            // Focus trap
            const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable.length) focusable[0].focus();

            return id;
        },

        close(id) {
            const modal = $(`#${id}`);
            if (!modal) return;

            const modalContent = $('.modal', modal);
            if (modalContent) {
                modalContent.style.animation = 'scaleOut 0.2s ease forwards';
            }

            setTimeout(() => {
                if (modal._onClose) modal._onClose();
                modal.remove();
                this.activeModals = this.activeModals.filter(m => m !== id);
                if (this.activeModals.length === 0) {
                    document.body.style.overflow = '';
                }
            }, 200);
        },

        closeAll() {
            this.activeModals.forEach(id => this.close(id));
        },

        confirm(message, onConfirm, onCancel) {
            return this.create({
                title: 'Confirm',
                content: createElement('p', {}, [message]),
                onConfirm,
                onClose: onCancel
            });
        },

        alert(title, message) {
            return this.create({
                title,
                content: createElement('p', {}, [message]),
                footer: createElement('button', {
                    className: 'btn btn-primary',
                    onClick: () => this.close(this.activeModals[this.activeModals.length - 1])
                }, ['OK'])
            });
        }
    };

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && Modal.activeModals.length > 0) {
            Modal.close(Modal.activeModals[Modal.activeModals.length - 1]);
        }
    });

    // =========================================
    // Loader Component
    // =========================================

    const Loader = {
        overlay: null,

        show(message = 'Loading...') {
            if (this.overlay) return;

            this.overlay = createElement('div', {
                className: 'loading-overlay',
                role: 'alert',
                'aria-busy': 'true'
            }, [
                createElement('div', { className: 'loader-content' }, [
                    createElement('div', { className: 'spinner spinner-lg' }),
                    createElement('p', { className: 'loader-text mt-4' }, [message])
                ])
            ]);

            document.body.appendChild(this.overlay);
            document.body.style.overflow = 'hidden';
        },

        hide() {
            if (!this.overlay) return;

            this.overlay.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => {
                if (this.overlay) {
                    this.overlay.remove();
                    this.overlay = null;
                }
                document.body.style.overflow = '';
            }, 300);
        },

        /**
         * Show loader during async operation
         */
        async wrap(promise, message) {
            this.show(message);
            try {
                return await promise;
            } finally {
                this.hide();
            }
        }
    };

    // =========================================
    // Dropdown Component
    // =========================================

    const Dropdown = {
        init() {
            // Toggle dropdowns
            on(document, 'click', '.dropdown-toggle', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const dropdown = this.closest('.dropdown');
                const wasOpen = dropdown.classList.contains('show');

                // Close all open dropdowns
                $$('.dropdown.show').forEach(d => d.classList.remove('show'));

                // Toggle current if it was closed
                if (!wasOpen) {
                    dropdown.classList.add('show');
                }
            });

            // Close dropdowns on outside click
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.dropdown')) {
                    $$('.dropdown.show').forEach(d => d.classList.remove('show'));
                }
            });

            // Close on escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    $$('.dropdown.show').forEach(d => d.classList.remove('show'));
                }
            });
        }
    };

    // =========================================
    // Tabs Component
    // =========================================

    const Tabs = {
        init() {
            on(document, 'click', '.tab-link', function(e) {
                e.preventDefault();

                const tabsContainer = this.closest('.tabs');
                const targetId = this.getAttribute('href') || this.dataset.tab;
                const target = $(targetId, tabsContainer.parentElement);

                if (!target) return;

                // Update tab links
                $$('.tab-link', tabsContainer).forEach(tab => {
                    tab.classList.remove('active');
                    tab.setAttribute('aria-selected', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-selected', 'true');

                // Update tab panels
                $$('.tab-panel', tabsContainer.parentElement).forEach(panel => {
                    panel.classList.remove('active');
                    panel.setAttribute('hidden', '');
                });
                target.classList.add('active');
                target.removeAttribute('hidden');
            });
        }
    };

    // =========================================
    // Accordion Component
    // =========================================

    const Accordion = {
        init() {
            on(document, 'click', '.accordion-header', function() {
                const item = this.closest('.accordion-item');
                const accordion = item.closest('.accordion');
                const content = $('.accordion-content', item);
                const isOpen = item.classList.contains('active');

                // Single mode: close others
                if (accordion && !accordion.dataset.multiple) {
                    $$('.accordion-item.active', accordion).forEach(openItem => {
                        if (openItem !== item) {
                            openItem.classList.remove('active');
                            const openContent = $('.accordion-content', openItem);
                            openContent.style.maxHeight = '0';
                        }
                    });
                }

                // Toggle current
                if (isOpen) {
                    item.classList.remove('active');
                    content.style.maxHeight = '0';
                } else {
                    item.classList.add('active');
                    content.style.maxHeight = content.scrollHeight + 'px';
                }
            });

            // Initialize open accordions
            $$('.accordion-item.active').forEach(item => {
                const content = $('.accordion-content', item);
                content.style.maxHeight = content.scrollHeight + 'px';
            });
        }
    };

    // =========================================
    // Tooltip Component
    // =========================================

    const Tooltip = {
        current: null,

        init() {
            // Show tooltip
            on(document, 'mouseenter', '[data-tooltip]', function() {
                const text = this.dataset.tooltip;
                const position = this.dataset.tooltipPosition || 'top';

                const tooltip = createElement('div', {
                    className: `tooltip tooltip-${position} animate-fade-in`,
                    role: 'tooltip'
                }, [text]);

                document.body.appendChild(tooltip);
                Tooltip.current = tooltip;

                // Position tooltip
                const rect = this.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();

                let top, left;

                switch (position) {
                    case 'bottom':
                        top = rect.bottom + 8;
                        left = rect.left + (rect.width - tooltipRect.width) / 2;
                        break;
                    case 'left':
                        top = rect.top + (rect.height - tooltipRect.height) / 2;
                        left = rect.left - tooltipRect.width - 8;
                        break;
                    case 'right':
                        top = rect.top + (rect.height - tooltipRect.height) / 2;
                        left = rect.right + 8;
                        break;
                    default: // top
                        top = rect.top - tooltipRect.height - 8;
                        left = rect.left + (rect.width - tooltipRect.width) / 2;
                }

                tooltip.style.top = `${top + window.scrollY}px`;
                tooltip.style.left = `${Math.max(8, left)}px`;
            });

            // Hide tooltip
            on(document, 'mouseleave', '[data-tooltip]', function() {
                if (Tooltip.current) {
                    Tooltip.current.remove();
                    Tooltip.current = null;
                }
            });
        }
    };

    // =========================================
    // Progress Bar Component
    // =========================================

    const ProgressBar = {
        update(element, value, max = 100) {
            const bar = $(typeof element === 'string' ? element : null) || element;
            if (!bar) return;

            const percentage = Math.min(100, Math.max(0, (value / max) * 100));
            bar.style.width = `${percentage}%`;
            bar.setAttribute('aria-valuenow', value);
            
            // Update text if present
            const text = $('.progress-text', bar.parentElement);
            if (text) {
                text.textContent = `${Math.round(percentage)}%`;
            }
        },

        animate(element, targetValue, duration = 1000) {
            const bar = $(typeof element === 'string' ? element : null) || element;
            if (!bar) return;

            const startValue = parseFloat(bar.style.width) || 0;
            const startTime = performance.now();

            const step = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // Ease out
                const easeProgress = 1 - Math.pow(1 - progress, 3);
                const currentValue = startValue + (targetValue - startValue) * easeProgress;

                this.update(bar, currentValue);

                if (progress < 1) {
                    requestAnimationFrame(step);
                }
            };

            requestAnimationFrame(step);
        }
    };

    // =========================================
    // Initialize All Components
    // =========================================

    function initComponents() {
        Dropdown.init();
        Tabs.init();
        Accordion.init();
        Tooltip.init();
    }

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initComponents);
    } else {
        initComponents();
    }

    // =========================================
    // Export Components
    // =========================================

    LiverWatch.Toast = Toast;
    LiverWatch.Modal = Modal;
    LiverWatch.Loader = Loader;
    LiverWatch.Dropdown = Dropdown;
    LiverWatch.Tabs = Tabs;
    LiverWatch.Accordion = Accordion;
    LiverWatch.Tooltip = Tooltip;
    LiverWatch.ProgressBar = ProgressBar;

})();
