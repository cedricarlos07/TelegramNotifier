document.addEventListener('DOMContentLoaded', function() {
    // Navigation buttons for courses table
    const tableResponsive = document.querySelector('.table-responsive');
    if (tableResponsive) {
        document.querySelectorAll('.courses-nav-button').forEach(button => {
            button.addEventListener('click', function() {
                const direction = this.getAttribute('data-slide');
                const scrollAmount = 300; // Adjust this value to scroll more or less
                
                if (direction === 'prev') {
                    tableResponsive.scrollLeft -= scrollAmount;
                } else {
                    tableResponsive.scrollLeft += scrollAmount;
                }
            });
        });
    }
    
    // Export to Excel button
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', function() {
            const button = this;
            const originalHtml = button.innerHTML;
            
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Exportation...';
            
            fetch('/api/export-excel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Function to handle exports
function handleExport(format) {
    const button = document.getElementById('exportExcelBtn');
    const originalHtml = button.innerHTML;
    button.disabled = true;
    
    fetch('/api/export-stats', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `format=${format}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.innerHTML = '<i class="fas fa-check me-2"></i>Exporté !';
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.disabled = false;
            }, 2000);
            showToast(`Export ${format.toUpperCase()} réussi !`, 'success');
        } else {
            button.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Erreur';
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.disabled = false;
            }, 2000);
            showToast('Erreur: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Erreur';
        setTimeout(() => {
            button.innerHTML = originalHtml;
            button.disabled = false;
        }, 2000);
        showToast('Une erreur est survenue lors de l\'exportation.', 'danger');
    });
}
                    setTimeout(() => {
                        button.innerHTML = originalHtml;
                        button.disabled = false;
                    }, 2000);
                    
                    // Show success notification instead of alert
                    showToast('Export Excel réussi !', 'success');
                } else {
                    button.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Erreur';
                    setTimeout(() => {
                        button.innerHTML = originalHtml;
                        button.disabled = false;
                    }, 2000);
                    
                    showToast('Erreur: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                button.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Erreur';
                setTimeout(() => {
                    button.innerHTML = originalHtml;
                    button.disabled = false;
                }, 2000);
                
                showToast('Une erreur est survenue lors de l\'exportation.', 'danger');
            });
        });
    }
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        // Course distribution by day chart
        const courseCtx = document.getElementById('courseDistributionChart');
        if (courseCtx && window.courseDistributionData) {
            new Chart(courseCtx, {
                type: 'doughnut',
                data: {
                    labels: window.courseDistributionData.labels,
                    datasets: [{
                        data: window.courseDistributionData.values,
                        backgroundColor: [
                            'rgba(78, 115, 223, 0.8)',
                            'rgba(54, 185, 204, 0.8)',
                            'rgba(28, 200, 138, 0.8)',
                            'rgba(246, 194, 62, 0.8)',
                            'rgba(231, 74, 59, 0.8)',
                            'rgba(133, 135, 150, 0.8)',
                            'rgba(108, 117, 125, 0.8)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                usePointStyle: true,
                                padding: 15
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }
        
        // Activity trend chart
        const activityCtx = document.getElementById('activityTrendChart');
        if (activityCtx && window.activityTrendData) {
            new Chart(activityCtx, {
                type: 'line',
                data: {
                    labels: window.activityTrendData.labels,
                    datasets: [{
                        label: 'Messages',
                        data: window.activityTrendData.messages,
                        borderColor: 'rgba(78, 115, 223, 1)',
                        backgroundColor: 'rgba(78, 115, 223, 0.1)',
                        pointBackgroundColor: 'rgba(78, 115, 223, 1)',
                        fill: true,
                        tension: 0.4
                    }, {
                        label: 'Présences',
                        data: window.activityTrendData.attendances,
                        borderColor: 'rgba(28, 200, 138, 1)',
                        backgroundColor: 'rgba(28, 200, 138, 0.1)',
                        pointBackgroundColor: 'rgba(28, 200, 138, 1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 15
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                borderDash: [2],
                                drawBorder: false
                            }
                        }
                    }
                }
            });
        }
    }
    
    // Initialisation des tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Helper function to show toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.zIndex = '1050';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Auto remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function () {
        document.body.removeChild(toast);
    });
}
