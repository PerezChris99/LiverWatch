/**
 * LiverWatch - Notification Center
 * =================================
 * 
 * Handles notification management and settings
 */

let allNotifications = [];

document.addEventListener('DOMContentLoaded', function() {
    loadNotifications();
    initializeEventListeners();
    
    // Auto-refresh notifications every 5 minutes
    setInterval(refreshNotifications, 300000);
});

function initializeEventListeners() {
    // Header control buttons
    const markAllBtn = document.querySelector('.notification-controls .btn-secondary');
    const refreshBtn = document.querySelector('.notification-controls .btn-primary');
    
    if (markAllBtn) markAllBtn.addEventListener('click', markAllAsRead);
    if (refreshBtn) refreshBtn.addEventListener('click', refreshNotifications);
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filterType = this.textContent.toLowerCase().trim();
            const filterMap = {
                'all': 'all',
                'info': 'info',
                'warnings': 'warning',
                'alerts': 'error'
            };
            filterNotifications(filterMap[filterType] || 'all');
            
            // Update active state
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Event delegation for notification actions
    const notificationsList = document.getElementById('notificationsList');
    if (notificationsList) {
        notificationsList.addEventListener('click', function(e) {
            const markReadBtn = e.target.closest('.mark-read-btn');
            const dismissBtn = e.target.closest('.dismiss-btn');
            
            if (markReadBtn) {
                const notificationItem = markReadBtn.closest('.notification-item');
                const notificationId = notificationItem?.dataset.id;
                if (notificationId) markAsRead(notificationId);
            }
            
            if (dismissBtn) {
                const notificationItem = dismissBtn.closest('.notification-item');
                const notificationId = notificationItem?.dataset.id;
                if (notificationId) dismissNotification(notificationId);
            }
        });
    }
    
    // Settings save button
    const saveSettingsBtn = document.querySelector('.save-settings-btn');
    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', saveSettings);
}

function loadNotifications() {
    fetch('/notifications/api/notifications')
        .then(response => response.json())
        .then(data => {
            allNotifications = data.notifications || [];
            renderNotifications(allNotifications);
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
            showError('Failed to load notifications');
        });
}

function renderNotifications(notifications) {
    const container = document.getElementById('notificationsList');
    if (!container) return;
    
    // Keep the server-rendered notifications but add data-id attributes
    const items = container.querySelectorAll('.notification-item');
    items.forEach(item => {
        const id = item.dataset.id;
        if (id && notifications.find(n => n.id == id && n.read)) {
            item.classList.remove('unread');
            item.classList.add('read');
        }
    });
}

function createNotificationElement(notification) {
    const div = document.createElement('div');
    div.className = `notification-item ${notification.read ? 'read' : 'unread'}`;
    div.dataset.id = notification.id;
    
    const iconClass = getNotificationIcon(notification.type);
    const timeAgo = formatTimeAgo(notification.timestamp);
    
    div.innerHTML = `
        <div class="notification-icon ${notification.type}">
            <i class="${iconClass}"></i>
        </div>
        <div class="notification-content">
            <div class="notification-title">${notification.title}</div>
            <div class="notification-message">${notification.message}</div>
            <div class="notification-time">${timeAgo}</div>
        </div>
        <div class="notification-actions">
            ${!notification.read ? '<button class="mark-read-btn" onclick="markAsRead(' + notification.id + ')"><i class="fas fa-check"></i></button>' : ''}
            <button class="delete-btn" onclick="deleteNotification(' + notification.id + ')"><i class="fas fa-trash"></i></button>
        </div>
    `;
    
    return div;
}

function getNotificationIcon(type) {
    const icons = {
        'info': 'fas fa-info-circle',
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'error': 'fas fa-times-circle',
        'health': 'fas fa-heartbeat',
        'reminder': 'fas fa-bell',
        'achievement': 'fas fa-trophy'
    };
    return icons[type] || 'fas fa-bell';
}

function formatTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now - time) / 1000); // seconds
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + ' minutes ago';
    if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
    if (diff < 604800) return Math.floor(diff / 86400) + ' days ago';
    return time.toLocaleDateString();
}

function filterNotifications(type) {
    const items = document.querySelectorAll('.notification-item');
    
    items.forEach(item => {
        const itemType = item.dataset.type;
        if (type === 'all' || itemType === type) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

function markAsRead(notificationId) {
    fetch(`/notifications/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI  - remove unread class
            const item = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (item) {
                item.classList.remove('unread');
                item.classList.add('read');
                // Remove mark as read button
                const markReadBtn = item.querySelector('.mark-read-btn');
                if (markReadBtn) markReadBtn.remove();
            }
        }
    })
    .catch(error => {
        console.error('Error marking as read:', error);
        showError('Failed to mark notification as read');
    });
}

function dismissNotification(notificationId) {
    const element = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
    if (element) {
        element.style.animation = 'slideOut 0.3s ease-out forwards';
        
        setTimeout(() => {
            fetch(`/notifications/api/notifications/${notificationId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    element.remove();
                }
            })
            .catch(error => {
                console.error('Error deleting notification:', error);
                showError('Failed to delete notification');
            });
        }, 300);
    }
}

function markAllAsRead() {
    fetch('/notifications/api/notifications/mark-all-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update all notifications in UI
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
                item.classList.add('read');
                const markReadBtn = item.querySelector('.mark-read-btn');
                if (markReadBtn) markReadBtn.remove();
            });
            showSuccess('All notifications marked as read');
        }
    })
    .catch(error => {
        console.error('Error marking all as read:', error);
        showError('Failed to mark all as read');
    });
}

function deleteAll() {
    if (!confirm('Delete all notifications? This cannot be undone.')) return;
    
    fetch('/notifications/api/notifications/delete-all', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            allNotifications = [];
            renderNotifications(allNotifications);
        }
    })
    .catch(error => {
        console.error('Error deleting all:', error);
        showError('Failed to delete all notifications');
    });
}

function refreshNotifications() {
    loadNotifications();
}

function initializeSettingsSave() {
    const saveButton = document.querySelector('.notification-settings button[onclick="saveSettings()"]');
    if (saveButton) {
        saveButton.onclick = null; // Remove inline handler
        saveButton.addEventListener('click', saveSettings);
    }
}

function saveSettings() {
    const settings = {
        email: document.getElementById('emailNotifications')?.checked || false,
        push: document.getElementById('pushNotifications')?.checked || false,
        health_reminders: document.getElementById('healthReminders')?.checked || false,
        community_updates: document.getElementById('communityUpdates')?.checked || false,
        appointment_reminders: document.getElementById('appointmentReminders')?.checked || false,
        medication_reminders: document.getElementById('medicationReminders')?.checked || false
    };
    
    fetch('/notifications/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Settings saved successfully!');
        } else {
            showError('Failed to save settings');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showError('Failed to save settings');
    });
}

function showError(message) {
    showToast(message, 'error');
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#f44336' : type === 'success' ? '#4caf50' : '#2196f3'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize tab switching
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            filterNotifications(filter);
        });
    });
});
