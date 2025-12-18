// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-icon');
    if (icon) {
        icon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    
    // Check which page we're on and initialize accordingly
    if (document.getElementById('projectsGrid')) {
        loadProjects();
    } else if (document.getElementById('chatMessages')) {
        initChat();
    }
});

// Explore Page Functions
let allProjects = [];

function loadProjects() {
    fetch('/api/ideas', {
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data); // Debug log
            if (data.success) {
                allProjects = data.ideas;
                console.log('Projects loaded:', allProjects); // Debug log
                displayProjects(allProjects);
            } else {
                console.error('Failed to load projects:', data.message);
                const grid = document.getElementById('projectsGrid');
                if (grid) {
                    grid.innerHTML = '<p style="text-align: center; color: #ff0000; padding: 40px;">Failed to load projects: ' + data.message + '</p>';
                }
            }
        })
        .catch(error => {
            console.error('Error loading projects:', error);
            const grid = document.getElementById('projectsGrid');
            if (grid) {
                grid.innerHTML = '<p style="text-align: center; color: #ff0000; padding: 40px;">Error loading projects. Please refresh the page.</p>';
            }
        });
}

function displayProjects(projects) {
    const grid = document.getElementById('projectsGrid');
    
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (projects.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">No projects found matching your filters.</p>';
        return;
    }
    
    projects.forEach(project => {
        const card = createProjectCard(project);
        grid.appendChild(card);
    });
}

function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'project-card';
    
    // Check if current user has liked this project
    const currentUserEmail = window.currentUserEmail || '';
    const likedBy = project.liked_by || [];
    const isLiked = likedBy.includes(currentUserEmail);
    
    // Parse tech stack
    const techStack = project.tech_stack ? project.tech_stack.split(',').map(t => t.trim()) : [];
    
    card.innerHTML = `
        <div class="project-header">
            <div class="project-icon-large">${project.icon || '💡'}</div>
            <div class="project-summary">
                <h3>${project.summary || 'Untitled Project'}</h3>
            </div>
        </div>
        
        <div class="project-section">
            <h4>Problem Statement</h4>
            <p>${project.problem || 'No problem statement provided.'}</p>
        </div>
        
        <div class="project-section">
            <h4>Proposed Solution</h4>
            <p>${project.solution || 'No solution provided.'}</p>
        </div>
        
        <div class="project-section">
            <h4>Recommended Tech Stack</h4>
            <div class="tech-stack">
                ${techStack.length > 0 ? techStack.map(tech => `<span class="tech-tag">${tech}</span>`).join('') : '<span class="tech-tag">Not specified</span>'}
            </div>
        </div>
        
        <div class="project-footer">
            <div class="project-meta">
                <span class="meta-badge field">${project.field || 'General'}</span>
                <span class="meta-badge ${(project.complexity || 'medium').toLowerCase()}">${project.complexity || 'Medium'}</span>
            </div>
            <div class="project-actions">
                <button class="like-btn ${isLiked ? 'liked' : ''}" onclick="toggleLike(${project.id}, this)">
                    <span>${isLiked ? '❤️' : '🤍'}</span>
                    <span class="like-count">${project.likes || 0}</span>
                </button>
                <button class="ai-btn" onclick="openChat(${project.id})">
                    🤖 AI Assistant
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function toggleLike(ideaId, button) {
    fetch('/api/like', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ idea_id: ideaId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button appearance
            const likeIcon = button.querySelector('span:first-child');
            const likeCount = button.querySelector('.like-count');
            
            if (data.liked) {
                button.classList.add('liked');
                likeIcon.textContent = '❤️';
            } else {
                button.classList.remove('liked');
                likeIcon.textContent = '🤍';
            }
            
            likeCount.textContent = data.likes;
            
            // Update the allProjects array
            const project = allProjects.find(p => p.id === ideaId);
            if (project) {
                project.likes = data.likes;
                const currentUserEmail = window.currentUserEmail || '';
                if (!project.liked_by) project.liked_by = [];
                if (data.liked) {
                    if (!project.liked_by.includes(currentUserEmail)) {
                        project.liked_by.push(currentUserEmail);
                    }
                } else {
                    project.liked_by = project.liked_by.filter(email => email !== currentUserEmail);
                }
            }
        } else {
            alert('Failed to toggle like: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error toggling like:', error);
        alert('An error occurred. Please try again.');
    });
}

function openChat(ideaId) {
    window.location.href = `/chat/${ideaId}`;
}

// Filtering and Sorting Functions
function applyFilters() {
    const fieldFilter = document.getElementById('fieldFilter');
    const complexityFilter = document.getElementById('complexityFilter');
    
    if (!fieldFilter || !complexityFilter) return;
    
    let filteredProjects = allProjects;
    
    // Apply field filter
    if (fieldFilter.value !== 'all') {
        filteredProjects = filteredProjects.filter(p => p.field === fieldFilter.value);
    }
    
    // Apply complexity filter
    if (complexityFilter.value !== 'all') {
        filteredProjects = filteredProjects.filter(p => p.complexity === complexityFilter.value);
    }
    
    displayProjects(filteredProjects);
}

// Chat Page Functions
function initChat() {
    // Load chat history
    loadChatHistory();
    
    // Send initial greeting from AI if not already sent
    if (typeof currentIdea !== 'undefined' && !sessionStorage.getItem(`chat_initialized_${currentIdea.id}`)) {
        setTimeout(() => {
            addMessage('assistant', 
                `Hello! I'm your AI assistant for the project: "${currentIdea.summary}"\n\n` +
                `I can help you understand:\n` +
                `• Folder structure and project organization\n` +
                `• System architecture and design patterns\n` +
                `• Module responsibilities\n` +
                `• Interview and viva questions\n\n` +
                `What would you like to know?`
            );
            sessionStorage.setItem(`chat_initialized_${currentIdea.id}`, 'true');
        }, 500);
    }
}

function loadChatHistory() {
    if (typeof currentIdea === 'undefined') return;
    
    fetch(`/api/chat/history/${currentIdea.id}`, {
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.history.length > 0) {
                // Clear existing messages
                const messagesContainer = document.getElementById('chatMessages');
                if (messagesContainer) {
                    messagesContainer.innerHTML = '';
                    
                    // Display history
                    data.history.forEach(msg => {
                        addMessage(msg.role, msg.message, false);
                    });
                    
                    // Mark as initialized
                    sessionStorage.setItem(`chat_initialized_${currentIdea.id}`, 'true');
                }
            }
        })
        .catch(error => console.error('Error loading chat history:', error));
}

function sendMessage(event) {
    event.preventDefault();
    
    const input = document.getElementById('messageInput');
    if (!input) return;
    
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to UI
    addMessage('user', message);
    
    // Clear input
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send message to backend
    fetch('/api/chat', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            idea_id: currentIdea.id,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        removeTypingIndicator();
        
        if (data.success) {
            // Add AI response to UI
            addMessage('assistant', data.response);
        } else {
            addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        }
    })
    .catch(error => {
        removeTypingIndicator();
        console.error('Error sending message:', error);
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    });
}

function addMessage(role, content, scroll = true) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format message content (preserve line breaks and code blocks)
    const formattedContent = content
        .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
        .replace(/\n/g, '<br>');
    
    contentDiv.innerHTML = formattedContent;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    
    if (scroll) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typingIndicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    
    contentDiv.appendChild(indicator);
    typingDiv.appendChild(avatar);
    typingDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}