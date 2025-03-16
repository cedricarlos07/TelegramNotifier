document.addEventListener('DOMContentLoaded', function() {
    const coachSelect = document.getElementById('filter_teacher');
    const courseSelect = document.getElementById('filter_class');
    const groupSelect = document.getElementById('filter_group');

    if (!coachSelect || !courseSelect || !groupSelect) return;

    // Store original options
    const originalCourses = Array.from(courseSelect.options);
    const originalGroups = Array.from(groupSelect.options);

    // Filter options based on coach
    function filterByCoach(coach) {
        // Get all course rows to find relationships
        const courseRows = document.querySelectorAll('.table tbody tr');

        // Filter courses
        courseSelect.innerHTML = '<option value="">Tous les cours</option>';
        originalCourses.forEach(option => {
            if (!option.value) return; // Skip empty option

            let include = !coach;
            courseRows.forEach(row => {
                const courseCell = row.querySelector('td:nth-child(2)');
                const coachCell = row.querySelector('td:nth-child(3)');
                if (courseCell && coachCell && 
                    courseCell.textContent.trim() === option.value &&
                    coachCell.textContent.trim() === coach) {
                    include = true;
                }
            });

            if (include) {
                courseSelect.appendChild(option.cloneNode(true));
            }
        });

        // Filter groups
        groupSelect.innerHTML = '<option value="">Tous les groupes</option>';
        originalGroups.forEach(option => {
            if (!option.value) return; // Skip empty option

            let include = !coach;
            courseRows.forEach(row => {
                const groupCell = row.querySelector('td:nth-child(4)');
                const coachCell = row.querySelector('td:nth-child(3)');
                if (groupCell && coachCell && 
                    groupCell.textContent.trim() === option.value &&
                    coachCell.textContent.trim() === coach) {
                    include = true;
                }
            });

            if (include) {
                groupSelect.appendChild(option.cloneNode(true));
            }
        });
    }

    // Event listeners
    coachSelect.addEventListener('change', function() {
        filterByCoach(this.value);
    });

    courseSelect.addEventListener('change', function() {
        if (this.value && !coachSelect.value) {
            // Find related coach
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

    groupSelect.addEventListener('change', function() {
        if (this.value && !coachSelect.value) {
            // Find related coach
            const courseRows = document.querySelectorAll('.table tbody tr');
            courseRows.forEach(row => {
                const groupCell = row.querySelector('td:nth-child(4)');
                if (groupCell && groupCell.textContent.trim() === this.value) {
                    const coachCell = row.querySelector('td:nth-child(3)');
                    if (coachCell) {
                        coachSelect.value = coachCell.textContent.trim();
                        filterByCoach(coachSelect.value);
                    }
                }
            });
        }
    });
});