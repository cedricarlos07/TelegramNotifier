// Fonctions utilitaires communes

// Gestion des notifications
const notificationQueue = [];
let isProcessingNotification = false;

function showNotification(message, type = 'success', duration = 5000) {
    notificationQueue.push({ message, type, duration });
    if (!isProcessingNotification) {
        processNotificationQueue();
    }
}

function processNotificationQueue() {
    if (notificationQueue.length === 0) {
        isProcessingNotification = false;
        return;
    }

    isProcessingNotification = true;
    const { message, type, duration } = notificationQueue.shift();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.zIndex = 'var(--z-index-toast)';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, {
        animation: true,
        autohide: true,
        delay: duration
    });
    
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
        processNotificationQueue();
    });
}

// Fonction pour gérer les erreurs AJAX avec retry
function handleAjaxError(error, retryCallback = null, maxRetries = 3) {
    console.error('Error:', error);
    
    if (retryCallback && maxRetries > 0) {
        showNotification('Tentative de reconnexion...', 'warning', 3000);
        setTimeout(() => {
            retryCallback(maxRetries - 1);
        }, 3000);
    } else {
        showNotification('Une erreur est survenue. Veuillez réessayer.', 'danger');
    }
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

// Fonction pour gérer les formulaires AJAX avec sécurité améliorée
function handleAjaxForm(form, successCallback = null) {
    let isSubmitting = false;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton ? submitButton.innerHTML : '';
    
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (isSubmitting) return;
        
        const isValid = validateForm(form);
        if (!isValid) {
            showNotification('Veuillez corriger les erreurs dans le formulaire', 'warning');
            return;
        }
        
        isSubmitting = true;
        
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Traitement en cours...';
        }
        
        try {
            const formData = new FormData(form);
            formData.append('csrf_token', csrfToken);
            
            for (let [key, value] of formData.entries()) {
                if (typeof value === 'string') {
                    formData.set(key, sanitizeInput(value));
                }
            }
            
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-TOKEN': csrfToken
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Erreur serveur: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                showNotification(data.message || 'Opération réussie', 'success');
                if (successCallback) {
                    successCallback(data);
                }
                form.reset();
                resetValidation(form);
            } else {
                showNotification(data.message || 'Une erreur est survenue', 'danger');
                if (data.errors) {
                    displayFormErrors(form, data.errors);
                }
            }
        } catch (error) {
            console.error('Form submission error:', error);
            showNotification(error.message || 'Une erreur est survenue', 'danger');
        } finally {
            isSubmitting = false;
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        }
    });
    
    // Validation en temps réel
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            validateInput(input);
        }, 300));
        
        input.addEventListener('blur', function() {
            validateInput(input);
        });
    });
}

// Fonction de sanitization des entrées
function sanitizeInput(value) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        "/": '&#x2F;',
    };
    const reg = /[&<>"'/]/ig;
    return value.replace(reg, (match)=>(map[match]));
}

// Fonction de debounce pour la validation
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Fonction de validation complète du formulaire
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        if (!validateInput(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Fonction pour réinitialiser la validation
function resetValidation(form) {
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.classList.remove('is-invalid', 'is-valid');
        const feedback = input.nextElementSibling;
        if (feedback && (feedback.classList.contains('invalid-feedback') || feedback.classList.contains('valid-feedback'))) {
            feedback.remove();
        }
    });
}

// Fonction pour afficher les erreurs du serveur
function displayFormErrors(form, errors) {
    for (const [field, message] of Object.entries(errors)) {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = message;
            input.parentNode.insertBefore(errorDiv, input.nextSibling);
        }
    }
}

// Fonction de validation des champs
function validateInput(input) {
    const validityState = input.validity;
    const errorElement = input.nextElementSibling;
    
    if (!validityState.valid) {
        input.classList.add('is-invalid');
        
        if (!errorElement || !errorElement.classList.contains('invalid-feedback')) {
            const error = document.createElement('div');
            error.className = 'invalid-feedback';
            error.textContent = input.validationMessage;
            input.parentNode.insertBefore(error, input.nextSibling);
        }
    } else {
        input.classList.remove('is-invalid');
        if (errorElement && errorElement.classList.contains('invalid-feedback')) {
            errorElement.remove();
        }
    }
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

// Gestion du menu mobile
document.addEventListener('DOMContentLoaded', function() {
    // Toggle du menu mobile
    const navbarToggler = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');
    let backdrop;
    
    function createBackdrop() {
        backdrop = document.createElement('div');
        backdrop.className = 'sidebar-backdrop';
        document.body.appendChild(backdrop);
        
        backdrop.addEventListener('click', () => {
            closeSidebar();
        });
    }
    
    function openSidebar() {
        sidebar.classList.add('show');
        backdrop.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
    
    function closeSidebar() {
        sidebar.classList.remove('show');
        backdrop.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    if (navbarToggler && sidebar) {
        createBackdrop();
        
        navbarToggler.addEventListener('click', function() {
            if (sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
        
        // Fermer le menu lors du changement d'orientation du device
        window.addEventListener('orientationchange', closeSidebar);
        
        // Fermer le menu lors du redimensionnement de la fenêtre
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (window.innerWidth > 991.98) {
                    closeSidebar();
                }
            }, 250);
        });
    }

    // Animation des cartes statistiques
    const statsCards = document.querySelectorAll('.stats-card');
    statsCards.forEach(card => {
        card.classList.add('fade-in');
    });

    // Gestion des alertes avec animation de sortie
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Effet hover sur les lignes de tableau avec transition douce
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach(row => {
        row.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = 'var(--shadow-md)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'var(--shadow-sm)';
        });
    });

    // Animation des boutons avec retour visuel
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.style.transition = 'transform 0.15s ease, box-shadow 0.15s ease';
        
        button.addEventListener('mousedown', function() {
            if (!this.disabled) {
                this.style.transform = 'scale(0.98)';
            }
        });
        
        button.addEventListener('mouseup', function() {
            if (!this.disabled) {
                this.style.transform = 'scale(1)';
            }
        });
        
        button.addEventListener('mouseleave', function() {
            if (!this.disabled) {
                this.style.transform = 'scale(1)';
            }
        });
    });

    // Gestion améliorée des formulaires
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                // Sauvegarder le contenu original
                if (!submitButton.dataset.originalContent) {
                    submitButton.dataset.originalContent = submitButton.innerHTML;
                }
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Chargement...';
                
                // Réactiver le bouton en cas d'erreur
                setTimeout(() => {
                    if (submitButton.disabled) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = submitButton.dataset.originalContent;
                    }
                }, 10000); // Timeout après 10 secondes
            }
        });
    });

    // Gestion améliorée des modales
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            this.classList.add('fade-in');
        });
        
        modal.addEventListener('hide.bs.modal', function() {
            const forms = this.querySelectorAll('form');
            forms.forEach(form => {
                form.reset();
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton && submitButton.dataset.originalContent) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = submitButton.dataset.originalContent;
                }
            });
        });
    });

    // Gestion du lazy loading des images
    initLazyLoading();
    initProfileImageOptimization();
    initBackgroundImageOptimization();
});

// Gestion du lazy loading des images
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    loadImage(img);
                    observer.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        loadAllImages();
    }
}

function loadImage(img) {
    const src = img.getAttribute('data-src');
    if (!src) return;

    return new Promise((resolve, reject) => {
        img.onload = () => {
            img.removeAttribute('data-src');
            resolve(img);
        };
        img.onerror = () => {
            img.src = '/static/img/placeholder.png';
            reject(new Error(`Failed to load image: ${src}`));
        };
        img.src = src;
    });
}

function loadAllImages() {
    document.querySelectorAll('img[data-src]').forEach(img => {
        loadImage(img).catch(console.error);
    });
}

// Optimisation des images de profil
function initProfileImageOptimization() {
    const profileImages = document.querySelectorAll('.profile-image');
    profileImages.forEach(img => {
        // Ajouter un placeholder en attendant le chargement
        if (!img.complete) {
            const placeholder = document.createElement('div');
            placeholder.className = 'profile-image-placeholder';
            placeholder.style.width = img.width + 'px';
            placeholder.style.height = img.height + 'px';
            img.parentNode.insertBefore(placeholder, img);
            
            img.onload = () => {
                placeholder.remove();
                img.style.opacity = '1';
            };
        }
    });
}

// Optimisation des images de fond
function initBackgroundImageOptimization() {
    const elements = document.querySelectorAll('[data-background]');
    
    if ('IntersectionObserver' in window) {
        const backgroundObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    loadBackgroundImage(element);
                    observer.unobserve(element);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        elements.forEach(element => {
            backgroundObserver.observe(element);
        });
    } else {
        elements.forEach(loadBackgroundImage);
    }
}

function loadBackgroundImage(element) {
    const src = element.getAttribute('data-background');
    if (!src) return;

    const img = new Image();
    img.onload = () => {
        element.style.backgroundImage = `url(${src})`;
        element.classList.add('background-loaded');
        element.removeAttribute('data-background');
    };
    img.src = src;
} 