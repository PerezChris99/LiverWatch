/**
 * LiverWatch - Question Detail
 * ============================
 * 
 * Handles voting functionality for questions and answers
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeVoting();
});

function initializeVoting() {
    // Event delegation for vote buttons
    document.addEventListener('click', function(e) {
        const voteBtn = e.target.closest('.vote-btn');
        if (voteBtn) {
            const type = voteBtn.dataset.type; // 'question' or 'answer'
            const id = voteBtn.dataset.id;
            const voteType = voteBtn.dataset.vote; // 'upvote' or 'downvote'
            
            if (type && id && voteType) {
                vote(type, id, voteType);
            }
        }
    });
}

async function vote(type, id, voteType) {
    try {
        const response = await fetch(`/forum/${type}/${id}/vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vote_type: voteType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update the UI with new vote counts
            const voteContainer = document.querySelector(`[data-${type}-id="${id}"]`);
            if (voteContainer) {
                const upvoteSpan = voteContainer.querySelector('.upvote-count');
                const downvoteSpan = voteContainer.querySelector('.downvote-count');
                
                if (upvoteSpan) upvoteSpan.textContent = data.upvotes || 0;
                if (downvoteSpan) downvoteSpan.textContent = data.downvotes || 0;
            }
            
            // Show success message
            showToast('Vote recorded successfully!', 'success');
        } else {
            showToast(data.message || 'Failed to record vote', 'error');
        }
    } catch (error) {
        console.error('Error voting:', error);
        showToast('Failed to record vote', 'error');
    }
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
