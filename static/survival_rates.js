document.addEventListener('DOMContentLoaded', function() {
    const globalCtx = document.getElementById('globalSurvivalChart').getContext('2d');
    const ugandanCtx = document.getElementById('ugandanSurvivalChart').getContext('2d');

    const globalSurvivalChart = new Chart(globalCtx, {
        type: 'line',
        data: {
            labels: ['2016', '2017', '2018', '2019', '2020', '2021', '2022'],
            datasets: [
                {
                    label: 'Global Survival Rate',
                    data: [85, 87, 88, 86, 89, 90, 91],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    fill: true,
                },
                {
                    label: 'Global Death Rate',
                    data: [15, 13, 12, 14, 11, 10, 9],
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    fill: true,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Global Survival vs. Death Rates in Liver Disease'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    const ugandanSurvivalChart = new Chart(ugandanCtx, {
        type: 'line',
        data: {
            labels: ['2016', '2017', '2018', '2019', '2020', '2021', '2022'],
            datasets: [
                {
                    label: 'Ugandan Survival Rate',
                    data: [80, 82, 83, 81, 84, 85, 86],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    fill: true,
                },
                {
                    label: 'Ugandan Death Rate',
                    data: [20, 18, 17, 19, 16, 15, 14],
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    fill: true,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Ugandan Survival vs. Death Rates in Liver Disease'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
});
