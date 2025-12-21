/**
 * 숙제 체크리스트 트래커 (Homework Tracker)
 * 상담 숙제 관리 및 진행 상황 추적
 */

// ============================================================================
// Homework Tracker Component
// ============================================================================

class HomeworkTracker {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.homework = [];
        this.streak = 0;
        this.maxStreak = 0;

        this.init();
    }

    init() {
        this.loadHomework();
        this.render();
        this.bindEvents();
    }

    // 데모 숙제 데이터 생성
    generateDemoData() {
        const today = new Date();
        const dayOfWeek = today.getDay();

        return [
            {
                id: 'hw1',
                title: '복식호흡 연습',
                description: '매일 아침, 저녁 5분씩',
                type: 'daily',
                icon: '🫁',
                category: 'breathing',
                dailyProgress: this.generateDailyProgress(5, dayOfWeek),
                targetDays: 7,
                assignedDate: this.getDateBefore(6),
                dueDate: this.getDateAfter(1)
            },
            {
                id: 'hw2',
                title: '감사일기 쓰기',
                description: '매일 감사한 일 3가지 적기',
                type: 'daily',
                icon: '📝',
                category: 'journaling',
                dailyProgress: this.generateDailyProgress(3, dayOfWeek),
                targetDays: 7,
                assignedDate: this.getDateBefore(6),
                dueDate: this.getDateAfter(1)
            },
            {
                id: 'hw3',
                title: '생각 기록지 작성',
                description: '부정적 생각이 들 때 기록',
                type: 'ongoing',
                icon: '💭',
                category: 'cognitive',
                completedCount: 2,
                targetCount: 5,
                status: 'in_progress',
                assignedDate: this.getDateBefore(3),
                dueDate: this.getDateAfter(4)
            },
            {
                id: 'hw4',
                title: '가치 탐색 워크시트',
                description: '10가지 삶의 영역 돌아보기',
                type: 'one_time',
                icon: '🎯',
                category: 'values',
                status: 'pending',
                assignedDate: this.getDateBefore(1),
                dueDate: this.getDateAfter(6)
            }
        ];
    }

    generateDailyProgress(completedDays, currentDayOfWeek) {
        const progress = {};
        const days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];

        // 이번 주 시작 (일요일)부터 현재까지
        for (let i = 0; i <= currentDayOfWeek; i++) {
            if (i < completedDays) {
                progress[days[i]] = 'completed';
            } else if (i === currentDayOfWeek) {
                progress[days[i]] = 'pending';
            } else {
                progress[days[i]] = 'missed';
            }
        }

        // 아직 안 온 날들
        for (let i = currentDayOfWeek + 1; i < 7; i++) {
            progress[days[i]] = 'future';
        }

        return progress;
    }

    getDateBefore(days) {
        const date = new Date();
        date.setDate(date.getDate() - days);
        return date.toISOString().split('T')[0];
    }

    getDateAfter(days) {
        const date = new Date();
        date.setDate(date.getDate() + days);
        return date.toISOString().split('T')[0];
    }

    async loadHomework() {
        try {
            // 실제 구현에서는 API 호출
            // const response = await api.request('/homework');
            // this.homework = response.data;

            this.homework = this.generateDemoData();
            this.calculateStreak();
        } catch (error) {
            console.error('숙제 로드 실패:', error);
        }
    }

    calculateStreak() {
        // 연속 달성일 계산 (데모)
        this.streak = 12;
        this.maxStreak = 15;
    }

    calculateCompletionRate() {
        let totalTasks = 0;
        let completedTasks = 0;

        this.homework.forEach(hw => {
            if (hw.type === 'daily') {
                const days = Object.values(hw.dailyProgress);
                totalTasks += days.filter(d => d !== 'future').length;
                completedTasks += days.filter(d => d === 'completed').length;
            } else if (hw.type === 'ongoing') {
                totalTasks += hw.targetCount;
                completedTasks += hw.completedCount;
            } else if (hw.type === 'one_time') {
                totalTasks += 1;
                if (hw.status === 'completed') completedTasks += 1;
            }
        });

        return totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    }

    render() {
        const completionRate = this.calculateCompletionRate();

        this.container.innerHTML = `
            <div class="homework-widget">
                <div class="homework-header">
                    <div class="homework-title">
                        <span class="homework-icon">📋</span>
                        <h3>이번 주 숙제</h3>
                    </div>
                    <div class="homework-completion">
                        <span class="completion-rate">${completionRate}%</span>
                        <span class="completion-label">완료</span>
                    </div>
                </div>

                <!-- 연속 달성 배지 -->
                <div class="streak-badge ${this.streak >= 7 ? 'fire' : ''}">
                    <span class="streak-icon">${this.streak >= 7 ? '🔥' : '⭐'}</span>
                    <span class="streak-count">${this.streak}일</span>
                    <span class="streak-label">연속 달성!</span>
                    ${this.streak >= this.maxStreak ? '<span class="streak-record">최고 기록!</span>' : ''}
                </div>

                <!-- 진행률 바 -->
                <div class="homework-progress-bar">
                    <div class="progress-fill" style="width: ${completionRate}%"></div>
                </div>

                <!-- 숙제 목록 -->
                <div class="homework-list" id="homework-list">
                    ${this.renderHomeworkItems()}
                </div>

                <!-- 오늘 할 일 요약 -->
                <div class="today-summary" id="today-summary">
                    ${this.renderTodaySummary()}
                </div>

                <!-- 격려 메시지 -->
                <div class="homework-encouragement">
                    ${this.getEncouragementMessage(completionRate)}
                </div>
            </div>
        `;

        this.bindEvents();
    }

    renderHomeworkItems() {
        return this.homework.map(hw => {
            if (hw.type === 'daily') {
                return this.renderDailyHomework(hw);
            } else if (hw.type === 'ongoing') {
                return this.renderOngoingHomework(hw);
            } else {
                return this.renderOneTimeHomework(hw);
            }
        }).join('');
    }

    renderDailyHomework(hw) {
        const days = ['일', '월', '화', '수', '목', '금', '토'];
        const dayKeys = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
        const completedDays = Object.values(hw.dailyProgress).filter(d => d === 'completed').length;
        const totalDays = Object.values(hw.dailyProgress).filter(d => d !== 'future').length;

        return `
            <div class="homework-item" data-id="${hw.id}">
                <div class="homework-item-header">
                    <span class="homework-item-icon">${hw.icon}</span>
                    <div class="homework-item-info">
                        <h4>${hw.title}</h4>
                        <p>${hw.description}</p>
                    </div>
                    <span class="homework-item-progress">${completedDays}/${totalDays}</span>
                </div>
                <div class="daily-tracker">
                    ${dayKeys.map((key, i) => {
                        const status = hw.dailyProgress[key];
                        const isToday = i === new Date().getDay();
                        return `
                            <div class="day-cell ${status} ${isToday ? 'today' : ''}"
                                 data-day="${key}" data-homework="${hw.id}">
                                <span class="day-label">${days[i]}</span>
                                <span class="day-status">
                                    ${status === 'completed' ? '✓' :
                                      status === 'missed' ? '✗' :
                                      status === 'pending' ? '○' : '·'}
                                </span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    renderOngoingHomework(hw) {
        const progress = (hw.completedCount / hw.targetCount) * 100;

        return `
            <div class="homework-item ongoing" data-id="${hw.id}">
                <div class="homework-item-header">
                    <span class="homework-item-icon">${hw.icon}</span>
                    <div class="homework-item-info">
                        <h4>${hw.title}</h4>
                        <p>${hw.description}</p>
                    </div>
                    <span class="homework-item-progress">${hw.completedCount}/${hw.targetCount}</span>
                </div>
                <div class="ongoing-progress">
                    <div class="ongoing-progress-bar">
                        <div class="ongoing-progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <button class="add-progress-btn" data-homework="${hw.id}">
                        + 기록하기
                    </button>
                </div>
            </div>
        `;
    }

    renderOneTimeHomework(hw) {
        const isOverdue = new Date(hw.dueDate) < new Date() && hw.status !== 'completed';
        const daysLeft = Math.ceil((new Date(hw.dueDate) - new Date()) / (1000 * 60 * 60 * 24));

        return `
            <div class="homework-item one-time ${hw.status} ${isOverdue ? 'overdue' : ''}"
                 data-id="${hw.id}">
                <div class="homework-item-header">
                    <button class="complete-checkbox ${hw.status === 'completed' ? 'checked' : ''}"
                            data-homework="${hw.id}">
                        ${hw.status === 'completed' ? '✓' : ''}
                    </button>
                    <span class="homework-item-icon">${hw.icon}</span>
                    <div class="homework-item-info">
                        <h4>${hw.title}</h4>
                        <p>${hw.description}</p>
                    </div>
                    <span class="homework-due ${isOverdue ? 'overdue' : ''}">
                        ${isOverdue ? '기한 초과' : daysLeft > 0 ? `${daysLeft}일 남음` : '오늘까지'}
                    </span>
                </div>
                ${hw.status !== 'completed' ? `
                    <button class="start-homework-btn" data-homework="${hw.id}">
                        시작하기 →
                    </button>
                ` : ''}
            </div>
        `;
    }

    renderTodaySummary() {
        const today = new Date().getDay();
        const dayKey = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'][today];

        const todayTasks = [];

        this.homework.forEach(hw => {
            if (hw.type === 'daily' && hw.dailyProgress[dayKey] === 'pending') {
                todayTasks.push({
                    id: hw.id,
                    title: hw.title,
                    icon: hw.icon,
                    type: 'daily'
                });
            } else if (hw.type === 'ongoing' && hw.completedCount < hw.targetCount) {
                todayTasks.push({
                    id: hw.id,
                    title: hw.title,
                    icon: hw.icon,
                    type: 'ongoing'
                });
            } else if (hw.type === 'one_time' && hw.status === 'pending') {
                const daysLeft = Math.ceil((new Date(hw.dueDate) - new Date()) / (1000 * 60 * 60 * 24));
                if (daysLeft <= 2) {
                    todayTasks.push({
                        id: hw.id,
                        title: hw.title,
                        icon: hw.icon,
                        type: 'one_time',
                        urgent: daysLeft <= 0
                    });
                }
            }
        });

        if (todayTasks.length === 0) {
            return `
                <div class="today-complete">
                    <span class="complete-icon">🎉</span>
                    <span>오늘 할 일을 모두 마쳤어요!</span>
                </div>
            `;
        }

        return `
            <div class="today-header">
                <span class="today-icon">📌</span>
                <span>오늘 할 일 ${todayTasks.length}개</span>
            </div>
            <div class="today-list">
                ${todayTasks.map(task => `
                    <div class="today-task ${task.urgent ? 'urgent' : ''}"
                         data-homework="${task.id}">
                        <span>${task.icon}</span>
                        <span>${task.title}</span>
                        ${task.urgent ? '<span class="urgent-badge">급함!</span>' : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    getEncouragementMessage(completionRate) {
        if (completionRate >= 90) {
            return `
                <span class="encouragement-icon">🌟</span>
                <span>대단해요! 거의 완벽하게 실천하고 계시네요!</span>
            `;
        } else if (completionRate >= 70) {
            return `
                <span class="encouragement-icon">💪</span>
                <span>잘하고 계세요! 조금만 더 힘내봐요!</span>
            `;
        } else if (completionRate >= 50) {
            return `
                <span class="encouragement-icon">🌱</span>
                <span>절반 이상 완료! 꾸준히 하는 게 중요해요.</span>
            `;
        } else if (completionRate >= 30) {
            return `
                <span class="encouragement-icon">🤗</span>
                <span>시작이 반이에요. 천천히 해나가요!</span>
            `;
        } else {
            return `
                <span class="encouragement-icon">💙</span>
                <span>작은 것부터 시작해봐요. 응원할게요!</span>
            `;
        }
    }

    bindEvents() {
        // 일일 과제 체크
        this.container.querySelectorAll('.day-cell.pending, .day-cell.today').forEach(cell => {
            cell.addEventListener('click', (e) => {
                const hwId = e.currentTarget.dataset.homework;
                const day = e.currentTarget.dataset.day;
                this.toggleDailyProgress(hwId, day);
            });
        });

        // 진행형 과제 추가
        this.container.querySelectorAll('.add-progress-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const hwId = e.currentTarget.dataset.homework;
                this.addOngoingProgress(hwId);
            });
        });

        // 일회성 과제 완료
        this.container.querySelectorAll('.complete-checkbox').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const hwId = e.currentTarget.dataset.homework;
                this.toggleOneTimeComplete(hwId);
            });
        });

        // 오늘 할 일 클릭
        this.container.querySelectorAll('.today-task').forEach(task => {
            task.addEventListener('click', (e) => {
                const hwId = e.currentTarget.dataset.homework;
                this.scrollToHomework(hwId);
            });
        });
    }

    async toggleDailyProgress(hwId, day) {
        const hw = this.homework.find(h => h.id === hwId);
        if (!hw) return;

        const currentStatus = hw.dailyProgress[day];
        if (currentStatus === 'future') return;

        // 토글
        hw.dailyProgress[day] = currentStatus === 'completed' ? 'pending' : 'completed';

        // UI 업데이트
        this.render();
        this.showToast(hw.dailyProgress[day] === 'completed' ?
            `✓ ${hw.title} 완료!` : `${hw.title} 취소됨`);

        // API 호출 (실제 구현)
        // await this.saveProgress(hwId, day, hw.dailyProgress[day]);
    }

    async addOngoingProgress(hwId) {
        const hw = this.homework.find(h => h.id === hwId);
        if (!hw || hw.completedCount >= hw.targetCount) return;

        hw.completedCount++;

        // UI 업데이트
        this.render();

        if (hw.completedCount >= hw.targetCount) {
            this.showToast(`🎉 ${hw.title} 목표 달성!`);
        } else {
            this.showToast(`+1 ${hw.title} (${hw.completedCount}/${hw.targetCount})`);
        }
    }

    async toggleOneTimeComplete(hwId) {
        const hw = this.homework.find(h => h.id === hwId);
        if (!hw) return;

        hw.status = hw.status === 'completed' ? 'pending' : 'completed';

        // UI 업데이트
        this.render();
        this.showToast(hw.status === 'completed' ?
            `🎉 ${hw.title} 완료!` : `${hw.title} 미완료로 변경`);
    }

    scrollToHomework(hwId) {
        const element = this.container.querySelector(`.homework-item[data-id="${hwId}"]`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            element.classList.add('highlight');
            setTimeout(() => element.classList.remove('highlight'), 2000);
        }
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'homework-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    // 외부에서 호출 가능한 메서드들
    refresh() {
        this.loadHomework();
        this.render();
    }

    getStats() {
        return {
            completionRate: this.calculateCompletionRate(),
            streak: this.streak,
            maxStreak: this.maxStreak,
            totalHomework: this.homework.length
        };
    }
}

// ============================================================================
// 전역 함수
// ============================================================================

function initHomeworkTracker(containerId = 'homework-tracker-container') {
    return new HomeworkTracker(containerId);
}

// 자동 초기화
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('homework-tracker-container');
    if (container) {
        window.homeworkTracker = new HomeworkTracker('homework-tracker-container');
    }
});
