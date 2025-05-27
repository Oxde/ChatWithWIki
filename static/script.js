/**
 * ChatWithWiki Frontend JavaScript
 * Handles user interactions, API calls, and chat functionality
 */

class ChatWithWiki {
    constructor() {
        this.sessionId = null;
        this.isLoading = false;
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // Sections
        this.urlSection = document.getElementById('urlSection');
        this.loadingSection = document.getElementById('loadingSection');
        this.chatSection = document.getElementById('chatSection');

        // URL input elements
        this.urlInput = document.getElementById('urlInput');
        this.loadBtn = document.getElementById('loadBtn');
        this.exampleLinks = document.querySelectorAll('.example-link');

        // Chat elements
        this.articleTitle = document.getElementById('articleTitle');
        this.articleStats = document.getElementById('articleStats');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.newArticleBtn = document.getElementById('newArticleBtn');
        this.suggestionBtns = document.querySelectorAll('.suggestion-btn');

        // Toast elements
        this.errorToast = document.getElementById('errorToast');
        this.successToast = document.getElementById('successToast');
    }

    bindEvents() {
        // URL input events
        this.loadBtn.addEventListener('click', () => this.loadArticle());
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.loadArticle();
        });
        this.urlInput.addEventListener('input', () => this.validateUrlInput());

        // Example links
        this.exampleLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                this.urlInput.value = e.target.dataset.url;
                this.validateUrlInput();
            });
        });

        // Chat events
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.chatInput.addEventListener('input', () => this.validateChatInput());

        // Suggestion buttons
        this.suggestionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.chatInput.value = e.target.textContent;
                this.validateChatInput();
                this.sendMessage();
            });
        });

        // New article button
        this.newArticleBtn.addEventListener('click', () => this.resetToUrlInput());

        // Toast close buttons
        document.querySelectorAll('.toast-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('.toast').classList.add('hidden');
            });
        });
    }

    validateUrlInput() {
        const url = this.urlInput.value.trim();
        const isValid = url && this.isValidWikipediaUrl(url);
        this.loadBtn.disabled = !isValid || this.isLoading;
    }

    validateChatInput() {
        const message = this.chatInput.value.trim();
        this.sendBtn.disabled = !message || this.isLoading;
    }

    isValidWikipediaUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.includes('wikipedia.org') && 
                   urlObj.pathname.startsWith('/wiki/');
        } catch {
            return false;
        }
    }

    async loadArticle() {
        const url = this.urlInput.value.trim();
        
        if (!url || !this.isValidWikipediaUrl(url)) {
            this.showError('Please enter a valid Wikipedia URL');
            return;
        }

        this.setLoading(true);
        this.showSection('loading');

        try {
            const response = await fetch('/api/load', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to load article');
            }

            this.sessionId = data.session_id;
            this.displayArticleInfo(data);
            this.showSection('chat');
            this.showSuccess(data.message);
            this.clearChatMessages();

        } catch (error) {
            console.error('Error loading article:', error);
            this.showError(error.message);
            this.showSection('url');
        } finally {
            this.setLoading(false);
        }
    }

    async sendMessage() {
        const question = this.chatInput.value.trim();
        
        if (!question || !this.sessionId) return;

        // Add user message to chat
        this.addMessage(question, 'user');
        this.chatInput.value = '';
        this.validateChatInput();

        // Show typing indicator
        const typingId = this.addTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    question: question
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to get response');
            }

            // Remove typing indicator and add bot response
            this.removeTypingIndicator(typingId);
            this.addMessage(data.answer, 'bot', data.sources);

        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage('Sorry, I encountered an error processing your question. Please try again.', 'bot');
            this.showError(error.message);
        }
    }

    displayArticleInfo(data) {
        this.articleTitle.textContent = data.article_title;
        
        const stats = data.stats;
        this.articleStats.innerHTML = `
            <span><i class="fas fa-file-text"></i> ${stats.character_count.toLocaleString()} characters</span>
            <span><i class="fas fa-align-left"></i> ${stats.word_count.toLocaleString()} words</span>
            <span><i class="fas fa-puzzle-piece"></i> ~${stats.estimated_chunks} chunks</span>
            <span><i class="fas fa-coins"></i> ~${stats.estimated_tokens.toLocaleString()} tokens</span>
        `;
    }

    addMessage(content, type, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const contentP = document.createElement('p');
        contentP.textContent = content;
        messageContent.appendChild(contentP);

        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = '<h4>Sources:</h4>';
            
            sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.textContent = source.content;
                sourcesDiv.appendChild(sourceItem);
            });
            
            messageContent.appendChild(sourcesDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addTypingIndicator() {
        const typingId = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message';
        typingDiv.id = typingId;

        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>Thinking...</p>
            </div>
        `;

        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
        return typingId;
    }

    removeTypingIndicator(typingId) {
        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
    }

    clearChatMessages() {
        this.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="message bot-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <p>Hi! I've loaded the Wikipedia article. Ask me anything about it!</p>
                    </div>
                </div>
            </div>
        `;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    showSection(section) {
        // Hide all sections
        this.urlSection.classList.add('hidden');
        this.loadingSection.classList.add('hidden');
        this.chatSection.classList.add('hidden');

        // Show requested section
        switch (section) {
            case 'url':
                this.urlSection.classList.remove('hidden');
                break;
            case 'loading':
                this.loadingSection.classList.remove('hidden');
                break;
            case 'chat':
                this.chatSection.classList.remove('hidden');
                this.chatInput.focus();
                break;
        }
    }

    resetToUrlInput() {
        this.sessionId = null;
        this.urlInput.value = '';
        this.validateUrlInput();
        this.showSection('url');
        this.urlInput.focus();
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.loadBtn.disabled = loading;
        this.validateUrlInput();
        this.validateChatInput();

        if (loading) {
            this.loadBtn.innerHTML = '<span class="btn-text">Loading...</span><i class="fas fa-spinner fa-spin btn-icon"></i>';
        } else {
            this.loadBtn.innerHTML = '<span class="btn-text">Load Article</span><i class="fas fa-arrow-right btn-icon"></i>';
        }
    }

    showToast(message, type = 'error') {
        const toast = type === 'error' ? this.errorToast : this.successToast;
        const messageElement = toast.querySelector('.toast-message');
        
        messageElement.textContent = message;
        toast.classList.remove('hidden');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 5000);
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatWithWiki();
});

// Handle page visibility changes to cleanup resources
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could cleanup resources here
        console.log('Page hidden');
    } else {
        // Page is visible again
        console.log('Page visible');
    }
});

// Handle beforeunload to warn about losing session
window.addEventListener('beforeunload', (e) => {
    // Only show warning if there's an active session
    if (window.chatApp && window.chatApp.sessionId) {
        e.preventDefault();
        e.returnValue = 'You have an active chat session. Are you sure you want to leave?';
        return e.returnValue;
    }
});

// Export for global access if needed
window.ChatWithWiki = ChatWithWiki; 