document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    const teacherFilter = document.getElementById('filter_teacher');
    const classFilter = document.getElementById('filter_class');
    const dayFilter = document.getElementById('filter_day');
    const statusFilter = document.getElementById('filter_status');

    if (!filterForm || !teacherFilter || !classFilter || !dayFilter || !statusFilter) return;

    function updateFilters() {
        const selectedTeacher = teacherFilter.value;

        // Get updated class list based on teacher selection
        fetch(`/api/filter-courses?teacher=${encodeURIComponent(selectedTeacher)}`)
            .then(response => response.json())
            .then(data => {
                // Update class filter options
                updateDropdown(classFilter, data.courses);
            })
            .catch(error => console.error('Error updating filters:', error));
    }

    function updateDropdown(select, values) {
        const defaultOption = select.querySelector('option[value=""]');
        select.innerHTML = '';
        if (defaultOption) {
            select.appendChild(defaultOption);
        }

        values.forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            select.appendChild(option);
        });
    }

    // Add event listeners
    teacherFilter.addEventListener('change', updateFilters);
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        window.location.href = '/zoom-links?' + new URLSearchParams(new FormData(filterForm)).toString();
    });
});