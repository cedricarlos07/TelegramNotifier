/**
 * Système de filtrage dynamique pour la page Zoom Links
 * - Filtre automatiquement les cours lorsqu'un coach est sélectionné
 * - Sélectionne automatiquement un coach lorsqu'un cours est sélectionné
 */
document.addEventListener('DOMContentLoaded', function() {
    const coachSelect = document.getElementById('filter_teacher');
    const courseSelect = document.getElementById('filter_class');
    const daySelect = document.getElementById('filter_day');
    const statusSelect = document.getElementById('filter_status');
    const filterForm = document.getElementById('filterForm');
    
    if (!coachSelect || !courseSelect || !daySelect || !statusSelect || !filterForm) return;
    
    // Stocker les options originales
    const originalCourses = Array.from(courseSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text,
        coach: getRelatedCoach(opt.value)
    }));
    
    // Récupérer les coachs liés à chaque cours en analysant la structure HTML
    function getRelatedCoach(courseName) {
        if (!courseName) return '';
        
        // Parcourir toutes les lignes de table pour trouver le coach associé
        let relatedCoach = '';
        const tables = document.querySelectorAll('.table');
        
        tables.forEach(table => {
            const courseRows = table.querySelectorAll('tbody tr');
            
            courseRows.forEach(row => {
                // Rechercher les différentes structures possibles du tableau
                // Essayons d'abord les cellules classiques
                let courseNameCell = null;
                let coachNameCell = null;
                
                // Essayer les différentes colonnes possibles (selon le layout du tableau)
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    // Si la cellule contient le nom du cours
                    if (cell.textContent.trim() === courseName) {
                        courseNameCell = cell;
                        
                        // Chercher le nom du coach dans la même ligne
                        // Le coach pourrait être dans différentes positions selon le tableau
                        const cellIndexes = [2, 3, 4]; // Positions probables du coach
                        cellIndexes.forEach(idx => {
                            if (cells[idx] && !coachNameCell) {
                                const potential = cells[idx].textContent.trim();
                                // Vérifier si cette cellule ressemble à un coach (pas un ID, une date, etc.)
                                if (potential && !potential.match(/^\d+$/) && potential.length > 2) {
                                    coachNameCell = cells[idx];
                                }
                            }
                        });
                    }
                });
                
                // Si on trouve le cours, on extrait le coach
                if (courseNameCell && coachNameCell) {
                    relatedCoach = coachNameCell.textContent.trim();
                }
            });
        });
        
        // Si on n'a pas trouvé avec la méthode classique, essayons avec les attributs de données
        if (!relatedCoach) {
            // Certains boutons d'édition contiennent les informations dans des attributs de données
            const buttons = document.querySelectorAll('[data-course-name]');
            buttons.forEach(button => {
                const btnCourseName = button.getAttribute('data-course-name');
                if (btnCourseName === courseName) {
                    const teacherName = button.getAttribute('data-teacher-name');
                    if (teacherName) {
                        relatedCoach = teacherName;
                    }
                }
            });
        }
        
        return relatedCoach;
    }
    
    // Event Listener pour le changement de coach
    coachSelect.addEventListener('change', function() {
        const selectedCoach = this.value;
        
        if (!selectedCoach) {
            // Réinitialiser la liste des cours si aucun coach n'est sélectionné
            resetSelect(courseSelect, originalCourses);
            return;
        }
        
        // Filtrer les cours par coach
        filterCoursesByCoach(selectedCoach);
        
        // Sélectionner automatiquement le premier cours de ce coach
        if (!courseSelect.value && courseSelect.options.length > 1) {
            courseSelect.selectedIndex = 1; // Premier cours après l'option "Tous"
        }
    });
    
    // Event Listener pour le changement de cours
    courseSelect.addEventListener('change', function() {
        const selectedCourse = this.value;
        
        if (selectedCourse && !coachSelect.value) {
            // Si un cours est sélectionné et qu'aucun coach n'est sélectionné,
            // sélectionner automatiquement le coach associé
            const relatedCoach = originalCourses.find(c => c.value === selectedCourse)?.coach;
            if (relatedCoach) {
                coachSelect.value = relatedCoach;
                coachSelect.dispatchEvent(new Event('change'));
            }
        }
    });
    
    // Fonction pour réinitialiser un select
    function resetSelect(select, originalOptions) {
        select.innerHTML = '';
        
        originalOptions.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.text;
            select.appendChild(option);
        });
    }
    
    // Fonction pour filtrer les cours par coach
    function filterCoursesByCoach(coachName) {
        // Sauvegarder la valeur sélectionnée
        const selectedValue = courseSelect.value;
        
        // Vider le select
        courseSelect.innerHTML = '';
        
        // Ajouter l'option "Tous"
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Tous les cours';
        courseSelect.appendChild(defaultOption);
        
        // Filtrer les cours par coach
        const filteredCourses = originalCourses.filter(course => 
            !course.coach || course.coach === coachName || course.value === ''
        );
        
        // Ajouter les options filtrées
        filteredCourses.forEach(course => {
            if (course.value === '') return; // Sauter l'option vide
            
            const option = document.createElement('option');
            option.value = course.value;
            option.textContent = course.text;
            courseSelect.appendChild(option);
        });
        
        // Restaurer la valeur si possible
        if (Array.from(courseSelect.options).some(opt => opt.value === selectedValue)) {
            courseSelect.value = selectedValue;
        } else {
            courseSelect.value = '';
        }
    }
    
    // Handle form submission
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const teacher = coachSelect.value;
        const course = courseSelect.value;
        const day = daySelect.value;
        const status = statusSelect.value;
        
        // Construire l'URL avec les paramètres
        let url = window.location.pathname;
        const params = new URLSearchParams();
        
        if (teacher) params.append('teacher', teacher);
        if (course) params.append('course', course);
        if (day) params.append('day', day);
        if (status) params.append('status', status);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        window.location.href = url;
    });
    
    // Handle reset button
    filterForm.querySelector('button[type="reset"]').addEventListener('click', function() {
        // Réinitialiser tous les selects
        coachSelect.value = '';
        courseSelect.value = '';
        daySelect.value = '';
        statusSelect.value = '';
        
        // Réinitialiser les options du select cours
        resetSelect(courseSelect, originalCourses);
        
        // Rediriger vers l'URL de base
        window.location.href = window.location.pathname;
    });
    
    // Pré-remplir les filtres depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('teacher')) {
        coachSelect.value = urlParams.get('teacher');
        // Déclencher l'événement change pour mettre à jour les autres filtres
        coachSelect.dispatchEvent(new Event('change'));
    }
    if (urlParams.has('course')) {
        courseSelect.value = urlParams.get('course');
    }
    if (urlParams.has('day')) {
        daySelect.value = urlParams.get('day');
    }
    if (urlParams.has('status')) {
        statusSelect.value = urlParams.get('status');
    }
    
    // Handle filter toggle button text
    const filterToggleBtn = document.querySelector('[data-bs-toggle="collapse"][data-bs-target="#filterCollapse"]');
    const filterToggleText = document.querySelector('.filter-toggle-text');
    
    if (filterToggleBtn && filterToggleText) {
        filterToggleBtn.addEventListener('click', function() {
            const isCollapsed = this.getAttribute('aria-expanded') === 'true';
            filterToggleText.textContent = isCollapsed ? 'Afficher' : 'Masquer';
            
            // Change icon as well
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = isCollapsed ? 'fas fa-chevron-down me-1' : 'fas fa-chevron-up me-1';
            }
        });
    }
});