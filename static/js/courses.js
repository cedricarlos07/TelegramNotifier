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
    // En analysant les données présentes dans le tableau des cours
    function getRelatedCoach(itemValue) {
        if (!itemValue) return '';
        
        const courseRows = document.querySelectorAll('.table tbody tr');
        let relatedCoach = '';
        
        courseRows.forEach(row => {
            // Récupérer le nom du cours
            const courseCell = row.querySelector('td:nth-child(2)');
            if (!courseCell) return;
            const courseName = courseCell.textContent.trim();
            
            // Récupérer le nom du coach
            const coachCell = row.querySelector('td:nth-child(3)');
            if (!coachCell) return;
            // Le coach est dans le second span ou directement dans la cellule
            const coachSpan = coachCell.querySelector('span:last-child');
            const coachName = coachSpan ? coachSpan.textContent.trim() : coachCell.textContent.trim();
            
            // Récupérer l'ID du groupe Telegram
            const groupCell = row.querySelector('td:nth-child(4)');
            if (!groupCell) return;
            // L'ID du groupe est peut-être dans un badge ou directement dans la cellule
            const groupBadge = groupCell.querySelector('.badge');
            const groupId = groupBadge ? groupBadge.textContent.trim() : groupCell.textContent.trim();
            
            // Vérifier si l'élément correspond à un cours ou un groupe
            if (itemValue === courseName || itemValue === groupId) {
                relatedCoach = coachName;
            }
        });
        
        // Si on n'a pas trouvé, essayons avec les boutons d'édition qui ont des data-attributes
        if (!relatedCoach) {
            document.querySelectorAll('.edit-course-btn').forEach(button => {
                const courseId = button.getAttribute('data-course-id');
                const courseName = button.getAttribute('data-course-name');
                const teacherName = button.getAttribute('data-teacher-name');
                const telegramGroupId = button.getAttribute('data-telegram-group-id');
                
                if (itemValue === courseName || itemValue === telegramGroupId) {
                    relatedCoach = teacherName;
                }
            });
        }
        
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
        
        // Sélectionner automatiquement le premier cours de ce coach s'il n'y a pas déjà un cours sélectionné
        if (!courseSelect.value && courseSelect.options.length > 1) {
            courseSelect.selectedIndex = 1; // Premier cours après l'option "Tous"
            // Si on change aussi le groupe automatiquement, on peut déclencher l'événement change
            courseSelect.dispatchEvent(new Event('change'));
        }
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
