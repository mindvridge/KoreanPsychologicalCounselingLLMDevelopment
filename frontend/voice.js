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
            // analyserNode를 먼저 연결 (파형 표시용)
            this.sourceNode.connect(this.analyserNode);

            // Setup processor for audio data
            await this.setupAudioProcessor();
            
            // processorNode도 analyserNode에 연결하여 파형 데이터 공유
            if (this.processorNode && this.analyserNode) {
                // analyserNode는 이미 sourceNode에서 데이터를 받고 있으므로
                // processorNode는 별도로 연결하지 않아도 됨
                console.log('Audio nodes connected:', {
                    source: !!this.sourceNode,
                    analyser: !!this.analyserNode,
                    processor: !!this.processorNode
                });
            }

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
                    // 항상 오디오 레벨 업데이트 (파형 표시용)
                    this.updateAudioLevel(event.data);
                    
                    // 녹음 중일 때만 오디오 데이터 전송
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
            const inputData = event.inputBuffer.getChannelData(0);
            // 항상 오디오 레벨 업데이트 (파형 표시용)
            this.updateAudioLevel(inputData);
            
            // 녹음 중일 때만 오디오 데이터 전송
            if (this.isRecording && !this.isPaused) {
                this.processAudioData(new Float32Array(inputData));
            }
        };

        // sourceNode를 processorNode에 연결 (녹음 데이터 처리용)
        // analyserNode는 이미 sourceNode에 연결되어 있으므로 파형은 계속 표시됨
        this.sourceNode.connect(this.processorNode);
        
        // ScriptProcessor가 작동하려면 출력이 필요함
        // 실제 스피커 출력은 하지 않기 위해 dummy destination 사용
        // createMediaStreamDestination()을 사용하면 실제 출력 없이 처리 가능
        const dummyDestination = this.audioContext.createMediaStreamDestination();
        this.processorNode.connect(dummyDestination);
        // dummyDestination은 사용하지 않으므로 연결만 유지 (가비지 컬렉션 방지)
        this._dummyDestination = dummyDestination;
    }

    // =========================================================================
    // WebSocket Connection
    // =========================================================================

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            const wsUrl = `${this.options.wsUrl}/ws/voice/${this.sessionId}`;
            console.log(`Connecting to WebSocket: ${wsUrl}`);

            try {
                this.ws = new WebSocket(wsUrl);
                this.ws.binaryType = 'arraybuffer';

                // 연결 타임아웃 설정
                const connectTimeout = setTimeout(() => {
                    if (!this.isConnected) {
                        console.error('WebSocket connection timeout');
                        this.ws.close();
                        reject(new Error('WebSocket connection timeout'));
                    }
                }, 10000); // 10초 타임아웃

                this.ws.onopen = () => {
                    clearTimeout(connectTimeout);
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;

                    // Send session info
                    try {
                        this.ws.send(JSON.stringify({
                            type: 'session_start',
                            session_id: this.sessionId,
                            counselor_id: this.counselorId,
                            sample_rate: this.options.sampleRate
                        }));
                    } catch (e) {
                        console.error('Failed to send session info:', e);
                    }

                    this.onStateChange({ state: 'connected', message: '서버 연결됨' });
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleWebSocketMessage(event);
                };

                this.ws.onerror = (error) => {
                    clearTimeout(connectTimeout);
                    console.error('WebSocket error:', error);
                    console.error('WebSocket URL:', wsUrl);
                    this.onError({ 
                        type: 'websocket', 
                        message: '연결 오류가 발생했습니다',
                        error: error,
                        url: wsUrl
                    });
                    reject(error);
                };

                this.ws.onclose = (event) => {
                    clearTimeout(connectTimeout);
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

            } catch (error) {
                clearTimeout(connectTimeout);
                console.error('WebSocket connection error:', error);
                this.onError({ 
                    type: 'websocket', 
                    message: '연결 설정 중 오류가 발생했습니다',
                    error: error
                });
                reject(error);
            }

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

            case 'response':
                // 서버에서 보낸 전체 응답 (하위 호환성)
                if (message.data) {
                    const data = message.data;
                    if (data.transcribed_text) {
                        this.onTranscript({
                            text: data.transcribed_text,
                            isFinal: true,
                            confidence: data.confidence || 1.0
                        });
                    }
                    if (data.response_text) {
                        this.onResponse({
                            text: data.response_text,
                            isComplete: true
                        });
                    }
                }
                this.onStateChange({ state: 'ready', message: '대기 중' });
                break;

            case 'tts_start':
                this.onPlaybackStart();
                break;

            case 'tts_end':
                this.onPlaybackEnd();
                break;

            case 'error':
                this.onError({ type: message.error_type || 'unknown', message: message.message || message.data?.error || 'Unknown error' });
                break;

            case 'safety_alert':
                this.onResponse({
                    text: message.message,
                    isSafetyAlert: true,
                    riskLevel: message.risk_level
                });
                break;

            case 'connected':
                // 서버 연결 확인 메시지 (무시하거나 로그만 남김)
                console.log('Server connection confirmed');
                break;

            case 'session_start':
                // 세션 시작 확인
                console.log('Session started:', message.session_id);
                break;

            default:
                console.log('Unknown message type:', message.type, message);
        }
    }

    // =========================================================================
    // Audio Processing
    // =========================================================================

    updateAudioLevel(audioData) {
        // Calculate audio level for visualization (항상 업데이트 - 파형 표시용)
        const level = this.calculateAudioLevel(audioData);
        this.onAudioLevel(level);
    }

    processAudioData(audioData) {
        // Calculate audio level
        const level = this.calculateAudioLevel(audioData);

        // Voice Activity Detection
        if (this.options.vadEnabled) {
            this.detectVoiceActivity(level);
        }

        // Send audio data if speaking or VAD disabled
        // 녹음 중일 때는 VAD를 무시하고 항상 전송 (서버에서 처리)
        if (!this.options.vadEnabled || this.isSpeaking || this.isRecording) {
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
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return; // WebSocket이 열려있지 않으면 전송하지 않음
        }
        
        if (!this.isRecording) {
            return; // 녹음 중이 아니면 전송하지 않음
        }
        
        try {
            // Convert Float32 to Int16 for transmission
            const int16Data = this.float32ToInt16(audioData);
            this.ws.send(int16Data.buffer);
        } catch (error) {
            console.error('Error sending audio data:', error);
            // 에러가 발생해도 계속 녹음은 유지
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

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.onError({ type: 'websocket', message: 'WebSocket이 열려있지 않습니다' });
            return false;
        }

        if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume().catch(error => {
                console.error('Failed to resume audio context:', error);
                this.onError({ type: 'audio', message: '오디오 컨텍스트를 재개할 수 없습니다' });
            });
        }

        try {
            this.isRecording = true;
            this.isPaused = false;
            this.isSpeaking = true; // 녹음 시작 시 즉시 전송 시작

            // 서버에 녹음 시작 알림
            this.ws.send(JSON.stringify({ type: 'start_recording' }));
            console.log('Recording started, sending audio data...');
            
            this.onStateChange({ state: 'recording', message: '녹음 중...' });
            return true;
        } catch (error) {
            console.error('Error starting recording:', error);
            this.onError({ type: 'recording', message: `녹음 시작 실패: ${error.message || error}` });
            this.isRecording = false;
            return false;
        }
    }

    stopRecording() {
        this.isRecording = false;
        this.isSpeaking = false;

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'stop_recording' }));
            console.log('Recording stopped, waiting for response...');
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

        // 시간 도메인 데이터는 fftSize를 사용해야 함 (frequencyBinCount는 주파수 도메인용)
        const dataArray = new Uint8Array(this.analyserNode.fftSize);
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
