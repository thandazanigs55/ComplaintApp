// main.js - Script for DUT Student Grievance Management System

// Helper function to format dates 
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    if (isNaN(date)) return dateString;
    
    return date.toLocaleDateString('en-ZA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Helper to format status badges
function formatStatusBadge(status) {
    const statusMap = {
        'pending': { class: 'status-badge status-pending', text: 'Pending' },
        'in_progress': { class: 'status-badge status-in_progress', text: 'In Progress' },
        'assigned': { class: 'status-badge status-assigned', text: 'Assigned' },
        'under_review': { class: 'status-badge status-under_review', text: 'Under Review' },
        'resolved': { class: 'status-badge status-resolved', text: 'Resolved' },
        'closed': { class: 'status-badge status-closed', text: 'Closed' }
    };
    
    const statusInfo = statusMap[status] || { class: 'status-badge', text: status };
    return `<span class="${statusInfo.class}">${statusInfo.text}</span>`;
}

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const dismissButton = message.querySelector('.btn-close');
            if (dismissButton) {
                dismissButton.click();
            }
        }, 5000);
    });
    
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // File input customization
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const fileName = this.files[0]?.name || 'No file chosen';
            const label = this.nextElementSibling;
            if (label) {
                label.innerText = fileName;
            }
        });
    });
}); 