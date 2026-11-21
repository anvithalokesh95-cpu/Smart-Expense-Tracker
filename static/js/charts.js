/**
 * SMART EXPENSE TRACKER - CHARTS ENGINE
 * Powered by Chart.js with Pastel Color Palettes
 */

document.addEventListener('DOMContentLoaded', async () => {
    const trendCanvas = document.getElementById('chart-monthly-trends');
    const donutCanvas = document.getElementById('chart-category-donut');
    const barCanvas = document.getElementById('chart-income-vs-expense');

    // Only fetch if at least one chart canvas is present on the page
    if (!trendCanvas && !donutCanvas && !barCanvas) {
        return;
    }

    try {
        const response = await fetch('/api/chart-data');
        if (!response.ok) return;
        const data = await response.json();

        // 1. Monthly Trends Line Chart (Income vs Expense)
        if (trendCanvas) {
            new Chart(trendCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.trends.labels,
                    datasets: [
                        {
                            label: 'Expenses',
                            data: data.trends.expenses,
                            borderColor: '#F43F5E',
                            backgroundColor: 'rgba(244, 63, 94, 0.08)',
                            borderWidth: 2.5,
                            fill: true,
                            tension: 0.35,
                            pointBackgroundColor: '#F43F5E',
                            pointHoverRadius: 6
                        },
                        {
                            label: 'Income',
                            data: data.trends.incomes,
                            borderColor: '#10B981',
                            backgroundColor: 'rgba(16, 185, 129, 0.08)',
                            borderWidth: 2.5,
                            fill: true,
                            tension: 0.35,
                            pointBackgroundColor: '#10B981',
                            pointHoverRadius: 6
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
                                usePointStyle: true,
                                font: { family: 'Plus Jakarta Sans', size: 12, weight: '600' },
                                color: '#475569'
                            }
                        },
                        tooltip: {
                            backgroundColor: '#1E293B',
                            padding: 12,
                            cornerRadius: 8,
                            titleFont: { family: 'Plus Jakarta Sans', size: 13, weight: 'bold' },
                            bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
                            callbacks: {
                                label: function(context) {
                                    return ` ${context.dataset.label}: $${Number(context.parsed.y).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { font: { family: 'Plus Jakarta Sans', size: 11 }, color: '#94A3B8' }
                        },
                        y: {
                            grid: { color: '#F1F5F9' },
                            ticks: {
                                font: { family: 'Plus Jakarta Sans', size: 11 },
                                color: '#94A3B8',
                                callback: function(value) {
                                    return '$' + Number(value).toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }

        // 2. Category Spending Donut Chart
        if (donutCanvas) {
            const hasData = data.categories.values && data.categories.values.length > 0;
            const labels = hasData ? data.categories.labels : ['No Expenses Yet'];
            const values = hasData ? data.categories.values : [1];
            const colors = hasData ? data.categories.colors : ['#E2E8F0'];

            new Chart(donutCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 3,
                        borderColor: '#FFFFFF',
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                padding: 14,
                                font: { family: 'Plus Jakarta Sans', size: 11, weight: '500' },
                                color: '#475569'
                            }
                        },
                        tooltip: {
                            enabled: hasData,
                            backgroundColor: '#1E293B',
                            padding: 10,
                            cornerRadius: 8,
                            callbacks: {
                                label: function(context) {
                                    const val = Number(context.parsed).toLocaleString(undefined, {minimumFractionDigits: 2});
                                    return ` ${context.label}: $${val}`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // 3. Income vs Expense Bar Chart
        if (barCanvas) {
            new Chart(barCanvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.trends.labels,
                    datasets: [
                        {
                            label: 'Income',
                            data: data.trends.incomes,
                            backgroundColor: 'rgba(16, 185, 129, 0.75)',
                            hoverBackgroundColor: '#10B981',
                            borderRadius: 6
                        },
                        {
                            label: 'Expenses',
                            data: data.trends.expenses,
                            backgroundColor: 'rgba(244, 63, 94, 0.75)',
                            hoverBackgroundColor: '#F43F5E',
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
                                usePointStyle: true,
                                font: { family: 'Plus Jakarta Sans', size: 12, weight: '600' },
                                color: '#475569'
                            }
                        },
                        tooltip: {
                            backgroundColor: '#1E293B',
                            padding: 12,
                            cornerRadius: 8,
                            callbacks: {
                                label: function(context) {
                                    return ` ${context.dataset.label}: $${Number(context.parsed.y).toLocaleString(undefined, {minimumFractionDigits: 2})}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { font: { family: 'Plus Jakarta Sans', size: 11 }, color: '#94A3B8' }
                        },
                        y: {
                            grid: { color: '#F1F5F9' },
                            ticks: {
                                font: { family: 'Plus Jakarta Sans', size: 11 },
                                color: '#94A3B8',
                                callback: function(value) {
                                    return '$' + Number(value).toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }

    } catch (error) {
        console.error('Error initializing charts:', error);
    }
});
