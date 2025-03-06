document.addEventListener('DOMContentLoaded', function() {
    var ctx = document.getElementById('healthChart').getContext('2d');
    var healthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: JSON.parse(document.getElementById('healthChart').dataset.labels),
            datasets: [{
                label: 'Alcohol Intake',
                data: JSON.parse(document.getElementById('healthChart').dataset.alcoholIntake),
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            },
            {
                label: 'Fatty Foods',
                data: JSON.parse(document.getElementById('healthChart').dataset.fattyFoods),
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            },
            {
                label: 'Sugar Intake',
                data: JSON.parse(document.getElementById('healthChart').dataset.sugarIntake),
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 1
            },
            {
                label: 'Water Intake',
                data: JSON.parse(document.getElementById('healthChart').dataset.waterIntake),
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            },
            {
                label: 'Exercise Level',
                data: JSON.parse(document.getElementById('healthChart').dataset.exerciseLevel),
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});
