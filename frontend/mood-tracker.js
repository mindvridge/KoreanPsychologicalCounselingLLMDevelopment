/**
 * 주간 기분 트래커 (Weekly Mood Tracker)
 * 기분 변화를 시각적으로 표현하는 인터랙티브 그래프
 */

// ============================================================================
// Mood Tracker Component
// ============================================================================

class MoodTracker {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.moodData = [];
        this.currentWeekOffset = 0;

        // 기분 이모지 매핑
        this.moodEmojis = {
            1: '😢', 2: '😢', 3: '😕', 4: '😕', 5: '😐',
            6: '🙂', 7: '🙂', 8: '😊', 9: '😊', 10: '😄'
        };

        // 기분 레이블
        this.moodLabels = {
            1: '매우 힘듦', 2: '힘듦', 3: '조금 힘듦', 4: '약간 힘듦', 5: '보통',
            6: '약간 좋음', 7: '괜찮음', 8: '좋음', 9: '매우 좋음', 10: '최고!'
        };

        // 요일
        this.dayNames = ['일', '월', '화', '수', '목', '금', '토'];

        this.init();
    }

    init() {
        this.render();
        this.loadMoodData();
    }

    // 데모 데이터 생성 (실제로는 API에서 로드)
    generateDemoData() {
        const data = [];
        const today = new Date();

        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);

            // 랜덤하지만 점진적으로 상승하는 트렌드
            const baseMood = 4 + Math.floor((7 - i) * 0.5);
            const variation = Math.floor(Math.random() * 3) - 1;
            const mood = Math.max(1, Math.min(10, baseMood + variation));

            data.push({
                date: date,
                dateStr: this.formatDate(date),
                dayName: this.dayNames[date.getDay()],
                mood: mood,
                note: ''
            });
        }

        return data;
    }

    formatDate(date) {
        return `${date.getMonth() + 1}/${date.getDate()}`;
    }

    async loadMoodData() {
        try {
            // 실제 구현에서는 API 호출
            // const response = await api.request('/mood/weekly');
            // this.moodData = response.data;

            // 데모 데이터 사용
            this.moodData = this.generateDemoData();
            this.updateChart();
        } catch (error) {
            console.error('기분 데이터 로드 실패:', error);
        }
    }

    calculateStats() {
        if (this.moodData.length === 0) return null;

        const moods = this.moodData.map(d => d.mood);
        const average = moods.reduce((a, b) => a + b, 0) / moods.length;

        // 트렌드 계산
        const firstHalf = moods.slice(0, Math.floor(moods.length / 2));
        const secondHalf = moods.slice(Math.floor(moods.length / 2));
        const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
        const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
        const trendDiff = secondAvg - firstAvg;

        let trend, trendIcon, trendClass;
        if (trendDiff > 0.5) {
            trend = '상승 중';
            trendIcon = '📈';
            trendClass = 'trend-up';
        } else if (trendDiff < -0.5) {
            trend = '주의 필요';
            trendIcon = '📉';
            trendClass = 'trend-down';
        } else {
            trend = '안정적';
            trendIcon = '➡️';
            trendClass = 'trend-stable';
        }

        return {
            average: average.toFixed(1),
            trend,
            trendIcon,
            trendClass,
            highest: Math.max(...moods),
            lowest: Math.min(...moods)
        };
    }

    generateInsight() {
        const stats = this.calculateStats();
        if (!stats) return '';

        const insights = [];

        if (stats.trendClass === 'trend-up') {
            insights.push('기분이 점점 좋아지고 있어요! 무엇이 도움이 되었나요?');
        } else if (stats.trendClass === 'trend-down') {
            insights.push('최근 힘든 시간을 보내고 계시네요. 이야기 나눠볼까요?');
        }

        if (parseFloat(stats.average) >= 7) {
            insights.push('평균 기분이 좋은 편이에요. 잘 지내고 계시네요! 💚');
        }

        if (stats.highest - stats.lowest >= 4) {
            insights.push('기분 변화가 큰 한 주였네요. 안정화에 도움이 필요할 수 있어요.');
        }

        return insights[0] || '꾸준히 기록해주셔서 감사해요!';
    }

    render() {
        this.container.innerHTML = `
            <div class="mood-tracker-widget">
                <div class="mood-tracker-header">
                    <div class="mood-tracker-title">
                        <span class="mood-tracker-icon">📈</span>
                        <h3>이번 주 기분 변화</h3>
                    </div>
                    <div class="mood-tracker-nav">
                        <button class="mood-nav-btn" id="mood-prev-week">◀</button>
                        <span class="mood-week-label" id="mood-week-label">이번 주</span>
                        <button class="mood-nav-btn" id="mood-next-week" disabled>▶</button>
                    </div>
                </div>

                <div class="mood-chart-container">
                    <div class="mood-chart" id="mood-chart">
                        <!-- 차트가 여기에 렌더링됨 -->
                    </div>
                    <div class="mood-y-axis">
                        <span>10</span>
                        <span>5</span>
                        <span>1</span>
                    </div>
                </div>

                <div class="mood-stats" id="mood-stats">
                    <!-- 통계가 여기에 렌더링됨 -->
                </div>

                <div class="mood-insight" id="mood-insight">
                    <!-- 인사이트가 여기에 렌더링됨 -->
                </div>

                <div class="mood-quick-log">
                    <span>오늘 기분 기록하기</span>
                    <div class="mood-quick-buttons" id="mood-quick-buttons">
                        <!-- 빠른 입력 버튼들 -->
                    </div>
                </div>
            </div>
        `;

        this.bindEvents();
        this.renderQuickLogButtons();
    }

    renderQuickLogButtons() {
        const container = document.getElementById('mood-quick-buttons');
        const quickMoods = [2, 4, 6, 8, 10];

        container.innerHTML = quickMoods.map(mood => `
            <button class="mood-quick-btn" data-mood="${mood}">
                ${this.moodEmojis[mood]}
            </button>
        `).join('');

        // 버튼 이벤트
        container.querySelectorAll('.mood-quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mood = parseInt(e.target.dataset.mood);
                this.logMood(mood);
            });
        });
    }

    updateChart() {
        const chartContainer = document.getElementById('mood-chart');
        const statsContainer = document.getElementById('mood-stats');
        const insightContainer = document.getElementById('mood-insight');

        // 차트 렌더링
        chartContainer.innerHTML = this.moodData.map((data, index) => {
            const height = (data.mood / 10) * 100;
            const isToday = index === this.moodData.length - 1;

            return `
                <div class="mood-bar-wrapper ${isToday ? 'today' : ''}">
                    <div class="mood-emoji">${this.moodEmojis[data.mood]}</div>
                    <div class="mood-bar-container">
                        <div class="mood-bar" style="height: ${height}%;" data-mood="${data.mood}">
                            <span class="mood-value">${data.mood}</span>
                        </div>
                    </div>
                    <div class="mood-day">${data.dayName}</div>
                    <div class="mood-date">${data.dateStr}</div>
                </div>
            `;
        }).join('');

        // 바 애니메이션
        setTimeout(() => {
            chartContainer.querySelectorAll('.mood-bar').forEach((bar, i) => {
                setTimeout(() => {
                    bar.classList.add('animated');
                }, i * 100);
            });
        }, 100);

        // 통계 렌더링
        const stats = this.calculateStats();
        if (stats) {
            statsContainer.innerHTML = `
                <div class="mood-stat-item">
                    <span class="stat-label">평균</span>
                    <span class="stat-value">${stats.average}</span>
                </div>
                <div class="mood-stat-item ${stats.trendClass}">
                    <span class="stat-label">추세</span>
                    <span class="stat-value">${stats.trendIcon} ${stats.trend}</span>
                </div>
                <div class="mood-stat-item">
                    <span class="stat-label">최고</span>
                    <span class="stat-value">${this.moodEmojis[stats.highest]}</span>
                </div>
            `;
        }

        // 인사이트 렌더링
        const insight = this.generateInsight();
        insightContainer.innerHTML = `
            <div class="insight-icon">💡</div>
            <p>${insight}</p>
        `;
    }

    bindEvents() {
        document.getElementById('mood-prev-week')?.addEventListener('click', () => {
            this.currentWeekOffset++;
            this.loadMoodData();
            this.updateWeekLabel();
        });

        document.getElementById('mood-next-week')?.addEventListener('click', () => {
            if (this.currentWeekOffset > 0) {
                this.currentWeekOffset--;
                this.loadMoodData();
                this.updateWeekLabel();
            }
        });
    }

    updateWeekLabel() {
        const label = document.getElementById('mood-week-label');
        const nextBtn = document.getElementById('mood-next-week');

        if (this.currentWeekOffset === 0) {
            label.textContent = '이번 주';
            nextBtn.disabled = true;
        } else {
            label.textContent = `${this.currentWeekOffset}주 전`;
            nextBtn.disabled = false;
        }
    }

    async logMood(mood) {
        try {
            // API 호출 (실제 구현)
            // await api.request('/mood', {
            //     method: 'POST',
            //     body: JSON.stringify({ mood, date: new Date() })
            // });

            // 로컬 업데이트 (데모)
            const today = this.moodData[this.moodData.length - 1];
            if (today) {
                today.mood = mood;
                this.updateChart();
                this.showToast(`오늘 기분: ${this.moodEmojis[mood]} ${this.moodLabels[mood]}`);
            }
        } catch (error) {
            console.error('기분 기록 실패:', error);
        }
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'mood-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }
}

// ============================================================================
// 전역 함수
// ============================================================================

function initMoodTracker(containerId = 'mood-tracker-container') {
    return new MoodTracker(containerId);
}

// 자동 초기화 (DOM 로드 후)
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('mood-tracker-container');
    if (container) {
        window.moodTracker = new MoodTracker('mood-tracker-container');
    }
});
