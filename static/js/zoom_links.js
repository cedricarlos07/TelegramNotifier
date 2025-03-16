document.addEventListener('DOMContentLoaded', function() {
    const coachSelect = document.getElementById('filter_teacher');
    const courseSelect = document.getElementById('filter_class');
    const daySelect = document.getElementById('filter_day');
    const statusSelect = document.getElementById('filter_status');
    const filterForm = document.getElementById('filterForm');

    if (!coachSelect || !courseSelect || !daySelect || !statusSelect || !filterForm) return;

    // Get all table rows for with/without zoom
    const courseRows = {
        with_zoom: document.querySelectorAll('.courses-with-zoom tbody tr'),
        without_zoom: document.querySelectorAll('.courses-without-zoom tbody tr')
    };

    function filterCourses() {
        const selectedTeacher = coachSelect.value;
        const selectedClass = courseSelect.value;
        const selectedDay = daySelect.value;
        const selectedStatus = statusSelect.value;

        // Function to check if a row matches filters
        function rowMatchesFilters(row) {
            const teacherCell = row.querySelector('td:nth-child(4)');
            const courseCell = row.querySelector('td:nth-child(3)');
            const dateCell = row.querySelector('td:nth-child(1)');

            const teacherMatch = !selectedTeacher || (teacherCell && teacherCell.textContent.trim() === selectedTeacher);
            const courseMatch = !selectedClass || (courseCell && courseCell.textContent.trim() === selectedClass);
            const dayMatch = !selectedDay || (dateCell && matchesDay(dateCell.textContent.trim(), selectedDay));

            return teacherMatch && courseMatch && dayMatch;
        }

        // Function to match day
        function matchesDay(dateText, dayIndex) {
            if (!dateText || dateText === 'Not scheduled') return true;
            const date = new Date(dateText.split('-').reverse().join('-'));
            return date.getDay().toString() === dayIndex;
        }

        // Hide/show rows based on filters
        Object.entries(courseRows).forEach(([type, rows]) => {
            const show = !selectedStatus || 
                        (selectedStatus === 'with_zoom' && type === 'with_zoom') ||
                        (selectedStatus === 'without_zoom' && type === 'without_zoom');

            rows.forEach(row => {
                const matches = show && rowMatchesFilters(row);
                row.style.display = matches ? '' : 'none';
            });
        });

        // Update dropdowns
        updateDropdowns();
    }

    function updateDropdowns() {
        const visibleRows = Array.from(document.querySelectorAll('tbody tr')).filter(row => 
            row.style.display !== 'none'
        );

        // Get unique values from visible rows
        const teachers = new Set();
        const courses = new Set();

        visibleRows.forEach(row => {
            const teacherCell = row.querySelector('td:nth-child(4)');
            const courseCell = row.querySelector('td:nth-child(3)');

            if (teacherCell) teachers.add(teacherCell.textContent.trim());
            if (courseCell) courses.add(courseCell.textContent.trim());
        });

        // Update dropdowns while preserving selected values
        updateDropdown(coachSelect, Array.from(teachers));
        updateDropdown(courseSelect, Array.from(courses));
    }

    function updateDropdown(select, values) {
        const currentValue = select.value;
        select.innerHTML = `<option value="">Tous</option>`;
        values.sort().forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            if (value === currentValue) option.selected = true;
            select.appendChild(option);
        });
    }

    // Add event listeners
    [coachSelect, courseSelect, daySelect, statusSelect].forEach(select => {
        select.addEventListener('change', filterCourses);
    });

    // Initial filtering
    filterCourses();
});rim();

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