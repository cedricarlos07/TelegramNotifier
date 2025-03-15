document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le système de filtrage dynamique
    initDynamicFiltering();
});

/**
 * Système de filtrage dynamique pour la page des cours
 * - Filtre automatiquement les cours et groupes Telegram lorsqu'un coach est sélectionné
 * - Met à jour les options disponibles dans les dropdowns en fonction des relations entre données
 */
function initDynamicFiltering() {
    const coachSelect = document.getElementById('filter_teacher');
    const courseSelect = document.getElementById('filter_class');
    const groupSelect = document.getElementById('filter_group');
    
    if (!coachSelect || !courseSelect || !groupSelect) return;
    
    // Stocker les options originales
    const originalCourses = Array.from(courseSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text,
        coach: getRelatedCoach(opt.value)
    }));
    
    const originalGroups = Array.from(groupSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text,
        coach: getRelatedCoach(opt.value)
    }));
    
    // Fonction helper pour déterminer quel coach est associé à un cours ou groupe
    // Note: Dans un système réel, ces informations viendraient de l'API ou des données en cache
    function getRelatedCoach(itemValue) {
        // Cette fonction serait normalement implémentée avec des données réelles
        // Pour l'instant, nous allons simplement récupérer les relations depuis les attributs de données
        const courseRows = document.querySelectorAll('tbody tr');
        let relatedCoach = '';
        
        courseRows.forEach(row => {
            const courseName = row.querySelector('td:nth-child(2)').textContent.trim();
            const groupId = row.querySelector('td:nth-child(4) .badge').textContent.trim();
            const coachName = row.querySelector('td:nth-child(3) span:last-child').textContent.trim();
            
            if (itemValue === courseName || itemValue === groupId) {
                relatedCoach = coachName;
            }
        });
        
        return relatedCoach;
    }
    
    // Event Listener pour le changement de coach
    coachSelect.addEventListener('change', function() {
        const selectedCoach = this.value;
        
        // Réinitialiser les listes si aucun coach n'est sélectionné
        if (!selectedCoach) {
            resetSelect(courseSelect, originalCourses);
            resetSelect(groupSelect, originalGroups);
            return;
        }
        
        // Filtrer les cours par coach
        filterSelectByCoach(courseSelect, originalCourses, selectedCoach);
        
        // Filtrer les groupes par coach
        filterSelectByCoach(groupSelect, originalGroups, selectedCoach);
    });
    
    // Event Listener pour le changement de cours
    courseSelect.addEventListener('change', function() {
        const selectedCourse = this.value;
        
        // Si un cours est sélectionné et qu'aucun coach n'est sélectionné,
        // on sélectionne automatiquement le coach associé
        if (selectedCourse && !coachSelect.value) {
            const relatedCoach = originalCourses.find(c => c.value === selectedCourse)?.coach;
            if (relatedCoach) {
                coachSelect.value = relatedCoach;
                // Déclencher l'événement change pour mettre à jour les autres filtres
                coachSelect.dispatchEvent(new Event('change'));
            }
        }
    });
    
    // Event Listener pour le changement de groupe
    groupSelect.addEventListener('change', function() {
        const selectedGroup = this.value;
        
        // Si un groupe est sélectionné et qu'aucun coach n'est sélectionné,
        // on sélectionne automatiquement le coach associé
        if (selectedGroup && !coachSelect.value) {
            const relatedCoach = originalGroups.find(g => g.value === selectedGroup)?.coach;
            if (relatedCoach) {
                coachSelect.value = relatedCoach;
                // Déclencher l'événement change pour mettre à jour les autres filtres
                coachSelect.dispatchEvent(new Event('change'));
            }
        }
    });
    
    // Fonction pour réinitialiser un select avec les options originales
    function resetSelect(select, originalOptions) {
        // Vider le select
        select.innerHTML = '';
        
        // Recréer les options originales
        originalOptions.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.text;
            select.appendChild(option);
        });
    }
    
    // Fonction pour filtrer un select par coach
    function filterSelectByCoach(select, originalOptions, coachName) {
        // Sauvegarder la valeur sélectionnée
        const selectedValue = select.value;
        
        // Vider le select
        select.innerHTML = '';
        
        // Ajouter l'option "Tous"
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = select === courseSelect ? 'Tous les cours' : 'Tous les groupes';
        select.appendChild(defaultOption);
        
        // Filtrer et ajouter les options correspondant au coach
        const filteredOptions = originalOptions.filter(opt => 
            !opt.coach || opt.coach === coachName || opt.value === ''
        );
        
        filteredOptions.forEach(opt => {
            if (opt.value === '') return; // Sauter l'option vide, déjà ajoutée
            
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.text;
            select.appendChild(option);
        });
        
        // Essayer de restaurer la valeur sélectionnée si elle existe toujours
        if (Array.from(select.options).some(opt => opt.value === selectedValue)) {
            select.value = selectedValue;
        } else {
            select.value = ''; // Sinon, sélectionner l'option par défaut
        }
    }
}
