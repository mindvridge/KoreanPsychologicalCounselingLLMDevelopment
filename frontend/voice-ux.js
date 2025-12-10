/**
 * Voice UX Enhancements
 * 음성 채팅 사용자 경험 개선
 *
 * 기능:
 * - 자동 음성 감지 (Hands-free 모드)
 * - 감정 분석 표시
 * - 대기 시간 표시
 * - 터치 제스처 지원
 * - 접근성 개선
 */

// ============================================================================
// 자동 음성 감지 (Hands-Free Mode)
// ============================================================================

class AutoVoiceDetector {
    constructor(options = {}) {
        this.options = {
            enabled: options.enabled || false,
            threshold: options.threshold || 0.02,
            silenceDuration: options.silenceDuration || 1500, // ms
            minSpeechDuration: options.minSpeechDuration || 500, // ms
            cooldownDuration: options.cooldownDuration || 1000, // ms (응답 후 대기)
            ...options
        };

        // 상태
        this.isListening = false;
        this.isSpeaking = false;
        this.speechStartTime = null;
        this.silenceStartTime = null;
        this.inCooldown = false;

        // 콜백
        this.onSpeechStart = options.onSpeechStart || (() => {});
        this.onSpeechEnd = options.onSpeechEnd || (() => {});
        this.onStateChange = options.onStateChange || (() => {});

        // 분석기
        this.analyser = null;
        this.dataArray = null;
    }

    /**
     * 분석기 설정
     */
    setAnalyser(analyser) {
        this.analyser = analyser;
        this.dataArray = new Float32Array(analyser.frequencyBinCount);
    }

    /**
     * 감지 시작
     */
    start() {
        if (!this.analyser) {
            console.error('Analyser not set');
            return;
        }

        this.isListening = true;
        this.onStateChange('listening');
        this.detectLoop();
    }

    /**
     * 감지 중지
     */
    stop() {
        this.isListening = false;
        this.isSpeaking = false;
        this.onStateChange('stopped');
    }

    /**
     * 쿨다운 시작 (응답 재생 중)
     */
    startCooldown() {
        this.inCooldown = true;
        setTimeout(() => {
            this.inCooldown = false;
        }, this.options.cooldownDuration);
    }

    /**
     * 감지 루프
     */
    detectLoop() {
        if (!this.isListening) return;

        const level = this.getAudioLevel();
        const now = Date.now();

        if (level > this.options.threshold) {
            // 음성 감지됨
            if (!this.isSpeaking && !this.inCooldown) {
                // 발화 시작
                this.isSpeaking = true;
                this.speechStartTime = now;
                this.silenceStartTime = null;
                this.onSpeechStart();
                this.onStateChange('speaking');
            } else {
                // 발화 계속
                this.silenceStartTime = null;
            }
        } else {
            // 침묵
            if (this.isSpeaking) {
                if (!this.silenceStartTime) {
                    this.silenceStartTime = now;
                }

                const silenceDuration = now - this.silenceStartTime;
                const speechDuration = now - this.speechStartTime;

                // 침묵이 임계값 초과 & 최소 발화 시간 충족
                if (silenceDuration >= this.options.silenceDuration &&
                    speechDuration >= this.options.minSpeechDuration) {
                    // 발화 종료
                    this.isSpeaking = false;
                    this.onSpeechEnd();
                    this.onStateChange('processing');
                    this.startCooldown();
                }
            }
        }

        requestAnimationFrame(() => this.detectLoop());
    }

    /**
     * 오디오 레벨 계산
     */
    getAudioLevel() {
        if (!this.analyser) return 0;

        this.analyser.getFloatTimeDomainData(this.dataArray);

        let sum = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
            sum += this.dataArray[i] * this.dataArray[i];
        }
        return Math.sqrt(sum / this.dataArray.length);
    }

    /**
     * 활성화/비활성화 토글
     */
    toggle() {
        this.options.enabled = !this.options.enabled;
        return this.options.enabled;
    }
}


// ============================================================================
// 감정 분석 표시
// ============================================================================

class EmotionDisplay {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.getElementById(container)
            : container;

        this.options = {
            showEmoji: options.showEmoji !== false,
            showLabel: options.showLabel !== false,
            animate: options.animate !== false,
            ...options
        };

        // 감정 매핑
        this.emotionMap = {
            // 긍정적 감정
            happy: { emoji: '😊', label: '기쁨', color: '#FFD93D' },
            hopeful: { emoji: '🌟', label: '희망', color: '#7ED6DF' },
            grateful: { emoji: '🙏', label: '감사', color: '#A8E6CF' },
            relieved: { emoji: '😌', label: '안도', color: '#B8E6CF' },
            encouraged: { emoji: '💪', label: '격려됨', color: '#74B9FF' },

            // 부정적 감정
            sad: { emoji: '😢', label: '슬픔', color: '#74B9FF' },
            anxious: { emoji: '😰', label: '불안', color: '#FDCB6E' },
            angry: { emoji: '😤', label: '분노', color: '#FF7675' },
            frustrated: { emoji: '😫', label: '좌절', color: '#E17055' },
            lonely: { emoji: '😔', label: '외로움', color: '#A29BFE' },
            stressed: { emoji: '😩', label: '스트레스', color: '#FD79A8' },

            // 중립/기타
            neutral: { emoji: '😐', label: '중립', color: '#B2BEC3' },
            confused: { emoji: '🤔', label: '혼란', color: '#DFE6E9' },
            thoughtful: { emoji: '🤔', label: '사려깊음', color: '#81ECEC' },
            calm: { emoji: '😌', label: '차분함', color: '#00B894' },

            // 상담 특화
            opening_up: { emoji: '💭', label: '마음 열기', color: '#A8E6CF' },
            seeking_help: { emoji: '🆘', label: '도움 요청', color: '#FF7675' },
            reflecting: { emoji: '💫', label: '성찰', color: '#A29BFE' }
        };

        this.currentEmotion = null;
        this.createElement();
    }

    createElement() {
        this.element = document.createElement('div');
        this.element.className = 'emotion-display';
        this.element.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            opacity: 0;
        `;

        if (this.options.showEmoji) {
            this.emojiEl = document.createElement('span');
            this.emojiEl.className = 'emotion-emoji';
            this.emojiEl.style.fontSize = '1.5rem';
            this.element.appendChild(this.emojiEl);
        }

        if (this.options.showLabel) {
            this.labelEl = document.createElement('span');
            this.labelEl.className = 'emotion-label';
            this.labelEl.style.cssText = `
                font-size: 0.875rem;
                color: white;
            `;
            this.element.appendChild(this.labelEl);
        }

        if (this.container) {
            this.container.appendChild(this.element);
        }
    }

    /**
     * 감정 표시
     */
    show(emotion, confidence = 1.0) {
        const emotionData = this.emotionMap[emotion] || this.emotionMap.neutral;

        this.currentEmotion = emotion;

        if (this.emojiEl) {
            this.emojiEl.textContent = emotionData.emoji;
        }

        if (this.labelEl) {
            this.labelEl.textContent = emotionData.label;
            if (confidence < 1) {
                this.labelEl.textContent += ` (${Math.round(confidence * 100)}%)`;
            }
        }

        this.element.style.background = `${emotionData.color}33`;
        this.element.style.borderColor = emotionData.color;
        this.element.style.opacity = '1';

        if (this.options.animate) {
            this.element.style.transform = 'scale(1.1)';
            setTimeout(() => {
                this.element.style.transform = 'scale(1)';
            }, 200);
        }
    }

    /**
     * 숨기기
     */
    hide() {
        this.element.style.opacity = '0';
        this.currentEmotion = null;
    }

    /**
     * 분석 결과에서 감정 추출
     */
    analyzeText(text) {
        // 간단한 키워드 기반 감정 분석
        const keywords = {
            // 긍정
            happy: ['기뻐', '행복', '좋아', '즐거', '웃', '감사'],
            hopeful: ['희망', '기대', '바라', '꿈', '가능', '할 수'],
            relieved: ['안심', '다행', '편안', '괜찮'],

            // 부정
            sad: ['슬퍼', '우울', '눈물', '힘들', '외로', '그리워'],
            anxious: ['불안', '걱정', '두려', '무서', '떨려'],
            angry: ['화가', '짜증', '열받', '분노', '억울'],
            stressed: ['스트레스', '지쳐', '피곤', '버거', '힘겨'],

            // 기타
            confused: ['모르겠', '이해가', '왜', '어떻게'],
            seeking_help: ['도와', '조언', '어떻게 해야', '방법']
        };

        const lowerText = text.toLowerCase();
        let detectedEmotion = 'neutral';
        let maxCount = 0;

        for (const [emotion, words] of Object.entries(keywords)) {
            let count = 0;
            for (const word of words) {
                if (lowerText.includes(word)) {
                    count++;
                }
            }
            if (count > maxCount) {
                maxCount = count;
                detectedEmotion = emotion;
            }
        }

        return {
            emotion: detectedEmotion,
            confidence: maxCount > 0 ? Math.min(maxCount * 0.3, 1.0) : 0.5
        };
    }
}


// ============================================================================
// 대기 시간 표시
// ============================================================================

class WaitTimeDisplay {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.getElementById(container)
            : container;

        this.options = {
            showEstimate: options.showEstimate !== false,
            showProgress: options.showProgress !== false,
            ...options
        };

        // 지연 시간 기록
        this.latencyHistory = [];
        this.maxHistory = 20;

        this.startTime = null;
        this.estimatedTime = null;

        this.createElement();
    }

    createElement() {
        this.element = document.createElement('div');
        this.element.className = 'wait-time-display';
        this.element.style.cssText = `
            display: none;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            border-radius: 12px;
            background: rgba(74, 144, 164, 0.2);
            color: white;
        `;

        // 상태 텍스트
        this.statusEl = document.createElement('div');
        this.statusEl.className = 'wait-status';
        this.statusEl.style.fontSize = '0.875rem';
        this.element.appendChild(this.statusEl);

        // 진행 바
        if (this.options.showProgress) {
            this.progressContainer = document.createElement('div');
            this.progressContainer.style.cssText = `
                width: 200px;
                height: 4px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
                overflow: hidden;
            `;

            this.progressBar = document.createElement('div');
            this.progressBar.style.cssText = `
                width: 0%;
                height: 100%;
                background: #7ED6DF;
                transition: width 0.1s linear;
            `;

            this.progressContainer.appendChild(this.progressBar);
            this.element.appendChild(this.progressContainer);
        }

        // 예상 시간
        if (this.options.showEstimate) {
            this.estimateEl = document.createElement('div');
            this.estimateEl.className = 'wait-estimate';
            this.estimateEl.style.cssText = `
                font-size: 0.75rem;
                color: rgba(255, 255, 255, 0.7);
            `;
            this.element.appendChild(this.estimateEl);
        }

        if (this.container) {
            this.container.appendChild(this.element);
        }
    }

    /**
     * 대기 시작
     */
    start(stage = 'processing') {
        this.startTime = Date.now();
        this.element.style.display = 'flex';

        const stageText = {
            'processing': '처리 중...',
            'stt': '음성 인식 중...',
            'llm': '응답 생성 중...',
            'tts': '음성 합성 중...'
        };

        this.statusEl.textContent = stageText[stage] || '처리 중...';

        // 예상 시간 계산
        if (this.latencyHistory.length > 0) {
            const avgLatency = this.latencyHistory.reduce((a, b) => a + b, 0) / this.latencyHistory.length;
            this.estimatedTime = avgLatency;

            if (this.estimateEl) {
                this.estimateEl.textContent = `예상 시간: ${(avgLatency / 1000).toFixed(1)}초`;
            }
        }

        // 진행 애니메이션 시작
        this.animateProgress();
    }

    /**
     * 단계 업데이트
     */
    updateStage(stage, progress = null) {
        const stageText = {
            'processing': '처리 중...',
            'stt': '음성 인식 중...',
            'llm': '응답 생성 중...',
            'tts': '음성 합성 중...'
        };

        this.statusEl.textContent = stageText[stage] || stage;

        if (progress !== null && this.progressBar) {
            this.progressBar.style.width = `${progress * 100}%`;
        }
    }

    /**
     * 대기 종료
     */
    end() {
        if (this.startTime) {
            const elapsed = Date.now() - this.startTime;
            this.recordLatency(elapsed);
        }

        this.element.style.display = 'none';
        this.startTime = null;

        if (this.progressBar) {
            this.progressBar.style.width = '0%';
        }
    }

    /**
     * 지연 시간 기록
     */
    recordLatency(latencyMs) {
        this.latencyHistory.push(latencyMs);
        if (this.latencyHistory.length > this.maxHistory) {
            this.latencyHistory.shift();
        }
    }

    /**
     * 진행 애니메이션
     */
    animateProgress() {
        if (!this.startTime || !this.progressBar) return;

        const elapsed = Date.now() - this.startTime;
        const estimated = this.estimatedTime || 3000;

        // 로그 스케일로 진행 (100%에 도달하지 않도록)
        const progress = Math.min(0.9, 1 - Math.exp(-elapsed / estimated));
        this.progressBar.style.width = `${progress * 100}%`;

        if (this.startTime) {
            requestAnimationFrame(() => this.animateProgress());
        }
    }
}


// ============================================================================
// 터치 제스처 지원
// ============================================================================

class TouchGestureHandler {
    constructor(element, options = {}) {
        this.element = typeof element === 'string'
            ? document.getElementById(element)
            : element;

        this.options = {
            longPressDuration: options.longPressDuration || 500,
            swipeThreshold: options.swipeThreshold || 50,
            ...options
        };

        // 콜백
        this.onLongPressStart = options.onLongPressStart || (() => {});
        this.onLongPressEnd = options.onLongPressEnd || (() => {});
        this.onTap = options.onTap || (() => {});
        this.onSwipe = options.onSwipe || (() => {});

        // 상태
        this.touchStartTime = null;
        this.touchStartPos = null;
        this.longPressTimer = null;
        this.isLongPress = false;

        this.bindEvents();
    }

    bindEvents() {
        this.element.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        this.element.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.element.addEventListener('touchend', (e) => this.handleTouchEnd(e));
        this.element.addEventListener('touchcancel', (e) => this.handleTouchEnd(e));
    }

    handleTouchStart(e) {
        e.preventDefault();

        this.touchStartTime = Date.now();
        this.touchStartPos = {
            x: e.touches[0].clientX,
            y: e.touches[0].clientY
        };
        this.isLongPress = false;

        // 롱 프레스 타이머
        this.longPressTimer = setTimeout(() => {
            this.isLongPress = true;
            this.onLongPressStart();
        }, this.options.longPressDuration);
    }

    handleTouchMove(e) {
        if (!this.touchStartPos) return;

        const deltaX = e.touches[0].clientX - this.touchStartPos.x;
        const deltaY = e.touches[0].clientY - this.touchStartPos.y;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

        // 이동이 크면 롱 프레스 취소
        if (distance > 10 && this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
    }

    handleTouchEnd(e) {
        // 롱 프레스 타이머 취소
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }

        if (this.isLongPress) {
            this.onLongPressEnd();
            this.isLongPress = false;
            return;
        }

        if (!this.touchStartPos) return;

        const touchEndPos = {
            x: e.changedTouches[0].clientX,
            y: e.changedTouches[0].clientY
        };

        const deltaX = touchEndPos.x - this.touchStartPos.x;
        const deltaY = touchEndPos.y - this.touchStartPos.y;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

        // 스와이프 감지
        if (distance > this.options.swipeThreshold) {
            const direction = Math.abs(deltaX) > Math.abs(deltaY)
                ? (deltaX > 0 ? 'right' : 'left')
                : (deltaY > 0 ? 'down' : 'up');

            this.onSwipe(direction);
        } else {
            // 탭
            this.onTap();
        }

        this.touchStartPos = null;
    }
}


// ============================================================================
// 접근성 개선
// ============================================================================

class AccessibilityHelper {
    constructor() {
        this.announcer = null;
        this.createAnnouncer();
    }

    createAnnouncer() {
        // 스크린 리더용 라이브 영역
        this.announcer = document.createElement('div');
        this.announcer.setAttribute('role', 'status');
        this.announcer.setAttribute('aria-live', 'polite');
        this.announcer.setAttribute('aria-atomic', 'true');
        this.announcer.className = 'sr-only';
        this.announcer.style.cssText = `
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        `;
        document.body.appendChild(this.announcer);
    }

    /**
     * 스크린 리더에 알림
     */
    announce(message, priority = 'polite') {
        this.announcer.setAttribute('aria-live', priority);
        this.announcer.textContent = message;

        // 다음 알림을 위해 초기화
        setTimeout(() => {
            this.announcer.textContent = '';
        }, 1000);
    }

    /**
     * 음성 채팅 접근성 설정
     */
    setupVoiceChatAccessibility() {
        // 키보드 단축키 안내
        const shortcuts = [
            { key: 'Space', action: '녹음 시작/중지' },
            { key: 'Escape', action: '녹음 취소' },
            { key: 'Enter', action: '메시지 전송' }
        ];

        // ARIA 레이블 설정
        const recordBtn = document.getElementById('voice-record-btn');
        if (recordBtn) {
            recordBtn.setAttribute('aria-label', '음성 녹음 버튼. 스페이스바로도 조작 가능');
            recordBtn.setAttribute('aria-pressed', 'false');
        }

        // 상태 영역 설정
        const statusArea = document.getElementById('voice-status-text');
        if (statusArea) {
            statusArea.setAttribute('role', 'status');
            statusArea.setAttribute('aria-live', 'polite');
        }
    }

    /**
     * 녹음 상태 변경 알림
     */
    announceRecordingState(isRecording) {
        const message = isRecording
            ? '녹음이 시작되었습니다. 말씀해 주세요.'
            : '녹음이 중지되었습니다.';

        this.announce(message, 'assertive');

        const recordBtn = document.getElementById('voice-record-btn');
        if (recordBtn) {
            recordBtn.setAttribute('aria-pressed', isRecording.toString());
        }
    }

    /**
     * 응답 알림
     */
    announceResponse(text) {
        this.announce(`상담사 응답: ${text}`);
    }
}


// Export
window.AutoVoiceDetector = AutoVoiceDetector;
window.EmotionDisplay = EmotionDisplay;
window.WaitTimeDisplay = WaitTimeDisplay;
window.TouchGestureHandler = TouchGestureHandler;
window.AccessibilityHelper = AccessibilityHelper;
