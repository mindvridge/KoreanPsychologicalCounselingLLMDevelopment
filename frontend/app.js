/**
 * Korean Mental Health Counseling Frontend Application
 * 마음챗 - AI 심리상담 서비스
 */

// ============================================================================
// Global State
// ============================================================================

const AppState = {
    currentScreen: 'home',
    userId: null,
    currentCounselor: null,
    currentSession: null,
    chatHistory: [],
    selectedConcerns: [],
    allPersonas: []
};

// ============================================================================
// API Client
// ============================================================================

class APIClient {
    constructor(baseURL, apiKey = null) {
        this.baseURL = baseURL;
        this.apiKey = apiKey;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // Persona Endpoints
    async getPersonaRecommendations(ageRange, concerns, userId = null, topK = 3) {
        return this.request('/personas/recommend', {
            method: 'POST',
            body: JSON.stringify({
                age_range: ageRange,
                concerns: concerns,
                user_id: userId,
                top_k: topK
            })
        });
    }

    async getAllPersonas() {
        return this.request('/personas/all', {
            method: 'GET'
        });
    }

    async getPersonaById(personaId) {
        return this.request(`/personas/${personaId}`, {
            method: 'GET'
        });
    }

    async searchPersonas(query, filters = {}) {
        return this.request('/personas/search', {
            method: 'POST',
            body: JSON.stringify({ query, filters })
        });
    }

    // Chat Endpoints
    async sendChatMessage(personaId, message, sessionId, userId = null) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                persona_id: personaId,
                message: message,
                session_id: sessionId,
                user_id: userId
            })
        });
    }

    // Feedback Endpoints
    async submitFeedback(personaId, feedbackData) {
        return this.request(`/personas/${personaId}/feedback`, {
            method: 'POST',
            body: JSON.stringify(feedbackData)
        });
    }

    async getPersonaPerformance(personaId) {
        return this.request(`/personas/${personaId}/performance`, {
            method: 'GET'
        });
    }

    async getAllPersonasAnalytics() {
        return this.request('/personas/analytics/all', {
            method: 'GET'
        });
    }

    // User Personalization Endpoints
    async getUserPreferences(userId) {
        return this.request(`/users/${userId}/preferences`, {
            method: 'GET'
        });
    }

    async getUserStats(userId) {
        return this.request(`/users/${userId}/stats`, {
            method: 'GET'
        });
    }
}

// Initialize API Client
const api = new APIClient(CONFIG.API_BASE_URL, CONFIG.API_KEY);

// ============================================================================
// UI Helper Functions
// ============================================================================

const UI = {
    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(`${screenId}-screen`).classList.add('active');
        AppState.currentScreen = screenId;
    },

    showLoading() {
        document.getElementById('loading-overlay').classList.add('active');
    },

    hideLoading() {
        document.getElementById('loading-overlay').classList.remove('active');
    },

    showToast(message, duration = CONFIG.TOAST_DURATION) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('active');

        setTimeout(() => {
            toast.classList.remove('active');
        }, duration);
    },

    getAvatar(personaId) {
        return CONFIG.AVATARS[personaId] || CONFIG.DEFAULT_AVATAR;
    },

    formatTime(date = new Date()) {
        return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    }
};

// ============================================================================
// Home Screen Logic
// ============================================================================

function initializeHomeScreen() {
    // Load user ID from storage
    const savedUserId = StorageHelper.get(CONFIG.STORAGE_KEYS.USER_ID);
    if (savedUserId) {
        document.getElementById('user-id-input').value = savedUserId;
        AppState.userId = savedUserId;
    }

    // Concern tags selection
    document.querySelectorAll('.concern-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            this.classList.toggle('selected');
            const concern = this.dataset.concern;

            if (this.classList.contains('selected')) {
                if (!AppState.selectedConcerns.includes(concern)) {
                    AppState.selectedConcerns.push(concern);
                }
            } else {
                AppState.selectedConcerns = AppState.selectedConcerns.filter(c => c !== concern);
            }
        });
    });

    // Find counselor button
    document.getElementById('find-counselor-btn').addEventListener('click', async function() {
        const ageRange = document.getElementById('age-range-select').value;
        const userIdInput = document.getElementById('user-id-input').value.trim();

        if (!ageRange && AppState.selectedConcerns.length === 0) {
            UI.showToast('연령대 또는 고민을 선택해주세요');
            return;
        }

        // Save user ID
        if (userIdInput) {
            AppState.userId = userIdInput;
            StorageHelper.set(CONFIG.STORAGE_KEYS.USER_ID, userIdInput);
        }

        UI.showLoading();

        try {
            const result = await api.getPersonaRecommendations(
                ageRange || null,
                AppState.selectedConcerns.length > 0 ? AppState.selectedConcerns : null,
                AppState.userId,
                CONFIG.DEFAULT_TOP_K
            );

            displayRecommendations(result.recommendations);
            document.getElementById('recommendations-section').style.display = 'block';

            // Scroll to recommendations
            document.getElementById('recommendations-section').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });

            UI.showToast('추천 상담사를 찾았습니다!');
        } catch (error) {
            console.error('Error getting recommendations:', error);
            UI.showToast('추천을 가져오는 중 오류가 발생했습니다');
        } finally {
            UI.hideLoading();
        }
    });

    // Load all counselors button
    document.getElementById('load-all-counselors-btn').addEventListener('click', async function() {
        UI.showLoading();

        try {
            const result = await api.getAllPersonas();
            AppState.allPersonas = result.personas;
            displayAllCounselors(result.personas);

            document.getElementById('all-counselors-container').style.display = 'grid';
            this.style.display = 'none';

            UI.showToast(`전체 ${result.total}명의 상담사를 불러왔습니다`);
        } catch (error) {
            console.error('Error loading all counselors:', error);
            UI.showToast('상담사 목록을 가져오는 중 오류가 발생했습니다');
        } finally {
            UI.hideLoading();
        }
    });
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    container.innerHTML = '';

    recommendations.forEach(rec => {
        const card = createCounselorCard(rec, true);
        container.appendChild(card);
    });
}

function displayAllCounselors(personas) {
    const container = document.getElementById('all-counselors-container');
    container.innerHTML = '';

    personas.forEach(persona => {
        const card = createCounselorCard(persona, false);
        container.appendChild(card);
    });
}

function createCounselorCard(data, isRecommendation = false) {
    const card = document.createElement('div');
    card.className = 'counselor-card';
    if (data.personalized) {
        card.classList.add('personalized');
    }

    const avatar = UI.getAvatar(data.id);
    const genderMap = { 'male': '남성', 'female': '여성' };
    const gender = genderMap[data.gender] || data.gender;

    card.innerHTML = `
        <div class="counselor-header">
            <div class="counselor-avatar">${avatar}</div>
            <div>
                <div class="counselor-name">${data.display_name || data.name}</div>
                <div class="counselor-title">${gender} · ${data.age_range}</div>
                ${data.personalized ? '<div class="personalized-badge">⭐ 회원님 선호</div>' : ''}
            </div>
        </div>
        <div class="counselor-details">
            <p><strong>성격:</strong> ${data.personality?.type || '상담 전문가'}</p>
            <p><strong>전문 분야:</strong> ${data.specialties?.join(', ') || '심리상담'}</p>
            ${isRecommendation && data.score ? `<div><span class="counselor-score">매칭도: ${data.score.toFixed(1)}</span></div>` : ''}
        </div>
        ${data.reason ? `<div class="counselor-reason">${data.reason}</div>` : ''}
    `;

    card.addEventListener('click', () => {
        selectCounselor(data);
    });

    return card;
}

function selectCounselor(counselor) {
    AppState.currentCounselor = counselor;
    StorageHelper.set(CONFIG.STORAGE_KEYS.SELECTED_COUNSELOR, counselor);

    // Generate session ID
    AppState.currentSession = {
        id: generateSessionId(),
        personaId: counselor.id,
        startTime: new Date().toISOString(),
        messageCount: 0
    };
    StorageHelper.set(CONFIG.STORAGE_KEYS.CURRENT_SESSION, AppState.currentSession);

    // Initialize chat
    initializeChatScreen(counselor);
    UI.showScreen('chat');
}

// ============================================================================
// Chat Screen Logic
// ============================================================================

function initializeChatScreen(counselor) {
    const avatar = UI.getAvatar(counselor.id);

    document.getElementById('chat-counselor-avatar').textContent = avatar;
    document.getElementById('chat-counselor-name').textContent = counselor.display_name || counselor.name;
    document.getElementById('chat-counselor-specialty').textContent =
        counselor.specialties?.slice(0, 3).join(', ') || '심리상담 전문가';

    // Clear chat history
    AppState.chatHistory = [];
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <p>${counselor.display_name || counselor.name} 상담사와의 대화가 시작됩니다.</p>
            <p>편안하게 이야기 나눠보세요. 🌸</p>
        </div>
    `;

    // Send initial greeting
    addBotMessage(`안녕하세요, ${counselor.display_name || counselor.name}입니다. 무엇을 도와드릴까요?`);

    // Setup event listeners
    setupChatEventListeners();
}

function setupChatEventListeners() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-message-btn');

    // Remove old listeners
    const newChatInput = chatInput.cloneNode(true);
    const newSendBtn = sendBtn.cloneNode(true);
    chatInput.parentNode.replaceChild(newChatInput, chatInput);
    sendBtn.parentNode.replaceChild(newSendBtn, sendBtn);

    // Send message
    const sendMessage = async () => {
        const message = newChatInput.value.trim();
        if (!message) return;

        // Clear input
        newChatInput.value = '';
        newChatInput.style.height = 'auto';

        // Add user message
        addUserMessage(message);

        // Update session
        AppState.currentSession.messageCount++;

        // Send to API
        UI.showLoading();
        try {
            const response = await api.sendChatMessage(
                AppState.currentCounselor.id,
                message,
                AppState.currentSession.id,
                AppState.userId
            );

            addBotMessage(response.response);

            // Handle safety checks
            if (response.safety_check?.risk_level === 'HIGH' || response.safety_check?.risk_level === 'CRITICAL') {
                addSystemMessage('⚠️ 위기 상황이 감지되었습니다. 전문가의 즉각적인 도움이 필요할 수 있습니다.');
                addSystemMessage('자살예방상담전화: ☎️ 1393 | 정신건강위기상담: ☎️ 1577-0199');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            addSystemMessage('메시지 전송 중 오류가 발생했습니다. 다시 시도해주세요.');
        } finally {
            UI.hideLoading();
        }
    };

    newSendBtn.addEventListener('click', sendMessage);

    newChatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    newChatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Back to home
    document.getElementById('back-to-home-btn').addEventListener('click', () => {
        if (confirm('상담을 종료하시겠습니까?')) {
            UI.showScreen('home');
        }
    });

    // End session with feedback
    document.getElementById('end-session-btn').addEventListener('click', () => {
        if (confirm('상담을 종료하고 피드백을 작성하시겠습니까?')) {
            initializeFeedbackScreen();
            UI.showScreen('feedback');
        }
    });
}

function addUserMessage(text) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">
            <div>${text}</div>
            <div class="message-time">${UI.formatTime()}</div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    AppState.chatHistory.push({ role: 'user', content: text, time: new Date().toISOString() });
}

function addBotMessage(text) {
    const messagesContainer = document.getElementById('chat-messages');
    const avatar = UI.getAvatar(AppState.currentCounselor?.id);
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div>${text}</div>
            <div class="message-time">${UI.formatTime()}</div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    AppState.chatHistory.push({ role: 'bot', content: text, time: new Date().toISOString() });
}

function addSystemMessage(text) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'welcome-message';
    messageDiv.innerHTML = `<p><strong>${text}</strong></p>`;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function scrollToBottom() {
    if (CONFIG.CHAT_AUTO_SCROLL) {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// ============================================================================
// Feedback Screen Logic
// ============================================================================

function initializeFeedbackScreen() {
    const counselor = AppState.currentCounselor;
    document.getElementById('feedback-counselor-name').textContent =
        counselor.display_name || counselor.name;

    // Reset form
    document.getElementById('rating-value').value = '0';
    document.querySelectorAll('.star').forEach(star => star.classList.remove('active'));
    document.getElementById('helpful-check').checked = true;
    document.getElementById('appropriate-check').checked = true;
    document.getElementById('recommend-check').checked = true;
    document.getElementById('feedback-text').value = '';

    // Setup rating stars
    setupRatingStars();

    // Setup form submission
    const form = document.getElementById('feedback-form');
    const newForm = form.cloneNode(true);
    form.parentNode.replaceChild(newForm, form);

    newForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitFeedback();
    });

    // Skip feedback
    const skipBtn = document.getElementById('skip-feedback-btn');
    const newSkipBtn = skipBtn.cloneNode(true);
    skipBtn.parentNode.replaceChild(newSkipBtn, skipBtn);

    newSkipBtn.addEventListener('click', () => {
        UI.showScreen('home');
        UI.showToast('피드백을 건너뛰었습니다');
    });
}

function setupRatingStars() {
    const stars = document.querySelectorAll('.star');
    const ratingValue = document.getElementById('rating-value');

    stars.forEach(star => {
        star.addEventListener('click', function() {
            const rating = parseInt(this.dataset.rating);
            ratingValue.value = rating;

            stars.forEach(s => {
                const sRating = parseInt(s.dataset.rating);
                if (sRating <= rating) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });
        });

        star.addEventListener('mouseenter', function() {
            const rating = parseInt(this.dataset.rating);
            stars.forEach(s => {
                const sRating = parseInt(s.dataset.rating);
                s.style.opacity = sRating <= rating ? '1' : '0.3';
            });
        });
    });

    document.querySelector('.rating-stars').addEventListener('mouseleave', function() {
        const currentRating = parseInt(ratingValue.value);
        stars.forEach(s => {
            const sRating = parseInt(s.dataset.rating);
            if (currentRating > 0) {
                s.style.opacity = sRating <= currentRating ? '1' : '0.3';
            } else {
                s.style.opacity = '0.3';
            }
        });
    });
}

async function submitFeedback() {
    const rating = parseInt(document.getElementById('rating-value').value);

    if (rating === 0) {
        UI.showToast('만족도를 선택해주세요');
        return;
    }

    const feedbackData = {
        user_id: AppState.userId || 'anonymous',
        session_id: AppState.currentSession.id,
        rating: rating,
        helpful: document.getElementById('helpful-check').checked,
        appropriate: document.getElementById('appropriate-check').checked,
        would_recommend_again: document.getElementById('recommend-check').checked,
        concerns_addressed: AppState.selectedConcerns,
        feedback_text: document.getElementById('feedback-text').value.trim() || null,
        user_age_range: document.getElementById('age-range-select').value || null
    };

    UI.showLoading();

    try {
        await api.submitFeedback(AppState.currentCounselor.id, feedbackData);
        UI.showToast('피드백이 제출되었습니다. 감사합니다! 🙏');

        // Clear session
        StorageHelper.remove(CONFIG.STORAGE_KEYS.CURRENT_SESSION);

        setTimeout(() => {
            UI.showScreen('home');
        }, 1500);
    } catch (error) {
        console.error('Error submitting feedback:', error);
        UI.showToast('피드백 제출 중 오류가 발생했습니다');
    } finally {
        UI.hideLoading();
    }
}

// ============================================================================
// Dashboard Screen Logic
// ============================================================================

async function loadDashboard() {
    if (!AppState.userId) {
        UI.showToast('사용자 ID를 입력해주세요');
        return;
    }

    UI.showLoading();
    UI.showScreen('dashboard');

    try {
        const [stats, preferences] = await Promise.all([
            api.getUserStats(AppState.userId),
            api.getUserPreferences(AppState.userId)
        ]);

        displayUserStats(stats);
        displayUserPreferences(preferences);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        UI.showToast('대시보드 로드 중 오류가 발생했습니다');
        UI.showScreen('home');
    } finally {
        UI.hideLoading();
    }

    // Back to home button
    const backBtn = document.getElementById('back-to-home-from-dashboard-btn');
    const newBackBtn = backBtn.cloneNode(true);
    backBtn.parentNode.replaceChild(newBackBtn, backBtn);
    newBackBtn.addEventListener('click', () => {
        UI.showScreen('home');
    });
}

function displayUserStats(stats) {
    document.getElementById('total-sessions').textContent = `${stats.total_sessions || 0}회`;
    document.getElementById('total-feedback').textContent = `${stats.total_feedback || 0}회`;
    document.getElementById('favorite-counselor').textContent =
        stats.favorite_persona?.display_name || '없음';
}

function displayUserPreferences(preferences) {
    const container = document.getElementById('user-preferences-container');
    container.innerHTML = '';

    if (!preferences || preferences.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">아직 선호도 데이터가 없습니다. 더 많은 상담을 이용해주세요.</p>';
        return;
    }

    preferences.forEach(pref => {
        const item = document.createElement('div');
        item.className = 'preference-item';

        const normalizedScore = ((pref.preference_score + 1) / 2) * 100; // -1~1 → 0~100
        const scoreColor = pref.preference_score > 0 ? 'var(--secondary-color)' : 'var(--danger-color)';

        item.innerHTML = `
            <div style="flex: 1;">
                <div class="preference-name">${pref.persona_name}</div>
                <div class="preference-score">
                    선호도: ${pref.preference_score.toFixed(2)} |
                    평균 평점: ${pref.average_rating.toFixed(1)} |
                    피드백: ${pref.feedback_count}회
                </div>
                <div class="preference-bar">
                    <div class="preference-bar-fill"
                         style="width: ${normalizedScore}%; background: ${scoreColor};">
                    </div>
                </div>
            </div>
        `;
        container.appendChild(item);
    });
}

// ============================================================================
// Utility Functions
// ============================================================================

function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================================================
// Legal Consent System
// ============================================================================

function checkConsent() {
    const consentData = StorageHelper.get(CONFIG.STORAGE_KEYS.CONSENT_DATA);
    return consentData && consentData.agreedAt;
}

function showConsentModal() {
    const modal = document.getElementById('consent-modal');
    modal.classList.add('active');

    // Setup checkboxes
    const requiredCheckboxes = [
        document.getElementById('consent-terms'),
        document.getElementById('consent-privacy'),
        document.getElementById('consent-sensitive'),
        document.getElementById('consent-age')
    ];

    const allCheckbox = document.getElementById('consent-all');
    const agreeBtn = document.getElementById('consent-agree-btn');

    // Check if all required are checked
    const updateAgreeButton = () => {
        const allRequired = requiredCheckboxes.every(cb => cb.checked);
        agreeBtn.disabled = !allRequired;
    };

    // Individual checkbox change
    requiredCheckboxes.forEach(cb => {
        cb.addEventListener('change', updateAgreeButton);
    });

    // All agree checkbox
    allCheckbox.addEventListener('change', function() {
        const checked = this.checked;
        document.querySelectorAll('.consent-checkbox').forEach(cb => {
            cb.checked = checked;
        });
        updateAgreeButton();
    });

    // View legal documents
    document.querySelectorAll('.consent-view-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.dataset.target;
            showLegalDocument(target);
        });
    });

    // Disagree button
    document.getElementById('consent-disagree-btn').addEventListener('click', () => {
        alert('서비스 이용약관에 동의하지 않으면 서비스를 이용할 수 없습니다.');
        // Optionally redirect or close
    });

    // Agree button
    agreeBtn.addEventListener('click', () => {
        const consentData = {
            agreedAt: new Date().toISOString(),
            terms: document.getElementById('consent-terms').checked,
            privacy: document.getElementById('consent-privacy').checked,
            sensitive: document.getElementById('consent-sensitive').checked,
            improvement: document.getElementById('consent-improvement').checked,
            age: document.getElementById('consent-age').checked
        };

        StorageHelper.set(CONFIG.STORAGE_KEYS.CONSENT_DATA, consentData);
        modal.classList.remove('active');
        UI.showToast('동의해주셔서 감사합니다. 서비스를 시작합니다.');
    });
}

function showLegalDocument(docType) {
    const viewerModal = document.getElementById('legal-viewer-modal');
    const titleEl = document.getElementById('legal-viewer-title');
    const bodyEl = document.getElementById('legal-viewer-body');

    const doc = LEGAL_DOCS[docType];
    if (doc) {
        titleEl.textContent = doc.title;
        // Simple markdown rendering (newlines and basic formatting)
        bodyEl.innerHTML = doc.content
            .replace(/\n/g, '<br>')
            .replace(/### (.*?)(<br>)/g, '<h3>$1</h3>')
            .replace(/## (.*?)(<br>)/g, '<h2>$1</h2>')
            .replace(/# (.*?)(<br>)/g, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        viewerModal.classList.add('active');
    }

    // Close buttons
    document.getElementById('legal-viewer-close').addEventListener('click', () => {
        viewerModal.classList.remove('active');
    });
    document.getElementById('legal-viewer-ok').addEventListener('click', () => {
        viewerModal.classList.remove('active');
    });
}

// ============================================================================
// Application Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🧠 마음챗 - Korean Mental Health Counseling System');
    console.log('Initializing application...');

    // Check consent first
    if (!checkConsent()) {
        console.log('⚠️ User consent not found. Showing consent modal...');
        showConsentModal();
    }

    // Initialize screens
    initializeHomeScreen();

    // User menu button (for future dashboard access)
    document.getElementById('user-menu-btn').addEventListener('click', () => {
        if (AppState.userId) {
            loadDashboard();
        } else {
            UI.showToast('먼저 사용자 ID를 입력해주세요');
        }
    });

    // Update user name display
    const updateUserDisplay = () => {
        const userName = AppState.userId || '사용자';
        document.getElementById('user-name').textContent = userName;
    };

    // Watch for user ID changes
    const userIdInput = document.getElementById('user-id-input');
    userIdInput.addEventListener('blur', updateUserDisplay);
    updateUserDisplay();

    console.log('✅ Application initialized successfully');
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    // Save current state if needed
    if (AppState.currentSession) {
        StorageHelper.set(CONFIG.STORAGE_KEYS.CHAT_HISTORY, AppState.chatHistory);
    }
});
