/**
 * LiverWatch - Health Tracker Module
 * ===================================
 * 
 * Health data tracking, charts, and analytics.
 */

(function() {
    'use strict';

    const { $, $$, api, formatDate, formatNumber, Toast, Modal } = LiverWatch;

    // =========================================
    // Chart Configuration
    // =========================================

    const ChartConfig = {
        colors: {
            primary: '#0d7377',
            secondary: '#ff8c57',
            accent: '#4caf50',
            warning: '#ff9800',
            danger: '#f44336',
            grid: '#e0e0e0',
            text: '#666666'
        },

        defaultOptions: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: "'Inter', sans-serif",
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        family: "'Inter', sans-serif",
                        size: 14
                    },
                    bodyFont: {
                        family: "'Inter', sans-serif",
                        size: 13
                    },
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        color: '#f0f0f0'
                    },
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        }
                    }
                }
            }
        }
    };

    // =========================================
    // Health Metrics Manager
    // =========================================

    const HealthMetrics = {
        normalRanges: {
            alt: { min: 7, max: 55, unit: 'U/L' },
            ast: { min: 8, max: 48, unit: 'U/L' },
            bilirubin: { min: 0.1, max: 1.2, unit: 'mg/dL' },
            albumin: { min: 3.5, max: 5.5, unit: 'g/dL' },
            weight: { unit: 'kg' },
            bp_systolic: { min: 90, max: 120, unit: 'mmHg' },
            bp_diastolic: { min: 60, max: 80, unit: 'mmHg' }
        },

        getStatus(metric, value) {
            const range = this.normalRanges[metric];
            if (!range || !range.min || !range.max) return 'normal';

            if (value < range.min) return 'low';
            if (value > range.max) return 'high';
            return 'normal';
        },

        getStatusLabel(status) {
            const labels = {
                low: 'Below Normal',
                normal: 'Normal',
                high: 'Above Normal'
            };
            return labels[status] || 'Unknown';
        },

        getStatusClass(status) {
            return status === 'normal' ? 'success' : (status === 'low' ? 'warning' : 'danger');
        },

        formatValue(metric, value) {
            const range = this.normalRanges[metric];
            return `${formatNumber(value)} ${range?.unit || ''}`;
        },

        calculateTrend(values) {
            if (values.length < 2) return 'stable';
            
            const recent = values.slice(-5);
            const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
            const lastValue = values[values.length - 1];
            
            const percentChange = ((lastValue - avg) / avg) * 100;
            
            if (percentChange > 5) return 'up';
            if (percentChange < -5) return 'down';
            return 'stable';
        }
    };

    // =========================================
    // Health Charts
    // =========================================

    const HealthCharts = {
        instances: {},

        create(canvasId, type, data, options = {}) {
            const canvas = typeof canvasId === 'string' ? $(`#${canvasId}`) : canvasId;
            if (!canvas) {
                console.error('Canvas not found:', canvasId);
                return null;
            }

            // Destroy existing chart
            if (this.instances[canvasId]) {
                this.instances[canvasId].destroy();
            }

            const ctx = canvas.getContext('2d');
            const mergedOptions = this.mergeOptions(type, options);

            this.instances[canvasId] = new Chart(ctx, {
                type,
                data,
                options: mergedOptions
            });

            return this.instances[canvasId];
        },

        mergeOptions(type, custom = {}) {
            const base = JSON.parse(JSON.stringify(ChartConfig.defaultOptions));
            
            // Type-specific defaults
            if (type === 'line') {
                base.elements = {
                    line: {
                        tension: 0.4,
                        borderWidth: 2
                    },
                    point: {
                        radius: 4,
                        hoverRadius: 6
                    }
                };
            }

            return { ...base, ...custom };
        },

        update(chartId, data) {
            const chart = this.instances[chartId];
            if (!chart) return;

            chart.data = data;
            chart.update('active');
        },

        destroy(chartId) {
            if (this.instances[chartId]) {
                this.instances[chartId].destroy();
                delete this.instances[chartId];
            }
        },

        destroyAll() {
            Object.keys(this.instances).forEach(id => this.destroy(id));
        }
    };

    // =========================================
    // Health Dashboard
    // =========================================

    const HealthDashboard = {
        data: null,
        timeRange: '30d',

        async init() {
            // Load initial data
            await this.loadData();

            // Initialize charts
            this.initCharts();

            // Set up event listeners
            this.bindEvents();
        },

        bindEvents() {
            // Time range filters
            $$('.chart-filter').forEach(btn => {
                btn.addEventListener('click', async () => {
                    $$('.chart-filter').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this.timeRange = btn.dataset.range;
                    await this.loadData();
                    this.updateCharts();
                });
            });

            // Refresh button
            const refreshBtn = $('#refresh-data');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.loadData());
            }
        },

        async loadData() {
            try {
                const response = await api(`/health/logs?range=${this.timeRange}`);
                this.data = response.data;
                this.updateMetricCards();
            } catch (error) {
                Toast.error('Failed to load health data');
                console.error('Load data error:', error);
            }
        },

        updateMetricCards() {
            if (!this.data || !this.data.latest) return;

            const { latest, trends } = this.data;

            Object.entries(latest).forEach(([metric, value]) => {
                const card = $(`[data-metric="${metric}"]`);
                if (!card) return;

                const status = HealthMetrics.getStatus(metric, value);
                const statusClass = HealthMetrics.getStatusClass(status);
                const trend = trends?.[metric] || 'stable';

                // Update value
                const valueEl = $('.metric-value', card);
                if (valueEl) {
                    valueEl.textContent = value;
                }

                // Update status
                const statusEl = $('.metric-status', card);
                if (statusEl) {
                    statusEl.textContent = HealthMetrics.getStatusLabel(status);
                    statusEl.className = `metric-status ${statusClass}`;
                }

                // Update trend
                const trendEl = $('.metric-trend', card);
                if (trendEl) {
                    const trendIcons = {
                        up: 'fas fa-arrow-up',
                        down: 'fas fa-arrow-down',
                        stable: 'fas fa-minus'
                    };
                    trendEl.className = `metric-trend ${trend}`;
                    trendEl.innerHTML = `<i class="${trendIcons[trend]}"></i> ${trend}`;
                }

                // Update card border color
                card.className = card.className.replace(/\b(normal|warning|danger)\b/g, '');
                card.classList.add(statusClass === 'success' ? 'normal' : statusClass);
            });
        },

        initCharts() {
            // Main health trends chart
            const trendsCanvas = $('#health-trends-chart');
            if (trendsCanvas) {
                this.createTrendsChart(trendsCanvas);
            }

            // ALT/AST comparison
            const enzymeCanvas = $('#enzyme-chart');
            if (enzymeCanvas) {
                this.createEnzymeChart(enzymeCanvas);
            }
        },

        createTrendsChart(canvas) {
            if (!this.data?.history) return;

            const labels = this.data.history.map(h => formatDate(h.date, { month: 'short', day: 'numeric' }));

            HealthCharts.create(canvas.id, 'line', {
                labels,
                datasets: [
                    {
                        label: 'ALT',
                        data: this.data.history.map(h => h.alt),
                        borderColor: ChartConfig.colors.primary,
                        backgroundColor: `${ChartConfig.colors.primary}20`,
                        fill: true
                    },
                    {
                        label: 'AST',
                        data: this.data.history.map(h => h.ast),
                        borderColor: ChartConfig.colors.secondary,
                        backgroundColor: `${ChartConfig.colors.secondary}20`,
                        fill: true
                    }
                ]
            }, {
                plugins: {
                    title: {
                        display: true,
                        text: 'Liver Enzyme Trends'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'U/L'
                        }
                    }
                }
            });
        },

        createEnzymeChart(canvas) {
            if (!this.data?.latest) return;

            HealthCharts.create(canvas.id, 'bar', {
                labels: ['Your Values', 'Normal High', 'Normal Low'],
                datasets: [
                    {
                        label: 'ALT',
                        data: [
                            this.data.latest.alt || 0,
                            HealthMetrics.normalRanges.alt.max,
                            HealthMetrics.normalRanges.alt.min
                        ],
                        backgroundColor: [
                            ChartConfig.colors.primary,
                            `${ChartConfig.colors.accent}80`,
                            `${ChartConfig.colors.accent}40`
                        ]
                    },
                    {
                        label: 'AST',
                        data: [
                            this.data.latest.ast || 0,
                            HealthMetrics.normalRanges.ast.max,
                            HealthMetrics.normalRanges.ast.min
                        ],
                        backgroundColor: [
                            ChartConfig.colors.secondary,
                            `${ChartConfig.colors.accent}80`,
                            `${ChartConfig.colors.accent}40`
                        ]
                    }
                ]
            });
        },

        updateCharts() {
            this.initCharts();
        }
    };

    // =========================================
    // Health Log Form
    // =========================================

    const HealthLogForm = {
        form: null,

        init() {
            this.form = $('#health-log-form');
            if (!this.form) return;

            this.form.addEventListener('submit', (e) => this.handleSubmit(e));

            // Real-time validation
            $$('input[type="number"]', this.form).forEach(input => {
                input.addEventListener('input', () => this.validateField(input));
            });
        },

        validateField(input) {
            const metric = input.name;
            const value = parseFloat(input.value);
            const range = HealthMetrics.normalRanges[metric];

            if (!range || isNaN(value)) {
                input.classList.remove('is-valid', 'is-invalid', 'is-warning');
                return;
            }

            const status = HealthMetrics.getStatus(metric, value);
            
            input.classList.remove('is-valid', 'is-invalid', 'is-warning');
            if (status === 'normal') {
                input.classList.add('is-valid');
            } else {
                input.classList.add('is-warning');
            }

            // Show feedback
            const feedback = input.nextElementSibling;
            if (feedback?.classList.contains('form-feedback')) {
                feedback.textContent = status !== 'normal' 
                    ? `${HealthMetrics.getStatusLabel(status)} (Normal: ${range.min}-${range.max} ${range.unit})`
                    : 'Within normal range';
                feedback.className = `form-feedback text-${status === 'normal' ? 'success' : 'warning'}`;
            }
        },

        async handleSubmit(e) {
            e.preventDefault();

            const formData = new FormData(this.form);
            const data = Object.fromEntries(formData);

            // Convert values to numbers
            Object.keys(data).forEach(key => {
                if (data[key] && !isNaN(data[key])) {
                    data[key] = parseFloat(data[key]);
                }
            });

            try {
                await api('/health/log', {
                    method: 'POST',
                    body: data
                });

                Toast.success('Health data logged successfully!');
                this.form.reset();
                
                // Refresh dashboard if on same page
                if (typeof HealthDashboard !== 'undefined') {
                    await HealthDashboard.loadData();
                    HealthDashboard.updateCharts();
                }
            } catch (error) {
                Toast.error('Failed to save health data. Please try again.');
                console.error('Submit error:', error);
            }
        }
    };

    // =========================================
    // Health Score Calculator
    // =========================================

    const HealthScore = {
        calculate(metrics) {
            let score = 100;
            let factors = 0;

            Object.entries(metrics).forEach(([metric, value]) => {
                const range = HealthMetrics.normalRanges[metric];
                if (!range || !range.min || !range.max || value === null) return;

                factors++;
                const status = HealthMetrics.getStatus(metric, value);

                if (status !== 'normal') {
                    // Calculate how far from normal
                    const deviation = status === 'high' 
                        ? (value - range.max) / range.max
                        : (range.min - value) / range.min;
                    
                    // Deduct points based on deviation
                    score -= Math.min(25, deviation * 50);
                }
            });

            // If no factors, return null
            if (factors === 0) return null;

            return Math.max(0, Math.round(score));
        },

        getGrade(score) {
            if (score >= 90) return { grade: 'A', label: 'Excellent', class: 'excellent' };
            if (score >= 80) return { grade: 'B', label: 'Good', class: 'good' };
            if (score >= 70) return { grade: 'C', label: 'Fair', class: 'fair' };
            if (score >= 60) return { grade: 'D', label: 'Needs Attention', class: 'poor' };
            return { grade: 'F', label: 'Critical', class: 'critical' };
        },

        render(containerId, metrics) {
            const container = typeof containerId === 'string' ? $(`#${containerId}`) : containerId;
            if (!container) return;

            const score = this.calculate(metrics);
            if (score === null) {
                container.innerHTML = '<p class="text-muted">No health data available</p>';
                return;
            }

            const { grade, label, class: className } = this.getGrade(score);

            container.innerHTML = `
                <div class="health-score ${className}" style="--score: ${score}">
                    <span>${score}</span>
                </div>
                <div class="health-score-label mt-3">
                    <span class="badge badge-lg badge-${className}">${grade}</span>
                    <p class="text-muted mt-2">${label}</p>
                </div>
            `;
        }
    };

    // =========================================
    // Initialize
    // =========================================

    function init() {
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded, health charts disabled');
            return;
        }

        // Initialize dashboard if on health tracker page
        if ($('#health-dashboard')) {
            HealthDashboard.init();
        }

        // Initialize log form
        HealthLogForm.init();
    }

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // =========================================
    // Export
    // =========================================

    LiverWatch.HealthMetrics = HealthMetrics;
    LiverWatch.HealthCharts = HealthCharts;
    LiverWatch.HealthDashboard = HealthDashboard;
    LiverWatch.HealthLogForm = HealthLogForm;
    LiverWatch.HealthScore = HealthScore;

})();
