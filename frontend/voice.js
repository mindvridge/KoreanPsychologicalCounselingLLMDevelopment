/**
 * Voice Chat Module - 실시간 WebSocket 스트리밍
 * 마음챗 음성 상담 시스템
 */

class VoiceChat {
    constructor(options = {}) {
        this.options = {
            wsUrl: options.wsUrl || this.getWebSocketUrl(),
            sampleRate: options.sampleRate || 16000,
            bufferSize: options.bufferSize || 4096,
            silenceThreshold: options.silenceThreshold || 0.01,
            silenceDuration: options.silenceDuration || 1500, // ms
            vadEnabled: options.vadEnabled !== false,
            ...options
        };

        // State
        this.isRecording = false;
        this.isConnected = false;
        this.isPaused = false;
        this.sessionId = null;
        this.counselorId = null;

        // Audio components
        this.audioContext = null;
        this.mediaStream = null;
        this.mediaRecorder = null;
        this.analyserNode = null;
        this.sourceNode = null;
        this.processorNode = null;

        // WebSocket
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;

        // Audio playback queue
        this.audioQueue = [];
        this.isPlaying = false;

        // VAD (Voice Activity Detection)
        this.silenceStart = null;
        this.isSpeaking = false;

        // Callbacks
        this.onStateChange = options.onStateChange || (() => {});
        this.onTranscript = options.onTranscript || (() => {});
        this.onResponse = options.onResponse || (() => {});
        this.onAudioLevel = options.onAudioLevel || (() => {});
        this.onError = options.onError || (() => {});
        this.onPlaybackStart = options.onPlaybackStart || (() => {});
        this.onPlaybackEnd = options.onPlaybackEnd || (() => {});
    }

    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = 8001; // Voice API port
        return `${protocol}//${host}:${port}`;
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    async initialize(sessionId, counselorId) {
        this.sessionId = sessionId;
        this.counselorId = counselorId;

        try {
            // Request microphone permission
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.options.sampleRate,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Setup audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: this.options.sampleRate
            });

            // Create analyser for visualization
            this.analyserNode = this.audioContext.createAnalyser();
            this.analyserNode.fftSize = 2048;
            this.analyserNode.smoothingTimeConstant = 0.8;

            // Connect nodes
            this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.sourceNode.connect(this.analyserNode);

            // Setup processor for audio data
            await this.setupAudioProcessor();

            // Connect to WebSocket
            await this.connectWebSocket();

            this.onStateChange({ state: 'initialized', message: '음성 채팅 준비 완료' });
            return true;

        } catch (error) {
            console.error('Voice initialization error:', error);
            this.onError({ type: 'init', message: this.getErrorMessage(error) });
            return false;
        }
    }

    async setupAudioProcessor() {
        // Use AudioWorklet if available, fallback to ScriptProcessor
        if (this.audioContext.audioWorklet) {
            try {
                await this.audioContext.audioWorklet.addModule(this.createAudioWorkletProcessor());
                this.processorNode = new AudioWorkletNode(this.audioContext, 'voice-processor');
                this.processorNode.port.onmessage = (event) => {
                    if (this.isRecording && !this.isPaused) {
                        this.processAudioData(event.data);
                    }
                };
                this.sourceNode.connect(this.processorNode);
            } catch (e) {
                console.warn('AudioWorklet not available, using ScriptProcessor');
                this.setupScriptProcessor();
            }
        } else {
            this.setupScriptProcessor();
        }
    }

    createAudioWorkletProcessor() {
        const processorCode = `
            class VoiceProcessor extends AudioWorkletProcessor {
                constructor() {
                    super();
                    this.bufferSize = 4096;
                    this.buffer = new Float32Array(this.bufferSize);
                    this.bufferIndex = 0;
                }

                process(inputs, outputs, parameters) {
                    const input = inputs[0];
                    if (input.length > 0) {
                        const channelData = input[0];
                        for (let i = 0; i < channelData.length; i++) {
                            this.buffer[this.bufferIndex++] = channelData[i];
                            if (this.bufferIndex >= this.bufferSize) {
                                this.port.postMessage(this.buffer.slice());
                                this.bufferIndex = 0;
                            }
                        }
                    }
                    return true;
                }
            }
            registerProcessor('voice-processor', VoiceProcessor);
        `;
        const blob = new Blob([processorCode], { type: 'application/javascript' });
        return URL.createObjectURL(blob);
    }

    setupScriptProcessor() {
        this.processorNode = this.audioContext.createScriptProcessor(
            this.options.bufferSize, 1, 1
        );

        this.processorNode.onaudioprocess = (event) => {
            if (this.isRecording && !this.isPaused) {
                const inputData = event.inputBuffer.getChannelData(0);
                this.processAudioData(new Float32Array(inputData));
            }
        };

        this.sourceNode.connect(this.processorNode);
        this.processorNode.connect(this.audioContext.destination);
    }

    // =========================================================================
    // WebSocket Connection
    // =========================================================================

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            const wsUrl = `${this.options.wsUrl}/ws/voice/${this.sessionId}`;

            this.ws = new WebSocket(wsUrl);
            this.ws.binaryType = 'arraybuffer';

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;

                // Send session info
                this.ws.send(JSON.stringify({
                    type: 'session_start',
                    session_id: this.sessionId,
                    counselor_id: this.counselorId,
                    sample_rate: this.options.sampleRate
                }));

                this.onStateChange({ state: 'connected', message: '서버 연결됨' });
                resolve();
            };

            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.onError({ type: 'websocket', message: '연결 오류가 발생했습니다' });
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.isConnected = false;
                this.onStateChange({ state: 'disconnected', message: '연결 끊김' });

                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connectWebSocket();
                    }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
                }
            };

            // Timeout
            setTimeout(() => {
                if (!this.isConnected) {
                    reject(new Error('WebSocket connection timeout'));
                }
            }, 10000);
        });
    }

    handleWebSocketMessage(event) {
        if (event.data instanceof ArrayBuffer) {
            // Audio data received
            this.queueAudioPlayback(event.data);
        } else {
            // JSON message
            try {
                const message = JSON.parse(event.data);
                this.handleJsonMessage(message);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        }
    }

    handleJsonMessage(message) {
        switch (message.type) {
            case 'transcript':
                this.onTranscript({
                    text: message.text,
                    isFinal: message.is_final,
                    confidence: message.confidence
                });
                break;

            case 'response_start':
                this.onStateChange({ state: 'responding', message: '응답 생성 중...' });
                break;

            case 'response_text':
                this.onResponse({
                    text: message.text,
                    isComplete: message.is_complete
                });
                break;

            case 'response_end':
                this.onStateChange({ state: 'ready', message: '대기 중' });
                break;

            case 'tts_start':
                this.onPlaybackStart();
                break;

            case 'tts_end':
                this.onPlaybackEnd();
                break;

            case 'error':
                this.onError({ type: message.error_type, message: message.message });
                break;

            case 'safety_alert':
                this.onResponse({
                    text: message.message,
                    isSafetyAlert: true,
                    riskLevel: message.risk_level
                });
                break;

            default:
                console.log('Unknown message type:', message.type);
        }
    }

    // =========================================================================
    // Audio Processing
    // =========================================================================

    processAudioData(audioData) {
        // Calculate audio level for visualization
        const level = this.calculateAudioLevel(audioData);
        this.onAudioLevel(level);

        // Voice Activity Detection
        if (this.options.vadEnabled) {
            this.detectVoiceActivity(level);
        }

        // Send audio data if speaking or VAD disabled
        if (!this.options.vadEnabled || this.isSpeaking) {
            this.sendAudioData(audioData);
        }
    }

    calculateAudioLevel(audioData) {
        let sum = 0;
        for (let i = 0; i < audioData.length; i++) {
            sum += audioData[i] * audioData[i];
        }
        return Math.sqrt(sum / audioData.length);
    }

    detectVoiceActivity(level) {
        if (level > this.options.silenceThreshold) {
            // Voice detected
            this.isSpeaking = true;
            this.silenceStart = null;
        } else {
            // Silence detected
            if (this.isSpeaking) {
                if (!this.silenceStart) {
                    this.silenceStart = Date.now();
                } else if (Date.now() - this.silenceStart > this.options.silenceDuration) {
                    // End of speech detected
                    this.isSpeaking = false;
                    this.sendEndOfSpeech();
                }
            }
        }
    }

    sendAudioData(audioData) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            // Convert Float32 to Int16 for transmission
            const int16Data = this.float32ToInt16(audioData);
            this.ws.send(int16Data.buffer);
        }
    }

    sendEndOfSpeech() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'end_of_speech' }));
        }
    }

    float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array;
    }

    // =========================================================================
    // Audio Playback
    // =========================================================================

    queueAudioPlayback(audioData) {
        this.audioQueue.push(audioData);
        if (!this.isPlaying) {
            this.playNextAudio();
        }
    }

    async playNextAudio() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }

        this.isPlaying = true;
        const audioData = this.audioQueue.shift();

        try {
            const audioBuffer = await this.audioContext.decodeAudioData(audioData.slice(0));
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            source.onended = () => {
                this.playNextAudio();
            };

            source.start();
        } catch (error) {
            console.error('Audio playback error:', error);
            this.playNextAudio(); // Continue with next audio
        }
    }

    // =========================================================================
    // Recording Controls
    // =========================================================================

    startRecording() {
        if (!this.isConnected) {
            this.onError({ type: 'state', message: '서버에 연결되어 있지 않습니다' });
            return false;
        }

        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }

        this.isRecording = true;
        this.isPaused = false;

        this.ws.send(JSON.stringify({ type: 'start_recording' }));
        this.onStateChange({ state: 'recording', message: '녹음 중...' });

        return true;
    }

    stopRecording() {
        this.isRecording = false;

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'stop_recording' }));
        }

        this.onStateChange({ state: 'processing', message: '처리 중...' });
    }

    pauseRecording() {
        this.isPaused = true;
        this.onStateChange({ state: 'paused', message: '일시 정지' });
    }

    resumeRecording() {
        this.isPaused = false;
        this.onStateChange({ state: 'recording', message: '녹음 중...' });
    }

    toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    // =========================================================================
    // Visualization Data
    // =========================================================================

    getFrequencyData() {
        if (!this.analyserNode) return new Uint8Array(0);

        const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
        this.analyserNode.getByteFrequencyData(dataArray);
        return dataArray;
    }

    getTimeDomainData() {
        if (!this.analyserNode) return new Uint8Array(0);

        const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
        this.analyserNode.getByteTimeDomainData(dataArray);
        return dataArray;
    }

    // =========================================================================
    // Cleanup
    // =========================================================================

    destroy() {
        this.stopRecording();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.isConnected = false;
        this.onStateChange({ state: 'destroyed', message: '음성 채팅 종료' });
    }

    // =========================================================================
    // Error Handling
    // =========================================================================

    getErrorMessage(error) {
        if (error.name === 'NotAllowedError') {
            return '마이크 접근이 거부되었습니다. 브라우저 설정에서 마이크 권한을 허용해주세요.';
        } else if (error.name === 'NotFoundError') {
            return '마이크를 찾을 수 없습니다. 마이크가 연결되어 있는지 확인해주세요.';
        } else if (error.name === 'NotReadableError') {
            return '마이크에 접근할 수 없습니다. 다른 앱에서 사용 중일 수 있습니다.';
        }
        return error.message || '알 수 없는 오류가 발생했습니다.';
    }
}

// ============================================================================
// Text-to-Speech Player (for text responses)
// ============================================================================

class TTSPlayer {
    constructor(options = {}) {
        this.apiUrl = options.apiUrl || '/api/v1/voice/synthesize';
        this.voiceProfile = options.voiceProfile || 'default_counselor';
        this.audioContext = null;
        this.isPlaying = false;
        this.queue = [];

        this.onStart = options.onStart || (() => {});
        this.onEnd = options.onEnd || (() => {});
        this.onError = options.onError || (() => {});
    }

    async initialize() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    async speak(text, options = {}) {
        if (!this.audioContext) {
            await this.initialize();
        }

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    voice_profile: options.voiceProfile || this.voiceProfile,
                    emotion: options.emotion || 'calm',
                    speed: options.speed || 1.0
                })
            });

            if (!response.ok) {
                throw new Error('TTS request failed');
            }

            const audioData = await response.arrayBuffer();
            this.queue.push(audioData);

            if (!this.isPlaying) {
                this.playNext();
            }

        } catch (error) {
            console.error('TTS error:', error);
            this.onError(error);
        }
    }

    async playNext() {
        if (this.queue.length === 0) {
            this.isPlaying = false;
            this.onEnd();
            return;
        }

        this.isPlaying = true;
        this.onStart();

        const audioData = this.queue.shift();

        try {
            const audioBuffer = await this.audioContext.decodeAudioData(audioData);
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            source.onended = () => {
                this.playNext();
            };

            source.start();
        } catch (error) {
            console.error('Audio playback error:', error);
            this.playNext();
        }
    }

    stop() {
        this.queue = [];
        this.isPlaying = false;
    }

    destroy() {
        this.stop();
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }
}

// Export for use
window.VoiceChat = VoiceChat;
window.TTSPlayer = TTSPlayer;
