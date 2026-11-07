/**
 * Dynamic Dashboard Charts powered by Chart.js
 */

document.addEventListener('DOMContentLoaded', function () {
    const monthlyTrendsCanvas = document.getElementById('monthlyTrendsChart');
    const categoryCanvas = document.getElementById('stockCategoryChart');
    const expiryCanvas = document.getElementById('expiryOverviewChart');

    if (!monthlyTrendsCanvas || !categoryCanvas || !expiryCanvas) {
        return; // Not on dashboard page
    }

    fetch('/api/dashboard-charts')
        .then(response => response.json())
        .then(data => {
            // 1. Monthly Trends Chart (Incoming vs Dispatched)
            new Chart(monthlyTrendsCanvas.getContext('2d'), {
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
                            borderRadius: 4
                        },
                        {
                            label: 'Dispatched Goods (Qty)',
                            data: data.dispatched_monthly,
                            backgroundColor: 'rgba(99, 102, 241, 0.85)',
                            borderColor: '#4338ca',
                            borderWidth: 1,
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } }
                        },
                        tooltip: {
                            backgroundColor: '#0f172a',
                            titleFont: { size: 13, family: 'Inter' },
                            bodyFont: { size: 12, family: 'Inter' },
                            padding: 10
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { font: { family: 'Inter', size: 11 } }
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: '#f1f5f9' },
                            ticks: { font: { family: 'Inter', size: 11 } }
                        }
                    }
                }
            });

            // 2. Stock Distribution by Category (Doughnut)
            new Chart(categoryCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: data.category_labels,
                    datasets: [{
                        data: data.category_stock,
                        backgroundColor: [
                            '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b'
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { boxWidth: 12, padding: 12, font: { family: 'Inter', size: 11 } }
                        }
                    },
                    cutout: '65%'
                }
            });

            // 3. Expiry Status Overview (Doughnut)
            new Chart(expiryCanvas.getContext('2d'), {
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
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { boxWidth: 12, padding: 12, font: { family: 'Inter', size: 11 } }
                        }
                    },
                    cutout: '65%'
                }
            });
        })
        .catch(err => {
            console.error('Failed to load dashboard chart data:', err);
        });
});
