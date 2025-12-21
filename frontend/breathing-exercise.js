/**
 * 호흡 운동 애니메이션 (Breathing Exercise)
 * 불안 감소를 위한 가이드 호흡 애니메이션
 */

// ============================================================================
// Breathing Exercise Component
// ============================================================================

class BreathingExercise {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.isRunning = false;
        this.isPaused = false;
        this.currentPhase = 'ready'; // ready, inhale, hold, exhale
        this.currentRound = 0;
        this.totalRounds = 4;
        this.timer = null;
        this.phaseTimer = null;

        // 호흡 패턴 정의 (초 단위)
        this.patterns = {
            '4-7-8': { inhale: 4, hold: 7, exhale: 8, name: '4-7-8 호흡', description: '깊은 이완과 수면에 도움' },
            'box': { inhale: 4, hold: 4, exhale: 4, holdAfter: 4, name: '박스 호흡', description: '스트레스 해소에 효과적' },
            'calm': { inhale: 4, hold: 2, exhale: 6, name: '진정 호흡', description: '빠른 진정에 적합' },
            'energize': { inhale: 4, hold: 0, exhale: 2, name: '활력 호흡', description: '에너지 충전' }
        };

        this.currentPattern = this.patterns['4-7-8'];
        this.selectedPatternKey = '4-7-8';

        // 배경 사운드
        this.sounds = {
            rain: '🌧️ 빗소리',
            wave: '🌊 파도소리',
            forest: '🌲 숲소리',
            silent: '🔇 무음'
        };
        this.currentSound = 'silent';

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="breathing-widget">
                <div class="breathing-header">
                    <span class="breathing-icon">😮‍💨</span>
                    <h3>호흡 운동</h3>
                    <button class="breathing-settings-btn" id="breathing-settings-btn">⚙️</button>
                </div>

                <!-- 설정 패널 (접힘) -->
                <div class="breathing-settings" id="breathing-settings">
                    <div class="settings-section">
                        <label>호흡 패턴</label>
                        <div class="pattern-options" id="pattern-options">
                            ${Object.entries(this.patterns).map(([key, pattern]) => `
                                <button class="pattern-btn ${key === this.selectedPatternKey ? 'active' : ''}"
                                        data-pattern="${key}">
                                    <strong>${pattern.name}</strong>
                                    <small>${pattern.description}</small>
                                </button>
                            `).join('')}
                        </div>
                    </div>

                    <div class="settings-section">
                        <label>반복 횟수</label>
                        <div class="round-selector">
                            ${[2, 4, 6, 8].map(n => `
                                <button class="round-btn ${n === this.totalRounds ? 'active' : ''}"
                                        data-rounds="${n}">${n}회</button>
                            `).join('')}
                        </div>
                    </div>

                    <div class="settings-section">
                        <label>배경 소리</label>
                        <div class="sound-options">
                            ${Object.entries(this.sounds).map(([key, label]) => `
                                <button class="sound-btn ${key === this.currentSound ? 'active' : ''}"
                                        data-sound="${key}">${label}</button>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- 메인 애니메이션 영역 -->
                <div class="breathing-main">
                    <div class="breathing-circle-container">
                        <div class="breathing-circle" id="breathing-circle">
                            <div class="breathing-inner-circle">
                                <div class="breathing-text" id="breathing-text">준비</div>
                                <div class="breathing-timer" id="breathing-timer"></div>
                            </div>
                        </div>
                        <svg class="breathing-progress-ring" viewBox="0 0 200 200">
                            <circle class="progress-ring-bg" cx="100" cy="100" r="90"/>
                            <circle class="progress-ring-fill" id="progress-ring"
                                    cx="100" cy="100" r="90"/>
                        </svg>
                    </div>

                    <div class="breathing-phase-indicator">
                        <div class="phase-step" data-phase="inhale">
                            <span class="phase-dot"></span>
                            <span>들숨</span>
                        </div>
                        <div class="phase-arrow">→</div>
                        <div class="phase-step" data-phase="hold">
                            <span class="phase-dot"></span>
                            <span>참기</span>
                        </div>
                        <div class="phase-arrow">→</div>
                        <div class="phase-step" data-phase="exhale">
                            <span class="phase-dot"></span>
                            <span>날숨</span>
                        </div>
                    </div>

                    <div class="breathing-round-info" id="breathing-round-info">
                        시작하려면 아래 버튼을 눌러주세요
                    </div>
                </div>

                <!-- 컨트롤 버튼 -->
                <div class="breathing-controls">
                    <button class="breathing-btn breathing-btn-start" id="breathing-start">
                        <span class="btn-icon">▶</span>
                        <span class="btn-text">시작하기</span>
                    </button>
                    <button class="breathing-btn breathing-btn-pause hidden" id="breathing-pause">
                        <span class="btn-icon">⏸</span>
                        <span class="btn-text">일시정지</span>
                    </button>
                    <button class="breathing-btn breathing-btn-stop hidden" id="breathing-stop">
                        <span class="btn-icon">⏹</span>
                        <span class="btn-text">종료</span>
                    </button>
                </div>

                <!-- 완료 메시지 -->
                <div class="breathing-complete hidden" id="breathing-complete">
                    <div class="complete-emoji">🎉</div>
                    <h4>잘하셨어요!</h4>
                    <p>${this.totalRounds}회 호흡 완료</p>
                    <p class="complete-tip">잠시 눈을 감고 평온함을 느껴보세요</p>
                    <button class="breathing-btn breathing-btn-restart" id="breathing-restart">
                        다시 시작
                    </button>
                </div>
            </div>
        `;
    }

    bindEvents() {
        // 시작 버튼
        document.getElementById('breathing-start')?.addEventListener('click', () => {
            this.start();
        });

        // 일시정지 버튼
        document.getElementById('breathing-pause')?.addEventListener('click', () => {
            this.togglePause();
        });

        // 종료 버튼
        document.getElementById('breathing-stop')?.addEventListener('click', () => {
            this.stop();
        });

        // 다시 시작 버튼
        document.getElementById('breathing-restart')?.addEventListener('click', () => {
            this.restart();
        });

        // 설정 토글
        document.getElementById('breathing-settings-btn')?.addEventListener('click', () => {
            const settings = document.getElementById('breathing-settings');
            settings.classList.toggle('open');
        });

        // 패턴 선택
        document.getElementById('pattern-options')?.addEventListener('click', (e) => {
            const btn = e.target.closest('.pattern-btn');
            if (btn && !this.isRunning) {
                const pattern = btn.dataset.pattern;
                this.selectPattern(pattern);
            }
        });

        // 라운드 선택
        document.querySelectorAll('.round-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!this.isRunning) {
                    this.totalRounds = parseInt(btn.dataset.rounds);
                    document.querySelectorAll('.round-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                }
            });
        });

        // 사운드 선택
        document.querySelectorAll('.sound-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentSound = btn.dataset.sound;
                document.querySelectorAll('.sound-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }

    selectPattern(patternKey) {
        this.selectedPatternKey = patternKey;
        this.currentPattern = this.patterns[patternKey];

        document.querySelectorAll('.pattern-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.pattern === patternKey);
        });
    }

    start() {
        this.isRunning = true;
        this.isPaused = false;
        this.currentRound = 1;
        this.currentPhase = 'inhale';

        // UI 업데이트
        document.getElementById('breathing-start').classList.add('hidden');
        document.getElementById('breathing-pause').classList.remove('hidden');
        document.getElementById('breathing-stop').classList.remove('hidden');
        document.getElementById('breathing-complete').classList.add('hidden');
        document.getElementById('breathing-settings').classList.remove('open');

        this.runPhase();
    }

    togglePause() {
        this.isPaused = !this.isPaused;
        const pauseBtn = document.getElementById('breathing-pause');

        if (this.isPaused) {
            pauseBtn.innerHTML = '<span class="btn-icon">▶</span><span class="btn-text">계속하기</span>';
            clearInterval(this.phaseTimer);
            document.getElementById('breathing-circle').classList.add('paused');
        } else {
            pauseBtn.innerHTML = '<span class="btn-icon">⏸</span><span class="btn-text">일시정지</span>';
            document.getElementById('breathing-circle').classList.remove('paused');
            this.runPhase();
        }
    }

    stop() {
        this.isRunning = false;
        this.isPaused = false;
        clearInterval(this.phaseTimer);

        document.getElementById('breathing-start').classList.remove('hidden');
        document.getElementById('breathing-pause').classList.add('hidden');
        document.getElementById('breathing-stop').classList.add('hidden');

        this.resetUI();
    }

    restart() {
        document.getElementById('breathing-complete').classList.add('hidden');
        this.start();
    }

    resetUI() {
        const circle = document.getElementById('breathing-circle');
        const text = document.getElementById('breathing-text');
        const timer = document.getElementById('breathing-timer');
        const roundInfo = document.getElementById('breathing-round-info');

        circle.className = 'breathing-circle';
        text.textContent = '준비';
        timer.textContent = '';
        roundInfo.textContent = '시작하려면 아래 버튼을 눌러주세요';

        this.updatePhaseIndicator(null);
        this.updateProgressRing(0);
    }

    runPhase() {
        if (!this.isRunning || this.isPaused) return;

        const circle = document.getElementById('breathing-circle');
        const text = document.getElementById('breathing-text');
        const roundInfo = document.getElementById('breathing-round-info');

        // 라운드 정보 업데이트
        roundInfo.textContent = `라운드 ${this.currentRound}/${this.totalRounds}`;

        // 현재 단계에 따른 설정
        let duration, nextPhase, displayText;

        switch (this.currentPhase) {
            case 'inhale':
                duration = this.currentPattern.inhale;
                nextPhase = 'hold';
                displayText = '들숨';
                circle.className = 'breathing-circle inhale';
                break;
            case 'hold':
                duration = this.currentPattern.hold;
                nextPhase = 'exhale';
                displayText = '참기';
                circle.className = 'breathing-circle hold';
                break;
            case 'exhale':
                duration = this.currentPattern.exhale;
                nextPhase = this.currentPattern.holdAfter ? 'holdAfter' : 'inhale';
                displayText = '날숨';
                circle.className = 'breathing-circle exhale';
                break;
            case 'holdAfter':
                duration = this.currentPattern.holdAfter || 0;
                nextPhase = 'inhale';
                displayText = '참기';
                circle.className = 'breathing-circle hold';
                break;
        }

        text.textContent = displayText;
        this.updatePhaseIndicator(this.currentPhase);

        // 타이머 카운트다운
        let remaining = duration;
        this.updateTimer(remaining);
        this.animateProgressRing(duration);

        this.phaseTimer = setInterval(() => {
            remaining--;
            this.updateTimer(remaining);

            if (remaining <= 0) {
                clearInterval(this.phaseTimer);

                // 다음 단계로 이동
                if (nextPhase === 'inhale') {
                    // 라운드 완료
                    if (this.currentRound >= this.totalRounds) {
                        this.complete();
                        return;
                    }
                    this.currentRound++;
                }

                this.currentPhase = nextPhase;
                this.runPhase();
            }
        }, 1000);
    }

    updateTimer(seconds) {
        const timer = document.getElementById('breathing-timer');
        timer.textContent = seconds > 0 ? seconds : '';
    }

    updatePhaseIndicator(activePhase) {
        document.querySelectorAll('.phase-step').forEach(step => {
            const phase = step.dataset.phase;
            step.classList.toggle('active', phase === activePhase ||
                (activePhase === 'holdAfter' && phase === 'hold'));
        });
    }

    animateProgressRing(duration) {
        const ring = document.getElementById('progress-ring');
        const circumference = 2 * Math.PI * 90;

        ring.style.strokeDasharray = `${circumference} ${circumference}`;
        ring.style.strokeDashoffset = circumference;
        ring.style.transition = `stroke-dashoffset ${duration}s linear`;

        // 약간의 딜레이 후 애니메이션 시작
        setTimeout(() => {
            ring.style.strokeDashoffset = 0;
        }, 50);
    }

    updateProgressRing(progress) {
        const ring = document.getElementById('progress-ring');
        const circumference = 2 * Math.PI * 90;
        const offset = circumference * (1 - progress);

        ring.style.transition = 'none';
        ring.style.strokeDasharray = `${circumference} ${circumference}`;
        ring.style.strokeDashoffset = offset;
    }

    complete() {
        this.isRunning = false;
        clearInterval(this.phaseTimer);

        // 완료 화면 표시
        document.getElementById('breathing-pause').classList.add('hidden');
        document.getElementById('breathing-stop').classList.add('hidden');
        document.getElementById('breathing-start').classList.remove('hidden');

        const completeDiv = document.getElementById('breathing-complete');
        completeDiv.querySelector('p').textContent = `${this.totalRounds}회 호흡 완료`;
        completeDiv.classList.remove('hidden');

        document.getElementById('breathing-circle').className = 'breathing-circle complete';
        document.getElementById('breathing-text').textContent = '완료';
        document.getElementById('breathing-timer').textContent = '🎉';

        // 완료 기록 (실제 구현에서는 API 호출)
        this.logCompletion();
    }

    async logCompletion() {
        try {
            // await api.request('/breathing/log', {
            //     method: 'POST',
            //     body: JSON.stringify({
            //         pattern: this.selectedPatternKey,
            //         rounds: this.totalRounds,
            //         completed_at: new Date()
            //     })
            // });
            console.log('호흡 운동 완료 기록:', {
                pattern: this.selectedPatternKey,
                rounds: this.totalRounds
            });
        } catch (error) {
            console.error('완료 기록 실패:', error);
        }
    }
}

// ============================================================================
// 전역 함수
// ============================================================================

function initBreathingExercise(containerId = 'breathing-container') {
    return new BreathingExercise(containerId);
}

// 자동 초기화
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('breathing-container');
    if (container) {
        window.breathingExercise = new BreathingExercise('breathing-container');
    }
});
