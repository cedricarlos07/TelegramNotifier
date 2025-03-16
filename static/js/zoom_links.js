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

    // Store original options
    const originalCourses = Array.from(courseSelect.options);

    // Filter options based on coach
    function filterByCoach(coach) {
        // Get all course rows
        const courseRows = document.querySelectorAll('.table tbody tr');

        // Reset courses
        courseSelect.innerHTML = '<option value="">Tous les cours</option>';
        const seenCourses = new Set();

        // Populate filtered options
        courseRows.forEach(row => {
            const courseCell = row.querySelector('td:nth-child(2)');
            const coachCell = row.querySelector('td:nth-child(3)');

            if (courseCell && coachCell) {
                const courseName = courseCell.textContent.trim();
                const coachName = coachCell.textContent.trim();

                if (!coach || coachName === coach) {
                    // Add course if not already added
                    if (!seenCourses.has(courseName)) {
                        seenCourses.add(courseName);
                        const option = document.createElement('option');
                        option.value = courseName;
                        option.textContent = courseName;
                        courseSelect.appendChild(option);
                    }
                }
            }
        });
    }

    // Event listeners
    coachSelect.addEventListener('change', function() {
        filterByCoach(this.value);
    });

    courseSelect.addEventListener('change', function() {
        if (this.value && !coachSelect.value) {
            const courseRows = document.querySelectorAll('.table tbody tr');
            courseRows.forEach(row => {
                const courseCell = row.querySelector('td:nth-child(2)');
                if (courseCell && courseCell.textContent.trim() === this.value) {
                    const coachCell = row.querySelector('td:nth-child(3)');
                    if (coachCell) {
                        coachSelect.value = coachCell.textContent.trim();
                        filterByCoach(coachSelect.value);
                    }
                }
            });
        }
    });

    // Handle form submission
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const teacher = coachSelect.value;
        const course = courseSelect.value;
        const day = daySelect.value;
        const status = statusSelect.value;

        // Build URL with parameters
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
        courseSelect.innerHTML = '';
        originalCourses.forEach(opt => courseSelect.appendChild(opt.cloneNode(true)));

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