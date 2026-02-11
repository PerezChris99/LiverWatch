/**
 * LiverWatch - Analytics Dashboard
 * =================================
 * 
 * Handles health analytics, charts, and insights
 */

let detailedChart = null;
let trendsChart = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeTrendsChart();
    initializeChartButtons();
    updateChart(30);
    loadRiskAssessment();
    loadCommunityStats();
    
    // Auto-refresh every 5 minutes
    setInterval(() => {
        loadTrendsData();
        loadRiskAssessment();
        loadCommunityStats();
    }, 300000);
});

function initializeChartButtons() {
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const days = parseInt(this.dataset.days || this.textContent.match(/\d+/)?.[0] || 30);
            updateChart(days, this);
        });
    });
}

function initializeTrendsChart() {
    const ctx = document.getElementById('healthTrendsChart');
    if (!ctx) return;
    
    const context = ctx.getContext('2d');
    
    // Simplified trends chart based on server data
    trendsChart = new Chart(context, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Health Score',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
    
    loadTrendsData();
}

function loadTrendsData() {
    fetch('/analytics/api/trends')
        .then(response => response.json())
        .then(data => {
            if (data.success && trendsChart) {
                trendsChart.data.labels = data.labels || [];
                trendsChart.data.datasets[0].data = data.values || [];
                trendsChart.update();
            }
        })
        .catch(error => {
            console.error('Error loading trends:', error);
        });
}

function updateChart(days, buttonElement) {
    // Update active button
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (buttonElement) {
        buttonElement.classList.add('active');
    } else {
        // Default to first button
        const defaultBtn = document.querySelector('.chart-btn');
        if (defaultBtn) defaultBtn.classList.add('active');
    }
    
    // Show loading state
    const chartContainer = document.getElementById('detailedChartContainer');
    if (chartContainer) {
        chartContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading data...</div>';
    }
    
    // Fetch detailed data
    fetch(`/analytics/api/detailed-chart?days=${days}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderDetailedChart(data);
            }
        })
        .catch(error => {
            console.error('Error loading chart:', error);
            if (chartContainer) {
                chartContainer.innerHTML = '<div class="error">Failed to load chart data</div>';
            }
        });
}

function renderDetailedChart(data) {
    const container = document.getElementById('detailedChartContainer');
    if (!container) return;
    
    container.innerHTML = '<canvas id="detailedChart"></canvas>';
    
    const ctx = document.getElementById('detailedChart').getContext('2d');
    
    // Destroy existing chart if present
    if (detailedChart) {
        detailedChart.destroy();
    }
    
    detailedChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: data.label || 'Health Metrics',
                data: data.values || [],
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function loadRiskAssessment() {
    fetch('/analytics/api/risk-assessment')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateRiskDisplay(data);
            }
        })
        .catch(error => {
            console.error('Error loading risk assessment:', error);
        });
}

function updateRiskDisplay(data) {
    const scoreElement = document.querySelector('.score-value');
    const levelElement = document.querySelector('.risk-level');
    
    if (scoreElement && data.score !== undefined) {
        scoreElement.textContent = data.score;
    }
    
    if (levelElement && data.level) {
        levelElement.textContent = data.level;
        levelElement.className = `risk-level ${data.level.toLowerCase()}`;
    }
}

function loadCommunityStats() {
    fetch('/analytics/api/community-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCommunityStats(data.stats);
            }
        })
        .catch(error => {
            console.error('Error loading community stats:', error);
        });
}

function updateCommunityStats(stats) {
    if (!stats) return;
    
    // Update stat items
    const statElements = document.querySelectorAll('.stat-item');
    if (statElements.length >= 3) {
        statElements[0].querySelector('.stat-value').textContent = stats.totalUsers || '0';
        statElements[1].querySelector('.stat-value').textContent = stats.activeToday || '0';
        statElements[2].querySelector('.stat-value').textContent = stats.postsToday || '0';
    }
}

function exportData() {
    // Show loading
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
    btn.disabled = true;
    
    fetch('/analytics/api/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.blob())
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health-data-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
        // Restore button
        btn.innerHTML = originalText;
        btn.disabled = false;
    })
    .catch(error => {
        console.error('Export error:', error);
        alert('Failed to export data. Please try again.');
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}

// Refresh data every 5 minutes
setInterval(() => {
    loadTrendsData();
    loadRiskAssessment();
    loadCommunityStats();
}, 300000);
