
document.addEventListener('DOMContentLoaded', function() {
    const coachSelect = document.getElementById('filter_teacher');
    const courseSelect = document.getElementById('filter_class');
    const groupSelect = document.getElementById('filter_group');
    const filterForm = document.getElementById('filterForm');

    if (!coachSelect || !courseSelect || !groupSelect || !filterForm) return;

    // Store original options
    const originalCourses = Array.from(courseSelect.options);
    const originalGroups = Array.from(groupSelect.options);

    // Filter options based on coach
    function filterByCoach(coach) {
        // Get all course rows
        const courseRows = document.querySelectorAll('.table tbody tr');

        // Reset courses
        courseSelect.innerHTML = '<option value="">Tous les cours</option>';
        const seenCourses = new Set();

        // Filter groups
        groupSelect.innerHTML = '<option value="">Tous les groupes</option>';
        const seenGroups = new Set();

        // Populate filtered options
        courseRows.forEach(row => {
            const courseCell = row.querySelector('td:nth-child(2)');
            const coachCell = row.querySelector('td:nth-child(3)');
            const groupCell = row.querySelector('td:nth-child(4)');

            if (courseCell && coachCell && groupCell) {
                const courseName = courseCell.textContent.trim();
                const coachName = coachCell.textContent.trim();
                const groupId = groupCell.textContent.trim();

                if (!coach || coachName === coach) {
                    // Add course if not already added
                    if (!seenCourses.has(courseName)) {
                        seenCourses.add(courseName);
                        const option = document.createElement('option');
                        option.value = courseName;
                        option.textContent = courseName;
                        courseSelect.appendChild(option);
                    }

                    // Add group if not already added
                    if (!seenGroups.has(groupId)) {
                        seenGroups.add(groupId);
                        const option = document.createElement('option');
                        option.value = groupId;
                        option.textContent = groupId;
                        groupSelect.appendChild(option);
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
        const group = groupSelect.value;
        
        // Build URL with parameters
        let url = window.location.pathname;
        const params = new URLSearchParams();
        
        if (teacher) params.append('teacher', teacher);
        if (course) params.append('course', course);
        if (group) params.append('group', group);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        window.location.href = url;
    });
});
