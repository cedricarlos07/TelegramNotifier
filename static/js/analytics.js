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
});