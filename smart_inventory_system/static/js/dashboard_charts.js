/**
 * Dynamic Dashboard Charts powered by Chart.js
 * Adaptive light & dark mode support
 */

document.addEventListener('DOMContentLoaded', function () {
    const monthlyTrendsCanvas = document.getElementById('monthlyTrendsChart');
    const categoryCanvas = document.getElementById('stockCategoryChart');
    const expiryCanvas = document.getElementById('expiryOverviewChart');

    if (!monthlyTrendsCanvas || !categoryCanvas || !expiryCanvas) {
        return; // Not on dashboard page
    }

    let monthlyChart = null;
    let categoryChart = null;
    let expiryChart = null;

    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        return {
            isDark: isDark,
            textColor: isDark ? '#94a3b8' : '#64748b',
            gridColor: isDark ? 'rgba(255, 255, 255, 0.06)' : '#f1f5f9',
            borderColor: isDark ? '#111827' : '#ffffff',
            tooltipBg: isDark ? '#1e293b' : '#0f172a'
        };
    }

    fetch('/api/dashboard-charts')
        .then(response => response.json())
        .then(data => {
            const colors = getThemeColors();

            // 1. Monthly Trends Chart (Incoming vs Dispatched)
            monthlyChart = new Chart(monthlyTrendsCanvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.monthly_labels,
                    datasets: [
                        {
                            label: 'Incoming Goods (Qty)',
                            data: data.incoming_monthly,
                            backgroundColor: 'rgba(37, 99, 235, 0.85)',
                            borderColor: '#1d4ed8',
                            borderWidth: 1,
                            borderRadius: 6
                        },
                        {
                            label: 'Dispatched Goods (Qty)',
                            data: data.dispatched_monthly,
                            backgroundColor: 'rgba(99, 102, 241, 0.85)',
                            borderColor: '#4338ca',
                            borderWidth: 1,
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                boxWidth: 12,
                                color: colors.textColor,
                                font: { family: 'Inter', size: 12, weight: 500 }
                            }
                        },
                        tooltip: {
                            backgroundColor: colors.tooltipBg,
                            titleFont: { size: 13, family: 'Inter' },
                            bodyFont: { size: 12, family: 'Inter' },
                            padding: 10,
                            cornerRadius: 8
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: colors.textColor,
                                font: { family: 'Inter', size: 11 }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: colors.gridColor },
                            ticks: {
                                color: colors.textColor,
                                font: { family: 'Inter', size: 11 }
                            }
                        }
                    }
                }
            });

            // 2. Stock Distribution by Category (Doughnut)
            categoryChart = new Chart(categoryCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: data.category_labels,
                    datasets: [{
                        data: data.category_stock,
                        backgroundColor: [
                            '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b'
                        ],
                        borderWidth: 2,
                        borderColor: colors.borderColor
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                padding: 12,
                                color: colors.textColor,
                                font: { family: 'Inter', size: 11 }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });

            // 3. Expiry Status Overview (Doughnut)
            expiryChart = new Chart(expiryCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: data.expiry_labels,
                    datasets: [{
                        data: data.expiry_counts,
                        backgroundColor: [
                            '#ef4444', // Expired - Red
                            '#f97316', // Expiring in 7d - Orange
                            '#facc15', // Expiring in 30d - Yellow
                            '#10b981'  // Safe - Green
                        ],
                        borderWidth: 2,
                        borderColor: colors.borderColor
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                padding: 12,
                                color: colors.textColor,
                                font: { family: 'Inter', size: 11 }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });
        })
        .catch(err => {
            console.error('Failed to load dashboard chart data:', err);
        });

    // React to theme changes dynamically
    window.addEventListener('smartlogix-theme-changed', function () {
        const c = getThemeColors();
        if (monthlyChart) {
            monthlyChart.options.plugins.legend.labels.color = c.textColor;
            monthlyChart.options.plugins.tooltip.backgroundColor = c.tooltipBg;
            monthlyChart.options.scales.x.ticks.color = c.textColor;
            monthlyChart.options.scales.y.ticks.color = c.textColor;
            monthlyChart.options.scales.y.grid.color = c.gridColor;
            monthlyChart.update();
        }
        if (categoryChart) {
            categoryChart.options.plugins.legend.labels.color = c.textColor;
            categoryChart.data.datasets[0].borderColor = c.borderColor;
            categoryChart.update();
        }
        if (expiryChart) {
            expiryChart.options.plugins.legend.labels.color = c.textColor;
            expiryChart.data.datasets[0].borderColor = c.borderColor;
            expiryChart.update();
        }
    });
});

