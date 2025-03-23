// Fonctions utilitaires communes

// Fonction pour afficher une notification
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Fonction pour gérer les erreurs AJAX
function handleAjaxError(error) {
    console.error('Error:', error);
    showNotification('Une erreur est survenue. Veuillez réessayer.', 'danger');
}

// Fonction pour formater une date
function formatDate(date) {
    return new Date(date).toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Fonction pour formater un nombre en pourcentage
function formatPercentage(number) {
    return `${Math.round(number)}%`;
}

// Fonction pour gérer les formulaires AJAX
function handleAjaxForm(form, successCallback = null) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Traitement en cours...';
        
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: form.method,
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message || 'Opération réussie');
                if (successCallback) {
                    successCallback(data);
                }
            } else {
                showNotification(data.message || 'Une erreur est survenue', 'danger');
            }
        })
        .catch(handleAjaxError)
        .finally(() => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        });
    });
}

// Fonction pour initialiser les tooltips Bootstrap
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Fonction pour initialiser les popovers Bootstrap
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les tooltips et popovers
    initTooltips();
    initPopovers();
    
    // Gérer les formulaires AJAX
    document.querySelectorAll('form[data-ajax="true"]').forEach(form => {
        handleAjaxForm(form);
    });
    
    // Gérer les confirmations de suppression
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
}); 