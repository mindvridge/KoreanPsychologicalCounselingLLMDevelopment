/**
 * Session Summary UI
 * 세션 요약 표시 및 관리
 */

class SessionSummaryManager {
    constructor(options = {}) {
        this.options = {
            apiUrl: options.apiUrl || CONFIG.API_URL,
            containerId: options.containerId || 'session-summary-container',
            userId: options.userId || 'default',
            ...options
        };

        this.currentSummary = null;
        this.summaryHistory = [];
    }

    // =========================================================================
    // 요약 요청
    // =========================================================================

    async requestSummary(sessionId, conversationHistory) {
        try {
            const response = await fetch(`${this.options.apiUrl}/session/summary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_id: this.options.userId,
                    conversation_history: conversationHistory
                })
            });

            if (!response.ok) {
                throw new Error('Summary request failed');
            }

            this.currentSummary = await response.json();
            return this.currentSummary;

        } catch (error) {
            console.error('Failed to get session summary:', error);
            // 데모 요약 생성
            this.currentSummary = this.generateDemoSummary(sessionId, conversationHistory);
            return this.currentSummary;
        }
    }

    async getSummaryHistory(limit = 10) {
        try {
            const response = await fetch(
                `${this.options.apiUrl}/session/history?user_id=${this.options.userId}&limit=${limit}`
            );

            if (!response.ok) {
                throw new Error('History fetch failed');
            }

            this.summaryHistory = await response.json();
            return this.summaryHistory;

        } catch (error) {
            console.error('Failed to get summary history:', error);
            return this.generateDemoHistory();
        }
    }

    // =========================================================================
    // UI 렌더링
    // =========================================================================

    showSummaryModal(summary = null) {
        const summaryData = summary || this.currentSummary;
        if (!summaryData) {
            console.warn('No summary data available');
            return;
        }

        // 모달 생성
        const modal = document.createElement('div');
        modal.className = 'summary-modal';
        modal.innerHTML = `
            <div class="summary-modal-overlay"></div>
            <div class="summary-modal-content">
                <button class="summary-modal-close">&times;</button>
                ${this.renderSummaryContent(summaryData)}
            </div>
        `;

        document.body.appendChild(modal);

        // 애니메이션
        requestAnimationFrame(() => {
            modal.classList.add('active');
        });

        // 닫기 이벤트
        modal.querySelector('.summary-modal-close').addEventListener('click', () => {
            this.closeModal(modal);
        });

        modal.querySelector('.summary-modal-overlay').addEventListener('click', () => {
            this.closeModal(modal);
        });

        // ESC 키
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.closeModal(modal);
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }

    closeModal(modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }

    renderSummaryContent(summary) {
        const emotionShiftLabels = {
            positive: { emoji: '📈', text: '긍정적 변화' },
            stable: { emoji: '➡️', text: '안정적' },
            negative: { emoji: '📉', text: '주의 필요' }
        };

        const shift = emotionShiftLabels[summary.emotional_shift] || emotionShiftLabels.stable;

        return `
            <div class="summary-header">
                <h2>📋 세션 요약</h2>
                <div class="summary-meta">
                    <span class="summary-date">
                        ${this.formatDate(summary.start_time || summary.date)}
                    </span>
                    <span class="summary-duration">
                        ⏱️ ${summary.duration_minutes || 0}분
                    </span>
                </div>
            </div>

            <div class="summary-body">
                <!-- 요약 -->
                <section class="summary-section">
                    <h3>요약</h3>
                    <p class="summary-text">${summary.brief_summary || '요약 정보가 없습니다.'}</p>
                </section>

                <!-- 주요 주제 -->
                ${summary.main_topics && summary.main_topics.length > 0 ? `
                    <section class="summary-section">
                        <h3>주요 주제</h3>
                        <div class="topic-tags">
                            ${summary.main_topics.slice(0, 4).map((topic, i) => `
                                <span class="topic-tag priority-${i + 1}">
                                    ${Array.isArray(topic) ? topic[0] : topic}
                                </span>
                            `).join('')}
                        </div>
                    </section>
                ` : ''}

                <!-- 감정 분석 -->
                <section class="summary-section emotion-section">
                    <h3>감정 분석</h3>
                    <div class="emotion-stats">
                        <div class="emotion-stat">
                            <span class="stat-label">지배적 감정</span>
                            <span class="stat-value emotion-badge">
                                ${this.getEmotionEmoji(summary.dominant_emotion)}
                                ${summary.dominant_emotion || '중립'}
                            </span>
                        </div>
                        <div class="emotion-stat">
                            <span class="stat-label">변화 추세</span>
                            <span class="stat-value shift-${summary.emotional_shift}">
                                ${shift.emoji} ${shift.text}
                            </span>
                        </div>
                    </div>

                    ${summary.emotional_journey && summary.emotional_journey.length > 0 ? `
                        <div class="emotion-journey">
                            <div class="journey-label">감정 흐름</div>
                            <div class="journey-track">
                                ${summary.emotional_journey.map((e, i) => `
                                    <span class="journey-point"
                                          style="left: ${(i / (summary.emotional_journey.length - 1)) * 100}%"
                                          title="${e.emotion}">
                                        ${this.getEmotionEmoji(e.emotion)}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </section>

                <!-- 핵심 포인트 -->
                ${summary.key_points && summary.key_points.length > 0 ? `
                    <section class="summary-section">
                        <h3>핵심 포인트</h3>
                        <ul class="key-points-list">
                            ${summary.key_points.slice(0, 4).map(point => `
                                <li>${point}</li>
                            `).join('')}
                        </ul>
                    </section>
                ` : ''}

                <!-- 인사이트 -->
                ${summary.insights && summary.insights.length > 0 ? `
                    <section class="summary-section insights-section">
                        <h3>💡 인사이트</h3>
                        <ul class="insights-list">
                            ${summary.insights.map(insight => `
                                <li>${insight}</li>
                            `).join('')}
                        </ul>
                    </section>
                ` : ''}

                <!-- 다음 단계 -->
                ${summary.homework && summary.homework.length > 0 ? `
                    <section class="summary-section homework-section">
                        <h3>✅ 다음 세션까지</h3>
                        <ul class="homework-list">
                            ${summary.homework.map(item => `
                                <li>
                                    <label class="homework-item">
                                        <input type="checkbox">
                                        <span>${item}</span>
                                    </label>
                                </li>
                            `).join('')}
                        </ul>
                    </section>
                ` : ''}

                <!-- 다음 세션 제안 -->
                ${summary.next_session_suggestions && summary.next_session_suggestions.length > 0 ? `
                    <section class="summary-section">
                        <h3>다음 세션 제안</h3>
                        <ul class="suggestions-list">
                            ${summary.next_session_suggestions.map(suggestion => `
                                <li>${suggestion}</li>
                            `).join('')}
                        </ul>
                    </section>
                ` : ''}
            </div>

            <div class="summary-footer">
                <button class="summary-action-btn share-btn" onclick="this.closest('.summary-modal-content').querySelector('.summary-body').classList.toggle('expanded')">
                    더 보기
                </button>
                <button class="summary-action-btn export-btn" data-action="export">
                    📤 내보내기
                </button>
            </div>
        `;
    }

    renderSummaryHistoryList() {
        const container = document.getElementById(this.options.containerId);
        if (!container) return;

        if (this.summaryHistory.length === 0) {
            container.innerHTML = `
                <div class="summary-empty">
                    <p>아직 상담 기록이 없습니다.</p>
                    <p>첫 상담을 시작해보세요!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="summary-history">
                <h3>상담 기록</h3>
                <div class="summary-list">
                    ${this.summaryHistory.map(summary => `
                        <div class="summary-card" data-session-id="${summary.session_id}">
                            <div class="card-header">
                                <span class="card-date">${this.formatDate(summary.start_time)}</span>
                                <span class="card-duration">${summary.duration_minutes}분</span>
                            </div>
                            <p class="card-summary">${summary.brief_summary?.substring(0, 100)}...</p>
                            <div class="card-tags">
                                ${(summary.main_topics || []).slice(0, 2).map(t => `
                                    <span class="tag">${Array.isArray(t) ? t[0] : t}</span>
                                `).join('')}
                            </div>
                            <div class="card-emotion">
                                ${this.getEmotionEmoji(summary.dominant_emotion)}
                                <span class="shift-indicator shift-${summary.emotional_shift}">
                                    ${summary.emotional_shift === 'positive' ? '↑' :
                                      summary.emotional_shift === 'negative' ? '↓' : '→'}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // 카드 클릭 이벤트
        container.querySelectorAll('.summary-card').forEach(card => {
            card.addEventListener('click', () => {
                const sessionId = card.dataset.sessionId;
                const summary = this.summaryHistory.find(s => s.session_id === sessionId);
                if (summary) {
                    this.showSummaryModal(summary);
                }
            });
        });
    }

    // =========================================================================
    // 유틸리티
    // =========================================================================

    getEmotionEmoji(emotion) {
        const emojiMap = {
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
        return emojiMap[emotion] || '😐';
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
    }

    generateDemoSummary(sessionId, conversationHistory) {
        return {
            session_id: sessionId,
            start_time: new Date().toISOString(),
            duration_minutes: Math.floor(Math.random() * 30) + 10,
            brief_summary: "오늘 상담에서는 최근 겪고 있는 스트레스와 불안에 대해 이야기를 나눴습니다. 상담을 통해 감정을 표현하고 정리하는 시간을 가졌습니다.",
            detailed_summary: "사용자는 일상에서 느끼는 압박감과 걱정에 대해 이야기했습니다. 상담사는 경청하며 공감적 반응을 보였고, 감정을 인식하고 표현하는 것의 중요성에 대해 함께 이야기했습니다.",
            main_topics: [["스트레스", 0.4], ["불안", 0.3], ["대인관계", 0.2]],
            key_points: [
                "최근 업무 스트레스가 증가했다",
                "수면 패턴이 불규칙해졌다",
                "감정 표현의 어려움을 느끼고 있다"
            ],
            dominant_emotion: "불안",
            emotional_shift: "stable",
            emotional_journey: [
                { emotion: "불안", index: 0 },
                { emotion: "슬픔", index: 1 },
                { emotion: "중립", index: 2 },
                { emotion: "평온", index: 3 }
            ],
            insights: [
                "감정을 말로 표현하는 연습이 도움이 될 것 같습니다.",
                "작은 성취감을 느낄 수 있는 활동을 찾아보세요."
            ],
            homework: [
                "하루에 10분씩 명상이나 깊은 호흡 연습하기",
                "감정 일기 쓰기 - 하루 3가지 감정 기록하기",
                "규칙적인 수면 시간 지키기"
            ],
            next_session_suggestions: [
                "스트레스 관리 기법을 더 자세히 다뤄볼까요?",
                "수면 위생에 대해 이야기해보면 좋겠어요."
            ]
        };
    }

    generateDemoHistory() {
        const emotions = ['기쁨', '슬픔', '불안', '평온', '스트레스'];
        const shifts = ['positive', 'stable', 'negative'];
        const topics = ['대인관계', '스트레스', '불안', '자존감', '직장'];

        return Array(5).fill(null).map((_, i) => ({
            session_id: `demo-${i}`,
            start_time: new Date(Date.now() - i * 3 * 24 * 60 * 60 * 1000).toISOString(),
            duration_minutes: Math.floor(Math.random() * 30) + 15,
            brief_summary: `${i + 1}번째 상담 세션의 요약입니다. 사용자와 의미있는 대화를 나눴습니다.`,
            main_topics: [[topics[i % topics.length], 0.5]],
            dominant_emotion: emotions[i % emotions.length],
            emotional_shift: shifts[i % shifts.length]
        }));
    }

    exportSummary(format = 'text') {
        if (!this.currentSummary) return;

        let content = '';
        const summary = this.currentSummary;

        if (format === 'text') {
            content = `세션 요약\n${'='.repeat(40)}\n`;
            content += `날짜: ${this.formatDate(summary.start_time)}\n`;
            content += `시간: ${summary.duration_minutes}분\n\n`;
            content += `요약:\n${summary.brief_summary}\n\n`;

            if (summary.key_points) {
                content += `핵심 포인트:\n`;
                summary.key_points.forEach(p => content += `- ${p}\n`);
            }

            if (summary.homework) {
                content += `\n다음 세션까지:\n`;
                summary.homework.forEach(h => content += `□ ${h}\n`);
            }
        }

        // 다운로드
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `session-summary-${summary.session_id}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
}


// CSS 스타일
const summaryStyles = `
<style>
/* 모달 */
.summary-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.summary-modal.active {
    opacity: 1;
}

.summary-modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
}

.summary-modal-content {
    position: relative;
    background: white;
    border-radius: 16px;
    max-width: 600px;
    width: 90%;
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    transform: translateY(20px);
    transition: transform 0.3s ease;
}

.summary-modal.active .summary-modal-content {
    transform: translateY(0);
}

.summary-modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 32px;
    height: 32px;
    border: none;
    background: #f0f0f0;
    border-radius: 50%;
    font-size: 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
}

.summary-modal-close:hover {
    background: #e0e0e0;
}

/* 헤더 */
.summary-header {
    padding: 24px;
    border-bottom: 1px solid #eee;
}

.summary-header h2 {
    margin: 0 0 8px 0;
    font-size: 22px;
    font-weight: 600;
}

.summary-meta {
    display: flex;
    gap: 16px;
    color: #666;
    font-size: 14px;
}

/* 본문 */
.summary-body {
    padding: 24px;
}

.summary-section {
    margin-bottom: 24px;
}

.summary-section:last-child {
    margin-bottom: 0;
}

.summary-section h3 {
    font-size: 15px;
    font-weight: 600;
    color: #333;
    margin: 0 0 12px 0;
}

.summary-text {
    color: #444;
    line-height: 1.7;
    margin: 0;
}

/* 주제 태그 */
.topic-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.topic-tag {
    padding: 6px 14px;
    border-radius: 16px;
    font-size: 13px;
    background: #e3f2fd;
    color: #1976d2;
}

.topic-tag.priority-1 {
    background: #fff3e0;
    color: #f57c00;
    font-weight: 500;
}

.topic-tag.priority-2 {
    background: #e8f5e9;
    color: #388e3c;
}

/* 감정 섹션 */
.emotion-stats {
    display: flex;
    gap: 24px;
    margin-bottom: 16px;
}

.emotion-stat {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.stat-label {
    font-size: 12px;
    color: #888;
}

.stat-value {
    font-size: 15px;
    font-weight: 500;
}

.emotion-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.shift-positive {
    color: #4CAF50;
}

.shift-negative {
    color: #f44336;
}

.shift-stable {
    color: #FF9800;
}

/* 감정 흐름 */
.emotion-journey {
    margin-top: 16px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
}

.journey-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 12px;
}

.journey-track {
    position: relative;
    height: 40px;
    background: linear-gradient(90deg, #ffcdd2, #fff9c4, #c8e6c9);
    border-radius: 20px;
}

.journey-point {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    font-size: 20px;
    cursor: help;
}

/* 리스트 */
.key-points-list,
.insights-list,
.homework-list,
.suggestions-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.key-points-list li,
.insights-list li,
.suggestions-list li {
    padding: 8px 0;
    padding-left: 20px;
    position: relative;
    color: #444;
    line-height: 1.6;
}

.key-points-list li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: #4CAF50;
}

.insights-list li {
    background: #fff8e1;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
}

.insights-list li::before {
    display: none;
}

/* 과제 */
.homework-list li {
    padding: 8px 0;
}

.homework-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    cursor: pointer;
}

.homework-item input[type="checkbox"] {
    margin-top: 4px;
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.homework-item span {
    flex: 1;
}

/* 푸터 */
.summary-footer {
    padding: 16px 24px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

.summary-action-btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.share-btn {
    background: #f0f0f0;
    color: #333;
}

.share-btn:hover {
    background: #e0e0e0;
}

.export-btn {
    background: #4CAF50;
    color: white;
}

.export-btn:hover {
    background: #388E3C;
}

/* 히스토리 */
.summary-history h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
}

.summary-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.summary-card {
    background: white;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    cursor: pointer;
    transition: all 0.2s;
}

.summary-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.card-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 13px;
    color: #666;
}

.card-summary {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: #333;
    line-height: 1.5;
}

.card-tags {
    display: flex;
    gap: 6px;
    margin-bottom: 8px;
}

.card-tags .tag {
    font-size: 11px;
    padding: 3px 8px;
    background: #f0f0f0;
    border-radius: 10px;
    color: #666;
}

.card-emotion {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
}

.shift-indicator {
    font-size: 14px;
    font-weight: bold;
}

.summary-empty {
    text-align: center;
    padding: 40px;
    color: #888;
}

/* 다크 모드 */
@media (prefers-color-scheme: dark) {
    .summary-modal-content {
        background: #1e1e1e;
        color: #fff;
    }

    .summary-modal-close {
        background: #333;
        color: #fff;
    }

    .summary-header {
        border-color: #333;
    }

    .summary-section h3 {
        color: #fff;
    }

    .summary-text,
    .key-points-list li,
    .suggestions-list li {
        color: #ccc;
    }

    .emotion-journey {
        background: #2d2d2d;
    }

    .insights-list li {
        background: #3d3d2d;
        color: #fff;
    }

    .summary-footer {
        border-color: #333;
    }

    .summary-card {
        background: #2d2d2d;
    }

    .card-summary {
        color: #eee;
    }
}
</style>
`;

// 스타일 주입
document.head.insertAdjacentHTML('beforeend', summaryStyles);

// Export
window.SessionSummaryManager = SessionSummaryManager;
