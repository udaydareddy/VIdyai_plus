// badges.js - Handles badge achievement display and notifications
document.addEventListener('DOMContentLoaded', function() {
    // Fetch user badges from the server
    function fetchUserBadges() {
        fetch('/api/user/badges')
            .then(response => response.json())
            .then(data => {
                displayBadges(data.badges);
                checkForNewBadges(data.badges);
            })
            .catch(error => console.error('Error fetching badges:', error));
    }

    // Display badges in the badge container
    function displayBadges(badges) {
        const badgeContainer = document.getElementById('badge-container');
        if (!badgeContainer) return;

        badgeContainer.innerHTML = '';
        
        if (badges.length === 0) {
            badgeContainer.innerHTML = '<p class="no-badges">Complete activities to earn your first badge!</p>';
            return;
        }

        badges.forEach(badge => {
            const badgeElement = document.createElement('div');
            badgeElement.className = 'badge-item';
            badgeElement.innerHTML = `
                <img src="/static/images/badges/${badge.icon}" alt="${badge.name}">
                <div class="badge-info">
                    <h4>${badge.name}</h4>
                    <p>${badge.description}</p>
                    <small>Earned on: ${new Date(badge.earned_date).toLocaleDateString()}</small>
                </div>
            `;
            
            // Add tooltip for badge details
            badgeElement.setAttribute('data-tooltip', badge.description);
            badgeContainer.appendChild(badgeElement);
        });
    }

    // Check if user has earned any new badges
    function checkForNewBadges(badges) {
        const newBadges = badges.filter(badge => badge.is_new);
        
        if (newBadges.length > 0) {
            showBadgeNotification(newBadges);
            
            // Mark badges as seen
            fetch('/api/user/badges/mark-seen', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    badge_ids: newBadges.map(badge => badge.id)
                })
            });
        }
    }

    // Display notification for new badges
    function showBadgeNotification(newBadges) {
        const notificationContainer = document.createElement('div');
        notificationContainer.className = 'badge-notification';
        
        const badgeInfo = newBadges[0]; // Show the first new badge
        notificationContainer.innerHTML = `
            <div class="badge-notification-content">
                <img src="/static/images/badges/${badgeInfo.icon}" alt="${badgeInfo.name}">
                <div>
                    <h4>New Badge Earned!</h4>
                    <p>${badgeInfo.name}</p>
                    <p>${badgeInfo.description}</p>
                </div>
                <button class="close-notification">×</button>
            </div>
        `;
        
        document.body.appendChild(notificationContainer);
        
        // Show notification with animation
        setTimeout(() => {
            notificationContainer.classList.add('show');
        }, 100);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notificationContainer.classList.remove('show');
            setTimeout(() => {
                notificationContainer.remove();
            }, 500);
        }, 5000);
        
        // Close button functionality
        notificationContainer.querySelector('.close-notification').addEventListener('click', () => {
            notificationContainer.classList.remove('show');
            setTimeout(() => {
                notificationContainer.remove();
            }, 500);
        });
    }

    // Handle badge sharing
    function setupBadgeSharing() {
        const shareButtons = document.querySelectorAll('.share-badge');
        shareButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const badgeId = this.getAttribute('data-badge-id');
                
                // Create shareable link
                const shareLink = `${window.location.origin}/badge/${badgeId}/share`;
                
                // Create temporary input to copy the link
                const tempInput = document.createElement('input');
                tempInput.value = shareLink;
                document.body.appendChild(tempInput);
                tempInput.select();
                document.execCommand('copy');
                document.body.removeChild(tempInput);
                
                // Show notification
                alert('Badge share link copied to clipboard!');
            });
        });
    }

    // Initialize badge functionality
    fetchUserBadges();
    setupBadgeSharing();
    
    // Refresh badges periodically (every 5 minutes)
    setInterval(fetchUserBadges, 300000);
});
