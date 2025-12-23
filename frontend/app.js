/**
 * Korean Mental Health Counseling Frontend Application
 * 마브AI - AI 심리상담 서비스
 */

// ============================================================================
// Global State
// ============================================================================

const AppState = {
    currentScreen: 'home',
    userId: null,
    currentSession: null,
    chatHistory: [],
    isRestoringHistory: false, // 세션 복원 중인지 여부
    ttsPlayer: null, // TTS 플레이어 인스턴스
    ttsEnabled: true // TTS 활성화 여부 (기본값: true)
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
            console.log(`[API] Request to: ${url}`, { method: options.method || 'GET', headers });
            
            const response = await fetch(url, {
                ...options,
                headers
            });

            console.log(`[API] Response status: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                // 응답 본문 읽기 시도
                let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorData.message || errorDetail;
                    console.error('[API] Error response:', errorData);
                } catch (e) {
                    // JSON 파싱 실패 시 텍스트로 읽기 시도
                    try {
                        const errorText = await response.text();
                        if (errorText) {
                            errorDetail = errorText;
                        }
                    } catch (e2) {
                        console.error('[API] Failed to read error response:', e2);
                    }
                }
                
                const error = new Error(errorDetail);
                error.status = response.status;
                error.statusText = response.statusText;
                throw error;
            }

            const data = await response.json();
            console.log('[API] Response data received');
            return data;
        } catch (error) {
            // 네트워크 오류 처리
            if (error instanceof TypeError && error.message.includes('fetch')) {
                const networkError = new Error('Network error: 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
                networkError.originalError = error;
                console.error('[API] Network error:', networkError);
                throw networkError;
            }
            
            console.error('[API] Request error:', error);
            throw error;
        }
    }

    // Chat Endpoints
    async sendChatMessage(message, sessionId, userId = null) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
                user_id: userId
            })
        });
    }

    // Feedback Endpoints
    async submitFeedback(feedbackData) {
        return this.request('/feedback', {
            method: 'POST',
            body: JSON.stringify(feedbackData)
        });
    }

    // User Endpoints
    async getUserStats(userId) {
        return this.request(`/user/${userId}/stats`, {
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
        // 채팅 화면에서는 채팅 로딩 오버레이 사용
        const chatLoading = document.getElementById('chat-loading-overlay');
        const globalLoading = document.getElementById('loading-overlay');
        
        if (AppState.currentScreen === 'chat' && chatLoading) {
            chatLoading.classList.add('active');
        } else if (globalLoading) {
            globalLoading.classList.add('active');
        }
    },

    hideLoading() {
        // 모든 로딩 오버레이 숨기기
        const chatLoading = document.getElementById('chat-loading-overlay');
        const globalLoading = document.getElementById('loading-overlay');
        
        if (chatLoading) chatLoading.classList.remove('active');
        if (globalLoading) globalLoading.classList.remove('active');
    },

    showToast(message, duration = CONFIG.TOAST_DURATION) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('active');

        setTimeout(() => {
            toast.classList.remove('active');
        }, duration);
    },

    formatTime(date = new Date()) {
        return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    }
};

// ============================================================================
// Home Screen Logic
// ============================================================================

function initializeHomeScreen() {
    // Start chat button
    const startChatBtn = document.getElementById('start-chat-btn');
    if (startChatBtn) {
        startChatBtn.addEventListener('click', function() {
            console.log('상담 시작하기 버튼 클릭됨');
            startChat();
        });
    } else {
        console.warn('start-chat-btn 요소를 찾을 수 없습니다.');
    }
    
    // Load session button
    const loadSessionBtn = document.getElementById('load-session-btn');
    if (loadSessionBtn) {
        loadSessionBtn.addEventListener('click', function() {
            showSessionModal();
        });
    }
    
    // Modal close button
    const closeModalBtn = document.getElementById('close-session-modal');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            hideSessionModal();
        });
    }
    
    // Close modal when clicking outside
    const sessionModal = document.getElementById('session-modal');
    if (sessionModal) {
        sessionModal.addEventListener('click', function(e) {
            if (e.target === sessionModal) {
                hideSessionModal();
            }
        });
    }
}

function startChat(sessionId = null) {
    // Use provided session ID or generate new one
    AppState.currentSession = {
        id: sessionId || generateSessionId(),
        startTime: new Date().toISOString(),
        messageCount: 0
    };
    StorageHelper.set(CONFIG.STORAGE_KEYS.CURRENT_SESSION, AppState.currentSession);

    // Initialize chat
    initializeChatScreen(sessionId);
    UI.showScreen('chat');
}

async function showSessionModal() {
    const modal = document.getElementById('session-modal');
    const loadingDiv = document.getElementById('session-loading');
    const listDiv = document.getElementById('session-list');
    const emptyDiv = document.getElementById('session-empty');
    
    if (!modal) return;
    
    modal.style.display = 'flex';
    modal.classList.add('active');
    
    // Show loading
    loadingDiv.style.display = 'block';
    listDiv.style.display = 'none';
    emptyDiv.style.display = 'none';
    
    try {
        // Fetch sessions
        const response = await fetch(`${CONFIG.API_BASE_URL}/sessions?limit=20`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...(CONFIG.API_KEY ? { 'X-API-Key': CONFIG.API_KEY } : {})
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        loadingDiv.style.display = 'none';
        
        if (data.sessions && data.sessions.length > 0) {
            listDiv.style.display = 'block';
            renderSessionList(data.sessions);
        } else {
            emptyDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
        loadingDiv.style.display = 'none';
        listDiv.innerHTML = `<p style="color: var(--danger); text-align: center; padding: 2rem;">세션 목록을 불러오는 중 오류가 발생했습니다: ${error.message}</p>`;
        listDiv.style.display = 'block';
    }
}

function renderSessionList(sessions) {
    const listDiv = document.getElementById('session-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = sessions.map(session => {
        const createdDate = new Date(session.created_at);
        const lastActivityDate = new Date(session.last_activity);
        const formattedDate = lastActivityDate.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="session-item" data-session-id="${session.session_id}">
                <div class="session-item-header">
                    <div class="session-item-title">대화 세션</div>
                    <div class="session-item-date">${formattedDate}</div>
                </div>
                <div class="session-item-info">
                    <span>💬 ${session.total_messages}개 메시지</span>
                    ${session.crisis_detected_count > 0 ? `<span>⚠️ 위기 감지: ${session.crisis_detected_count}회</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // Add click event listeners
    listDiv.querySelectorAll('.session-item').forEach(item => {
        item.addEventListener('click', async function() {
            const sessionId = this.getAttribute('data-session-id');
            await loadSession(sessionId);
        });
    });
}

async function loadSession(sessionId) {
    try {
        // Fetch session history
        const response = await fetch(`${CONFIG.API_BASE_URL}/sessions/${sessionId}/history`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...(CONFIG.API_KEY ? { 'X-API-Key': CONFIG.API_KEY } : {})
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Set current session
        AppState.currentSession = {
            id: sessionId,
            startTime: new Date().toISOString(),
            messageCount: data.total_messages
        };
        StorageHelper.set(CONFIG.STORAGE_KEYS.CURRENT_SESSION, AppState.currentSession);
        
        // Load conversation history
        AppState.chatHistory = data.conversation_history || [];
        
        // Close modal
        hideSessionModal();
        
        // Initialize chat screen with history
        initializeChatScreen(sessionId);
        UI.showScreen('chat');
        
    } catch (error) {
        console.error('Error loading session:', error);
        alert(`세션을 불러오는 중 오류가 발생했습니다: ${error.message}`);
    }
}

function hideSessionModal() {
    const modal = document.getElementById('session-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
    }
}

// ============================================================================
// Chat Screen Logic
// ============================================================================

function initializeChatScreen(sessionId = null) {
    const messagesContainer = document.getElementById('chat-messages');
    
    // TTS 플레이어 초기화
    if (typeof TTSPlayer !== 'undefined' && !AppState.ttsPlayer) {
        AppState.ttsPlayer = new TTSPlayer({
            apiUrl: CONFIG.API_BASE_URL ? `${CONFIG.API_BASE_URL}/tts` : '/api/v1/tts',
            voiceProfile: 'default_counselor',
            onStart: () => {
                console.log('[TTS] 재생 시작');
            },
            onEnd: () => {
                console.log('[TTS] 재생 완료');
            },
            onError: (error) => {
                console.error('[TTS] 오류:', error);
            }
        });
        // TTS 플레이어 초기화
        AppState.ttsPlayer.initialize().catch(err => {
            console.error('[TTS] 초기화 실패:', err);
        });
    }
    
    // TTS 토글 초기화
    const ttsToggle = document.getElementById('tts-toggle');
    if (ttsToggle) {
        // 로컬 스토리지에서 TTS 상태 불러오기
        const savedTtsState = localStorage.getItem('tts_enabled');
        if (savedTtsState !== null) {
            AppState.ttsEnabled = savedTtsState === 'true';
            ttsToggle.checked = AppState.ttsEnabled;
        }
        
        // TTS 토글 이벤트 리스너
        ttsToggle.addEventListener('change', (e) => {
            AppState.ttsEnabled = e.target.checked;
            localStorage.setItem('tts_enabled', AppState.ttsEnabled.toString());
            console.log('[TTS] 상태 변경:', AppState.ttsEnabled ? 'ON' : 'OFF');
        });
    }
    
    // If loading existing session, restore chat history
    if (sessionId && AppState.chatHistory && AppState.chatHistory.length > 0) {
        messagesContainer.innerHTML = '';
        
        // 임시로 chatHistory 추가를 비활성화
        const originalChatHistory = [...AppState.chatHistory];
        AppState.isRestoringHistory = true;
        
        // Restore all messages from history
        originalChatHistory.forEach(msg => {
            if (msg.role === 'user') {
                addUserMessage(msg.content, null, false); // skipHistoryAdd = true
            } else if (msg.role === 'assistant' || msg.role === 'bot') {
                addBotMessage(msg.content, false); // skipHistoryAdd = true
            }
        });
        
        // Restore complete
        AppState.isRestoringHistory = false;
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else {
        // Clear chat history for new session
        AppState.chatHistory = [];
        messagesContainer.innerHTML = `
        <div class="welcome-message">
            <p>AI 심리상담사와의 대화가 시작됩니다.</p>
            <p>편안하게 이야기 나눠보세요. 🌸</p>
        </div>
    `;

    // Send initial greeting
        addBotMessage('안녕하세요, 마브AI입니다. 오늘 어떤 이야기를 나누고 싶으신가요? 편하게 말씀해주세요.');
    }

    // Setup event listeners
    setupChatEventListeners();
    
    // 실시간 감정 분석 초기화
    initializeRealtimeEmotion();
}

function initializeRealtimeEmotion() {
    console.log('실시간 감정 분석 초기화 시작...');
    
    // emotion-sidebar가 존재하는지 확인
    const sidebarElement = document.getElementById('emotion-sidebar');
    if (!sidebarElement) {
        console.error('emotion-sidebar 요소를 찾을 수 없습니다.');
        return;
    }
    console.log('emotion-sidebar 요소 발견:', sidebarElement);
    
    // 사이드바가 확실히 보이도록 강제 설정
    sidebarElement.style.display = 'flex';
    sidebarElement.style.visibility = 'visible';
    sidebarElement.style.opacity = '1';
    
    // realtime-emotion.js가 로드되었는지 확인
    if (typeof RealtimeEmotionUI !== 'undefined') {
        try {
            const widgetElement = document.getElementById('realtime-emotion-widget');
            if (widgetElement) {
                console.log('realtime-emotion-widget 요소 발견:', widgetElement);
                
                // 실시간 감정 분석 UI 초기화 (자동 시작 활성화)
                const emotionUI = new RealtimeEmotionUI('realtime-emotion-widget', {
                    sessionId: AppState.currentSession?.id || generateSessionId(),
                    apiBaseUrl: CONFIG.API_BASE_URL || 'http://localhost:8000',
                    autoStart: true // 자동 시작 활성화
                });
                
                // 전역 변수로 저장하여 다른 곳에서 접근 가능하도록
                window.realtimeEmotionUI = emotionUI;
                
                console.log('✅ 실시간 감정 분석 UI 초기화 완료');
            } else {
                console.warn('⚠️ realtime-emotion-widget 요소를 찾을 수 없습니다.');
                // 위젯이 없어도 사이드바는 표시되도록 기본 내용 추가
                sidebarElement.innerHTML = `
                    <div style="padding: 20px; text-align: center;">
                        <h3>실시간 감정 분석</h3>
                        <p>위젯 초기화 중...</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('❌ 실시간 감정 분석 초기화 실패:', error);
            // 오류 발생 시에도 사이드바는 표시
            sidebarElement.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <h3>실시간 감정 분석</h3>
                    <p style="color: red;">초기화 오류: ${error.message}</p>
                </div>
            `;
        }
    } else {
        console.warn('⚠️ RealtimeEmotionUI가 로드되지 않았습니다. realtime-emotion.js를 확인하세요.');
        // RealtimeEmotionUI가 없어도 사이드바는 표시
        sidebarElement.innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <h3>🎭 실시간 감정 분석</h3>
                <p>모듈 로딩 중...</p>
                <p style="font-size: 0.9em; color: #666;">realtime-emotion.js를 확인하세요.</p>
            </div>
        `;
    }
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

        // "생각중" 메시지 표시
        const thinkingMessageId = addThinkingMessage();
        
        try {
            const response = await api.sendChatMessage(
                message,
                AppState.currentSession.id,
                AppState.userId
            );

            // "생각중" 메시지 제거
            removeThinkingMessage(thinkingMessageId);
            
            addBotMessage(response.response);

            // TTS 재생 (봇 응답)
            if (AppState.ttsPlayer && response.response) {
                try {
                    // TTS가 활성화되어 있을 때만 재생
                    if (AppState.ttsEnabled && AppState.ttsPlayer) {
                        // 채팅 TTS 엔진 선택 가져오기
                        const chatTtsSelect = document.getElementById('chat-tts-engine-select');
                        const savedEngine = localStorage.getItem('tts_engine');
                        const ttsEngine = chatTtsSelect ? chatTtsSelect.value : (savedEngine || 'zonos');
                        
                        AppState.ttsPlayer.speak(response.response, {
                            emotion: 'calm',
                            voiceProfile: 'default_counselor',
                            tts_engine: ttsEngine
                        }).catch(err => {
                            console.error('[TTS] 재생 실패:', err);
                        });
                    } else {
                        console.log('[TTS] TTS가 비활성화되어 있습니다.');
                    }
                } catch (error) {
                    console.error('[TTS] 오류:', error);
                }
            }

            // Display emotion analysis result if available
            console.log('[감정 분석] API 응답:', response);
            console.log('[감정 분석] 감정 데이터:', response.emotions);
            
            if (response.emotions) {
                // 채팅창 감정 분석 표시 제거 (사이드바에만 표시)
                console.log('[감정 분석] 사이드바 업데이트 시작');
                updateChatEmotionSidebar(message, response.emotions);
            } else {
                console.warn('[감정 분석] 응답에 감정 데이터가 없습니다.');
            }

            // Handle safety checks
            if (response.crisis_detected) {
                addSystemMessage('⚠️ 위기 상황이 감지되었습니다. 전문가의 즉각적인 도움이 필요할 수 있습니다.');
                addSystemMessage('자살예방상담전화: ☎️ 1393 | 정신건강위기상담: ☎️ 1577-0199');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            
            // "생각중" 메시지 제거
            removeThinkingMessage(thinkingMessageId);
            
            // 더 상세한 에러 메시지 제공
            let errorMessage = '메시지 전송 중 오류가 발생했습니다.';
            
            if (error.message) {
                if (error.message.includes('503') || error.message.includes('Service Unavailable')) {
                    errorMessage = '서버가 초기화 중입니다. 잠시 후 다시 시도해주세요.';
                } else if (error.message.includes('500') || error.message.includes('Internal Server Error')) {
                    errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                } else if (error.message.includes('Network') || error.message.includes('Failed to fetch')) {
                    errorMessage = '네트워크 연결을 확인해주세요. 서버에 연결할 수 없습니다.';
                } else if (error.message.includes('404') || error.message.includes('Not Found')) {
                    errorMessage = 'API 엔드포인트를 찾을 수 없습니다. 서버 설정을 확인해주세요.';
                } else {
                    errorMessage = `오류: ${error.message}`;
                }
            }
            
            addSystemMessage(errorMessage);
            
            // 에러 상세 정보를 콘솔에 출력 (디버깅용)
            console.error('Detailed error info:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
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

function addUserMessage(text, emotion = null, addToHistory = true) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    
    // 감정 분석 배지 제거 (채팅창에서는 표시하지 않음)
    
    messageDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">
            <div>${text}</div>
            <div class="message-time">${UI.formatTime()}</div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    // 세션 복원 중이 아니고 addToHistory가 true일 때만 히스토리에 추가
    if (addToHistory && !AppState.isRestoringHistory) {
        AppState.chatHistory.push({ role: 'user', content: text, time: new Date().toISOString(), emotion: emotion });
    }
}

// 채팅창 감정 분석 표시 제거됨 (사이드바에만 표시)
// function displayMessageEmotion(message, emotions) {
//     // 사용자 메시지에 감정 배지 추가
//     const userMessages = document.querySelectorAll('.message.user');
//     if (userMessages.length > 0) {
//         const lastUserMessage = userMessages[userMessages.length - 1];
//         const messageContent = lastUserMessage.querySelector('.message-content');
//         if (messageContent && !messageContent.querySelector('.emotion-badge')) {
//             const emotionBadge = createEmotionBadge(emotions);
//             messageContent.insertAdjacentHTML('afterbegin', emotionBadge);
//         }
//     }
// }

function createEmotionBadge(emotions) {
    const emotionEmojis = {
        '기쁨': '😊',
        '슬픔': '😢',
        '분노': '😠',
        '불안': '😰',
        '두려움': '😨',
        '평온': '😌',
        '희망': '🌟',
        '외로움': '😔',
        '스트레스': '😫',
        '감사': '🙏',
        '중립': '😐',
        '혼란': '🤔',
        '좌절': '😫',
        '안도': '😌'
    };
    
    const primaryEmotion = emotions.primary_emotion || emotions.dominant_emotion || '중립';
    const emoji = emotionEmojis[primaryEmotion] || '😐';
    const confidence = emotions.confidence || emotions.intensity || 0;
    const confidencePercent = Math.round(confidence * 100);
    
    return `
        <div class="emotion-badge" title="감정 분석: ${primaryEmotion} (${confidencePercent}%)">
            <span class="emotion-emoji">${emoji}</span>
            <span class="emotion-label">${primaryEmotion}</span>
            ${confidencePercent > 0 ? `<span class="emotion-confidence">${confidencePercent}%</span>` : ''}
        </div>
    `;
}

// "생각중" 메시지 추가
function addThinkingMessage() {
    const messagesContainer = document.getElementById('chat-messages');
    const messageId = `thinking-${Date.now()}`;
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = 'message bot thinking';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <img src="/static/images/counselor_avatar.png" alt="상담사" class="message-avatar-image avatar-clickable" onclick="showAvatarModal('/static/images/counselor_avatar.png')" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <span style="display:none;">👩‍⚕️</span>
        </div>
        <div class="message-content">
            <div class="thinking-indicator">
                <span class="thinking-dot"></span>
                <span class="thinking-dot"></span>
                <span class="thinking-dot"></span>
                <span class="thinking-text">생각 중...</span>
            </div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return messageId;
}

// "생각중" 메시지 제거
function removeThinkingMessage(messageId) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.remove();
    }
}

function addBotMessage(text, addToHistory = true) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <img src="/static/images/counselor_avatar.png" alt="상담사" class="message-avatar-image avatar-clickable" onclick="showAvatarModal('/static/images/counselor_avatar.png')" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <span style="display:none;">👩‍⚕️</span>
        </div>
        <div class="message-content">
            <div>${text}</div>
            <div class="message-time">${UI.formatTime()}</div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    // 세션 복원 중이 아니고 addToHistory가 true일 때만 히스토리에 추가
    if (addToHistory && !AppState.isRestoringHistory) {
        // 세션 복원 중이 아니고 addToHistory가 true일 때만 히스토리에 추가
    if (addToHistory && !AppState.isRestoringHistory) {
        AppState.chatHistory.push({ role: 'bot', content: text, time: new Date().toISOString() });
    }
    }
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
        session_id: AppState.currentSession.id,
        rating: rating,
        feedback_type: document.getElementById('helpful-check').checked ? 'helpful' : 'not_helpful',
        feedback_text: document.getElementById('feedback-text').value.trim() || null
    };

    UI.showLoading();

    try {
        await api.submitFeedback(feedbackData);
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
    // 사용자 ID가 없으면 생성
    if (!AppState.userId) {
        AppState.userId = StorageHelper.get(CONFIG.STORAGE_KEYS.USER_ID);
    if (!AppState.userId) {
            AppState.userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            StorageHelper.set(CONFIG.STORAGE_KEYS.USER_ID, AppState.userId);
        }
    }

    UI.showLoading();
    UI.showScreen('dashboard');

    try {
        // 사용자 통계 로드
        const stats = await api.getUserStats(AppState.userId);
        displayUserStats(stats);
        
        // 최근 세션 목록 로드
        await loadRecentSessions();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        // 통계가 없어도 대시보드 표시 (새 사용자일 수 있음)
        if (error.message && error.message.includes('404')) {
            displayUserStats({
                total_conversations: 0,
                total_messages: 0,
                crisis_count: 0
            });
            await loadRecentSessions();
        } else {
        UI.showToast('대시보드 로드 중 오류가 발생했습니다');
        }
    } finally {
        UI.hideLoading();
    }

    // Back to home button
    const backBtn = document.getElementById('back-to-home-from-dashboard-btn');
    if (backBtn) {
    const newBackBtn = backBtn.cloneNode(true);
    backBtn.parentNode.replaceChild(newBackBtn, backBtn);
    newBackBtn.addEventListener('click', () => {
        UI.showScreen('home');
        });
    }
}

async function loadRecentSessions() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/sessions?limit=5`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...(CONFIG.API_KEY ? { 'X-API-Key': CONFIG.API_KEY } : {})
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        displayRecentSessions(data.sessions || []);
    } catch (error) {
        console.error('Error loading recent sessions:', error);
        displayRecentSessions([]);
    }
}

function displayRecentSessions(sessions) {
    const container = document.getElementById('recent-sessions');
    if (!container) return;
    
    if (sessions.length === 0) {
        container.innerHTML = '<p class="no-data">최근 상담 내역이 없습니다.</p>';
        return;
    }
    
    container.innerHTML = sessions.map(session => {
        const date = new Date(session.created_at || Date.now());
        const formattedDate = date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="session-item" data-session-id="${session.session_id}">
                <div class="session-item-header">
                    <div class="session-item-title">상담 세션</div>
                    <div class="session-item-date">${formattedDate}</div>
                </div>
                <div class="session-item-info">
                    <span>💬 ${session.total_messages || 0}개 메시지</span>
                    ${session.crisis_detected_count > 0 ? `<span>⚠️ 위기 감지: ${session.crisis_detected_count}회</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // 세션 클릭 이벤트
    container.querySelectorAll('.session-item').forEach(item => {
        item.addEventListener('click', async function() {
            const sessionId = this.getAttribute('data-session-id');
            await loadSession(sessionId);
        });
    });
}

function displayUserStats(stats) {
    // 통계 카드 업데이트
    const totalSessionsEl = document.getElementById('total-sessions');
    const totalMessagesEl = document.getElementById('total-messages');
    const crisisCountEl = document.getElementById('crisis-count');
    const totalFeedbackEl = document.getElementById('total-feedback');
    
    if (totalSessionsEl) {
        totalSessionsEl.textContent = `${stats.total_conversations || stats.total_sessions || 0}회`;
    }
    if (totalMessagesEl) {
        totalMessagesEl.textContent = `${stats.total_messages || 0}개`;
    }
    if (crisisCountEl) {
        crisisCountEl.textContent = `${stats.crisis_count || 0}회`;
    }
    if (totalFeedbackEl) {
        totalFeedbackEl.textContent = `${stats.total_feedback || stats.total_feedback_count || 0}회`;
    }
    
    // 활동 타임라인 업데이트
    updateActivityTimeline(stats);
}

// 대화 감정 히스토리 저장
let chatEmotionHistory = [];

function updateChatEmotionSidebar(message, emotions) {
    console.log('[감정 분석] updateChatEmotionSidebar 호출:', { message, emotions });
    
    if (!emotions) {
        console.warn('[감정 분석] emotions가 없습니다.');
        return;
    }
    
    // primary_emotion이 없어도 다른 필드가 있으면 처리
    let primaryEmotion = emotions.primary_emotion || emotions.dominant_emotion || emotions.emotion || null;
    if (!primaryEmotion && !emotions.emotions) {
        console.warn('[감정 분석] primary_emotion과 emotions 모두 없습니다.');
        return;
    }
    
    const emotionEmojis = {
        '기쁨': '😊',
        '슬픔': '😢',
        '분노': '😠',
        '불안': '😰',
        '두려움': '😨',
        '평온': '😌',
        '희망': '🌟',
        '외로움': '😔',
        '스트레스': '😫',
        '감사': '🙏',
        '중립': '😐',
        '혼란': '🤔',
        '좌절': '😫',
        '안도': '😌'
    };
    
    // primaryEmotion이 null이면 기본값 설정
    primaryEmotion = primaryEmotion || '중립';
    const emoji = emotionEmojis[primaryEmotion] || '😐';
    const confidence = emotions.confidence || emotions.confidence_score || emotions.intensity || 0;
    const confidencePercent = Math.round(confidence * 100);
    
    console.log('[감정 분석] 처리된 감정:', { primaryEmotion, emoji, confidence, confidencePercent });
    
    // 현재 감정 배지 업데이트
    const badge = document.getElementById('chat-emotion-badge');
    if (badge) {
        const emojiEl = badge.querySelector('.emotion-emoji-large');
        const nameEl = badge.querySelector('.emotion-name-large');
        const confidenceEl = badge.querySelector('.emotion-confidence-large');
        
        if (emojiEl) emojiEl.textContent = emoji;
        if (nameEl) nameEl.textContent = primaryEmotion;
        if (confidenceEl) confidenceEl.textContent = `신뢰도 (confidence): ${confidencePercent}%`;
        
        // 색상 업데이트
        const emotionColors = {
            '기쁨': '#FFD93D',
            '슬픔': '#74B9FF',
            '분노': '#FF7675',
            '불안': '#FDCB6E',
            '두려움': '#E17055',
            '평온': '#00B894',
            '희망': '#7ED6DF',
            '외로움': '#A29BFE',
            '스트레스': '#FD79A8',
            '감사': '#A8E6CF',
            '중립': '#B2BEC3',
            '혼란': '#DFE6E9',
            '좌절': '#E17055',
            '안도': '#B8E6CF'
        };
        
        const color = emotionColors[primaryEmotion] || '#B2BEC3';
        badge.style.borderColor = color;
        badge.style.background = `linear-gradient(135deg, ${color}15 0%, ${color}08 100%)`;
    }
    
    // 감정 분포 바 업데이트
    updateChatEmotionBars(emotions);
    
    // 히스토리에 추가
    chatEmotionHistory.push({
        emotion: primaryEmotion,
        emoji: emoji,
        confidence: confidencePercent,
        message: message.substring(0, 30) + (message.length > 30 ? '...' : ''),
        timestamp: new Date()
    });
    
    // 최대 10개만 유지
    if (chatEmotionHistory.length > 10) {
        chatEmotionHistory.shift();
    }
    
    // 타임라인 업데이트
    updateChatEmotionTimeline();
}

function updateChatEmotionBars(emotions) {
    const barsContainer = document.getElementById('chat-emotion-bars');
    if (!barsContainer) return;
    
    const emotionEmojis = {
        '기쁨': '😊',
        '슬픔': '😢',
        '분노': '😠',
        '불안': '😰',
        '두려움': '😨',
        '평온': '😌',
        '희망': '🌟',
        '외로움': '😔',
        '스트레스': '😫',
        '감사': '🙏',
        '중립': '😐',
        '혼란': '🤔',
        '좌절': '😫',
        '안도': '😌'
    };
    
    // 감정 데이터 구조 확인 및 처리
    console.log('[감정 분석] updateChatEmotionBars 호출:', emotions);
    
    // emotions 객체에서 감정 데이터 추출
    let emotionData = emotions.emotions || emotions.emotion_scores || emotions;
    
    // emotions가 객체가 아닌 경우 처리
    if (typeof emotionData !== 'object' || Array.isArray(emotionData)) {
        console.warn('[감정 분석] emotions.emotions가 올바른 형식이 아닙니다:', emotionData);
        // primary_emotion이 있으면 그것만 표시
        if (emotions.primary_emotion) {
            emotionData = { [emotions.primary_emotion]: emotions.confidence || emotions.confidence_score || 0.5 };
        } else {
            barsContainer.innerHTML = '<p class="no-data">감정 데이터가 없습니다.</p>';
            return;
        }
    }
    
    // 감정을 확률 순으로 정렬
    // 메타데이터 키 필터링 (감정이 아닌 필드들 제외)
    const nonEmotionKeys = ['intensity', 'confidence', 'confidence_score', 'timestamp', 'primary_emotion', 'valence', 'arousal', 'engagement'];

    const sortedEmotions = Object.entries(emotionData)
        .filter(([emotion, value]) =>
            typeof value === 'number' &&
            value > 0 &&
            !nonEmotionKeys.includes(emotion.toLowerCase())
        )
        .map(([emotion, value]) => ({ emotion, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 5); // 상위 5개만 표시
    
    console.log('[감정 분석] 정렬된 감정:', sortedEmotions);
    
    if (sortedEmotions.length === 0) {
        barsContainer.innerHTML = '<p class="no-data">감정 데이터가 없습니다.</p>';
        return;
    }
    
    barsContainer.innerHTML = sortedEmotions.map(({ emotion, value }) => {
        const emoji = emotionEmojis[emotion] || '😐';
        
        // 값 검증: 0-1 범위로 제한
        let normalizedValue = typeof value === 'number' ? value : 0;
        normalizedValue = Math.max(0, Math.min(1, normalizedValue)); // 0-1 범위로 제한
        
        const percent = Math.round(normalizedValue * 100);
        // 퍼센트도 0-100 범위로 제한 (이중 안전장치)
        const safePercent = Math.max(0, Math.min(100, percent));
        
        // 감정 한글/영어 매핑
        const emotionMap = {
            'happy': { ko: '기쁨', en: 'happy' },
            'sad': { ko: '슬픔', en: 'sad' },
            'angry': { ko: '분노', en: 'angry' },
            'fearful': { ko: '불안', en: 'fearful' },
            'disgusted': { ko: '혐오', en: 'disgusted' },
            'surprised': { ko: '놀람', en: 'surprised' },
            'neutral': { ko: '중립', en: 'neutral' },
            'joy': { ko: '기쁨', en: 'joy' },
            'anger': { ko: '분노', en: 'anger' },
            'fear': { ko: '두려움', en: 'fear' },
            'disgust': { ko: '혐오', en: 'disgust' },
            'surprise': { ko: '놀람', en: 'surprise' }
        };
        
        // 이미 한글이면 그대로 사용, 영어면 변환
        let koreanLabel, englishLabel;
        if (emotionMap[emotion]) {
            koreanLabel = emotionMap[emotion].ko;
            englishLabel = emotionMap[emotion].en;
        } else if (/[가-힣]/.test(emotion)) {
            // 이미 한글이면
            koreanLabel = emotion;
            englishLabel = '';
        } else {
            // 알 수 없는 감정
            koreanLabel = emotion;
            englishLabel = '';
        }
        
        const labelText = englishLabel 
            ? `${koreanLabel} (${englishLabel})`
            : koreanLabel;
        
        return `
            <div class="chat-emotion-bar-item">
                <div class="chat-emotion-bar-label">
                    <span class="chat-emotion-bar-emoji">${emoji}</span>
                    <span>${labelText}</span>
                </div>
                <div class="chat-emotion-bar-track">
                    <div class="chat-emotion-bar-fill" style="width: ${safePercent}%"></div>
                </div>
                <div class="chat-emotion-bar-value">${safePercent}%</div>
            </div>
        `;
    }).join('');
}

// 채팅 헤더의 감정 표시 업데이트
// 채팅창 헤더 감정 분석 표시 제거됨 (사이드바에만 표시)
// function updateChatEmotionDisplay(emotions) {
//     if (!emotions || !emotions.primary_emotion) return;
//     
//     const emotionDisplay = document.getElementById('current-chat-emotion');
//     if (!emotionDisplay) return;
//     
//     const emotionEmojis = {
//         '기쁨': '😊',
//         '슬픔': '😢',
//         '분노': '😠',
//         '불안': '😰',
//         '두려움': '😨',
//         '평온': '😌',
//         '희망': '🌟',
//         '외로움': '😔',
//         '스트레스': '😫',
//         '감사': '🙏',
//         '중립': '😐',
//         '혼란': '🤔'
//     };
//     
//     const primaryEmotion = emotions.primary_emotion;
//     const emoji = emotionEmojis[primaryEmotion] || '😐';
//     const confidence = emotions.confidence || emotions.confidence_score || 0;
//     const confidencePercent = Math.round(confidence * 100);
//     
//     const emojiEl = emotionDisplay.querySelector('.emotion-emoji-small');
//     const labelEl = emotionDisplay.querySelector('.emotion-label-small');
//     
//     if (emojiEl) emojiEl.textContent = emoji;
//     if (labelEl) labelEl.textContent = `${primaryEmotion} ${confidencePercent}%`;
// }

function updateChatEmotionTimeline() {
    const timeline = document.getElementById('chat-emotion-timeline');
    if (!timeline) return;
    
    if (chatEmotionHistory.length === 0) {
        timeline.innerHTML = '<p class="no-data">대화를 시작하면 감정 분석이 표시됩니다.</p>';
        return;
    }
    
    timeline.innerHTML = chatEmotionHistory.slice().reverse().map(item => {
        const time = item.timestamp.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
        
        return `
            <div class="chat-emotion-timeline-item">
                <span class="chat-emotion-timeline-emoji">${item.emoji}</span>
                <div class="chat-emotion-timeline-text">
                    <div>${item.emotion} (${item.confidence}%)</div>
                    <div style="font-size: 0.75rem; color: var(--text-light); margin-top: 2px;">${item.message}</div>
                </div>
                <span class="chat-emotion-timeline-time">${time}</span>
            </div>
        `;
    }).join('');
}

function updateActivityTimeline(stats) {
    const timelineEl = document.getElementById('activity-timeline');
    if (!timelineEl) return;
    
    const activities = [];
    
    if (stats.member_since) {
        activities.push({
            date: new Date(stats.member_since),
            type: 'join',
            text: '서비스 가입'
        });
    }
    
    if (stats.last_active) {
        activities.push({
            date: new Date(stats.last_active),
            type: 'active',
            text: '마지막 활동'
        });
    }
    
    if (activities.length === 0) {
        timelineEl.innerHTML = '<p class="no-data">활동 내역이 없습니다.</p>';
        return;
    }
    
    // 날짜순 정렬
    activities.sort((a, b) => b.date - a.date);
    
    timelineEl.innerHTML = activities.map(activity => {
        const formattedDate = activity.date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const icon = activity.type === 'join' ? '🎉' : '🕐';
        
        return `
            <div class="timeline-item">
                <div class="timeline-icon">${icon}</div>
                <div class="timeline-content">
                    <div class="timeline-text">${activity.text}</div>
                    <div class="timeline-date">${formattedDate}</div>
                </div>
            </div>
        `;
    }).join('');
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
    console.log('마브AI - Korean Mental Health Counseling System');
    console.log('Initializing application...');

    // Check consent first
    if (!checkConsent()) {
        console.log('⚠️ User consent not found. Showing consent modal...');
        showConsentModal();
    }

    // Initialize screens
    initializeHomeScreen();

    // User menu button - 대시보드로 이동
    const userMenuBtn = document.getElementById('user-menu-btn');
    if (userMenuBtn) {
        userMenuBtn.addEventListener('click', () => {
            if (AppState.userId) {
                loadDashboard();
            } else {
                // 사용자 ID가 없으면 생성
                AppState.userId = StorageHelper.get(CONFIG.STORAGE_KEYS.USER_ID);
                if (!AppState.userId) {
                    AppState.userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                    StorageHelper.set(CONFIG.STORAGE_KEYS.USER_ID, AppState.userId);
                }
                loadDashboard();
            }
        });
    }

    console.log('✅ Application initialized successfully');
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    // Save current state if needed
    if (AppState.currentSession) {
        StorageHelper.set(CONFIG.STORAGE_KEYS.CHAT_HISTORY, AppState.chatHistory);
    }
});

// 아바타 확대 모달 표시
function showAvatarModal(imageSrc) {
    const modal = document.getElementById('avatar-modal');
    const modalImage = document.getElementById('avatar-modal-image');
    if (modal && modalImage) {
        modalImage.src = imageSrc;
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
    }
}

// 아바타 확대 모달 닫기
function closeAvatarModal() {
    const modal = document.getElementById('avatar-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // 배경 스크롤 복원
    }
}

// 전역 함수로 등록 (HTML에서 onclick으로 사용)
window.showAvatarModal = showAvatarModal;
window.closeAvatarModal = closeAvatarModal;

// 아바타 모달 이벤트 리스너는 위의 DOMContentLoaded에 통합됨
