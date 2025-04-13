document.addEventListener('DOMContentLoaded', function() {
    // Check if skill blocks exist on the page
    const skillBlocks = document.querySelectorAll('.skill-block');
    if (skillBlocks.length === 0) return;
    
    // Add interaction for skill blocks
    skillBlocks.forEach(block => {
        block.addEventListener('mouseover', function() {
            const skillName = this.dataset.skill;
            const proficiency = parseInt(this.querySelector('.skill-level').textContent);
            
            // Show tooltip
            showTooltip(this, skillName, proficiency);
        });
        
        block.addEventListener('mouseout', function() {
            // Hide tooltip
            hideTooltip();
        });
    });
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.classList.add('skill-tooltip');
    tooltip.style.position = 'absolute';
    tooltip.style.backgroundColor = '#333';
    tooltip.style.color = 'white';
    tooltip.style.padding = '0.5rem 1rem';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '0.9rem';
    tooltip.style.zIndex = '100';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.opacity = '0';
    tooltip.style.transition = 'opacity 0.2s';
    document.body.appendChild(tooltip);
    
    function showTooltip(element, skillName, proficiency) {
        // Set tooltip content
        tooltip.innerHTML = `
            <div><strong>${skillName}</strong></div>
            <div>Proficiency: ${proficiency}%</div>
            <div class="tooltip-hint">Practice to improve!</div>
        `;
        
        // Position tooltip above the element
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
        
        // Show tooltip
        tooltip.style.opacity = '1';
    }
    
    function hideTooltip() {
        tooltip.style.opacity = '0';
    }
    
    // Add proficiency level indicators
    const categoryHeadings = document.querySelectorAll('.skill-category h4');
    categoryHeadings.forEach(heading => {
        const category = heading.textContent;
        const skillsInCategory = document.querySelectorAll(`.skill-category:has(h4:contains("${category}")) .skill-block`);
        
        let totalProficiency = 0;
        skillsInCategory.forEach(skill => {
            const proficiency = parseInt(skill.querySelector('.skill-level').textContent);
            totalProficiency += proficiency;
        });
        
        const averageProficiency = totalProficiency / skillsInCategory.length;
        const badge = document.createElement('span');
        badge.classList.add('category-badge');
        badge.style.marginLeft = '0.5rem';
        badge.style.fontSize = '0.8rem';
        badge.style.padding = '0.2rem 0.5rem';
        badge.style.borderRadius = '4px';
        badge.style.color = 'white';
        
        if (averageProficiency < 30) {
            badge.style.backgroundColor = '#dc3545';
            badge.textContent = 'Beginner';
        } else if (averageProficiency < 70) {
            badge.style.backgroundColor = '#fd7e14';
            badge.textContent = 'Intermediate';
        } else {
            badge.style.backgroundColor = '#28a745';
            badge.textContent = 'Advanced';
        }
        
        heading.appendChild(badge);
    });
});