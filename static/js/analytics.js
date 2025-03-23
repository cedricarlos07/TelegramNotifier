/**
 * JavaScript pour la page d'analyse des données de participation
 * - Ajoute des fonctionnalités d'interaction aux tableaux et graphiques
 * - Limite la hauteur des tableaux et ajoute des barres de défilement pour éviter l'allongement vertical
 */
document.addEventListener('DOMContentLoaded', function() {
    // Limiter la hauteur des tableaux et ajouter une barre de défilement
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(tableContainer => {
        // Uniquement si une hauteur maximale n'a pas déjà été définie
        if (!tableContainer.style.maxHeight) {
            tableContainer.style.maxHeight = '350px';
            tableContainer.style.overflowY = 'auto';
        }
        
        // Fixer l'en-tête du tableau pour qu'il reste visible pendant le défilement
        const thead = tableContainer.querySelector('thead');
        if (thead) {
            thead.classList.add('sticky-top', 'bg-light');
        }
    });
    
    // Ajouter des tooltips aux barres des graphiques pour plus d'informations
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(container => {
        // Ajouter une classe pour limiter la hauteur du graphique
        container.style.maxHeight = '400px';
    });
    
    // Précharger les filtres depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const filters = ['telegram_group', 'period', 'weekday'];
    
    filters.forEach(filter => {
        const element = document.getElementById(`${filter}-filter`);
        if (element && urlParams.has(filter)) {
            element.value = urlParams.get(filter);
        }
    });

    // Graphique de distribution des cours par jour
    const courseDaysCtx = document.getElementById('courseDaysChart');
    if (courseDaysCtx) {
        new Chart(courseDaysCtx, {
            type: 'bar',
            data: {
                labels: courseDaysLabels,
                datasets: [{
                    label: 'Nombre de cours',
                    data: courseDaysValues,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    // Graphique de distribution des étudiants par cours
    const courseStudentsCtx = document.getElementById('courseStudentsChart');
    if (courseStudentsCtx) {
        new Chart(courseStudentsCtx, {
            type: 'pie',
            data: {
                labels: courseStudentCounts.map(item => item.name),
                datasets: [{
                    data: courseStudentCounts.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(153, 102, 255, 0.5)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
});