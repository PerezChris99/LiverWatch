/**
 * LiverWatch - AI Assistant
 * ==========================
 * 
 * Chat interface for AI health assistant
 */

let sessionId = null;
let isWaiting = false;

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const welcomeMessage = document.getElementById('welcomeMessage');
const quickActions = document.getElementById('quickActions');

document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

function initializeChat() {
    // Auto-resize textarea
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            sendBtn.disabled = this.value.trim() === '' || isWaiting;
        });
        
        // Submit on Enter (Shift+Enter for new line)
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Send button
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Quick action buttons
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const question = this.dataset.question || this.textContent.replace(/^[^\s]+\s/, '').trim();
            if (question) {
                askQuestion(question);
            }
        });
    });
    
    // Welcome feature cards
    document.querySelectorAll('.welcome-feature').forEach(card => {
        card.addEventListener('click', function() {
            const question = this.dataset.question;
            if (question) {
                askQuestion(question);
            }
        });
    });
}

function askQuestion(question) {
    if (chatInput && !isWaiting) {
        chatInput.value = question;
        sendMessage();
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isWaiting) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // Hide welcome message and quick actions
    if (welcomeMessage) welcomeMessage.style.display = 'none';
    if (quickActions) quickActions.style.display = 'none';
    
    // Disable input while waiting
    isWaiting = true;
    sendBtn.disabled = true;
    chatInput.disabled = true;
    
    // Show loading indicator
    const loadingId = showLoading();
    
    try {
        const response = await fetch('/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        
        // Remove loading indicator
        removeLoading(loadingId);
        
        if (data.success) {
            // Update session ID if provided
            if (data.session_id) {
                sessionId = data.session_id;
            }
            
            // Add assistant response
            addMessage(data.response, 'assistant');
            
            // Show suggested questions if provided
            if (data.suggested_questions && data.suggested_questions.length > 0) {
                showSuggestedQuestions(data.suggested_questions);
            }
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeLoading(loadingId);
        addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'assistant');
    } finally {
        // Re-enable input
        isWaiting = false;
        sendBtn.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' 
        ? '<i class="fas fa-user"></i>' 
        : '<i class="fas fa-robot"></i>';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMessage(text);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom with animation
    setTimeout(() => {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

function formatMessage(text) {
    // Convert markdown-style formatting
    let formatted = text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    
    // Convert links
    formatted = formatted.replace(
        /\[(.+?)\]\((.+?)\)/g,
        '<a href="$2" target="_blank">$1</a>'
    );
    
    return formatted;
}

function showLoading() {
    const loadingId = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = loadingId;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = `
        <div class="loading-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return loadingId;
}

function removeLoading(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

function showSuggestedQuestions(questions) {
    // Remove existing suggestions
    const existingSuggestions = document.querySelector('.suggested-questions');
    if (existingSuggestions) {
        existingSuggestions.remove();
    }
    
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'suggested-questions';
    
    const title = document.createElement('p');
    title.textContent = 'You might also want to ask:';
    suggestionsDiv.appendChild(title);
    
    questions.forEach(question => {
        const btn = document.createElement('button');
        btn.className = 'suggested-question-btn';
        btn.textContent = question;
        btn.onclick = function() {
            chatInput.value = question;
            sendMessage();
        };
        suggestionsDiv.appendChild(btn);
    });
    
    chatMessages.appendChild(suggestionsDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearChat() {
    if (confirm('Clear all chat history?')) {
        chatMessages.innerHTML = '';
        sessionId = null;
        if (welcomeMessage) welcomeMessage.style.display = 'block';
        if (quickActions) quickActions.style.display = 'grid';
    }
}

// Export chat clearing function
window.clearChat = clearChat;
