document.addEventListener('DOMContentLoaded', function() {
    const healthLogCards = document.querySelectorAll('.health-log-card canvas');

    healthLogCards.forEach(canvas => {
        const ctx = canvas.getContext('2d');
        const alcoholIntake = parseInt(canvas.dataset.alcoholIntake);
        const fattyFoods = parseInt(canvas.dataset.fattyFoods);
        const sugarIntake = parseInt(canvas.dataset.sugarIntake);
        const waterIntake = parseInt(canvas.dataset.waterIntake);
        const exerciseLevel = parseInt(canvas.dataset.exerciseLevel);
        const medicationUsage = parseInt(canvas.dataset.medicationUsage);

        const likelihood = (alcoholIntake > 1 ? 1 : 0) +
                           (fattyFoods > 1 ? 1 : 0) +
                           (sugarIntake > 1 ? 1 : 0) +
                           (waterIntake < 3 ? 1 : 0) +
                           (exerciseLevel < 30 ? 1 : 0) +
                           (medicationUsage > 1 ? 1 : 0);

        const healthChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Likely to have liver disease', 'Unlikely to have liver disease'],
                datasets: [{
                    data: [likelihood, 6 - likelihood],
                    backgroundColor: ['rgba(255, 99, 132, 0.2)', 'rgba(75, 192, 192, 0.2)'],
                    borderColor: ['rgba(255, 99, 132, 1)', 'rgba(75, 192, 192, 1)'],
                    borderWidth: 1
                }]
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
                        text: 'Liver Disease Likelihood'
                    }
                }
            }
        });
    });
});
