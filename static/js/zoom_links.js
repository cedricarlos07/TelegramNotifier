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

    // Gestion du formulaire d'ajout de lien Zoom
    const addZoomLinkForm = document.getElementById('addZoomLinkForm');
    if (addZoomLinkForm) {
        addZoomLinkForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(html => {
                // Recharger la page pour afficher le nouveau lien
                window.location.reload();
            })
            .catch(error => {
                console.error('Erreur:', error);
                alert('Une erreur est survenue lors de l\'ajout du lien Zoom.');
            });
        });
    }

    // Gestion de la suppression des liens Zoom
    const deleteButtons = document.querySelectorAll('.delete-zoom-link');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('Êtes-vous sûr de vouloir supprimer ce lien Zoom ?')) {
                const linkId = this.dataset.linkId;
                const deleteUrl = `/zoom-links/${linkId}/delete`;
                
                fetch(deleteUrl, {
                    method: 'POST'
                })
                .then(response => response.text())
                .then(html => {
                    // Recharger la page pour mettre à jour la liste
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    alert('Une erreur est survenue lors de la suppression du lien Zoom.');
                });
            }
        });
    });

    // Gestion de la copie des liens Zoom
    const copyButtons = document.querySelectorAll('.copy-zoom-link');
    copyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const linkUrl = this.dataset.linkUrl;
            navigator.clipboard.writeText(linkUrl)
                .then(() => {
                    // Afficher une notification de succès
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    alert('Une erreur est survenue lors de la copie du lien.');
                });
        });
    });
});