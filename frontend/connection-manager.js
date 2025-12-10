/**
 * Connection Manager
 * WebSocket 연결 안정성 관리
 *
 * 기능:
 * - 자동 재연결 (지수 백오프)
 * - 세션 복구
 * - 하트비트/핑-퐁
 * - 연결 상태 모니터링
 * - 오프라인 큐
 */

class ConnectionManager {
    constructor(options = {}) {
        this.options = {
            url: options.url || CONFIG.VOICE_WS_URL,
            reconnectAttempts: options.reconnectAttempts || 10,
            reconnectBaseDelay: options.reconnectBaseDelay || 1000,
            reconnectMaxDelay: options.reconnectMaxDelay || 30000,
            heartbeatInterval: options.heartbeatInterval || 5000,
            heartbeatTimeout: options.heartbeatTimeout || 10000,
            sessionRecoveryEnabled: options.sessionRecoveryEnabled !== false,
            offlineQueueEnabled: options.offlineQueueEnabled !== false,
            ...options
        };

        // 상태
        this.ws = null;
        this.state = 'disconnected'; // disconnected, connecting, connected, reconnecting
        this.sessionId = null;
        this.reconnectAttempt = 0;
        this.lastConnectedAt = null;

        // 하트비트
        this.heartbeatTimer = null;
        this.heartbeatTimeoutTimer = null;
        this.lastPongAt = null;

        // 세션 복구
        this.sessionData = null;
        this.conversationHistory = [];

        // 오프라인 큐
        this.offlineQueue = [];
        this.maxQueueSize = 100;

        // 콜백
        this.onStateChange = options.onStateChange || (() => {});
        this.onMessage = options.onMessage || (() => {});
        this.onError = options.onError || (() => {});
        this.onSessionRecovered = options.onSessionRecovered || (() => {});

        // 네트워크 상태 모니터링
        this.setupNetworkMonitoring();
    }

    // =========================================================================
    // 연결 관리
    // =========================================================================

    async connect(sessionId = null) {
        if (this.state === 'connected' || this.state === 'connecting') {
            return;
        }

        this.sessionId = sessionId || this.generateSessionId();
        this.state = 'connecting';
        this.onStateChange(this.state, '연결 중...');

        try {
            const wsUrl = `${this.options.url}/ws/voice/${this.sessionId}`;
            this.ws = new WebSocket(wsUrl);
            this.ws.binaryType = 'arraybuffer';

            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (error) => this.handleError(error);
            this.ws.onclose = (event) => this.handleClose(event);

        } catch (error) {
            this.handleError(error);
        }
    }

    disconnect() {
        this.stopHeartbeat();
        this.saveSessionForRecovery();

        if (this.ws) {
            this.ws.close(1000, 'User disconnect');
            this.ws = null;
        }

        this.state = 'disconnected';
        this.onStateChange(this.state, '연결 종료');
    }

    // =========================================================================
    // 이벤트 핸들러
    // =========================================================================

    handleOpen() {
        console.log('WebSocket connected');

        this.state = 'connected';
        this.reconnectAttempt = 0;
        this.lastConnectedAt = Date.now();

        // 세션 복구 시도
        if (this.sessionData && this.options.sessionRecoveryEnabled) {
            this.attemptSessionRecovery();
        } else {
            this.sendSessionStart();
        }

        // 하트비트 시작
        this.startHeartbeat();

        // 오프라인 큐 전송
        this.flushOfflineQueue();

        this.onStateChange(this.state, '연결됨');
    }

    handleMessage(event) {
        // 바이너리 (오디오) vs 텍스트 (JSON)
        if (event.data instanceof ArrayBuffer) {
            this.onMessage({ type: 'audio', data: event.data });
        } else {
            try {
                const message = JSON.parse(event.data);

                // Pong 처리
                if (message.type === 'pong') {
                    this.handlePong(message);
                    return;
                }

                // 세션 복구 응답
                if (message.type === 'session_recovered') {
                    this.handleSessionRecovered(message);
                    return;
                }

                this.onMessage(message);

            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        }
    }

    handleError(error) {
        console.error('WebSocket error:', error);
        this.onError({ type: 'connection', message: '연결 오류' });
    }

    handleClose(event) {
        console.log('WebSocket closed:', event.code, event.reason);

        this.stopHeartbeat();
        this.saveSessionForRecovery();

        // 정상 종료가 아니면 재연결 시도
        if (event.code !== 1000) {
            this.attemptReconnect();
        } else {
            this.state = 'disconnected';
            this.onStateChange(this.state, '연결 종료');
        }
    }

    // =========================================================================
    // 재연결
    // =========================================================================

    attemptReconnect() {
        if (this.reconnectAttempt >= this.options.reconnectAttempts) {
            this.state = 'disconnected';
            this.onStateChange(this.state, '재연결 실패');
            this.onError({ type: 'reconnect_failed', message: '재연결에 실패했습니다' });
            return;
        }

        this.state = 'reconnecting';
        this.reconnectAttempt++;

        // 지수 백오프 계산
        const delay = Math.min(
            this.options.reconnectBaseDelay * Math.pow(2, this.reconnectAttempt - 1),
            this.options.reconnectMaxDelay
        );

        // 지터 추가 (±20%)
        const jitter = delay * (0.8 + Math.random() * 0.4);

        this.onStateChange(this.state, `재연결 중... (${this.reconnectAttempt}/${this.options.reconnectAttempts})`);

        console.log(`Reconnecting in ${Math.round(jitter)}ms (attempt ${this.reconnectAttempt})`);

        setTimeout(() => {
            if (this.state === 'reconnecting') {
                this.connect(this.sessionId);
            }
        }, jitter);
    }

    // =========================================================================
    // 하트비트
    // =========================================================================

    startHeartbeat() {
        this.stopHeartbeat();

        this.heartbeatTimer = setInterval(() => {
            this.sendPing();
        }, this.options.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }

        if (this.heartbeatTimeoutTimer) {
            clearTimeout(this.heartbeatTimeoutTimer);
            this.heartbeatTimeoutTimer = null;
        }
    }

    sendPing() {
        if (this.state !== 'connected') return;

        const pingTime = Date.now();

        this.send({
            type: 'ping',
            timestamp: pingTime
        });

        // 타임아웃 설정
        this.heartbeatTimeoutTimer = setTimeout(() => {
            console.warn('Heartbeat timeout');
            this.handleHeartbeatTimeout();
        }, this.options.heartbeatTimeout);
    }

    handlePong(message) {
        this.lastPongAt = Date.now();

        if (this.heartbeatTimeoutTimer) {
            clearTimeout(this.heartbeatTimeoutTimer);
            this.heartbeatTimeoutTimer = null;
        }

        // RTT 계산
        if (message.timestamp) {
            const rtt = Date.now() - message.timestamp;
            console.debug(`Heartbeat RTT: ${rtt}ms`);
        }
    }

    handleHeartbeatTimeout() {
        console.warn('Connection appears dead, attempting reconnect');

        if (this.ws) {
            this.ws.close(4000, 'Heartbeat timeout');
        }

        this.attemptReconnect();
    }

    // =========================================================================
    // 세션 복구
    // =========================================================================

    saveSessionForRecovery() {
        if (!this.options.sessionRecoveryEnabled) return;

        this.sessionData = {
            sessionId: this.sessionId,
            conversationHistory: this.conversationHistory.slice(-20), // 최근 20개
            savedAt: Date.now()
        };

        // 로컬 스토리지에도 저장
        try {
            localStorage.setItem(
                'voice_session_recovery',
                JSON.stringify(this.sessionData)
            );
        } catch (e) {
            console.warn('Failed to save session to localStorage:', e);
        }
    }

    loadSessionForRecovery() {
        try {
            const saved = localStorage.getItem('voice_session_recovery');
            if (saved) {
                const data = JSON.parse(saved);

                // 1시간 이내 세션만 복구
                if (Date.now() - data.savedAt < 60 * 60 * 1000) {
                    return data;
                }
            }
        } catch (e) {
            console.warn('Failed to load session from localStorage:', e);
        }
        return null;
    }

    attemptSessionRecovery() {
        const savedSession = this.sessionData || this.loadSessionForRecovery();

        if (savedSession) {
            console.log('Attempting session recovery:', savedSession.sessionId);

            this.send({
                type: 'session_recover',
                session_id: savedSession.sessionId,
                conversation_history: savedSession.conversationHistory
            });
        } else {
            this.sendSessionStart();
        }
    }

    handleSessionRecovered(message) {
        console.log('Session recovered:', message);

        this.conversationHistory = message.conversation_history || [];
        this.sessionData = null;

        // 로컬 스토리지 정리
        localStorage.removeItem('voice_session_recovery');

        this.onSessionRecovered({
            sessionId: this.sessionId,
            historyLength: this.conversationHistory.length
        });
    }

    sendSessionStart() {
        this.send({
            type: 'session_start',
            session_id: this.sessionId,
            sample_rate: CONFIG.VOICE?.SAMPLE_RATE || 16000,
            voice_profile: CONFIG.VOICE?.DEFAULT_VOICE_PROFILE || 'seoyun_counselor'
        });
    }

    // =========================================================================
    // 메시지 전송
    // =========================================================================

    send(data) {
        if (this.state !== 'connected' || !this.ws) {
            // 오프라인 큐에 추가
            if (this.options.offlineQueueEnabled && typeof data !== 'object') {
                return; // 바이너리는 큐잉 안 함
            }

            this.queueMessage(data);
            return false;
        }

        try {
            if (data instanceof ArrayBuffer || data instanceof Uint8Array) {
                this.ws.send(data);
            } else {
                this.ws.send(JSON.stringify(data));
            }
            return true;

        } catch (e) {
            console.error('Send error:', e);
            this.queueMessage(data);
            return false;
        }
    }

    sendAudio(audioData) {
        if (this.state !== 'connected' || !this.ws) {
            return false;
        }

        try {
            this.ws.send(audioData);
            return true;
        } catch (e) {
            console.error('Audio send error:', e);
            return false;
        }
    }

    // =========================================================================
    // 오프라인 큐
    // =========================================================================

    queueMessage(data) {
        if (!this.options.offlineQueueEnabled) return;

        // 큐 크기 제한
        if (this.offlineQueue.length >= this.maxQueueSize) {
            this.offlineQueue.shift(); // 오래된 것 제거
        }

        this.offlineQueue.push({
            data: data,
            timestamp: Date.now()
        });
    }

    flushOfflineQueue() {
        if (this.offlineQueue.length === 0) return;

        console.log(`Flushing ${this.offlineQueue.length} queued messages`);

        // 오래된 메시지 제거 (30초 이상)
        const now = Date.now();
        this.offlineQueue = this.offlineQueue.filter(
            item => now - item.timestamp < 30000
        );

        // 전송
        while (this.offlineQueue.length > 0) {
            const item = this.offlineQueue.shift();
            this.send(item.data);
        }
    }

    // =========================================================================
    // 네트워크 모니터링
    // =========================================================================

    setupNetworkMonitoring() {
        // 온라인/오프라인 이벤트
        window.addEventListener('online', () => {
            console.log('Network online');
            if (this.state === 'disconnected' || this.state === 'reconnecting') {
                this.connect(this.sessionId);
            }
        });

        window.addEventListener('offline', () => {
            console.log('Network offline');
            this.onStateChange('disconnected', '네트워크 연결 끊김');
        });

        // 페이지 가시성 변경
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // 탭이 다시 활성화되면 연결 확인
                if (this.state === 'connected') {
                    this.sendPing();
                } else if (this.state === 'disconnected') {
                    this.connect(this.sessionId);
                }
            }
        });
    }

    // =========================================================================
    // 유틸리티
    // =========================================================================

    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    addToHistory(role, content) {
        this.conversationHistory.push({
            role: role,
            content: content,
            timestamp: new Date().toISOString()
        });

        // 최대 50개 유지
        if (this.conversationHistory.length > 50) {
            this.conversationHistory = this.conversationHistory.slice(-50);
        }
    }

    getState() {
        return {
            state: this.state,
            sessionId: this.sessionId,
            reconnectAttempt: this.reconnectAttempt,
            lastConnectedAt: this.lastConnectedAt,
            queueLength: this.offlineQueue.length
        };
    }

    destroy() {
        this.stopHeartbeat();
        this.saveSessionForRecovery();

        if (this.ws) {
            this.ws.close(1000, 'Destroy');
            this.ws = null;
        }
    }
}


// Export
window.ConnectionManager = ConnectionManager;
