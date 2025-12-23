/**
 * 고급 감정 분석 시스템 (Advanced Emotion Analysis System)
 * - 감정 변화 타임라인 그래프
 * - 웹캠 + 텍스트 통합 분석
 * - 지능형 상담 제안
 */

// ============================================================================
// 감정 타임라인 그래프 시스템
// ============================================================================

class EmotionTimelineGraph {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.ctx = null;
        this.data = [];
        this.maxDataPoints = 60; // 최대 60개 데이터 포인트 (약 30초)
        this.animationFrame = null;

        this.colors = {
            valence: '#5B8A72',
            arousal: '#E8B298',
            engagement: '#7C9EB2',
            grid: '#e5e7eb',
            text: '#6b7280',
            positive: '#22c55e',
            negative: '#ef4444',
            neutral: '#6b7280'
        };

        this.init();
    }

    init() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="timeline-graph-container">
                <div class="timeline-header">
                    <h4>📈 감정 변화 타임라인</h4>
                    <div class="timeline-legend">
                        <span class="legend-item" data-type="valence">
                            <span class="legend-dot" style="background: ${this.colors.valence}"></span>
                            감정가
                        </span>
                        <span class="legend-item" data-type="arousal">
                            <span class="legend-dot" style="background: ${this.colors.arousal}"></span>
                            각성도
                        </span>
                        <span class="legend-item" data-type="engagement">
                            <span class="legend-dot" style="background: ${this.colors.engagement}"></span>
                            참여도
                        </span>
                    </div>
                </div>
                <div class="timeline-chart-area">
                    <canvas id="emotion-timeline-canvas"></canvas>
                </div>
                <div class="timeline-stats">
                    <div class="stat-item">
                        <span class="stat-label">평균 감정가</span>
                        <span class="stat-value" id="avg-valence">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">감정 변동성</span>
                        <span class="stat-value" id="emotion-volatility">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">주요 감정</span>
                        <span class="stat-value" id="dominant-emotion">-</span>
                    </div>
                </div>
            </div>
        `;

        this.canvas = document.getElementById('emotion-timeline-canvas');
        if (this.canvas) {
            this.ctx = this.canvas.getContext('2d');
            this.resizeCanvas();
            window.addEventListener('resize', () => this.resizeCanvas());
        }
    }

    resizeCanvas() {
        if (!this.canvas || !this.canvas.parentElement) return;

        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height || 120;
        this.render();
    }

    addDataPoint(emotionData) {
        const point = {
            timestamp: Date.now(),
            valence: emotionData.valence || 0,
            arousal: emotionData.arousal || 0,
            engagement: emotionData.engagement || 0,
            primaryEmotion: emotionData.primaryEmotion || 'neutral',
            confidence: emotionData.confidence || 0
        };

        this.data.push(point);

        // 최대 데이터 포인트 유지
        if (this.data.length > this.maxDataPoints) {
            this.data.shift();
        }

        this.render();
        this.updateStats();
    }

    render() {
        if (!this.ctx || !this.canvas) return;

        const { width, height } = this.canvas;
        const padding = { top: 10, right: 10, bottom: 20, left: 30 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        // 클리어
        this.ctx.clearRect(0, 0, width, height);

        // 배경 그라데이션
        const bgGradient = this.ctx.createLinearGradient(0, 0, 0, height);
        bgGradient.addColorStop(0, 'rgba(91, 138, 114, 0.05)');
        bgGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        this.ctx.fillStyle = bgGradient;
        this.ctx.fillRect(0, 0, width, height);

        // 그리드 라인
        this.drawGrid(padding, chartWidth, chartHeight);

        // 데이터가 없으면 여기서 종료
        if (this.data.length < 2) {
            this.ctx.fillStyle = this.colors.text;
            this.ctx.font = '12px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('데이터 수집 중...', width / 2, height / 2);
            return;
        }

        // 라인 그리기
        this.drawLine(padding, chartWidth, chartHeight, 'valence', this.colors.valence, true);
        this.drawLine(padding, chartWidth, chartHeight, 'arousal', this.colors.arousal, false);
        this.drawLine(padding, chartWidth, chartHeight, 'engagement', this.colors.engagement, false);
    }

    drawGrid(padding, chartWidth, chartHeight) {
        this.ctx.strokeStyle = this.colors.grid;
        this.ctx.lineWidth = 1;

        // 수평선 (5개)
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            this.ctx.beginPath();
            this.ctx.moveTo(padding.left, y);
            this.ctx.lineTo(padding.left + chartWidth, y);
            this.ctx.stroke();

            // Y축 레이블
            const value = 1 - (i / 4) * 2; // 1 to -1 for valence
            this.ctx.fillStyle = this.colors.text;
            this.ctx.font = '10px sans-serif';
            this.ctx.textAlign = 'right';
            this.ctx.fillText(value.toFixed(1), padding.left - 5, y + 3);
        }

        // 중앙선 (0) 강조
        const centerY = padding.top + chartHeight / 2;
        this.ctx.strokeStyle = this.colors.neutral;
        this.ctx.setLineDash([5, 5]);
        this.ctx.beginPath();
        this.ctx.moveTo(padding.left, centerY);
        this.ctx.lineTo(padding.left + chartWidth, centerY);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }

    drawLine(padding, chartWidth, chartHeight, dataKey, color, isValence) {
        if (this.data.length < 2) return;

        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.ctx.beginPath();

        this.data.forEach((point, index) => {
            const x = padding.left + (index / (this.data.length - 1)) * chartWidth;
            let value = point[dataKey];

            // valence는 -1~1, 나머지는 0~1
            let normalizedValue;
            if (isValence) {
                normalizedValue = (1 - value) / 2; // -1~1 -> 0~1
            } else {
                normalizedValue = 1 - value; // 0~1 -> 1~0 (위쪽이 높은 값)
            }

            const y = padding.top + normalizedValue * chartHeight;

            if (index === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });

        this.ctx.stroke();

        // 마지막 점에 원 표시
        if (this.data.length > 0) {
            const lastPoint = this.data[this.data.length - 1];
            const x = padding.left + chartWidth;
            let value = lastPoint[dataKey];
            let normalizedValue = isValence ? (1 - value) / 2 : 1 - value;
            const y = padding.top + normalizedValue * chartHeight;

            this.ctx.fillStyle = color;
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    updateStats() {
        if (this.data.length === 0) return;

        // 평균 감정가
        const avgValence = this.data.reduce((sum, p) => sum + p.valence, 0) / this.data.length;
        const avgValenceEl = document.getElementById('avg-valence');
        if (avgValenceEl) {
            const label = avgValence > 0.2 ? '긍정적' : avgValence < -0.2 ? '부정적' : '중립';
            const color = avgValence > 0.2 ? this.colors.positive : avgValence < -0.2 ? this.colors.negative : this.colors.neutral;
            avgValenceEl.innerHTML = `<span style="color: ${color}">${label}</span>`;
        }

        // 감정 변동성 (표준편차)
        const variance = this.data.reduce((sum, p) => sum + Math.pow(p.valence - avgValence, 2), 0) / this.data.length;
        const volatility = Math.sqrt(variance);
        const volatilityEl = document.getElementById('emotion-volatility');
        if (volatilityEl) {
            const label = volatility > 0.3 ? '높음' : volatility > 0.15 ? '보통' : '안정';
            volatilityEl.textContent = label;
        }

        // 주요 감정
        const emotionCounts = {};
        this.data.forEach(p => {
            emotionCounts[p.primaryEmotion] = (emotionCounts[p.primaryEmotion] || 0) + 1;
        });
        const dominantEmotion = Object.entries(emotionCounts).sort((a, b) => b[1] - a[1])[0];
        const dominantEl = document.getElementById('dominant-emotion');
        if (dominantEl && dominantEmotion) {
            const emotionLabels = {
                happy: '😊 행복', sad: '😢 슬픔', angry: '😠 분노',
                fearful: '😨 두려움', disgusted: '🤢 혐오',
                surprised: '😮 놀람', neutral: '😐 중립'
            };
            dominantEl.textContent = emotionLabels[dominantEmotion[0]] || dominantEmotion[0];
        }
    }

    clear() {
        this.data = [];
        this.render();
    }
}

// ============================================================================
// 웹캠 + 텍스트 통합 감정 분석
// ============================================================================

class IntegratedEmotionAnalyzer {
    constructor() {
        this.webcamEmotion = null;  // 웹캠 기반 감정
        this.textEmotion = null;    // 텍스트 기반 감정
        this.integratedScore = null; // 통합 점수
        this.weights = {
            webcam: 0.6,  // 웹캠 가중치
            text: 0.4     // 텍스트 가중치
        };
        this.emotionHistory = [];
        this.onIntegratedUpdate = null;
    }

    // 웹캠 감정 업데이트
    updateWebcamEmotion(emotionData) {
        this.webcamEmotion = {
            primaryEmotion: emotionData.primaryEmotion,
            confidence: emotionData.confidence,
            valence: emotionData.valence,
            arousal: emotionData.arousal,
            engagement: emotionData.engagement,
            emotions: emotionData.emotions || {},
            timestamp: Date.now(),
            source: 'webcam'
        };

        this.calculateIntegratedScore();
    }

    // 텍스트 감정 업데이트
    updateTextEmotion(emotionData) {
        this.textEmotion = {
            primaryEmotion: emotionData.primaryEmotion || emotionData.primary_emotion,
            confidence: emotionData.confidence || emotionData.intensity || 0.5,
            valence: this.emotionToValence(emotionData.primaryEmotion || emotionData.primary_emotion),
            emotions: emotionData.emotions || {},
            timestamp: Date.now(),
            source: 'text'
        };

        this.calculateIntegratedScore();
    }

    // 감정을 valence로 변환
    emotionToValence(emotion) {
        const valenceMap = {
            happy: 0.8, joy: 0.8, 기쁨: 0.8, 행복: 0.8,
            sad: -0.6, 슬픔: -0.6,
            angry: -0.7, anger: -0.7, 분노: -0.7,
            fearful: -0.5, fear: -0.5, 두려움: -0.5, 불안: -0.5,
            disgusted: -0.4, disgust: -0.4, 혐오: -0.4,
            surprised: 0.3, surprise: 0.3, 놀람: 0.3,
            neutral: 0, 중립: 0, 평온: 0.2
        };
        return valenceMap[emotion] || 0;
    }

    // 통합 점수 계산
    calculateIntegratedScore() {
        if (!this.webcamEmotion && !this.textEmotion) {
            return null;
        }

        let integratedValence = 0;
        let integratedArousal = 0.5;
        let integratedEngagement = 0.5;
        let totalWeight = 0;
        let primaryEmotions = [];

        // 웹캠 감정 반영
        if (this.webcamEmotion && this.isRecent(this.webcamEmotion.timestamp)) {
            const weight = this.weights.webcam * this.webcamEmotion.confidence;
            integratedValence += this.webcamEmotion.valence * weight;
            integratedArousal = this.webcamEmotion.arousal || 0.5;
            integratedEngagement = this.webcamEmotion.engagement || 0.5;
            totalWeight += weight;
            primaryEmotions.push({
                emotion: this.webcamEmotion.primaryEmotion,
                weight: weight,
                source: 'webcam'
            });
        }

        // 텍스트 감정 반영
        if (this.textEmotion && this.isRecent(this.textEmotion.timestamp)) {
            const weight = this.weights.text * this.textEmotion.confidence;
            integratedValence += this.textEmotion.valence * weight;
            totalWeight += weight;
            primaryEmotions.push({
                emotion: this.textEmotion.primaryEmotion,
                weight: weight,
                source: 'text'
            });
        }

        // 정규화
        if (totalWeight > 0) {
            integratedValence /= totalWeight;
        }

        // 주요 감정 결정
        const dominantEmotion = primaryEmotions.sort((a, b) => b.weight - a.weight)[0];

        this.integratedScore = {
            valence: Math.max(-1, Math.min(1, integratedValence)),
            arousal: integratedArousal,
            engagement: integratedEngagement,
            primaryEmotion: dominantEmotion?.emotion || 'neutral',
            confidence: totalWeight,
            webcamContribution: this.webcamEmotion ? this.weights.webcam : 0,
            textContribution: this.textEmotion ? this.weights.text : 0,
            timestamp: Date.now()
        };

        // 히스토리 추가
        this.emotionHistory.push(this.integratedScore);
        if (this.emotionHistory.length > 100) {
            this.emotionHistory.shift();
        }

        // 콜백 호출
        if (this.onIntegratedUpdate) {
            this.onIntegratedUpdate(this.integratedScore);
        }

        return this.integratedScore;
    }

    // 최근 데이터인지 확인 (5초 이내)
    isRecent(timestamp) {
        return Date.now() - timestamp < 5000;
    }

    // 감정 일치도 계산
    getEmotionAgreement() {
        if (!this.webcamEmotion || !this.textEmotion) {
            return null;
        }

        const webcamValence = this.webcamEmotion.valence;
        const textValence = this.textEmotion.valence;

        // 같은 방향이면 일치, 다른 방향이면 불일치
        const agreement = 1 - Math.abs(webcamValence - textValence) / 2;

        return {
            score: agreement,
            label: agreement > 0.7 ? '높음' : agreement > 0.4 ? '보통' : '낮음',
            description: this.getAgreementDescription(agreement, webcamValence, textValence)
        };
    }

    getAgreementDescription(agreement, webcamValence, textValence) {
        if (agreement > 0.7) {
            return '표정과 대화 내용이 일치합니다.';
        } else if (webcamValence < -0.2 && textValence > 0.2) {
            return '표정은 부정적이지만 대화는 긍정적입니다. 감정을 숨기고 있을 수 있습니다.';
        } else if (webcamValence > 0.2 && textValence < -0.2) {
            return '표정은 긍정적이지만 대화는 부정적입니다. 내면의 감정을 탐색해 보세요.';
        } else {
            return '표정과 대화의 감정이 다소 다릅니다.';
        }
    }

    // 세션 요약
    getSessionSummary() {
        if (this.emotionHistory.length === 0) {
            return null;
        }

        const avgValence = this.emotionHistory.reduce((sum, e) => sum + e.valence, 0) / this.emotionHistory.length;
        const avgArousal = this.emotionHistory.reduce((sum, e) => sum + e.arousal, 0) / this.emotionHistory.length;

        // 감정 변화 추이
        const recentEmotions = this.emotionHistory.slice(-10);
        const earlyEmotions = this.emotionHistory.slice(0, 10);

        const recentAvg = recentEmotions.reduce((sum, e) => sum + e.valence, 0) / recentEmotions.length;
        const earlyAvg = earlyEmotions.length > 0
            ? earlyEmotions.reduce((sum, e) => sum + e.valence, 0) / earlyEmotions.length
            : recentAvg;

        const trend = recentAvg - earlyAvg;

        return {
            averageValence: avgValence,
            averageArousal: avgArousal,
            emotionTrend: trend > 0.1 ? '개선' : trend < -0.1 ? '하락' : '안정',
            totalDataPoints: this.emotionHistory.length,
            sessionDuration: this.emotionHistory.length > 0
                ? (this.emotionHistory[this.emotionHistory.length - 1].timestamp - this.emotionHistory[0].timestamp) / 1000
                : 0
        };
    }
}

// ============================================================================
// 지능형 상담 제안 시스템
// ============================================================================

class SmartCounselingSuggestion {
    constructor() {
        this.currentSuggestion = null;
        this.suggestionHistory = [];
        this.cooldownTime = 30000; // 30초 쿨다운
        this.lastSuggestionTime = 0;
        this.onSuggestion = null;

        this.suggestions = {
            // 부정적 감정 대응
            highSadness: {
                trigger: (data) => data.primaryEmotion === 'sad' && data.confidence > 0.6,
                priority: 'high',
                type: 'breathing',
                title: '😢 슬픔이 느껴지시나요?',
                message: '잠시 깊은 호흡을 해보시는 건 어떨까요? 4-7-8 호흡법이 마음을 진정시키는 데 도움이 됩니다.',
                action: {
                    label: '호흡 연습 시작',
                    type: 'breathing',
                    pattern: '4-7-8'
                }
            },
            highAnger: {
                trigger: (data) => data.primaryEmotion === 'angry' && data.confidence > 0.6,
                priority: 'high',
                type: 'grounding',
                title: '😠 화가 나셨나요?',
                message: '잠시 멈추고 주변을 둘러보세요. 5-4-3-2-1 그라운딩 기법으로 현재에 집중해 보세요.',
                action: {
                    label: '그라운딩 시작',
                    type: 'grounding'
                }
            },
            highFear: {
                trigger: (data) => data.primaryEmotion === 'fearful' && data.confidence > 0.5,
                priority: 'high',
                type: 'reassurance',
                title: '😨 불안하신가요?',
                message: '지금 이 순간은 안전합니다. 천천히 호흡하며 몸의 긴장을 풀어보세요.',
                action: {
                    label: '안정화 연습',
                    type: 'breathing',
                    pattern: 'calm'
                }
            },
            lowEngagement: {
                trigger: (data) => data.engagement < 0.3,
                priority: 'medium',
                type: 'engagement',
                title: '🎯 잠시 쉬어가도 괜찮아요',
                message: '집중이 어려우신 것 같아요. 잠시 스트레칭을 하거나 물을 마시는 건 어떨까요?',
                action: {
                    label: '휴식 타이머',
                    type: 'break',
                    duration: 60
                }
            },
            negativeValence: {
                trigger: (data) => data.valence < -0.4,
                priority: 'medium',
                type: 'support',
                title: '💚 힘든 감정이 느껴져요',
                message: '지금 느끼시는 감정은 자연스러운 거예요. 편하게 이야기해 주세요.',
                action: {
                    label: '감정 일기 쓰기',
                    type: 'journaling'
                }
            },
            emotionMismatch: {
                trigger: (data, analyzer) => {
                    const agreement = analyzer?.getEmotionAgreement();
                    return agreement && agreement.score < 0.4;
                },
                priority: 'low',
                type: 'exploration',
                title: '🤔 표정과 말이 다른 것 같아요',
                message: '내면의 감정을 탐색해 보시겠어요? 진짜 느끼시는 감정이 무엇인지 알아보는 건 어떨까요?',
                action: {
                    label: '감정 탐색하기',
                    type: 'exploration'
                }
            },
            positiveReinforcement: {
                trigger: (data) => data.primaryEmotion === 'happy' && data.valence > 0.5,
                priority: 'low',
                type: 'positive',
                title: '😊 좋은 에너지가 느껴져요!',
                message: '밝은 표정이 좋아요! 이 긍정적인 순간을 기억해 두세요.',
                action: {
                    label: '긍정 기록하기',
                    type: 'gratitude'
                }
            },
            crisis: {
                trigger: (data) => {
                    // 위기 감지: 지속적인 부정적 감정
                    return data.valence < -0.7 && data.arousal > 0.6;
                },
                priority: 'critical',
                type: 'crisis',
                title: '⚠️ 많이 힘드신 것 같아요',
                message: '지금 많이 힘드시다면, 전문 상담을 받아보시는 것도 좋습니다.',
                action: {
                    label: '위기 상담 연결',
                    type: 'crisis',
                    hotline: '1393'
                }
            }
        };
    }

    // 감정 데이터 평가 및 제안 생성
    evaluate(emotionData, integratedAnalyzer = null) {
        // 쿨다운 체크
        if (Date.now() - this.lastSuggestionTime < this.cooldownTime) {
            return null;
        }

        // 우선순위별 제안 평가
        const priorities = ['critical', 'high', 'medium', 'low'];

        for (const priority of priorities) {
            for (const [key, suggestion] of Object.entries(this.suggestions)) {
                if (suggestion.priority !== priority) continue;

                try {
                    if (suggestion.trigger(emotionData, integratedAnalyzer)) {
                        return this.createSuggestion(key, suggestion);
                    }
                } catch (e) {
                    console.warn(`제안 평가 오류 (${key}):`, e);
                }
            }
        }

        return null;
    }

    createSuggestion(key, suggestionConfig) {
        const suggestion = {
            id: `suggestion_${Date.now()}`,
            key: key,
            ...suggestionConfig,
            timestamp: Date.now()
        };

        this.currentSuggestion = suggestion;
        this.suggestionHistory.push(suggestion);
        this.lastSuggestionTime = Date.now();

        // 콜백 호출
        if (this.onSuggestion) {
            this.onSuggestion(suggestion);
        }

        return suggestion;
    }

    // 제안 표시 UI
    showSuggestion(suggestion, container) {
        if (!container || !suggestion) return;

        const suggestionEl = document.createElement('div');
        suggestionEl.className = `smart-suggestion suggestion-${suggestion.priority}`;
        suggestionEl.id = suggestion.id;

        suggestionEl.innerHTML = `
            <div class="suggestion-header">
                <span class="suggestion-title">${suggestion.title}</span>
                <button class="suggestion-close" onclick="this.parentElement.parentElement.remove()">✕</button>
            </div>
            <p class="suggestion-message">${suggestion.message}</p>
            ${suggestion.action ? `
                <button class="suggestion-action" data-action-type="${suggestion.action.type}">
                    ${suggestion.action.label}
                </button>
            ` : ''}
        `;

        container.appendChild(suggestionEl);

        // 액션 버튼 이벤트
        const actionBtn = suggestionEl.querySelector('.suggestion-action');
        if (actionBtn) {
            actionBtn.addEventListener('click', () => {
                this.executeAction(suggestion.action);
                suggestionEl.remove();
            });
        }

        // 자동 제거 (30초 후)
        setTimeout(() => {
            if (document.getElementById(suggestion.id)) {
                suggestionEl.classList.add('suggestion-fade-out');
                setTimeout(() => suggestionEl.remove(), 500);
            }
        }, 30000);
    }

    executeAction(action) {
        switch (action.type) {
            case 'breathing':
                // 호흡 연습 모달 열기
                if (window.breathingExercise) {
                    window.breathingExercise.startExercise(action.pattern);
                } else {
                    this.showBreathingModal(action.pattern);
                }
                break;
            case 'grounding':
                this.showGroundingExercise();
                break;
            case 'journaling':
                this.showJournalingPrompt();
                break;
            case 'break':
                this.startBreakTimer(action.duration);
                break;
            case 'crisis':
                this.showCrisisSupport(action.hotline);
                break;
            case 'gratitude':
                this.showGratitudePrompt();
                break;
            default:
                console.log('액션 실행:', action);
        }
    }

    showBreathingModal(pattern) {
        const patterns = {
            '4-7-8': { inhale: 4, hold: 7, exhale: 8, name: '4-7-8 호흡법' },
            'calm': { inhale: 4, hold: 4, exhale: 6, name: '안정 호흡법' },
            'box': { inhale: 4, hold: 4, exhale: 4, holdAfter: 4, name: '박스 호흡법' }
        };

        const p = patterns[pattern] || patterns['calm'];
        alert(`${p.name}\n\n1. ${p.inhale}초 동안 들이쉬세요\n2. ${p.hold}초 동안 참으세요\n3. ${p.exhale}초 동안 내쉬세요\n\n3-5회 반복해 보세요.`);
    }

    showGroundingExercise() {
        alert('5-4-3-2-1 그라운딩\n\n눈으로 5가지를 보세요\n귀로 4가지 소리를 들으세요\n3가지를 만져보세요\n2가지 냄새를 맡아보세요\n1가지를 맛보세요');
    }

    showJournalingPrompt() {
        const prompt = prompt('지금 느끼시는 감정을 자유롭게 적어보세요:');
        if (prompt) {
            console.log('감정 일기:', prompt);
            alert('감정을 표현해 주셔서 감사합니다. 기록되었습니다.');
        }
    }

    startBreakTimer(seconds) {
        alert(`${seconds}초 휴식 타이머가 시작됩니다. 잠시 스트레칭을 하거나 눈을 감고 쉬어보세요.`);
    }

    showCrisisSupport(hotline) {
        const confirmed = confirm(`위기 상담 전화: ${hotline}\n\n지금 많이 힘드시다면, 전문 상담사와 이야기해 보세요.\n\n전화 연결하시겠습니까?`);
        if (confirmed) {
            window.location.href = `tel:${hotline}`;
        }
    }

    showGratitudePrompt() {
        const gratitude = prompt('오늘 감사한 것 한 가지를 적어보세요:');
        if (gratitude) {
            console.log('감사 기록:', gratitude);
            alert('소중한 마음을 기록했습니다. 💚');
        }
    }
}

// ============================================================================
// 통합 매니저
// ============================================================================

class AdvancedEmotionManager {
    constructor(options = {}) {
        this.timelineGraph = null;
        this.integratedAnalyzer = new IntegratedEmotionAnalyzer();
        this.counselingSuggestion = new SmartCounselingSuggestion();

        this.options = {
            timelineContainerId: options.timelineContainerId || 'emotion-timeline-container',
            suggestionContainerId: options.suggestionContainerId || 'suggestion-container',
            enableTimeline: options.enableTimeline !== false,
            enableSuggestions: options.enableSuggestions !== false,
            ...options
        };

        this.init();
    }

    init() {
        // 타임라인 그래프 초기화
        if (this.options.enableTimeline) {
            const container = document.getElementById(this.options.timelineContainerId);
            if (container) {
                this.timelineGraph = new EmotionTimelineGraph(this.options.timelineContainerId);
            }
        }

        // 통합 분석 콜백 설정
        this.integratedAnalyzer.onIntegratedUpdate = (data) => {
            this.onIntegratedEmotionUpdate(data);
        };

        // 상담 제안 콜백 설정
        this.counselingSuggestion.onSuggestion = (suggestion) => {
            const container = document.getElementById(this.options.suggestionContainerId);
            if (container) {
                this.counselingSuggestion.showSuggestion(suggestion, container);
            }
        };
    }

    // 웹캠 감정 업데이트
    updateWebcamEmotion(emotionData) {
        this.integratedAnalyzer.updateWebcamEmotion(emotionData);

        if (this.timelineGraph) {
            this.timelineGraph.addDataPoint(emotionData);
        }
    }

    // 텍스트 감정 업데이트
    updateTextEmotion(emotionData) {
        this.integratedAnalyzer.updateTextEmotion(emotionData);
    }

    // 통합 감정 업데이트 처리
    onIntegratedEmotionUpdate(data) {
        // 상담 제안 평가
        if (this.options.enableSuggestions) {
            this.counselingSuggestion.evaluate(data, this.integratedAnalyzer);
        }

        // UI 업데이트 (통합 점수 표시)
        this.updateIntegratedUI(data);
    }

    updateIntegratedUI(data) {
        // 통합 감정 점수 표시
        const integratedScoreEl = document.getElementById('integrated-emotion-score');
        if (integratedScoreEl) {
            const emoji = data.valence > 0.2 ? '😊' : data.valence < -0.2 ? '😔' : '😐';
            const label = data.valence > 0.2 ? '긍정적' : data.valence < -0.2 ? '부정적' : '중립';
            integratedScoreEl.innerHTML = `
                <span class="integrated-emoji">${emoji}</span>
                <span class="integrated-label">${label}</span>
                <span class="integrated-confidence">(신뢰도: ${Math.round(data.confidence * 100)}%)</span>
            `;
        }

        // 일치도 표시
        const agreement = this.integratedAnalyzer.getEmotionAgreement();
        const agreementEl = document.getElementById('emotion-agreement');
        if (agreementEl && agreement) {
            agreementEl.innerHTML = `
                <span class="agreement-label">표정-대화 일치도:</span>
                <span class="agreement-value">${agreement.label}</span>
                <span class="agreement-desc">${agreement.description}</span>
            `;
        }
    }

    // 세션 요약 가져오기
    getSessionSummary() {
        return this.integratedAnalyzer.getSessionSummary();
    }

    // 리셋
    reset() {
        if (this.timelineGraph) {
            this.timelineGraph.clear();
        }
        this.integratedAnalyzer.emotionHistory = [];
    }
}

// ============================================================================
// CSS 스타일 주입
// ============================================================================

const advancedEmotionStyles = `
<style>
/* 타임라인 그래프 */
.timeline-graph-container {
    background: var(--surface, #fff);
    border-radius: var(--radius-md, 8px);
    padding: var(--space-sm, 12px);
    border: 1px solid var(--border, #e5e7eb);
    margin-bottom: var(--space-md, 16px);
}

.timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm, 12px);
    flex-wrap: wrap;
    gap: 8px;
}

.timeline-header h4 {
    margin: 0;
    font-size: 0.9rem;
    color: var(--text, #333);
}

.timeline-legend {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    color: var(--text-light, #666);
}

.legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.timeline-chart-area {
    height: 120px;
    background: linear-gradient(180deg, rgba(91, 138, 114, 0.03) 0%, transparent 100%);
    border-radius: var(--radius, 6px);
    overflow: hidden;
}

.timeline-chart-area canvas {
    width: 100%;
    height: 100%;
}

.timeline-stats {
    display: flex;
    justify-content: space-around;
    margin-top: var(--space-sm, 12px);
    padding-top: var(--space-sm, 12px);
    border-top: 1px solid var(--border, #e5e7eb);
}

.stat-item {
    text-align: center;
}

.stat-label {
    display: block;
    font-size: 0.7rem;
    color: var(--text-light, #666);
    margin-bottom: 2px;
}

.stat-value {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text, #333);
}

/* 스마트 제안 */
.smart-suggestion {
    background: var(--surface, #fff);
    border-radius: var(--radius-md, 8px);
    padding: var(--space-md, 16px);
    margin-bottom: var(--space-sm, 12px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    animation: suggestionSlideIn 0.3s ease;
    border-left: 4px solid var(--primary, #5B8A72);
}

.smart-suggestion.suggestion-critical {
    border-left-color: #ef4444;
    background: linear-gradient(135deg, #fff 0%, #fef2f2 100%);
}

.smart-suggestion.suggestion-high {
    border-left-color: #f59e0b;
    background: linear-gradient(135deg, #fff 0%, #fffbeb 100%);
}

.smart-suggestion.suggestion-medium {
    border-left-color: var(--primary, #5B8A72);
}

.smart-suggestion.suggestion-low {
    border-left-color: #6b7280;
}

@keyframes suggestionSlideIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.suggestion-fade-out {
    animation: suggestionFadeOut 0.5s ease forwards;
}

@keyframes suggestionFadeOut {
    to {
        opacity: 0;
        transform: translateY(-10px);
    }
}

.suggestion-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.suggestion-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text, #333);
}

.suggestion-close {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-light, #666);
    font-size: 1.2rem;
    padding: 0;
    line-height: 1;
}

.suggestion-message {
    font-size: 0.85rem;
    color: var(--text-light, #666);
    margin: 0 0 12px 0;
    line-height: 1.5;
}

.suggestion-action {
    background: var(--primary, #5B8A72);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: var(--radius-full, 20px);
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s;
}

.suggestion-action:hover {
    background: var(--primary-dark, #4a7360);
    transform: translateY(-1px);
}

/* 통합 감정 표시 */
.integrated-emotion-display {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: var(--space-sm, 12px);
    background: linear-gradient(135deg, rgba(91, 138, 114, 0.1) 0%, rgba(232, 178, 152, 0.1) 100%);
    border-radius: var(--radius-md, 8px);
    margin-bottom: var(--space-sm, 12px);
}

.integrated-emoji {
    font-size: 1.5rem;
}

.integrated-label {
    font-weight: 600;
    color: var(--text, #333);
}

.integrated-confidence {
    font-size: 0.75rem;
    color: var(--text-light, #666);
}

/* 일치도 표시 */
.emotion-agreement {
    font-size: 0.8rem;
    padding: 8px;
    background: var(--bg, #f9fafb);
    border-radius: var(--radius, 6px);
}

.agreement-label {
    color: var(--text-light, #666);
}

.agreement-value {
    font-weight: 600;
    color: var(--primary, #5B8A72);
    margin-left: 4px;
}

.agreement-desc {
    display: block;
    margin-top: 4px;
    color: var(--text-light, #666);
    font-size: 0.75rem;
}
</style>
`;

// 스타일 주입
if (typeof document !== 'undefined') {
    document.head.insertAdjacentHTML('beforeend', advancedEmotionStyles);
}

// ============================================================================
// 전역 내보내기
// ============================================================================

if (typeof window !== 'undefined') {
    window.EmotionTimelineGraph = EmotionTimelineGraph;
    window.IntegratedEmotionAnalyzer = IntegratedEmotionAnalyzer;
    window.SmartCounselingSuggestion = SmartCounselingSuggestion;
    window.AdvancedEmotionManager = AdvancedEmotionManager;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        EmotionTimelineGraph,
        IntegratedEmotionAnalyzer,
        SmartCounselingSuggestion,
        AdvancedEmotionManager
    };
}
