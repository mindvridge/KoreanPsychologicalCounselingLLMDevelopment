/**
 * Emotion Tracking Visualization
 * 감정 추적 차트 및 리포트 UI
 *
 * 의존성: Chart.js (CDN)
 */

class EmotionChartManager {
    constructor(options = {}) {
        this.options = {
            apiUrl: options.apiUrl || CONFIG.API_URL,
            containerId: options.containerId || 'emotion-dashboard',
            refreshInterval: options.refreshInterval || 60000, // 1분
            ...options
        };

        this.charts = {};
        this.currentData = null;
        this.userId = options.userId || 'default';

        // Chart.js 로드 확인
        this.chartJsLoaded = typeof Chart !== 'undefined';
    }

    // =========================================================================
    // 초기화
    // =========================================================================

    async initialize() {
        if (!this.chartJsLoaded) {
            await this.loadChartJs();
        }

        this.createDashboard();
        await this.refreshData();

        // 자동 새로고침
        if (this.options.refreshInterval > 0) {
            setInterval(() => this.refreshData(), this.options.refreshInterval);
        }
    }

    async loadChartJs() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            script.onload = () => {
                this.chartJsLoaded = true;
                resolve();
            };
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    createDashboard() {
        const container = document.getElementById(this.options.containerId);
        if (!container) {
            console.error('Emotion dashboard container not found');
            return;
        }

        container.innerHTML = `
            <div class="emotion-dashboard">
                <div class="emotion-header">
                    <h2>감정 추적</h2>
                    <div class="emotion-period-selector">
                        <button class="period-btn active" data-days="7">7일</button>
                        <button class="period-btn" data-days="14">14일</button>
                        <button class="period-btn" data-days="30">30일</button>
                    </div>
                </div>

                <div class="emotion-charts-grid">
                    <!-- 감정 타임라인 차트 -->
                    <div class="chart-card timeline-card">
                        <h3>감정 변화</h3>
                        <div class="chart-container">
                            <canvas id="emotion-timeline-chart"></canvas>
                        </div>
                    </div>

                    <!-- 감정 분포 파이 차트 -->
                    <div class="chart-card pie-card">
                        <h3>감정 분포</h3>
                        <div class="chart-container pie-container">
                            <canvas id="emotion-pie-chart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- 주간 리포트 -->
                <div class="weekly-report-card">
                    <h3>주간 리포트</h3>
                    <div id="weekly-report-content" class="report-content">
                        <p class="loading">리포트를 불러오는 중...</p>
                    </div>
                </div>

                <!-- 최근 감정 기록 -->
                <div class="recent-emotions-card">
                    <h3>최근 감정</h3>
                    <div id="recent-emotions-list" class="emotions-list">
                        <p class="loading">로딩 중...</p>
                    </div>
                </div>
            </div>
        `;

        // 이벤트 리스너
        container.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                container.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.refreshData(parseInt(e.target.dataset.days));
            });
        });
    }

    // =========================================================================
    // 데이터 로드
    // =========================================================================

    async refreshData(days = 7) {
        try {
            // API에서 데이터 가져오기
            const [chartData, pieData, reportData, recentData] = await Promise.all([
                this.fetchChartData(days),
                this.fetchPieData(days),
                this.fetchWeeklyReport(),
                this.fetchRecentEmotions()
            ]);

            this.currentData = { chartData, pieData, reportData, recentData };

            // 차트 업데이트
            this.updateTimelineChart(chartData);
            this.updatePieChart(pieData);
            this.updateWeeklyReport(reportData);
            this.updateRecentEmotions(recentData);

        } catch (error) {
            console.error('Failed to refresh emotion data:', error);
            this.showError('데이터를 불러오는데 실패했습니다.');
        }
    }

    async fetchChartData(days) {
        try {
            const response = await fetch(
                `${this.options.apiUrl}/emotion/chart?user_id=${this.userId}&days=${days}`
            );
            if (!response.ok) throw new Error('Chart data fetch failed');
            return await response.json();
        } catch {
            // 데모 데이터 반환
            return this.generateDemoChartData(days);
        }
    }

    async fetchPieData(days) {
        try {
            const response = await fetch(
                `${this.options.apiUrl}/emotion/distribution?user_id=${this.userId}&days=${days}`
            );
            if (!response.ok) throw new Error('Pie data fetch failed');
            return await response.json();
        } catch {
            return this.generateDemoPieData();
        }
    }

    async fetchWeeklyReport() {
        try {
            const response = await fetch(
                `${this.options.apiUrl}/emotion/weekly-report?user_id=${this.userId}`
            );
            if (!response.ok) throw new Error('Report fetch failed');
            return await response.json();
        } catch {
            return this.generateDemoReport();
        }
    }

    async fetchRecentEmotions() {
        try {
            const response = await fetch(
                `${this.options.apiUrl}/emotion/recent?user_id=${this.userId}&hours=24`
            );
            if (!response.ok) throw new Error('Recent emotions fetch failed');
            return await response.json();
        } catch {
            return this.generateDemoRecentEmotions();
        }
    }

    // =========================================================================
    // 차트 업데이트
    // =========================================================================

    updateTimelineChart(data) {
        const ctx = document.getElementById('emotion-timeline-chart');
        if (!ctx) return;

        if (this.charts.timeline) {
            this.charts.timeline.destroy();
        }

        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: '감정 상태',
                        data: data.datasets[0].data,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: data.datasets[0].data.map(v =>
                            v > 0.3 ? '#4CAF50' : v < -0.3 ? '#f44336' : '#FFC107'
                        )
                    },
                    {
                        label: '활성화 수준',
                        data: data.datasets[1].data,
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        hidden: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            font: { family: "'Noto Sans KR', sans-serif" }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                if (value === null) return '기록 없음';

                                if (context.datasetIndex === 0) {
                                    if (value > 0.3) return `긍정적: ${(value * 100).toFixed(0)}%`;
                                    if (value < -0.3) return `부정적: ${(Math.abs(value) * 100).toFixed(0)}%`;
                                    return `중립: ${(Math.abs(value) * 100).toFixed(0)}%`;
                                }
                                return `활성화: ${(value * 100).toFixed(0)}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: -1,
                        max: 1,
                        ticks: {
                            callback: (value) => {
                                if (value === 1) return '긍정';
                                if (value === 0) return '중립';
                                if (value === -1) return '부정';
                                return '';
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    updatePieChart(data) {
        const ctx = document.getElementById('emotion-pie-chart');
        if (!ctx) return;

        if (this.charts.pie) {
            this.charts.pie.destroy();
        }

        this.charts.pie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.datasets[0].data,
                    backgroundColor: data.datasets[0].backgroundColor,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: { family: "'Noto Sans KR', sans-serif" },
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    updateWeeklyReport(data) {
        const container = document.getElementById('weekly-report-content');
        if (!container) return;

        const trendIcons = {
            improving: '📈',
            stable: '➡️',
            declining: '📉',
            insufficient_data: '❓'
        };

        const trendLabels = {
            improving: '개선 중',
            stable: '안정적',
            declining: '주의 필요',
            insufficient_data: '데이터 부족'
        };

        container.innerHTML = `
            <div class="report-summary">
                <div class="report-stat">
                    <span class="stat-icon">${trendIcons[data.overall_trend] || '❓'}</span>
                    <span class="stat-label">전체 트렌드</span>
                    <span class="stat-value">${trendLabels[data.overall_trend] || '알 수 없음'}</span>
                </div>
                <div class="report-stat">
                    <span class="stat-icon">💬</span>
                    <span class="stat-label">총 세션</span>
                    <span class="stat-value">${data.total_sessions || 0}회</span>
                </div>
            </div>

            ${data.dominant_emotions && data.dominant_emotions.length > 0 ? `
                <div class="report-section">
                    <h4>주요 감정</h4>
                    <div class="emotion-tags">
                        ${data.dominant_emotions.slice(0, 3).map((e, i) => `
                            <span class="emotion-tag rank-${i + 1}">${e[0] || e}</span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            ${data.insights && data.insights.length > 0 ? `
                <div class="report-section">
                    <h4>인사이트</h4>
                    <ul class="insight-list">
                        ${data.insights.map(insight => `
                            <li>${insight}</li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}

            ${data.recommendations && data.recommendations.length > 0 ? `
                <div class="report-section">
                    <h4>추천</h4>
                    <ul class="recommendation-list">
                        ${data.recommendations.map(rec => `
                            <li>${rec}</li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    }

    updateRecentEmotions(data) {
        const container = document.getElementById('recent-emotions-list');
        if (!container) return;

        if (!data || data.length === 0) {
            container.innerHTML = '<p class="no-data">최근 감정 기록이 없습니다.</p>';
            return;
        }

        const emotionEmojis = {
            '기쁨': '😊',
            '슬픔': '😢',
            '분노': '😠',
            '두려움': '😨',
            '불안': '😰',
            '평온': '😌',
            '희망': '🌟',
            '외로움': '😔',
            '스트레스': '😫',
            '감사': '🙏',
            '중립': '😐'
        };

        container.innerHTML = data.slice(0, 5).map(emotion => `
            <div class="emotion-item">
                <span class="emotion-emoji">${emotionEmojis[emotion.primary_emotion] || '😐'}</span>
                <div class="emotion-details">
                    <span class="emotion-name">${emotion.primary_emotion}</span>
                    <span class="emotion-time">${this.formatTime(emotion.timestamp)}</span>
                </div>
                <div class="emotion-intensity" style="width: ${emotion.intensity * 100}%"></div>
            </div>
        `).join('');
    }

    // =========================================================================
    // 데모 데이터
    // =========================================================================

    generateDemoChartData(days) {
        const labels = [];
        const valenceData = [];
        const arousalData = [];

        for (let i = days - 1; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(`${date.getMonth() + 1}/${date.getDate()}`);

            // 랜덤 데이터 (트렌드 있게)
            const baseValence = -0.2 + (i / days) * 0.4 + (Math.random() - 0.5) * 0.3;
            valenceData.push(Math.max(-1, Math.min(1, baseValence)));

            const arousal = 0.4 + (Math.random() - 0.5) * 0.4;
            arousalData.push(arousal);
        }

        return {
            labels,
            datasets: [
                { data: valenceData },
                { data: arousalData }
            ]
        };
    }

    generateDemoPieData() {
        return {
            labels: ['평온', '불안', '기쁨', '스트레스', '슬픔'],
            datasets: [{
                data: [30, 25, 20, 15, 10],
                backgroundColor: ['#90EE90', '#FFA500', '#FFD700', '#FF6347', '#4169E1']
            }]
        };
    }

    generateDemoReport() {
        return {
            overall_trend: 'stable',
            total_sessions: 12,
            dominant_emotions: ['평온', '불안', '기쁨'],
            insights: [
                '➡️ 이번 주 감정 상태가 안정적으로 유지되고 있어요.',
                '😌 평온한 시간이 많았어요. 좋은 흐름이에요!',
                '💬 하루 평균 2.4회 대화하셨어요.'
            ],
            recommendations: [
                '✨ 지금의 좋은 에너지를 유지하세요!',
                '🧘 깊은 호흡 운동으로 불안감을 관리해보세요.',
                '📔 이 좋은 순간들을 기록으로 남겨두세요.'
            ]
        };
    }

    generateDemoRecentEmotions() {
        const emotions = ['평온', '불안', '기쁨', '스트레스', '희망'];
        const result = [];

        for (let i = 0; i < 5; i++) {
            const timestamp = new Date();
            timestamp.setHours(timestamp.getHours() - i * 3);

            result.push({
                primary_emotion: emotions[i],
                intensity: 0.4 + Math.random() * 0.5,
                timestamp: timestamp.toISOString()
            });
        }

        return result;
    }

    // =========================================================================
    // 유틸리티
    // =========================================================================

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return '방금 전';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
        return `${Math.floor(diff / 86400000)}일 전`;
    }

    showError(message) {
        const container = document.getElementById(this.options.containerId);
        if (container) {
            const errorEl = document.createElement('div');
            errorEl.className = 'emotion-error';
            errorEl.textContent = message;
            container.prepend(errorEl);
            setTimeout(() => errorEl.remove(), 5000);
        }
    }

    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }
}


// CSS 스타일 추가
const emotionChartStyles = `
<style>
.emotion-dashboard {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.emotion-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}

.emotion-header h2 {
    font-size: 24px;
    font-weight: 600;
    color: #333;
}

.emotion-period-selector {
    display: flex;
    gap: 8px;
}

.period-btn {
    padding: 8px 16px;
    border: 1px solid #ddd;
    border-radius: 20px;
    background: white;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
}

.period-btn:hover {
    background: #f5f5f5;
}

.period-btn.active {
    background: #4CAF50;
    color: white;
    border-color: #4CAF50;
}

.emotion-charts-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

@media (max-width: 768px) {
    .emotion-charts-grid {
        grid-template-columns: 1fr;
    }
}

.chart-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chart-card h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #333;
}

.chart-container {
    height: 250px;
    position: relative;
}

.pie-container {
    height: 200px;
}

.weekly-report-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.weekly-report-card h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #333;
}

.report-summary {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.report-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 24px;
    background: #f8f9fa;
    border-radius: 12px;
    min-width: 120px;
}

.stat-icon {
    font-size: 24px;
    margin-bottom: 8px;
}

.stat-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
}

.stat-value {
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

.report-section {
    margin-top: 16px;
}

.report-section h4 {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin-bottom: 12px;
}

.emotion-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.emotion-tag {
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 13px;
    background: #e3f2fd;
    color: #1976d2;
}

.emotion-tag.rank-1 {
    background: #fff3e0;
    color: #f57c00;
    font-weight: 600;
}

.emotion-tag.rank-2 {
    background: #e8f5e9;
    color: #388e3c;
}

.emotion-tag.rank-3 {
    background: #f3e5f5;
    color: #7b1fa2;
}

.insight-list, .recommendation-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.insight-list li, .recommendation-list li {
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
    font-size: 14px;
    line-height: 1.6;
    color: #444;
}

.insight-list li:last-child, .recommendation-list li:last-child {
    border-bottom: none;
}

.recent-emotions-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.recent-emotions-card h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #333;
}

.emotions-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.emotion-item {
    display: flex;
    align-items: center;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 8px;
    position: relative;
    overflow: hidden;
}

.emotion-emoji {
    font-size: 24px;
    margin-right: 12px;
}

.emotion-details {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.emotion-name {
    font-weight: 500;
    color: #333;
}

.emotion-time {
    font-size: 12px;
    color: #888;
}

.emotion-intensity {
    position: absolute;
    left: 0;
    bottom: 0;
    height: 3px;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    border-radius: 0 3px 3px 0;
}

.loading {
    color: #888;
    text-align: center;
    padding: 20px;
}

.no-data {
    color: #888;
    text-align: center;
    padding: 20px;
    font-style: italic;
}

.emotion-error {
    background: #ffebee;
    color: #c62828;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    text-align: center;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    .emotion-dashboard {
        background: #1a1a1a;
    }

    .emotion-header h2 {
        color: #fff;
    }

    .period-btn {
        background: #2d2d2d;
        border-color: #404040;
        color: #fff;
    }

    .period-btn:hover {
        background: #3d3d3d;
    }

    .chart-card, .weekly-report-card, .recent-emotions-card {
        background: #2d2d2d;
    }

    .chart-card h3, .weekly-report-card h3, .recent-emotions-card h3 {
        color: #fff;
    }

    .report-stat {
        background: #383838;
    }

    .stat-value, .emotion-name {
        color: #fff;
    }

    .emotion-item {
        background: #383838;
    }

    .insight-list li, .recommendation-list li {
        color: #ccc;
        border-color: #404040;
    }
}
</style>
`;

// 스타일 주입
document.head.insertAdjacentHTML('beforeend', emotionChartStyles);

// Export
window.EmotionChartManager = EmotionChartManager;
