/**
 * Voice Application Controller
 * 음성 채팅 UI 통합 모듈
 */

class VoiceApp {
    constructor() {
        // Components
        this.voiceChat = null;
        this.visualizer = null;
        this.fullVisualizer = null;
        this.levelMeter = null;
        this.recordingIndicator = null;
        this.ttsPlayer = null;

        // State
        this.isVoiceMode = false;
        this.isFullScreen = false;
        this.isInitialized = false;
        this.isMuted = false;
        this.eventListenersSetup = false;

        // Session info
        this.sessionId = null;
        this.counselorId = 'default';  // 기본 상담사 ID

        // Bind methods
        this.handleStateChange = this.handleStateChange.bind(this);
        this.handleTranscript = this.handleTranscript.bind(this);
        this.handleResponse = this.handleResponse.bind(this);
        this.handleAudioLevel = this.handleAudioLevel.bind(this);
        this.handleError = this.handleError.bind(this);
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    async initialize(sessionId, counselorId = 'default') {
        this.sessionId = sessionId;
        this.counselorId = counselorId || 'default';

        try {
            // Initialize VoiceChat
            this.voiceChat = new VoiceChat({
                onStateChange: this.handleStateChange,
                onTranscript: this.handleTranscript,
                onResponse: this.handleResponse,
                onAudioLevel: this.handleAudioLevel,
                onError: this.handleError,
                onPlaybackStart: () => this.setCounselorSpeaking(true),
                onPlaybackEnd: () => this.setCounselorSpeaking(false)
            });

            // Initialize Visualizers
            this.setupVisualizers();

            // Initialize TTS Player for fallback
            this.ttsPlayer = new TTSPlayer({
                onStart: () => this.setCounselorSpeaking(true),
                onEnd: () => this.setCounselorSpeaking(false)
            });

            // Setup additional event listeners (record buttons, etc.)
            this.setupRecordEventListeners();

            // Connect to voice service
            const success = await this.voiceChat.initialize(sessionId, this.counselorId);

            if (success) {
                this.isInitialized = true;
                this.enableRecordButton();
                this.updateStatus('ready', '음성 채팅 준비 완료');
            }

            return success;

        } catch (error) {
            console.error('Voice app initialization error:', error);
            this.updateStatus('error', '음성 채팅 초기화 실패');
            return false;
        }
    }

    setupVisualizers() {
        // Chat mode visualizer
        const visualizerCanvas = document.getElementById('voice-visualizer');
        if (visualizerCanvas) {
            this.visualizer = new AudioVisualizer(visualizerCanvas, {
                type: 'waveform',
                color: '#4A90A4',
                backgroundColor: '#1a1a2e'
            });
        }

        // Full screen visualizer
        const fullVisualizerCanvas = document.getElementById('full-visualizer');
        if (fullVisualizerCanvas) {
            this.fullVisualizer = new AudioVisualizer(fullVisualizerCanvas, {
                type: 'circle',
                color: '#4A90A4',
                backgroundColor: '#0f0f1a'
            });
        }

        // Level meter
        const levelMeterContainer = document.getElementById('level-meter-container');
        if (levelMeterContainer) {
            this.levelMeter = new LevelMeter(levelMeterContainer, {
                height: 80
            });
        }

        // Recording indicator
        const recordingContainer = document.getElementById('recording-indicator-container');
        if (recordingContainer) {
            this.recordingIndicator = new RecordingIndicator(recordingContainer);
        }
    }

    // 모드 전환 버튼 리스너 (DOMContentLoaded에서 호출)
    setupModeToggleListeners() {
        if (this.eventListenersSetup) return;

        // Mode toggle buttons
        const textModeBtn = document.getElementById('text-mode-btn');
        const voiceModeBtn = document.getElementById('voice-mode-btn');

        if (textModeBtn) {
            textModeBtn.addEventListener('click', () => this.switchToTextMode());
        }

        if (voiceModeBtn) {
            voiceModeBtn.addEventListener('click', () => this.switchToVoiceMode());
        }

        // Switch to text from full screen
        const switchToTextBtn = document.getElementById('switch-to-text-btn');
        if (switchToTextBtn) {
            switchToTextBtn.addEventListener('click', () => {
                this.isFullScreen = false;
                this.switchToTextMode();
                UI.showScreen('chat');
            });
        }

        // Voice back button
        const voiceBackBtn = document.getElementById('voice-back-btn');
        if (voiceBackBtn) {
            voiceBackBtn.addEventListener('click', () => {
                this.isFullScreen = false;
                UI.showScreen('chat');
            });
        }

        // Voice end button
        const voiceEndBtn = document.getElementById('voice-end-btn');
        if (voiceEndBtn) {
            voiceEndBtn.addEventListener('click', () => {
                if (confirm('음성 상담을 종료하시겠습니까?')) {
                    this.destroy();
                    UI.showScreen('feedback');
                }
            });
        }

        this.eventListenersSetup = true;
    }

    // 녹음 관련 이벤트 리스너 (initialize에서 호출)
    setupRecordEventListeners() {
        // Record buttons
        const recordBtn = document.getElementById('voice-record-btn');
        const fullRecordBtn = document.getElementById('full-record-btn');

        if (recordBtn) {
            recordBtn.addEventListener('click', () => this.toggleRecording());
        }

        if (fullRecordBtn) {
            fullRecordBtn.addEventListener('click', () => this.toggleRecording());
        }

        // Visualizer type selector
        const visualizerSelect = document.getElementById('visualizer-type');
        if (visualizerSelect) {
            visualizerSelect.addEventListener('change', (e) => {
                if (this.visualizer) {
                    this.visualizer.setType(e.target.value);
                }
            });
        }

        // Mute button
        const muteBtn = document.getElementById('mute-btn');
        if (muteBtn) {
            muteBtn.addEventListener('click', () => this.toggleMute());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.isVoiceMode && e.code === 'Space' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                this.toggleRecording();
            }
        });
    }

    // =========================================================================
    // Mode Switching
    // =========================================================================

    async switchToVoiceMode() {
        const textInput = document.getElementById('text-input-container');
        const voiceInput = document.getElementById('voice-input-container');
        const textModeBtn = document.getElementById('text-mode-btn');
        const voiceModeBtn = document.getElementById('voice-mode-btn');

        // Update UI
        if (textInput) textInput.style.display = 'none';
        if (voiceInput) voiceInput.style.display = 'block';
        if (textModeBtn) textModeBtn.classList.remove('active');
        if (voiceModeBtn) voiceModeBtn.classList.add('active');

        this.isVoiceMode = true;

        // 세션 ID가 없으면 AppState에서 가져오기
        if (!this.sessionId && typeof AppState !== 'undefined' && AppState.currentSession) {
            this.sessionId = AppState.currentSession.id;
        }

        // Initialize if needed (counselorId 없이도 동작)
        if (!this.isInitialized && this.sessionId) {
            await this.initialize(this.sessionId, this.counselorId);
        }

        // Start visualizer
        if (this.visualizer && this.voiceChat) {
            this.visualizer.setDataSource(this.voiceChat);
            this.visualizer.start();
        }
    }

    switchToTextMode() {
        const textInput = document.getElementById('text-input-container');
        const voiceInput = document.getElementById('voice-input-container');
        const textModeBtn = document.getElementById('text-mode-btn');
        const voiceModeBtn = document.getElementById('voice-mode-btn');

        // Update UI
        if (textInput) textInput.style.display = 'block';
        if (voiceInput) voiceInput.style.display = 'none';
        if (textModeBtn) textModeBtn.classList.add('active');
        if (voiceModeBtn) voiceModeBtn.classList.remove('active');

        this.isVoiceMode = false;

        // Stop recording if active
        if (this.voiceChat && this.voiceChat.isRecording) {
            this.voiceChat.stopRecording();
        }

        // Stop visualizer
        if (this.visualizer) {
            this.visualizer.stop();
        }
    }

    switchToFullScreen() {
        this.isFullScreen = true;

        // Update counselor info (기본 AI 상담사 표시)
        const avatar = document.getElementById('voice-counselor-avatar');
        const name = document.getElementById('voice-counselor-name');
        const speakingAvatar = document.getElementById('speaking-avatar');

        if (avatar) {
            avatar.textContent = '🤖';
        }
        if (name) {
            name.textContent = '마음챗 AI 상담';
        }
        if (speakingAvatar) {
            speakingAvatar.textContent = '🤖';
        }

        // Start full visualizer
        if (this.fullVisualizer && this.voiceChat) {
            this.fullVisualizer.setDataSource(this.voiceChat);
            this.fullVisualizer.start();
        }

        UI.showScreen('voice');
    }

    // =========================================================================
    // Recording Control
    // =========================================================================

    toggleRecording() {
        if (!this.voiceChat || !this.isInitialized) {
            UI.showToast('음성 채팅이 초기화되지 않았습니다');
            return;
        }

        if (this.voiceChat.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    startRecording() {
        if (this.voiceChat.startRecording()) {
            this.updateRecordButton(true);
            if (this.recordingIndicator) {
                this.recordingIndicator.start();
            }
        }
    }

    stopRecording() {
        this.voiceChat.stopRecording();
        this.updateRecordButton(false);
        if (this.recordingIndicator) {
            this.recordingIndicator.stop();
        }
    }

    updateRecordButton(isRecording) {
        const recordBtn = document.getElementById('voice-record-btn');
        const fullRecordBtn = document.getElementById('full-record-btn');

        const buttons = [recordBtn, fullRecordBtn].filter(Boolean);

        buttons.forEach(btn => {
            if (isRecording) {
                btn.classList.add('recording');
                btn.querySelector('.record-icon').textContent = '⏹️';
                if (btn.querySelector('.record-text')) {
                    btn.querySelector('.record-text').textContent = '중지';
                }
            } else {
                btn.classList.remove('recording');
                btn.querySelector('.record-icon').textContent = '🎤';
                if (btn.querySelector('.record-text')) {
                    btn.querySelector('.record-text').textContent = '말하기';
                }
            }
        });
    }

    enableRecordButton() {
        const recordBtn = document.getElementById('voice-record-btn');
        const fullRecordBtn = document.getElementById('full-record-btn');

        if (recordBtn) recordBtn.disabled = false;
        if (fullRecordBtn) fullRecordBtn.disabled = false;
    }

    // =========================================================================
    // Event Handlers
    // =========================================================================

    handleStateChange(data) {
        console.log('Voice state change:', data);
        this.updateStatus(data.state, data.message);

        // Update connection status in full screen mode
        const connectionStatus = document.getElementById('voice-connection-status');
        if (connectionStatus) {
            connectionStatus.textContent = data.message;
        }
    }

    handleTranscript(data) {
        const liveTranscript = document.getElementById('live-transcript');
        const userTranscript = document.getElementById('user-transcript');

        const text = data.text + (data.isFinal ? '' : '...');

        if (liveTranscript) {
            liveTranscript.textContent = text;
            liveTranscript.classList.toggle('final', data.isFinal);
        }

        if (userTranscript) {
            userTranscript.textContent = text;
        }

        // If final, add to chat history
        if (data.isFinal && data.text.trim()) {
            this.addToChat('user', data.text);
        }
    }

    handleResponse(data) {
        const responseText = document.getElementById('counselor-response-text');

        if (responseText) {
            if (data.isSafetyAlert) {
                responseText.innerHTML = `<span class="safety-alert">${data.text}</span>`;
                responseText.classList.add('safety-alert');
            } else {
                responseText.textContent = data.text;
                responseText.classList.remove('safety-alert');
            }
        }

        // Add to chat if complete
        if (data.isComplete || data.isSafetyAlert) {
            this.addToChat('bot', data.text, data.isSafetyAlert);
        }
    }

    handleAudioLevel(level) {
        if (this.levelMeter) {
            this.levelMeter.update(level * 5); // Scale up for visibility
        }
    }

    handleError(data) {
        console.error('Voice error:', data);
        UI.showToast(data.message || '음성 처리 중 오류가 발생했습니다');
        this.updateStatus('error', data.message);
    }

    // =========================================================================
    // UI Updates
    // =========================================================================

    updateStatus(state, message) {
        const statusIcon = document.getElementById('voice-status-icon');
        const statusText = document.getElementById('voice-status-text');

        if (statusIcon) {
            statusIcon.className = `voice-status-icon ${state}`;
        }

        if (statusText) {
            statusText.textContent = message;
        }
    }

    setCounselorSpeaking(isSpeaking) {
        const speakingIndicator = document.getElementById('counselor-speaking');

        if (speakingIndicator) {
            speakingIndicator.classList.toggle('active', isSpeaking);
        }
    }

    addToChat(role, text, isSafetyAlert = false) {
        // Use the existing chat message functions from app.js
        if (role === 'user') {
            if (typeof addUserMessage === 'function') {
                addUserMessage(text);
            }
        } else {
            if (isSafetyAlert) {
                if (typeof addSystemMessage === 'function') {
                    addSystemMessage(text);
                }
            } else {
                if (typeof addBotMessage === 'function') {
                    addBotMessage(text);
                }
            }
        }
    }

    toggleMute() {
        this.isMuted = !this.isMuted;

        const muteBtn = document.getElementById('mute-btn');
        if (muteBtn) {
            muteBtn.querySelector('span').textContent = this.isMuted ? '🔇' : '🔊';
        }

        // TODO: Actually mute audio playback
    }

    // =========================================================================
    // Cleanup
    // =========================================================================

    destroy() {
        if (this.voiceChat) {
            this.voiceChat.destroy();
            this.voiceChat = null;
        }

        if (this.visualizer) {
            this.visualizer.stop();
        }

        if (this.fullVisualizer) {
            this.fullVisualizer.stop();
        }

        if (this.levelMeter) {
            this.levelMeter.reset();
        }

        if (this.recordingIndicator) {
            this.recordingIndicator.stop();
        }

        if (this.ttsPlayer) {
            this.ttsPlayer.destroy();
        }

        this.isInitialized = false;
        this.isVoiceMode = false;
    }

    // =========================================================================
    // Public API
    // =========================================================================

    setSession(sessionId, counselorId = 'default') {
        this.sessionId = sessionId;
        this.counselorId = counselorId || 'default';
    }

    isReady() {
        return this.isInitialized && this.voiceChat && this.voiceChat.isConnected;
    }
}

// ============================================================================
// Global Instance
// ============================================================================

const voiceApp = new VoiceApp();

// Integration with main app
window.voiceApp = voiceApp;

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // 모드 전환 버튼 리스너 설정 (초기화 없이도 동작)
    voiceApp.setupModeToggleListeners();

    // Watch for chat screen activation
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const chatScreen = document.getElementById('chat-screen');
                if (chatScreen && chatScreen.classList.contains('active')) {
                    // Chat screen is now active - 세션 ID만 설정
                    if (typeof AppState !== 'undefined' && AppState.currentSession) {
                        voiceApp.setSession(AppState.currentSession.id);
                    }
                }
            }
        });
    });

    const chatScreen = document.getElementById('chat-screen');
    if (chatScreen) {
        observer.observe(chatScreen, { attributes: true });
    }
});
