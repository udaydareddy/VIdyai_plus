document.addEventListener('DOMContentLoaded', function() {
    // Check if the streak counter exists on the page
    const streakCounter = document.querySelector('.streak-counter');
    if (!streakCounter) return;
    
    // Get the current streak
    const streakDays = parseInt(streakCounter.querySelector('.streak-info p').textContent);
    
    // Animate the streak progress bar
    const progressBar = streakCounter.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = '0%';
        
        setTimeout(() => {
            const targetWidth = Math.min(streakDays * 10, 100) + '%';
            progressBar.style.width = targetWidth;
            progressBar.style.transition = 'width 1s ease-in-out';
        }, 300);
    }
    
    // If it's a new streak milestone, show celebration
    const milestones = [7, 30, 100, 365];
    if (milestones.includes(streakDays)) {
        showStreakCelebration(streakDays);
    }
});

function showStreakCelebration(days) {
    // Create celebration overlay
    const overlay = document.createElement('div');
    overlay.classList.add('celebration-overlay');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.zIndex = '1000';
    
    // Create celebration message
    const message = document.createElement('div');
    message.classList.add('celebration-message');
    message.style.backgroundColor = 'white';
    message.style.padding = '2rem';
    message.style.borderRadius = '10px';
    message.style.textAlign = 'center';
    message.style.maxWidth = '400px';
    
    let title = '';
    let description = '';
    
    if (days === 7) {
        title = 'Week Warrior!';
        description = 'Congratulations! You\'ve maintained a 7-day streak. Keep up the excellent work!';
    } else if (days === 30) {
        title = 'Month Master!';
        description = 'Amazing! A 30-day learning streak is a significant achievement. Your dedication is impressive!';
    } else if (days === 100) {
        title = 'Century Champion!';
        description = 'Incredible! 100 days of continuous learning. You\'re building life-changing habits!';
    } else if (days === 365) {
        title = 'Year-long Legend!';
        description = 'Outstanding! A full year of daily learning. You\'re truly a master of commitment!';
    }
    
    message.innerHTML = `
        <h2 style="color: #4a6bff; margin-bottom: 1rem;">${title}</h2>
        <p style="margin-bottom: 1.5rem;">${description}</p>
        <div style="font-size: 3rem; margin-bottom: 1.5rem;">🏆</div>
        <button class="close-celebration" style="padding: 0.5rem 1.5rem; background-color: #4a6bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Continue</button>
    `;
    
    overlay.appendChild(message);
    document.body.appendChild(overlay);
    
    // Close on button click
    document.querySelector('.close-celebration').addEventListener('click', function() {
        document.body.removeChild(overlay);
    });
}