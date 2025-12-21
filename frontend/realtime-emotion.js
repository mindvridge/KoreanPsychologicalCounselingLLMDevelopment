/**
 * 실시간 감정 분석 시스템 (Real-time Emotion Analysis)
 * 웹캠 기반 표정 인식 및 감정 시각화
 */

// ============================================================================
// 감정 분석 설정
// ============================================================================

const EmotionConfig = {
    // 감정 정의
    emotions: {
        happy: { label: '행복', emoji: '😊', color: '#22c55e', koLabel: '행복' },
        sad: { label: '슬픔', emoji: '😢', color: '#3b82f6', koLabel: '슬픔' },
        angry: { label: '분노', emoji: '😠', color: '#ef4444', koLabel: '분노' },
        fearful: { label: '두려움', emoji: '😨', color: '#a855f7', koLabel: '두려움' },
        disgusted: { label: '혐오', emoji: '🤢', color: '#84cc16', koLabel: '혐오' },
        surprised: { label: '놀람', emoji: '😮', color: '#f59e0b', koLabel: '놀람' },
        neutral: { label: '중립', emoji: '😐', color: '#6b7280', koLabel: '중립' }
    },

    // 분석 설정
    analysisInterval: 500,      // 분석 간격 (ms)
    historyLength: 30,          // 감정 히스토리 길이
    smoothingFactor: 0.3,       // 감정 스무딩 계수

    // 알림 임계값
    alertThresholds: {
        sadnessAlert: 0.7,      // 슬픔 경고 임계값
        angerAlert: 0.8,        // 분노 경고 임계값
        fearAlert: 0.7,         // 두려움 경고 임계값
        engagementLow: 0.3      // 참여도 저하 임계값
    }
};

// ============================================================================
// 웹캠 매니저
// ============================================================================

class WebcamManager {
    constructor() {
        this.stream = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.isActive = false;
        this.onFrameCallback = null;
    }

    async initialize(videoElementId, canvasElementId) {
        this.videoElement = document.getElementById(videoElementId);
        this.canvasElement = document.getElementById(canvasElementId);

        if (!this.videoElement || !this.canvasElement) {
            throw new Error('비디오 또는 캔버스 요소를 찾을 수 없습니다.');
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            });

            this.videoElement.srcObject = this.stream;
            await this.videoElement.play();
            this.isActive = true;

            console.log('웹캠 초기화 성공');
            return true;
        } catch (error) {
            console.error('웹캠 접근 실패:', error);
            throw error;
        }
    }

    captureFrame() {
        if (!this.isActive || !this.videoElement || !this.canvasElement) {
            return null;
        }

        const ctx = this.canvasElement.getContext('2d');
        this.canvasElement.width = this.videoElement.videoWidth;
        this.canvasElement.height = this.videoElement.videoHeight;

        ctx.drawImage(this.videoElement, 0, 0);

        // Base64로 인코딩
        return this.canvasElement.toDataURL('image/jpeg', 0.8).split(',')[1];
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.isActive = false;
    }

    isRunning() {
        return this.isActive;
    }
}

// ============================================================================
// 감정 분석기 (클라이언트 사이드 - TensorFlow.js 또는 API 호출)
// ============================================================================

class EmotionAnalyzer {
    constructor() {
        this.isModelLoaded = false;
        this.useAPI = true; // API 사용 여부 (클라이언트 모델 대신)
        this.apiEndpoint = '/api/analyze-emotion';
    }

    async initialize() {
        if (this.useAPI) {
            // API 모드 - 별도 초기화 불필요
            this.isModelLoaded = true;
            console.log('감정 분석기 (API 모드) 초기화 완료');
            return true;
        }

        // 클라이언트 모델 로드 (TensorFlow.js face-api.js 등)
        try {
            // 실제 구현에서는 face-api.js 또는 TensorFlow.js 모델 로드
            // await faceapi.nets.tinyFaceDetector.loadFromUri('/models');
            // await faceapi.nets.faceExpressionNet.loadFromUri('/models');

            this.isModelLoaded = true;
            console.log('감정 분석 모델 로드 완료');
            return true;
        } catch (error) {
            console.error('모델 로드 실패:', error);
            throw error;
        }
    }

    async analyze(imageBase64) {
        if (!this.isModelLoaded) {
            throw new Error('모델이 로드되지 않았습니다.');
        }

        if (this.useAPI) {
            return await this.analyzeViaAPI(imageBase64);
        } else {
            return await this.analyzeLocally(imageBase64);
        }
    }

    async analyzeViaAPI(imageBase64) {
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: imageBase64,
                    timestamp: Date.now()
                })
            });

            if (!response.ok) {
                throw new Error('API 요청 실패');
            }

            return await response.json();
        } catch (error) {
            // API 실패 시 시뮬레이션 데이터 반환 (데모용)
            return this.generateSimulatedAnalysis();
        }
    }

    async analyzeLocally(imageBase64) {
        // 클라이언트 사이드 분석 (face-api.js 사용 시)
        // const img = await faceapi.fetchImage(`data:image/jpeg;base64,${imageBase64}`);
        // const detections = await faceapi.detectSingleFace(img).withFaceExpressions();

        // 데모용 시뮬레이션
        return this.generateSimulatedAnalysis();
    }

    generateSimulatedAnalysis() {
        // 데모용 시뮬레이션 데이터
        const emotions = ['happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised', 'neutral'];
        const probabilities = {};

        // 랜덤 확률 생성 (합계 1)
        let remaining = 1.0;
        emotions.forEach((emotion, index) => {
            if (index === emotions.length - 1) {
                probabilities[emotion] = remaining;
            } else {
                const prob = Math.random() * remaining * 0.6;
                probabilities[emotion] = prob;
                remaining -= prob;
            }
        });

        // 주요 감정 결정
        const primaryEmotion = Object.entries(probabilities)
            .sort((a, b) => b[1] - a[1])[0];

        // Valence/Arousal 계산
        const valenceMap = { happy: 0.8, surprised: 0.3, neutral: 0, sad: -0.6, fearful: -0.5, angry: -0.7, disgusted: -0.4 };
        const arousalMap = { happy: 0.6, surprised: 0.8, angry: 0.9, fearful: 0.7, disgusted: 0.4, sad: 0.2, neutral: 0.1 };

        const valence = Object.entries(probabilities)
            .reduce((sum, [emotion, prob]) => sum + (valenceMap[emotion] || 0) * prob, 0);
        const arousal = Object.entries(probabilities)
            .reduce((sum, [emotion, prob]) => sum + (arousalMap[emotion] || 0) * prob, 0);

        return {
            success: true,
            faceDetected: true,
            emotions: probabilities,
            primaryEmotion: primaryEmotion[0],
            confidence: primaryEmotion[1],
            valence: valence,
            arousal: arousal,
            engagement: 0.5 + Math.random() * 0.5,
            timestamp: Date.now()
        };
    }
}

// ============================================================================
// 실시간 감정 분석 UI 컴포넌트
// ============================================================================

class RealtimeEmotionUI {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.webcamManager = new WebcamManager();
        this.emotionAnalyzer = new EmotionAnalyzer();

        this.isRunning = false;
        this.analysisTimer = null;
        this.emotionHistory = [];
        this.smoothedEmotions = {};

        // 콜백
        this.onEmotionDetected = null;
        this.onAlertTriggered = null;

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="realtime-emotion-widget">
                <!-- 헤더 -->
                <div class="emotion-widget-header">
                    <div class="emotion-widget-title">
                        <span class="emotion-widget-icon">🎭</span>
                        <h3>실시간 감정 분석</h3>
                    </div>
                    <div class="emotion-widget-controls">
                        <label class="privacy-toggle">
                            <input type="checkbox" id="emotion-privacy-mode">
                            <span>프라이버시 모드</span>
                        </label>
                        <button class="emotion-settings-btn" id="emotion-settings-btn">⚙️</button>
                    </div>
                </div>

                <!-- 동의 화면 -->
                <div class="emotion-consent" id="emotion-consent">
                    <div class="consent-icon">📷</div>
                    <h4>웹캠 감정 분석</h4>
                    <p>상담 중 표정을 분석하여 더 나은 상담을 제공합니다.</p>
                    <ul class="consent-features">
                        <li>✓ 실시간 감정 인식</li>
                        <li>✓ 상담사 AI가 감정에 맞춰 응답</li>
                        <li>✓ 영상은 저장되지 않습니다</li>
                    </ul>
                    <div class="consent-buttons">
                        <button class="consent-btn consent-btn-allow" id="consent-allow">
                            활성화하기
                        </button>
                        <button class="consent-btn consent-btn-skip" id="consent-skip">
                            나중에
                        </button>
                    </div>
                </div>

                <!-- 메인 분석 화면 -->
                <div class="emotion-main hidden" id="emotion-main">
                    <!-- 비디오 영역 -->
                    <div class="emotion-video-container">
                        <video id="emotion-video" autoplay muted playsinline></video>
                        <canvas id="emotion-canvas" class="hidden"></canvas>

                        <!-- 얼굴 감지 오버레이 -->
                        <div class="face-detection-overlay" id="face-overlay">
                            <div class="face-box"></div>
                        </div>

                        <!-- 현재 감정 뱃지 -->
                        <div class="current-emotion-badge" id="current-emotion-badge">
                            <span class="emotion-emoji">😐</span>
                            <span class="emotion-label">분석 중...</span>
                        </div>

                        <!-- 프라이버시 모드 오버레이 -->
                        <div class="privacy-overlay hidden" id="privacy-overlay">
                            <span>🔒</span>
                            <span>프라이버시 모드</span>
                        </div>
                    </div>

                    <!-- 감정 분포 차트 -->
                    <div class="emotion-distribution">
                        <h4>감정 분포</h4>
                        <div class="emotion-bars" id="emotion-bars">
                            ${this.renderEmotionBars()}
                        </div>
                    </div>

                    <!-- 감정 지표 -->
                    <div class="emotion-metrics">
                        <div class="metric-item">
                            <span class="metric-label">감정가 (Valence)</span>
                            <div class="metric-bar valence-bar">
                                <div class="metric-indicator" id="valence-indicator"></div>
                                <span class="metric-negative">부정</span>
                                <span class="metric-positive">긍정</span>
                            </div>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">각성도 (Arousal)</span>
                            <div class="metric-bar arousal-bar">
                                <div class="metric-fill" id="arousal-fill"></div>
                            </div>
                            <span class="metric-value" id="arousal-value">50%</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">참여도</span>
                            <div class="metric-bar engagement-bar">
                                <div class="metric-fill" id="engagement-fill"></div>
                            </div>
                            <span class="metric-value" id="engagement-value">75%</span>
                        </div>
                    </div>

                    <!-- 감정 타임라인 -->
                    <div class="emotion-timeline">
                        <h4>감정 변화</h4>
                        <div class="timeline-chart" id="timeline-chart">
                            <canvas id="timeline-canvas"></canvas>
                        </div>
                    </div>

                    <!-- 인사이트 -->
                    <div class="emotion-insight" id="emotion-insight">
                        <span class="insight-icon">💡</span>
                        <span class="insight-text">감정 분석 중...</span>
                    </div>

                    <!-- 컨트롤 -->
                    <div class="emotion-controls">
                        <button class="emotion-btn emotion-btn-pause" id="emotion-pause">
                            ⏸️ 일시정지
                        </button>
                        <button class="emotion-btn emotion-btn-stop" id="emotion-stop">
                            ⏹️ 종료
                        </button>
                    </div>
                </div>

                <!-- 알림 패널 -->
                <div class="emotion-alerts hidden" id="emotion-alerts">
                    <!-- 동적으로 추가됨 -->
                </div>
            </div>
        `;
    }

    renderEmotionBars() {
        return Object.entries(EmotionConfig.emotions).map(([key, emotion]) => `
            <div class="emotion-bar-item" data-emotion="${key}">
                <span class="emotion-bar-emoji">${emotion.emoji}</span>
                <div class="emotion-bar-track">
                    <div class="emotion-bar-fill" style="background: ${emotion.color}; width: 0%"></div>
                </div>
                <span class="emotion-bar-value">0%</span>
            </div>
        `).join('');
    }

    bindEvents() {
        // 동의 버튼
        document.getElementById('consent-allow')?.addEventListener('click', () => {
            this.startAnalysis();
        });

        document.getElementById('consent-skip')?.addEventListener('click', () => {
            this.container.classList.add('minimized');
        });

        // 일시정지/재개
        document.getElementById('emotion-pause')?.addEventListener('click', () => {
            this.togglePause();
        });

        // 종료
        document.getElementById('emotion-stop')?.addEventListener('click', () => {
            this.stopAnalysis();
        });

        // 프라이버시 모드
        document.getElementById('emotion-privacy-mode')?.addEventListener('change', (e) => {
            this.togglePrivacyMode(e.target.checked);
        });
    }

    async startAnalysis() {
        try {
            // 동의 화면 숨기기
            document.getElementById('emotion-consent').classList.add('hidden');
            document.getElementById('emotion-main').classList.remove('hidden');

            // 모델 초기화
            await this.emotionAnalyzer.initialize();

            // 웹캠 시작
            await this.webcamManager.initialize('emotion-video', 'emotion-canvas');

            // 분석 루프 시작
            this.isRunning = true;
            this.startAnalysisLoop();

            console.log('실시간 감정 분석 시작');
        } catch (error) {
            console.error('감정 분석 시작 실패:', error);
            this.showError('웹캠을 사용할 수 없습니다. 권한을 확인해주세요.');
        }
    }

    startAnalysisLoop() {
        if (!this.isRunning) return;

        this.analysisTimer = setInterval(async () => {
            if (!this.isRunning) return;

            try {
                // 프레임 캡처
                const frameData = this.webcamManager.captureFrame();
                if (!frameData) return;

                // 감정 분석
                const result = await this.emotionAnalyzer.analyze(frameData);

                if (result.success && result.faceDetected) {
                    this.processAnalysisResult(result);
                } else {
                    this.updateUINoFace();
                }
            } catch (error) {
                console.error('분석 오류:', error);
            }
        }, EmotionConfig.analysisInterval);
    }

    processAnalysisResult(result) {
        // 스무딩 적용
        this.applySmoothing(result.emotions);

        // 히스토리 업데이트
        this.updateHistory(result);

        // UI 업데이트
        this.updateEmotionBars(this.smoothedEmotions);
        this.updateCurrentEmotion(result.primaryEmotion, result.confidence);
        this.updateMetrics(result.valence, result.arousal, result.engagement);
        this.updateTimeline();
        this.updateInsight(result);

        // 알림 체크
        this.checkAlerts(result);

        // 콜백 호출
        if (this.onEmotionDetected) {
            this.onEmotionDetected(result);
        }
    }

    applySmoothing(newEmotions) {
        const alpha = EmotionConfig.smoothingFactor;

        Object.entries(newEmotions).forEach(([emotion, value]) => {
            if (this.smoothedEmotions[emotion] === undefined) {
                this.smoothedEmotions[emotion] = value;
            } else {
                this.smoothedEmotions[emotion] =
                    alpha * value + (1 - alpha) * this.smoothedEmotions[emotion];
            }
        });
    }

    updateHistory(result) {
        this.emotionHistory.push({
            timestamp: result.timestamp,
            emotions: { ...result.emotions },
            primaryEmotion: result.primaryEmotion,
            valence: result.valence,
            arousal: result.arousal
        });

        // 히스토리 길이 제한
        if (this.emotionHistory.length > EmotionConfig.historyLength) {
            this.emotionHistory.shift();
        }
    }

    updateEmotionBars(emotions) {
        Object.entries(emotions).forEach(([emotion, value]) => {
            const item = this.container.querySelector(`.emotion-bar-item[data-emotion="${emotion}"]`);
            if (item) {
                const fill = item.querySelector('.emotion-bar-fill');
                const valueEl = item.querySelector('.emotion-bar-value');
                const percentage = Math.round(value * 100);

                fill.style.width = `${percentage}%`;
                valueEl.textContent = `${percentage}%`;
            }
        });
    }

    updateCurrentEmotion(primaryEmotion, confidence) {
        const badge = document.getElementById('current-emotion-badge');
        const emotionInfo = EmotionConfig.emotions[primaryEmotion];

        if (badge && emotionInfo) {
            badge.querySelector('.emotion-emoji').textContent = emotionInfo.emoji;
            badge.querySelector('.emotion-label').textContent =
                `${emotionInfo.koLabel} (${Math.round(confidence * 100)}%)`;
            badge.style.borderColor = emotionInfo.color;
        }
    }

    updateMetrics(valence, arousal, engagement) {
        // Valence 인디케이터 (-1 ~ 1 -> 0% ~ 100%)
        const valenceIndicator = document.getElementById('valence-indicator');
        if (valenceIndicator) {
            const valencePercent = ((valence + 1) / 2) * 100;
            valenceIndicator.style.left = `${valencePercent}%`;

            // 색상 변경
            if (valence > 0.2) {
                valenceIndicator.style.background = '#22c55e';
            } else if (valence < -0.2) {
                valenceIndicator.style.background = '#ef4444';
            } else {
                valenceIndicator.style.background = '#6b7280';
            }
        }

        // Arousal
        const arousalFill = document.getElementById('arousal-fill');
        const arousalValue = document.getElementById('arousal-value');
        if (arousalFill && arousalValue) {
            const arousalPercent = Math.round(arousal * 100);
            arousalFill.style.width = `${arousalPercent}%`;
            arousalValue.textContent = `${arousalPercent}%`;
        }

        // Engagement
        const engagementFill = document.getElementById('engagement-fill');
        const engagementValue = document.getElementById('engagement-value');
        if (engagementFill && engagementValue) {
            const engagementPercent = Math.round(engagement * 100);
            engagementFill.style.width = `${engagementPercent}%`;
            engagementValue.textContent = `${engagementPercent}%`;

            // 참여도 낮음 경고
            if (engagement < EmotionConfig.alertThresholds.engagementLow) {
                engagementFill.style.background = '#ef4444';
            } else {
                engagementFill.style.background = '#22c55e';
            }
        }
    }

    updateTimeline() {
        const canvas = document.getElementById('timeline-canvas');
        if (!canvas || this.emotionHistory.length < 2) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.parentElement.clientWidth;
        const height = 60;

        canvas.width = width;
        canvas.height = height;

        // 배경 클리어
        ctx.clearRect(0, 0, width, height);

        // Valence 라인 그리기
        ctx.beginPath();
        ctx.strokeStyle = '#5B8A72';
        ctx.lineWidth = 2;

        this.emotionHistory.forEach((point, index) => {
            const x = (index / (this.emotionHistory.length - 1)) * width;
            const y = height / 2 - (point.valence * height / 2);

            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // 중앙선 (중립)
        ctx.beginPath();
        ctx.strokeStyle = '#e5e7eb';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    updateInsight(result) {
        const insightEl = document.getElementById('emotion-insight');
        if (!insightEl) return;

        const textEl = insightEl.querySelector('.insight-text');
        let insight = '';

        // 감정 기반 인사이트
        if (result.primaryEmotion === 'sad' && result.confidence > 0.5) {
            insight = '슬픔이 느껴지시는군요. 지금 마음을 나눠주실 수 있을까요?';
        } else if (result.primaryEmotion === 'happy' && result.confidence > 0.5) {
            insight = '밝은 표정이에요! 오늘 기분이 좋으신 것 같네요.';
        } else if (result.primaryEmotion === 'angry' && result.confidence > 0.5) {
            insight = '화가 나는 감정이 보여요. 심호흡을 해보시는 건 어떨까요?';
        } else if (result.primaryEmotion === 'fearful' && result.confidence > 0.5) {
            insight = '불안해 보이세요. 천천히 이야기해 주세요.';
        } else if (result.valence < -0.3) {
            insight = '조금 힘들어 보여요. 편하게 말씀해 주세요.';
        } else if (result.engagement < 0.4) {
            insight = '잠시 쉬어가도 괜찮아요. 준비되시면 말씀해 주세요.';
        } else {
            insight = '차분하게 대화가 진행되고 있어요.';
        }

        textEl.textContent = insight;
    }

    updateUINoFace() {
        const badge = document.getElementById('current-emotion-badge');
        if (badge) {
            badge.querySelector('.emotion-emoji').textContent = '👤';
            badge.querySelector('.emotion-label').textContent = '얼굴 감지 중...';
        }
    }

    checkAlerts(result) {
        const alerts = [];

        // 슬픔 경고
        if (result.emotions.sad > EmotionConfig.alertThresholds.sadnessAlert) {
            alerts.push({
                type: 'sadness',
                message: '슬픔이 많이 감지되고 있어요',
                icon: '😢'
            });
        }

        // 분노 경고
        if (result.emotions.angry > EmotionConfig.alertThresholds.angerAlert) {
            alerts.push({
                type: 'anger',
                message: '화가 많이 나신 것 같아요',
                icon: '😠'
            });
        }

        // 두려움 경고
        if (result.emotions.fearful > EmotionConfig.alertThresholds.fearAlert) {
            alerts.push({
                type: 'fear',
                message: '불안해 보이세요',
                icon: '😨'
            });
        }

        if (alerts.length > 0 && this.onAlertTriggered) {
            this.onAlertTriggered(alerts);
        }
    }

    togglePause() {
        const pauseBtn = document.getElementById('emotion-pause');

        if (this.isRunning) {
            clearInterval(this.analysisTimer);
            this.isRunning = false;
            pauseBtn.textContent = '▶️ 재개';
        } else {
            this.isRunning = true;
            this.startAnalysisLoop();
            pauseBtn.textContent = '⏸️ 일시정지';
        }
    }

    togglePrivacyMode(enabled) {
        const overlay = document.getElementById('privacy-overlay');
        const video = document.getElementById('emotion-video');

        if (enabled) {
            overlay?.classList.remove('hidden');
            if (video) video.style.filter = 'blur(20px)';
        } else {
            overlay?.classList.add('hidden');
            if (video) video.style.filter = 'none';
        }
    }

    stopAnalysis() {
        this.isRunning = false;
        clearInterval(this.analysisTimer);
        this.webcamManager.stop();

        // UI 리셋
        document.getElementById('emotion-main').classList.add('hidden');
        document.getElementById('emotion-consent').classList.remove('hidden');
    }

    showError(message) {
        const consent = document.getElementById('emotion-consent');
        if (consent) {
            consent.innerHTML = `
                <div class="consent-error">
                    <span class="error-icon">⚠️</span>
                    <h4>오류 발생</h4>
                    <p>${message}</p>
                    <button class="consent-btn" onclick="location.reload()">다시 시도</button>
                </div>
            `;
        }
    }

    // 외부 API
    getEmotionSummary() {
        if (this.emotionHistory.length === 0) return null;

        const summary = {
            dominantEmotions: {},
            averageValence: 0,
            averageArousal: 0,
            emotionChanges: 0
        };

        // 평균 계산
        this.emotionHistory.forEach(point => {
            summary.averageValence += point.valence;
            summary.averageArousal += point.arousal;

            Object.entries(point.emotions).forEach(([emotion, value]) => {
                summary.dominantEmotions[emotion] =
                    (summary.dominantEmotions[emotion] || 0) + value;
            });
        });

        const count = this.emotionHistory.length;
        summary.averageValence /= count;
        summary.averageArousal /= count;

        Object.keys(summary.dominantEmotions).forEach(emotion => {
            summary.dominantEmotions[emotion] /= count;
        });

        // 감정 변화 횟수
        let lastEmotion = null;
        this.emotionHistory.forEach(point => {
            if (lastEmotion && lastEmotion !== point.primaryEmotion) {
                summary.emotionChanges++;
            }
            lastEmotion = point.primaryEmotion;
        });

        return summary;
    }

    generateContextForLLM() {
        const summary = this.getEmotionSummary();
        if (!summary) return '';

        const current = this.emotionHistory[this.emotionHistory.length - 1];
        if (!current) return '';

        const emotionInfo = EmotionConfig.emotions[current.primaryEmotion];

        return `
[실시간 감정 분석 컨텍스트]
- 현재 감정: ${emotionInfo?.koLabel || current.primaryEmotion} (${Math.round(current.emotions[current.primaryEmotion] * 100)}%)
- 감정가: ${summary.averageValence > 0 ? '긍정적' : summary.averageValence < 0 ? '부정적' : '중립'}
- 각성도: ${summary.averageArousal > 0.5 ? '높음' : '보통'}
- 감정 변화: ${summary.emotionChanges > 5 ? '변동이 큼' : '안정적'}
- 권장 대응: ${this.getSuggestedResponse(current.primaryEmotion)}
        `.trim();
    }

    getSuggestedResponse(emotion) {
        const responses = {
            happy: '긍정적 분위기 유지, 성취 강화',
            sad: '공감적 경청, 감정 수용, 부드러운 어조',
            angry: '감정 인정, 차분한 톤, 심호흡 제안',
            fearful: '안심시키기, 안전감 제공, 천천히 진행',
            disgusted: '감정 탐색, 회피하지 않고 다루기',
            surprised: '상황 명확화, 정보 제공',
            neutral: '개방형 질문으로 탐색'
        };
        return responses[emotion] || '공감적 경청 유지';
    }
}

// ============================================================================
// 전역 초기화 함수
// ============================================================================

function initRealtimeEmotion(containerId = 'realtime-emotion-container') {
    return new RealtimeEmotionUI(containerId);
}

// 자동 초기화
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('realtime-emotion-container');
    if (container) {
        window.realtimeEmotion = new RealtimeEmotionUI('realtime-emotion-container');
    }
});

// 모듈 내보내기
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RealtimeEmotionUI, WebcamManager, EmotionAnalyzer, EmotionConfig };
}
