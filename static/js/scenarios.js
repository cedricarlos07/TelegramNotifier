
// Function to validate simulation form
function validateSimulationForm() {
    const simulationEnabled = document.getElementById('simulation_mode').checked;
    const testGroupIdField = document.getElementById('test_group_id');
    
    if (simulationEnabled) {
        testGroupIdField.setAttribute('required', '');
    } else {
        testGroupIdField.removeAttribute('required');
    }
}

// Initialize validation when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize simulation form validation if form exists
    const simulationForm = document.getElementById('simulationForm');
    if (simulationForm) {
        validateSimulationForm();
    }
});

// Function to send test message via AJAX
function sendTestMessage(event) {
    event.preventDefault();
    
    const formData = new FormData(document.getElementById('testMessageForm'));
    const submitButton = event.submitter;
    const originalText = submitButton.innerHTML;
    
    // Disable the button and show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Envoi en cours...';
    
    fetch('/api/send-test-message', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = data.success ? 'alert alert-success' : 'alert alert-danger';
        alertDiv.innerHTML = `<i class="${data.success ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'} me-2"></i>${data.message}`;
        
        // Insert alert before the form
        const form = document.getElementById('testMessageForm');
        form.parentNode.insertBefore(alertDiv, form);
        
        // Reset form if successful
        if (data.success) {
            form.reset();
        }
        
        // Auto-dismiss alert after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    })
    .catch(error => {
        console.error('Error:', error);
        // Create error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        alertDiv.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>Une erreur s'est produite lors de l'envoi du message.`;
        
        // Insert alert before the form
        const form = document.getElementById('testMessageForm');
        form.parentNode.insertBefore(alertDiv, form);
    })
    .finally(() => {
        // Re-enable the button and restore text
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    });
}
