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
    currentSession: null,
    chatHistory: []
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

    // Streaming Chat Endpoint
    async sendChatMessageStream(message, sessionId, userId = null, imageBase64 = null, onChunk = null) {
        const url = `${this.baseURL}/chat/stream`;
        console.log('Sending chat message to:', url);
        console.log('Request data:', { message, sessionId, userId, hasImage: !!imageBase64 });
        
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        const requestBody = {
            message: message,
            session_id: sessionId,
            user_id: userId
        };
        
        // 이미지가 있으면 추가
        if (imageBase64) {
            requestBody.image_base64 = imageBase64;
        }
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody)
            });
            
            console.log('Response status:', response.status, response.statusText);
            
            if (!response.ok) {
                const errorText = await response.text().catch(() => '');
                console.error('Response error:', errorText);
                let errorData = {};
                try {
                    errorData = JSON.parse(errorText);
                } catch (e) {
                    errorData = { detail: errorText || `HTTP ${response.status}: ${response.statusText}` };
                }
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Server-Sent Events 처리
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            const result = {
                session_id: null,
                text: '',
                audioChunks: [],
                isComplete: false
            };
            
            console.log('Starting SSE stream reading...');
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('SSE stream finished');
                    break;
                }
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // 마지막 불완전한 라인은 버퍼에 보관
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            console.log('SSE data received:', data.type);
                            
                            if (data.type === 'session') {
                                result.session_id = data.session_id;
                            } else if (data.type === 'text') {
                                if (data.is_partial) {
                                    // 부분 텍스트 업데이트
                                    result.text = data.text;
                                } else {
                                    // 최종 텍스트
                                    result.text = data.text;
                                }
                            } else if (data.type === 'audio') {
                                result.audioChunks.push({
                                    audio_base64: data.audio_base64,
                                    sample_rate: data.sample_rate,
                                    duration_ms: data.duration_ms,
                                    text: data.text,
                                    is_last: data.is_last
                                });
                            } else if (data.type === 'done') {
                                result.isComplete = true;
                            } else if (data.type === 'error') {
                                throw new Error(data.message);
                            }
                            
                            // 콜백 호출
                            if (onChunk) {
                                onChunk(data);
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                            console.error('Problematic line:', line);
                            console.error('Buffer state:', buffer.substring(0, 200));
                        }
                    }
                }
            }
            
            console.log('SSE stream completed, result:', {
                session_id: result.session_id,
                text_length: result.text.length,
                audio_chunks: result.audioChunks.length
            });
            
            return result;
        } catch (fetchError) {
            console.error('Fetch error in sendChatMessageStream:', fetchError);
            throw fetchError;
        }
    }
    
    // Health check to verify server is ready
    async checkHealth() {
        return this.request('/health', {
            method: 'GET'
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
        // 화면 전환 전에 현재 화면 확인
        const targetScreen = document.getElementById(`${screenId}-screen`);
        
        if (!targetScreen) {
            console.error(`Screen not found: ${screenId}-screen`);
            return;
        }
        
        // 모든 화면 비활성화
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        // 대상 화면 활성화
        targetScreen.classList.add('active');
        AppState.currentScreen = screenId;
        
        // 채팅 화면으로 전환 시 이벤트 리스너 재설정
        if (screenId === 'chat') {
            setupChatEventListeners();
            // 사이드바 토글 기능 제거됨
        }
        
        console.log(`Screen changed: ${screenId}`);
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

    formatTime(date = new Date()) {
        return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    }
};

// ============================================================================
// Home Screen Logic
// ============================================================================

function initializeHomeScreen() {
    // Start chat button - 중복 리스너 방지
    const startBtn = document.getElementById('start-chat-btn');
    if (!startBtn) {
        console.warn('start-chat-btn not found');
        return;
    }

    // 기존 리스너 제거를 위해 클론 (하지만 이벤트 리스너는 새로 추가)
    // 클론하지 않고 직접 이벤트 리스너 추가 (중복 방지를 위해 기존 리스너 제거)
    const newBtn = startBtn.cloneNode(true);
    startBtn.parentNode.replaceChild(newBtn, startBtn);
    
    // 새 버튼에 이벤트 리스너 추가
    newBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('Start chat button clicked, systemReady:', systemReady);
        
        // 버튼이 비활성화되어 있으면 클릭 무시
        if (newBtn.disabled) {
            console.log('Button is disabled, ignoring click');
            return;
        }
        
        // 시스템이 준비되지 않았으면 클릭 무시
        if (!systemReady) {
            console.warn('시스템이 아직 준비되지 않았습니다. 잠시만 기다려주세요.');
            UI.showToast('시스템이 아직 준비 중입니다. 잠시만 기다려주세요.');
            return;
        }
        
        console.log('Starting chat...');
        startChat();
    });
    
    console.log('Home screen initialized, button event listener added');
}

function startChat() {
    // 이미 채팅 화면이면 중복 실행 방지
    if (AppState.currentScreen === 'chat') {
        console.log('Already in chat screen, skipping...');
        return;
    }
    
    // 시스템이 준비되지 않았으면 시작하지 않음
    if (!systemReady) {
        console.warn('시스템이 아직 준비되지 않았습니다.');
        UI.showToast('시스템이 아직 준비 중입니다. 잠시만 기다려주세요.');
        return;
    }
    
    // 버튼 비활성화하여 중복 클릭 방지
    const startBtn = document.getElementById('start-chat-btn');
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.textContent = '시작 중...';
    }
    
    try {
    // Generate session ID
    AppState.currentSession = {
        id: generateSessionId(),
        startTime: new Date().toISOString(),
        messageCount: 0
    };
    StorageHelper.set(CONFIG.STORAGE_KEYS.CURRENT_SESSION, AppState.currentSession);

    // Initialize chat
    initializeChatScreen();
    UI.showScreen('chat');
    } catch (error) {
        console.error('Error starting chat:', error);
        // 에러 발생 시 버튼 다시 활성화
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = '상담 시작하기';
        }
    }
}

// ============================================================================
// Chat Screen Logic
// ============================================================================

// 웹캠 감정 감지기 인스턴스 (전역 변수)
let faceEmotionDetector = null;

function initializeChatScreen() {
    // Clear chat history
    AppState.chatHistory = [];
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <p>AI 심리상담사와의 대화가 시작됩니다.</p>
            <p>편안하게 이야기 나눠보세요. 🌸</p>
        </div>
    `;

    // Send initial greeting
    addBotMessage('안녕하세요, 마음챗입니다. 오늘 어떤 이야기를 나누고 싶으신가요? 편하게 말씀해주세요.');

    // 텍스트 입력창 표시 (기본 모드)
    const textInputContainer = document.getElementById('text-input-container');
    const voiceInputContainer = document.getElementById('voice-input-container');
    const textModeBtn = document.getElementById('text-mode-btn');
    const voiceModeBtn = document.getElementById('voice-mode-btn');
    
    if (textInputContainer) textInputContainer.style.display = 'block';
    if (voiceInputContainer) voiceInputContainer.style.display = 'none';
    if (textModeBtn) textModeBtn.classList.add('active');
    if (voiceModeBtn) voiceModeBtn.classList.remove('active');

    // Setup event listeners
    setupChatEventListeners();
    
    // 웹캠 모드 설정
    setupCameraMode();
}

function setupChatEventListeners() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-message-btn');
    const backBtn = document.getElementById('back-to-home-btn');
    
    if (!chatInput || !sendBtn) {
        console.error('Chat input or send button not found:', { chatInput, sendBtn });
        return;
    }
    
    // 기존 이벤트 리스너 제거 (중복 방지)
    const newChatInput = chatInput.cloneNode(true);
    chatInput.parentNode.replaceChild(newChatInput, chatInput);
    
    const newSendBtn = sendBtn.cloneNode(true);
    sendBtn.parentNode.replaceChild(newSendBtn, sendBtn);
    
    // 돌아가기 버튼 이벤트 리스너 재설정
    if (backBtn) {
        const newBackBtn = backBtn.cloneNode(true);
        backBtn.parentNode.replaceChild(newBackBtn, backBtn);
        newBackBtn.addEventListener('click', () => {
            if (confirm('상담을 종료하시겠습니까?')) {
                // 웹캠 중지
                if (faceEmotionDetector && faceEmotionDetector.isDetecting) {
                    faceEmotionDetector.stopCamera();
                }
                
                // 홈 화면으로 전환
                UI.showScreen('home');
                
                // 시작 버튼 상태 초기화
                const startBtn = document.getElementById('start-chat-btn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.textContent = '상담 시작하기';
                    startBtn.classList.remove('loading');
                }
                
                // 세션 초기화
                AppState.currentSession = null;
                AppState.chatHistory = [];
            }
        });
    }
    
    // 버튼 초기 상태 확인 및 활성화
    console.log('Setup chat event listeners:', {
        sendBtnExists: !!newSendBtn,
        sendBtnDisabled: newSendBtn.disabled,
        chatInputExists: !!newChatInput
    });
    
    // 버튼이 비활성화되어 있으면 활성화
    if (newSendBtn.disabled) {
        console.log('Send button was disabled, enabling it...');
        newSendBtn.disabled = false;
    }

    // Send message
    const sendMessage = async () => {
        console.log('sendMessage() called');
        
        const message = newChatInput.value.trim();
        console.log('Message extracted:', { message, length: message.length });
        
        if (!message) {
            console.log('Message is empty, returning');
            return;
        }

        console.log('Clearing input and adding user message...');
        // Clear input
        newChatInput.value = '';
        newChatInput.style.height = 'auto';

        // Add user message
        addUserMessage(message);
        console.log('User message added to UI');

        // Update session
        if (!AppState.currentSession) {
            console.error('AppState.currentSession is not initialized!');
            AppState.currentSession = {
                id: generateSessionId(),
                startTime: new Date().toISOString(),
                messageCount: 0
            };
        }
        AppState.currentSession.messageCount++;
        console.log('Session updated:', AppState.currentSession);

        // Send to API - 인라인 로딩 표시
        console.log('Adding typing indicator and disabling button...');
        let loadingMessageId = addTypingIndicator();
        newSendBtn.disabled = true;
        newSendBtn.textContent = '전송 중...';
        
        // 웹캠에서 이미지 캡처 (얼굴 인식 중인 경우)
        let capturedImage = null;
        if (faceEmotionDetector && faceEmotionDetector.isDetecting) {
            try {
                capturedImage = faceEmotionDetector.captureImage();
                if (capturedImage) {
                    console.log('Image captured from webcam:', capturedImage.substring(0, 50) + '...');
                } else {
                    console.log('Failed to capture image from webcam');
                }
            } catch (error) {
                console.error('Error capturing image:', error);
            }
        }
        
        console.log('Calling api.sendChatMessageStream with:', {
            message: message.substring(0, 50),
            sessionId: AppState.currentSession.id,
            userId: AppState.userId,
            hasImage: !!capturedImage
        });
        
        try {
            // 스트리밍 모드 사용
            let botMessageElement = null;
            let accumulatedText = '';
            let audioQueue = [];
            let isPlayingAudio = false;
            
            console.log('Starting API call...');
            const response = await api.sendChatMessageStream(
                message,
                AppState.currentSession.id,
                AppState.userId,
                capturedImage, // 이미지 전달
                async (chunk) => {
                    console.log('Chunk received in callback:', chunk.type);
                    // 실시간 청크 처리
                    if (chunk.type === 'session') {
                        if (chunk.session_id) {
                            AppState.currentSession.id = chunk.session_id;
                        }
                    } else if (chunk.type === 'emotion') {
                        // 감정 데이터 표시
                        displayEmotionData(chunk.data);
                    } else if (chunk.type === 'crisis') {
                        // 위기 감지 데이터 표시
                        displayCrisisAlert(chunk);
                    } else if (chunk.type === 'therapy') {
                        // 치료 기법 표시
                        displayTherapyTechnique(chunk.technique);
                    } else if (chunk.type === 'text') {
                        // 타이핑 인디케이터 제거
                        if (loadingMessageId) {
                            removeTypingIndicator(loadingMessageId);
                            loadingMessageId = null;
                        }
                        
                        if (chunk.is_partial) {
                            // 부분 텍스트 업데이트
                            if (!botMessageElement) {
                                botMessageElement = addBotMessage(chunk.text, true);
                            } else {
                                updateBotMessage(botMessageElement, chunk.text);
                            }
                            accumulatedText = chunk.text;
                        } else {
                            // 최종 텍스트
                            if (!botMessageElement) {
                                botMessageElement = addBotMessage(chunk.text);
                            } else {
                                updateBotMessage(botMessageElement, chunk.text);
                            }
                            accumulatedText = chunk.text;
                        }
                    } else if (chunk.type === 'audio') {
                        // 오디오 수신 확인
                        console.log('Audio received:', {
                            has_audio: !!chunk.audio_base64,
                            audio_length: chunk.audio_base64 ? chunk.audio_base64.length : 0,
                            sample_rate: chunk.sample_rate,
                            duration_ms: chunk.duration_ms,
                            is_last: chunk.is_last
                        });
                        
                        // 완성된 WAV 직접 재생 (병합 불필요)
                        if (chunk.audio_base64 && !isPlayingAudio) {
                            isPlayingAudio = true;
                            try {
                                await playCompleteWav(chunk.audio_base64);
                            } catch (error) {
                                console.error('Audio playback error:', error);
                            } finally {
                                isPlayingAudio = false;
                            }
                        }
                    } else if (chunk.type === 'error') {
                        throw new Error(chunk.message);
                    }
                }
            );
            
            console.log('API call completed, response:', {
                hasText: !!response.text,
                textLength: response.text ? response.text.length : 0,
                audioChunks: response.audioChunks ? response.audioChunks.length : 0
            });
            
            // 타이핑 인디케이터 제거 (혹시 남아있으면)
            if (loadingMessageId) {
                removeTypingIndicator(loadingMessageId);
            }
            
            // 최종 텍스트가 있으면 표시
            if (response.text && !botMessageElement) {
                console.log('Adding final bot message:', response.text.substring(0, 50));
                botMessageElement = addBotMessage(response.text);
            }
            
            // 스트림 완료 (오디오는 이미 재생됨)
            console.log('Stream completed');
            
            console.log('sendMessage() completed successfully');
            
            // 완성된 WAV 직접 재생 (병합 불필요)
            async function playCompleteWav(audioBase64) {
                return new Promise((resolve, reject) => {
                    try {
                        // Base64 디코딩
                        const audioData = atob(audioBase64);
                        const audioArray = new Uint8Array(audioData.length);
                        for (let i = 0; i < audioData.length; i++) {
                            audioArray[i] = audioData.charCodeAt(i);
                        }
                        
                        console.log('Playing complete WAV:', {
                            size: audioArray.length,
                            header: String.fromCharCode(audioArray[0], audioArray[1], audioArray[2], audioArray[3])
                        });
                        
                        // Blob으로 변환
                        const blob = new Blob([audioArray], { type: 'audio/wav' });
                        const audioUrl = URL.createObjectURL(blob);
                        
                        // Audio 요소 생성 및 재생
                        const audio = new Audio(audioUrl);
                        audio.volume = 1.0;
                        
                        audio.onended = () => {
                            URL.revokeObjectURL(audioUrl);
                            console.log('Audio playback finished');
                            resolve();
                        };
                        
                        audio.onerror = (error) => {
                            URL.revokeObjectURL(audioUrl);
                            console.error('Audio playback error:', error);
                            resolve(); // 에러가 나도 계속 진행
                        };
                        
                        audio.play().then(() => {
                            console.log('Audio playing, duration:', audio.duration, 'seconds');
                        }).catch(error => {
                            console.error('Audio play failed:', error);
                            resolve();
                        });
                        
                    } catch (error) {
                        console.error('Error processing audio:', error);
                        resolve();
                    }
                });
            }
            
            // 이전 버전 호환용 (사용되지 않음)
            async function playAudioQueue() {
                if (isPlayingAudio || audioQueue.length === 0) return;
                
                isPlayingAudio = true;
                console.log('Merging and playing audio queue, total chunks:', audioQueue.length);
                
                try {
                    // 모든 청크의 PCM 데이터를 수집
                    const pcmDataArrays = [];
                    let sampleRate = 24000;
                    
                    for (const chunk of audioQueue) {
                        if (chunk.audio_base64) {
                            // Base64 디코딩
                            const audioData = atob(chunk.audio_base64);
                            const audioArray = new Uint8Array(audioData.length);
                            for (let i = 0; i < audioData.length; i++) {
                                audioArray[i] = audioData.charCodeAt(i);
                            }
                            
                            // WAV 헤더 확인 및 PCM 데이터 추출 (헤더 44바이트 건너뛰기)
                            const isWav = audioArray.length >= 44 && 
                                String.fromCharCode(audioArray[0], audioArray[1], audioArray[2], audioArray[3]) === 'RIFF';
                            
                            if (isWav && audioArray.length > 44) {
                                // PCM 데이터만 추출 (헤더 제외)
                                pcmDataArrays.push(audioArray.slice(44));
                                sampleRate = chunk.sample_rate || 24000;
                            } else if (audioArray.length > 0) {
                                // WAV가 아니면 전체 데이터 사용
                                pcmDataArrays.push(audioArray);
                            }
                        }
                    }
                    
                    // 오디오 큐 비우기
                    audioQueue.length = 0;
                    
                    if (pcmDataArrays.length === 0) {
                        console.log('No audio data to play');
                        isPlayingAudio = false;
                        return;
                    }
                    
                    // 모든 PCM 데이터 병합
                    const totalLength = pcmDataArrays.reduce((sum, arr) => sum + arr.length, 0);
                    const mergedPcm = new Uint8Array(totalLength);
                    let offset = 0;
                    for (const arr of pcmDataArrays) {
                        mergedPcm.set(arr, offset);
                        offset += arr.length;
                    }
                    
                    console.log('Merged PCM data:', {
                        chunks: pcmDataArrays.length,
                        totalBytes: totalLength,
                        sampleRate: sampleRate,
                        durationSec: (totalLength / 2) / sampleRate  // 16-bit = 2 bytes per sample
                    });
                    
                    // WAV 헤더 생성 및 병합된 오디오 재생
                    const wavData = createWavFromPcm(mergedPcm, sampleRate);
                    await playMergedAudio(wavData);
                    
                } catch (error) {
                    console.error('Error playing merged audio:', error);
                }
                
                isPlayingAudio = false;
            }
            
            // PCM 데이터에 WAV 헤더 추가
            function createWavFromPcm(pcmData, sampleRate) {
                const numChannels = 1;
                const bitsPerSample = 16;
                const byteRate = sampleRate * numChannels * bitsPerSample / 8;
                const blockAlign = numChannels * bitsPerSample / 8;
                const dataSize = pcmData.length;
                
                const buffer = new ArrayBuffer(44 + dataSize);
                const view = new DataView(buffer);
                
                // RIFF 헤더
                writeString(view, 0, 'RIFF');
                view.setUint32(4, 36 + dataSize, true);
                writeString(view, 8, 'WAVE');
                
                // fmt 청크
                writeString(view, 12, 'fmt ');
                view.setUint32(16, 16, true);  // fmt 청크 크기
                view.setUint16(20, 1, true);   // PCM 포맷
                view.setUint16(22, numChannels, true);
                view.setUint32(24, sampleRate, true);
                view.setUint32(28, byteRate, true);
                view.setUint16(32, blockAlign, true);
                view.setUint16(34, bitsPerSample, true);
                
                // data 청크
                writeString(view, 36, 'data');
                view.setUint32(40, dataSize, true);
                
                // PCM 데이터 복사
                const wavArray = new Uint8Array(buffer);
                wavArray.set(pcmData, 44);
                
                return wavArray;
            }
            
            function writeString(view, offset, string) {
                for (let i = 0; i < string.length; i++) {
                    view.setUint8(offset + i, string.charCodeAt(i));
                }
            }
            
            // 병합된 오디오 재생
            async function playMergedAudio(wavData) {
                return new Promise((resolve, reject) => {
                    const blob = new Blob([wavData], { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(blob);
                    const audio = new Audio(audioUrl);
                    audio.volume = 1.0;
                    
                    audio.onended = () => {
                        URL.revokeObjectURL(audioUrl);
                        console.log('Merged audio finished playing');
                        resolve();
                    };
                    
                    audio.onerror = (error) => {
                        URL.revokeObjectURL(audioUrl);
                        console.error('Error playing merged audio:', error);
                        resolve(); // 에러가 발생해도 계속 진행
                    };
                    
                    audio.play().then(() => {
                        console.log('Merged audio started playing, duration:', audio.duration, 'seconds');
                    }).catch(error => {
                        console.error('Error starting merged audio:', error);
                        resolve();
                    });
                });
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name,
                fullError: error
            });
            removeTypingIndicator(loadingMessageId);
            
            // 503 오류인 경우 특별 처리
            if (error.message && error.message.includes('503')) {
                addBotMessage("시스템이 아직 초기화 중입니다. 잠시만 기다려주시면 더 나은 응답을 받으실 수 있습니다.");
                addSystemMessage('💡 초기화가 완료되면 자동으로 정상 작동합니다. 잠시 후 다시 시도해주세요.');
            } else if (error.message && error.message.includes('Failed to fetch')) {
                addSystemMessage('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
                console.error('Network error - 서버 연결 실패');
            } else if (error.message && error.message.includes('404')) {
                addSystemMessage('API 엔드포인트를 찾을 수 없습니다. 서버 설정을 확인해주세요.');
                console.error('404 error - 엔드포인트 없음');
            } else {
                addSystemMessage(`메시지 전송 중 오류가 발생했습니다: ${error.message || '알 수 없는 오류'}`);
            }
        } finally {
            newSendBtn.disabled = false;
            newSendBtn.textContent = '전송';
        }
    };

    // 전송 버튼 클릭 시 오디오 컨텍스트 활성화
    newSendBtn.addEventListener('click', async (e) => {
        console.log('Send button clicked!', {
            disabled: newSendBtn.disabled,
            text: newSendBtn.textContent
        });
        
        e.preventDefault();
        e.stopPropagation();
        
        // 버튼이 비활성화되어 있으면 무시
        if (newSendBtn.disabled) {
            console.log('Send button is disabled, ignoring click');
            return;
        }
        
        try {
            console.log('Activating audio context and sending message...');
            console.log('Step 1: Activating audio context...');
            await activateAudioContext();
            console.log('Step 2: Audio context activated, calling sendMessage()...');
            await sendMessage();
            console.log('Step 3: sendMessage() completed');
        } catch (error) {
            console.error('Error in send button click handler:', error);
            console.error('Error stack:', error.stack);
            // 에러 발생 시에도 버튼 다시 활성화
            newSendBtn.disabled = false;
            newSendBtn.textContent = '전송';
            // 사용자에게 에러 메시지 표시
            UI.showToast('메시지 전송 중 오류가 발생했습니다. 콘솔을 확인해주세요.');
        }
    });
    
    // 버튼이 제대로 연결되었는지 확인
    console.log('Send button event listener attached:', {
        buttonId: newSendBtn.id,
        buttonText: newSendBtn.textContent,
        buttonDisabled: newSendBtn.disabled,
        hasClickListener: true
    });

    newChatInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            
            // 버튼이 비활성화되어 있으면 무시
            if (newSendBtn.disabled) {
                console.log('Send button is disabled, ignoring Enter key');
                return;
            }
            
            try {
                await activateAudioContext();
                await sendMessage();
            } catch (error) {
                console.error('Error in Enter key handler:', error);
            }
        }
    });

    // Auto-resize textarea
    newChatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Back to home (이미 위에서 설정됨)

    // 텍스트/음성 모드 전환 버튼 이벤트 리스너
    const textModeBtn = document.getElementById('text-mode-btn');
    const voiceModeBtn = document.getElementById('voice-mode-btn');
    
    if (textModeBtn) {
        textModeBtn.addEventListener('click', () => {
            const textInputContainer = document.getElementById('text-input-container');
            const voiceInputContainer = document.getElementById('voice-input-container');
            
            if (textInputContainer) textInputContainer.style.display = 'block';
            if (voiceInputContainer) voiceInputContainer.style.display = 'none';
            
            textModeBtn.classList.add('active');
            if (voiceModeBtn) voiceModeBtn.classList.remove('active');
        });
    }
    
    if (voiceModeBtn) {
        voiceModeBtn.addEventListener('click', () => {
            const textInputContainer = document.getElementById('text-input-container');
            const voiceInputContainer = document.getElementById('voice-input-container');
            
            if (textInputContainer) textInputContainer.style.display = 'none';
            if (voiceInputContainer) voiceInputContainer.style.display = 'block';
            
            voiceModeBtn.classList.add('active');
            if (textModeBtn) textModeBtn.classList.remove('active');
        });
    }

    // End session with feedback
    document.getElementById('end-session-btn').addEventListener('click', () => {
        if (confirm('상담을 종료하고 피드백을 작성하시겠습니까?')) {
            initializeFeedbackScreen();
            UI.showScreen('feedback');
        }
    });
}

// ============================================================================
// 감정/위기/치료 기법 표시 함수
// ============================================================================

/**
 * 감정 데이터 표시 (사이드바에 표시)
 */
function displayEmotionData(emotionData) {
    if (!emotionData) return;
    
    const sidebarEmotionDisplay = document.getElementById('sidebar-emotion-display');
    if (!sidebarEmotionDisplay) return;
    
    const primaryEmotion = emotionData.primary_emotion || emotionData.emotion || '중립';
    const intensity = emotionData.intensity || 5;
    const confidence = emotionData.confidence || 0;
    const secondaryEmotions = emotionData.secondary_emotions || [];
    
    const emotionEmojis = {
        '기쁨': '😊', '슬픔': '😢', '분노': '😠', '두려움': '😨', '놀람': '😲',
        '우울': '😔', '불안': '😰', '외로움': '😞', '스트레스': '😫', '중립': '😐',
        '한': '💔', '서러움': '😞', '아쉬움': '😌', '수치심': '😳', '죄책감': '😔'
    };
    
    const emoji = emotionEmojis[primaryEmotion] || '😐';
    const intensityPercent = Math.round((intensity / 10) * 100);
    
    // 강도에 따른 색상
    let intensityColor = '#4CAF50'; // 낮음 (녹색)
    if (intensity >= 7) intensityColor = '#F44336'; // 높음 (빨강)
    else if (intensity >= 5) intensityColor = '#FF9800'; // 중간 (주황)
    
    sidebarEmotionDisplay.innerHTML = `
        <div class="emotion-card">
            <div class="emotion-main">
                <span class="emotion-emoji-large">${emoji}</span>
                <div class="emotion-info">
                    <div class="emotion-name">${primaryEmotion}</div>
                    <div class="emotion-intensity-value">${intensity.toFixed(1)}/10</div>
                </div>
            </div>
            <div class="emotion-intensity-bar-container">
                <div class="emotion-intensity-bar">
                    <div class="emotion-intensity-fill" style="width: ${intensityPercent}%; background: ${intensityColor}"></div>
                </div>
            </div>
            ${secondaryEmotions.length > 0 ? `
                <div class="emotion-secondary">
                    <span class="secondary-label">부가 감정:</span>
                    <span class="secondary-emotions">${secondaryEmotions.slice(0, 3).map(e => emotionEmojis[e] || '•').join(' ')} ${secondaryEmotions.slice(0, 3).join(', ')}</span>
                </div>
            ` : ''}
            ${confidence > 0 ? `
                <div class="emotion-confidence">신뢰도: ${(confidence * 100).toFixed(0)}%</div>
            ` : ''}
        </div>
    `;
    
    // 감정 히스토리에 추가
    if (!AppState.emotionHistory) {
        AppState.emotionHistory = [];
    }
    AppState.emotionHistory.push({
        emotion: primaryEmotion,
        intensity: intensity,
        timestamp: new Date().toISOString()
    });
    
    // 히스토리 차트 업데이트
    updateEmotionHistoryChart();
}

/**
 * 위기 감지 경고 표시 (사이드바에 표시)
 */
function displayCrisisAlert(crisisData) {
    if (!crisisData || !crisisData.crisis_detected) {
        // 위기 감지 해제
        const crisisSection = document.getElementById('crisis-section');
        if (crisisSection) {
            crisisSection.style.display = 'none';
        }
        return;
    }
    
    const crisisLevel = crisisData.crisis_level || 0;
    const levelNames = ['없음', '낮음', '보통', '높음', '위급'];
    const levelColors = ['', '#4CAF50', '#FF9800', '#F44336', '#D32F2F'];
    const levelIcons = ['', '⚠️', '⚠️', '🚨', '🆘'];
    
    const sidebarCrisisDisplay = document.getElementById('sidebar-crisis-display');
    const crisisSection = document.getElementById('crisis-section');
    
    if (!sidebarCrisisDisplay || !crisisSection) return;
    
    // 위기 섹션 표시
    crisisSection.style.display = 'block';
    
    sidebarCrisisDisplay.innerHTML = `
        <div class="crisis-card" style="border-left: 4px solid ${levelColors[crisisLevel] || '#F44336'}">
            <div class="crisis-header">
                <span class="crisis-icon-large">${levelIcons[crisisLevel] || '⚠️'}</span>
                <div class="crisis-level">
                    <strong>${levelNames[crisisLevel] || '위험'} 수준</strong>
                </div>
            </div>
            <div class="crisis-message">
                전문가 상담이 필요합니다
            </div>
            <div class="crisis-resources">
                <a href="tel:1393" class="crisis-link-btn">☎️ 1393</a>
                <a href="tel:1577-0199" class="crisis-link-btn">☎️ 1577-0199</a>
                <a href="tel:119" class="crisis-link-btn emergency">🚨 119</a>
            </div>
        </div>
    `;
}

/**
 * 치료 기법 표시 (사이드바에 표시)
 */
function displayTherapyTechnique(technique) {
    if (!technique) {
        const therapySection = document.getElementById('therapy-section');
        if (therapySection) {
            therapySection.style.display = 'none';
        }
        return;
    }
    
    const sidebarTherapyDisplay = document.getElementById('sidebar-therapy-display');
    const therapySection = document.getElementById('therapy-section');
    
    if (!sidebarTherapyDisplay || !therapySection) return;
    
    const techniqueNames = {
        'active_listening': '적극적 경청',
        'reflection': '감정 반영',
        'validation': '타당화',
        'grounding': '그라운딩',
        'breathing': '호흡법',
        'cognitive_restructuring': '인지 재구성',
        'behavioral_activation': '행동 활성화',
        'mindfulness': '마음챙김',
        'crisis_intervention': '위기 개입'
    };
    
    const techniqueIcons = {
        'active_listening': '👂',
        'reflection': '🪞',
        'validation': '✅',
        'grounding': '🌍',
        'breathing': '🫁',
        'cognitive_restructuring': '🧠',
        'behavioral_activation': '🚶',
        'mindfulness': '🧘',
        'crisis_intervention': '🆘'
    };
    
    const name = techniqueNames[technique] || technique;
    const icon = techniqueIcons[technique] || '💡';
    
    // 치료 섹션 표시
    therapySection.style.display = 'block';
    
    sidebarTherapyDisplay.innerHTML = `
        <div class="therapy-card">
            <span class="therapy-icon-large">${icon}</span>
            <div class="therapy-info">
                <div class="therapy-name">${name}</div>
                <div class="therapy-status">활성화됨</div>
            </div>
        </div>
    `;
}

/**
 * 감정 히스토리 차트 업데이트
 */
function updateEmotionHistoryChart() {
    if (!AppState.emotionHistory || AppState.emotionHistory.length === 0) return;
    
    const historyChart = document.getElementById('emotion-history-chart');
    if (!historyChart) return;
    
    // 최근 10개만 표시
    const recent = AppState.emotionHistory.slice(-10);
    
    if (recent.length === 0) {
        historyChart.innerHTML = '<div class="no-data">감정 히스토리가 없습니다</div>';
        return;
    }
    
    // 간단한 막대 그래프
    const maxIntensity = Math.max(...recent.map(e => e.intensity));
    
    historyChart.innerHTML = recent.map((emotion, index) => {
        const height = (emotion.intensity / maxIntensity) * 100;
        const emotionEmojis = {
            '기쁨': '😊', '슬픔': '😢', '분노': '😠', '두려움': '😨',
            '우울': '😔', '불안': '😰', '외로움': '😞', '스트레스': '😫'
        };
        const emoji = emotionEmojis[emotion.emotion] || '•';
        
        return `
            <div class="history-bar-item">
                <div class="history-bar" style="height: ${height}%">
                    <span class="history-emoji">${emoji}</span>
                </div>
                <div class="history-label">${emotion.intensity.toFixed(1)}</div>
            </div>
        `;
    }).join('');
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

function addBotMessage(text, isStreaming = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    if (isStreaming) {
        messageDiv.classList.add('streaming');
    }
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `
        <div class="message-text">${text}</div>
        <div class="message-time">${UI.formatTime()}</div>
    `;
    messageDiv.innerHTML = `
        <div class="message-avatar">🧠</div>
    `;
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    if (!isStreaming) {
    AppState.chatHistory.push({ role: 'bot', content: text, time: new Date().toISOString() });
    }
    
    return messageDiv;
}

function updateBotMessage(messageElement, text) {
    const textElement = messageElement.querySelector('.message-text');
    if (textElement) {
        textElement.textContent = text;
        scrollToBottom();
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

function addTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    const indicatorId = `typing-${Date.now()}`;
    messageDiv.id = indicatorId;
    messageDiv.className = 'message bot typing-indicator';
    messageDiv.innerHTML = `
        <div class="message-avatar">🧠</div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
            <div class="message-time">입력 중...</div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return indicatorId;
}

function removeTypingIndicator(indicatorId) {
    const indicator = document.getElementById(indicatorId);
    if (indicator) {
        indicator.remove();
    }
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
    if (!AppState.userId) {
        UI.showToast('사용자 ID가 필요합니다');
        return;
    }

    UI.showLoading();
    UI.showScreen('dashboard');

    try {
        const stats = await api.getUserStats(AppState.userId);
        displayUserStats(stats);
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

// 사이드바 토글 기능 제거됨 (항상 펼쳐진 상태로 유지)

document.addEventListener('DOMContentLoaded', async () => {
    // 사이드바 토글 기능 제거됨
    console.log('🧠 마음챗 - Korean Mental Health Counseling System');
    console.log('Initializing application...');

    // Check consent first
    if (!checkConsent()) {
        console.log('⚠️ User consent not found. Showing consent modal...');
        showConsentModal();
    }

    // 서버 초기화 상태 확인 먼저 (버튼 상태 설정)
    await checkServerStatus();

    // Initialize screens (버튼 이벤트 리스너 설정)
    initializeHomeScreen();

    // User menu button (for future dashboard access)
    document.getElementById('user-menu-btn').addEventListener('click', () => {
        UI.showToast('대시보드 기능은 준비 중입니다');
    });

    console.log('✅ Application initialized successfully');
});

// 서버 초기화 상태 확인 및 버튼 제어
let systemReady = false;
let statusCheckInterval = null;

async function checkServerStatus() {
    // 버튼을 매번 다시 찾아서 최신 상태 유지
    let startBtn = document.getElementById('start-chat-btn');
    const statusMessage = document.getElementById('system-status-message');
    
    // 초기 상태: 버튼 비활성화 및 로딩 표시
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.textContent = '시스템 초기화 중...';
        startBtn.classList.add('loading');
    }
    
    if (statusMessage) {
        statusMessage.textContent = '시스템을 초기화하고 있습니다. 잠시만 기다려주세요...';
        statusMessage.style.display = 'block';
    }
    
    // 주기적으로 상태 확인
    const checkStatus = async () => {
        // 매번 버튼을 다시 찾아서 최신 상태 유지
        startBtn = document.getElementById('start-chat-btn');
        
        try {
            const response = await api.checkHealth();
            console.log('Health check response:', response);
            
            // LLM이 준비되었는지 확인
            const isLLMReady = response.components && response.components.llm === true;
            
            if (response.status === 'healthy' && isLLMReady) {
                systemReady = true;
                
                // 상태 확인 중지
                if (statusCheckInterval) {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                }
                
                // 버튼 활성화 (다시 찾아서 업데이트)
                // initializeHomeScreen에서 버튼이 클론되었을 수 있으므로 다시 찾기
                startBtn = document.getElementById('start-chat-btn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.textContent = '상담 시작하기';
                    startBtn.classList.remove('loading');
                    console.log('Button enabled and ready');
                } else {
                    console.warn('start-chat-btn not found after system ready');
                }
                
                if (statusMessage) {
                    statusMessage.textContent = '✅ 시스템이 준비되었습니다. 이제 상담을 시작할 수 있습니다.';
                    statusMessage.style.color = 'var(--success-color, #4caf50)';
                    
                    // 3초 후 메시지 숨기기
                    setTimeout(() => {
                        if (statusMessage) {
                            statusMessage.style.display = 'none';
                        }
                    }, 3000);
                }
                
                console.log('✅ 서버 초기화 완료! LLM 준비됨');
                UI.showToast('시스템이 준비되었습니다. 이제 정상적으로 사용할 수 있습니다.');
                return true;
            } else {
                // 아직 초기화 중
                const components = response.components || {};
                const readyComponents = Object.entries(components)
                    .filter(([_, ready]) => ready === true)
                    .map(([name, _]) => name);
                
                if (statusMessage) {
                    statusMessage.textContent = `시스템 초기화 중... (${readyComponents.length}/${Object.keys(components).length} 컴포넌트 준비됨)`;
                }
                
                console.log('⏳ 아직 초기화 중...', {
                    status: response.status,
                    components: components,
                    llm_ready: isLLMReady
                });
                return false;
            }
        } catch (error) {
            console.error('서버 상태 확인 중 오류:', error);
            if (statusMessage) {
                statusMessage.textContent = '서버 상태를 확인하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                statusMessage.style.color = 'var(--error-color, #f44336)';
            }
            return false;
        }
    };
    
    // 즉시 한 번 확인
    await checkStatus();
    
    // 2초마다 상태 확인 (최대 60초)
    let checkCount = 0;
    const maxChecks = 30; // 30회 * 2초 = 60초
    
    statusCheckInterval = setInterval(async () => {
        checkCount++;
        const isReady = await checkStatus();
        
        if (isReady || checkCount >= maxChecks) {
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
            }
            
            // 최대 시간 초과 시에도 버튼 활성화 (시스템이 부분적으로 작동할 수 있음)
            if (checkCount >= maxChecks && !systemReady) {
                console.warn('⚠️ 시스템 초기화 시간 초과. 부분 기능만 사용 가능할 수 있습니다.');
                // 버튼을 다시 찾아서 업데이트
                startBtn = document.getElementById('start-chat-btn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.textContent = '상담 시작하기 (제한적)';
                    startBtn.classList.remove('loading');
                    // 제한적 모드도 사용 가능하도록 설정
                    systemReady = true;
                    console.log('Button enabled in limited mode');
                }
                if (statusMessage) {
                    statusMessage.textContent = '⚠️ 시스템 초기화가 완료되지 않았습니다. 일부 기능이 제한될 수 있습니다.';
                    statusMessage.style.color = 'var(--warning-color, #ff9800)';
                }
            }
        }
    }, 2000);
}

// TTS 오디오 재생 함수 (전체 오디오)
function playTTSAudio(audioBase64) {
    try {
        // Base64 디코딩
        const audioData = atob(audioBase64);
        const audioArray = new Uint8Array(audioData.length);
        for (let i = 0; i < audioData.length; i++) {
            audioArray[i] = audioData.charCodeAt(i);
        }
        
        // Blob을 사용하여 WAV 파일 생성
        const blob = new Blob([audioArray], { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(blob);
        
        // Audio 요소를 사용하여 재생 (더 안정적)
        const audio = new Audio(audioUrl);
        audio.volume = 1.0; // 볼륨 설정
        
        audio.onloadeddata = () => {
            console.log('TTS audio loaded, duration:', audio.duration, 'seconds');
        };
        
        audio.onplay = () => {
            console.log('TTS audio playing...');
        };
        
        audio.onended = () => {
            console.log('TTS audio finished');
            // 메모리 정리
            URL.revokeObjectURL(audioUrl);
        };
        
        audio.onerror = (error) => {
            console.error('Error playing TTS audio:', error);
            URL.revokeObjectURL(audioUrl);
        };
        
        // 재생 시작
        audio.play().catch(error => {
            console.error('Error starting audio playback:', error);
            URL.revokeObjectURL(audioUrl);
        });
        
    } catch (error) {
        console.error('Error decoding TTS audio:', error);
    }
}

// 오디오 컨텍스트 활성화 (브라우저 자동 재생 정책 대응)
let audioContextActivated = false;
function activateAudioContext() {
    console.log('activateAudioContext() called, audioContextActivated:', audioContextActivated);
    
    if (audioContextActivated) {
        console.log('Audio context already activated, returning immediately');
        return Promise.resolve();
    }
    
    return new Promise((resolve) => {
        console.log('Creating test audio for context activation...');
        
        // 타임아웃 설정 (1초 후 자동으로 진행)
        const timeout = setTimeout(() => {
            console.warn('Audio context activation timeout, continuing anyway...');
            audioContextActivated = true;
            resolve();
        }, 1000);
        
        // 사용자 상호작용이 있었는지 확인하고 오디오 컨텍스트 활성화
        const audio = new Audio();
        audio.volume = 0.01; // 거의 들리지 않는 볼륨으로 테스트
        
        // 빈 오디오 소스로 빠르게 처리
        audio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
        
        const testPlay = audio.play();
        
        if (testPlay !== undefined) {
            console.log('Audio.play() returned promise, waiting...');
            testPlay
                .then(() => {
                    clearTimeout(timeout);
                    console.log('Audio play promise resolved');
                    audio.pause();
                    audioContextActivated = true;
                    console.log('Audio context activated successfully');
                    resolve();
                })
                .catch((err) => {
                    clearTimeout(timeout);
                    console.warn('Audio context activation failed:', err);
                    console.warn('Continuing anyway...');
                    audioContextActivated = true; // 실패해도 표시
                    resolve(); // 실패해도 계속 진행
                });
        } else {
            clearTimeout(timeout);
            console.log('Audio.play() returned undefined, assuming already activated');
            audioContextActivated = true;
            resolve();
        }
    });
}

// 스트리밍 TTS 오디오 청크 재생 함수
async function playTTSAudioChunk(audioBase64, sampleRate = 24000) {
    // 오디오 컨텍스트 활성화 시도
    await activateAudioContext();
    
    return new Promise((resolve, reject) => {
        try {
            if (!audioBase64 || audioBase64.length === 0) {
                console.warn('Empty audio base64 data');
                resolve();
                return;
            }
            
            console.log('Decoding audio chunk, base64 length:', audioBase64.length);
            
            // Base64 디코딩
            const audioData = atob(audioBase64);
            const audioArray = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                audioArray[i] = audioData.charCodeAt(i);
            }
            
            console.log('Audio decoded, array length:', audioArray.length);
            
            // WAV 파일인지 확인 (RIFF 헤더 확인)
            const isWav = audioArray.length >= 4 && 
                         String.fromCharCode(audioArray[0], audioArray[1], audioArray[2], audioArray[3]) === 'RIFF';
            
            console.log('Audio format check - isWav:', isWav, 'first 4 bytes:', 
                String.fromCharCode(audioArray[0], audioArray[1], audioArray[2], audioArray[3]));
            
            // MIME 타입 설정
            const mimeType = isWav ? 'audio/wav' : 'audio/wave';
            
            // Blob을 사용하여 오디오 파일 생성
            const blob = new Blob([audioArray], { type: mimeType });
            const audioUrl = URL.createObjectURL(blob);
            
            console.log('Audio blob created, URL:', audioUrl.substring(0, 50) + '...');
            
            // Audio 요소를 사용하여 재생
            const audio = new Audio(audioUrl);
            audio.volume = 1.0;
            
            // 이벤트 리스너 설정
            const cleanup = () => {
                URL.revokeObjectURL(audioUrl);
                console.log('Audio URL revoked');
            };
            
            let hasStarted = false;
            
            audio.onloadeddata = () => {
                console.log('TTS audio chunk loaded, duration:', audio.duration, 'seconds', 'readyState:', audio.readyState);
            };
            
            audio.oncanplay = () => {
                console.log('Audio can play, readyState:', audio.readyState);
            };
            
            audio.onplay = () => {
                if (!hasStarted) {
                    console.log('TTS audio chunk started playing');
                    hasStarted = true;
                }
            };
            
            audio.onended = () => {
                console.log('TTS audio chunk finished playing');
                cleanup();
                resolve();
            };
            
            audio.onerror = (error) => {
                console.error('Error playing TTS audio chunk:', {
                    error: error,
                    errorCode: audio.error ? audio.error.code : 'unknown',
                    errorMessage: audio.error ? audio.error.message : 'unknown',
                    MIME_type: mimeType,
                    audioLength: audioArray.length,
                    readyState: audio.readyState
                });
                cleanup();
                // 오류가 발생해도 다음 청크 재생 계속
                resolve();
            };
            
            // 재생 시작
            console.log('Attempting to play audio...');
            const playPromise = audio.play();
            
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log('Audio play() promise resolved');
                    })
                    .catch(error => {
                        console.error('Error starting audio chunk playback:', error);
                        console.error('Audio element state:', {
                            readyState: audio.readyState,
                            paused: audio.paused,
                            error: audio.error
                        });
                        cleanup();
                        // 재생 실패해도 다음 청크 재생 계속
                        resolve();
                    });
            } else {
                console.warn('audio.play() returned undefined');
                resolve();
            }
            
        } catch (error) {
            console.error('Error decoding TTS audio chunk:', error);
            console.error('Error stack:', error.stack);
            // 오류가 발생해도 다음 청크 재생 계속
            resolve();
        }
    });
}

// ============================================================================
// 웹캠 감정 감지 모드 설정
// ============================================================================

function setupCameraMode() {
    const cameraVideo = document.getElementById('camera-video');
    const cameraCanvas = document.getElementById('camera-canvas');
    const emotionDisplay = document.getElementById('camera-emotion-display');

    if (!cameraVideo || !cameraCanvas || !emotionDisplay) {
        console.log('Camera elements not found, skipping setup');
        return;
    }

    // 웹캠 감정 감지기 초기화
    if (!faceEmotionDetector) {
        faceEmotionDetector = new FaceEmotionDetector({
            videoElement: cameraVideo,
            canvasElement: cameraCanvas,
            emotionDisplayElement: emotionDisplay,
            detectionInterval: 100,
            minConfidence: 0.5,
            onEmotionDetected: (emotionData) => {
                // 감정이 감지되면 채팅 시스템에 전달
                console.log('Emotion detected:', emotionData);
                // 필요시 채팅 메시지에 감정 정보 포함
            }
        });
    }

    // 자동 시작 함수 정의
    const autoStartCamera = async () => {
        try {
            console.log('Auto-starting camera...');
            const cameraPlaceholder = document.getElementById('camera-placeholder');
            const cameraVideo = document.getElementById('camera-video');
            const emotionDisplay = document.getElementById('camera-emotion-display');
            
            // 초기 상태 메시지 업데이트
            if (emotionDisplay) {
                emotionDisplay.innerHTML = `
                    <div class="no-data">웹캠 초기화 중...</div>
                `;
            }
            
            if (cameraPlaceholder) {
                cameraPlaceholder.style.display = 'none';
            }
            if (cameraVideo) {
                cameraVideo.style.display = 'block';
            }
            
            await faceEmotionDetector.startCamera();
            console.log('Camera started successfully');
            
            // 웹캠 시작 후 메시지 업데이트
            if (emotionDisplay) {
                emotionDisplay.innerHTML = `
                    <div class="no-data">얼굴을 인식하는 중...</div>
                `;
            }
        } catch (error) {
            console.error('Error auto-starting camera:', error);
            const cameraPlaceholder = document.getElementById('camera-placeholder');
            const emotionDisplay = document.getElementById('camera-emotion-display');
            
            if (cameraPlaceholder) {
                cameraPlaceholder.innerHTML = `
                    <div style="text-align: center; color: var(--danger);">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
                        <div>웹캠 접근 실패</div>
                        <div style="font-size: 0.8rem; margin-top: 0.5rem;">브라우저 권한을 확인해주세요</div>
                    </div>
                `;
                cameraPlaceholder.style.display = 'flex';
            }
            
            if (emotionDisplay) {
                emotionDisplay.innerHTML = `
                    <div class="no-data" style="color: var(--danger);">웹캠 접근 실패</div>
                `;
            }
        }
    };

    // 웹캠 항상 자동 시작 (채팅 화면 시작 시)
    setTimeout(() => {
        autoStartCamera();
    }, 500);

    // 텍스트/음성 모드 전환 시에도 웹캠은 계속 실행 (중지하지 않음)
    // 웹캠은 항상 활성화되어 감정 분석 수행
}

// Handle page unload
window.addEventListener('beforeunload', () => {
    // 웹캠 중지
    if (faceEmotionDetector && faceEmotionDetector.isDetecting) {
        faceEmotionDetector.stopCamera();
    }
    
    // Save current state if needed
    if (AppState.currentSession) {
        StorageHelper.set(CONFIG.STORAGE_KEYS.CHAT_HISTORY, AppState.chatHistory);
    }
});
