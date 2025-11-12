"""
마음이 - AI 심리상담 도우미 웹 인터페이스
Gradio-based Web Interface for Korean Mental Health LLM

따뜻하고 안전한 분위기의 대화형 심리상담 인터페이스를 제공합니다.
"""

import os
import sys
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import gradio as gr
import plotly.graph_objects as go
import plotly.express as px

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.emotion_analyzer_v2 import KoreanEmotionAnalyzer
from src.safety_system_v2 import SafetySystem, RiskLevel
from src.assessments import AssessmentManager, PHQ9Assessment, GAD7Assessment, K10Assessment

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# 세션 관리
# ============================================================================

class SessionManager:
    """세션 관리 클래스"""

    def __init__(self, timeout_minutes: int = 30):
        """
        초기화

        Args:
            timeout_minutes: 세션 타임아웃 (분)
        """
        self.sessions = {}
        self.timeout = timedelta(minutes=timeout_minutes)

    def create_session(self) -> str:
        """
        새 세션 생성

        Returns:
            str: 세션 ID
        """
        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "conversation_history": [],
            "emotion_history": [],
            "safety_checks": [],
            "assessments": {},
            "current_assessment": None
        }

        logger.info(f"새 세션 생성: {session_id}")

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        세션 가져오기

        Args:
            session_id: 세션 ID

        Returns:
            Optional[Dict]: 세션 데이터
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # 타임아웃 체크
        if datetime.now() - session["last_activity"] > self.timeout:
            logger.info(f"세션 타임아웃: {session_id}")
            del self.sessions[session_id]
            return None

        return session

    def update_activity(self, session_id: str):
        """세션 활동 시간 업데이트"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.now()


# ============================================================================
# CSS 스타일
# ============================================================================

CUSTOM_CSS = """
/* 색상 팔레트 */
:root {
    --primary-color: #7C93C3;
    --secondary-color: #E8B4B8;
    --background: #F5F5F7;
    --text-color: #2C3E50;
    --warning-color: #FFA726;
    --critical-color: #EF5350;
    --success-color: #66BB6A;
    --border-radius: 12px;
}

/* 전체 레이아웃 */
.gradio-container {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: var(--background) !important;
}

/* 헤더 */
.header-container {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    padding: 2rem;
    border-radius: var(--border-radius);
    margin-bottom: 1.5rem;
    color: white;
    text-align: center;
}

.header-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.header-subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
}

/* 면책조항 */
.disclaimer {
    background-color: #FFF3E0;
    padding: 1rem;
    border-radius: var(--border-radius);
    border-left: 4px solid var(--warning-color);
    margin-bottom: 1rem;
}

/* 채팅 영역 */
.chatbot {
    border-radius: var(--border-radius) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

/* 위기 모드 */
.crisis-mode {
    background-color: #FFEBEE !important;
    border: 2px solid var(--critical-color) !important;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

/* 감정 카드 */
.emotion-card {
    background: white;
    padding: 1.5rem;
    border-radius: var(--border-radius);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}

.emotion-label {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.emotion-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-color);
}

/* 위기 자원 버튼 */
.emergency-button {
    background-color: var(--critical-color) !important;
    color: white !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    padding: 1rem 2rem !important;
    border-radius: var(--border-radius) !important;
    border: none !important;
    cursor: pointer !important;
    transition: all 0.3s !important;
}

.emergency-button:hover {
    background-color: #D32F2F !important;
    transform: scale(1.05);
}

/* 버튼 */
.primary-button {
    background-color: var(--primary-color) !important;
    color: white !important;
    border-radius: var(--border-radius) !important;
}

.secondary-button {
    background-color: var(--secondary-color) !important;
    color: white !important;
    border-radius: var(--border-radius) !important;
}

/* 툴팁 */
.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    background-color: var(--text-color);
    color: white;
    text-align: center;
    border-radius: 6px;
    padding: 5px 10px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -60px;
    opacity: 0;
    transition: opacity 0.3s;
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}
"""

# ============================================================================
# 전역 객체
# ============================================================================

# 세션 매니저
session_manager = SessionManager(timeout_minutes=30)

# 분석 시스템 (모델 없이 사용)
emotion_analyzer = KoreanEmotionAnalyzer()
assessment_manager = AssessmentManager()


# ============================================================================
# 핵심 함수
# ============================================================================

def create_new_session() -> str:
    """새 세션 생성"""
    return session_manager.create_session()


def chat_response(
    message: str,
    history: List[List[str]],
    session_id: str
) -> Tuple[str, List[List[str]], str, str, str, Dict]:
    """
    채팅 응답 생성

    Args:
        message: 사용자 메시지
        history: 대화 히스토리
        session_id: 세션 ID

    Returns:
        Tuple: (응답, 업데이트된 히스토리, 감정 상태, 위기 경고, 세션 ID, 감정 그래프 데이터)
    """
    # 세션 가져오기
    session = session_manager.get_session(session_id)

    if not session:
        session_id = create_new_session()
        session = session_manager.get_session(session_id)

    # 활동 업데이트
    session_manager.update_activity(session_id)

    # 감정 분석
    emotion_result = emotion_analyzer.analyze(message)

    # 안전 체크
    safety_system = SafetySystem(user_id=session_id)
    safety_result = safety_system.check_safety(
        text=message,
        emotion_data=emotion_result
    )

    # 세션에 저장
    session["conversation_history"].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })

    session["emotion_history"].append({
        "emotion": emotion_result["primary_emotion"],
        "intensity": emotion_result["intensity"],
        "timestamp": datetime.now().isoformat()
    })

    session["safety_checks"].append({
        "risk_level": safety_result["risk_level"].value,
        "score": safety_result["weighted_score"],
        "timestamp": datetime.now().isoformat()
    })

    # 응답 생성 (실제 LLM 없이 템플릿 기반)
    response = generate_template_response(message, emotion_result, safety_result)

    # 위기 상황이면 개입 메시지 추가
    if safety_result["requires_intervention"]:
        response = safety_result["intervention_message"] + "\n\n" + response

    session["conversation_history"].append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })

    # 히스토리 업데이트
    history = history + [[message, response]]

    # 감정 상태 텍스트
    emotion_status = format_emotion_status(emotion_result)

    # 위기 경고
    crisis_warning = format_crisis_warning(safety_result) if safety_result["requires_intervention"] else ""

    # 감정 그래프 데이터
    emotion_graph = create_emotion_graph(session["emotion_history"])

    return "", history, emotion_status, crisis_warning, session_id, emotion_graph


def generate_template_response(
    message: str,
    emotion_result: Dict,
    safety_result: Dict
) -> str:
    """
    템플릿 기반 응답 생성 (실제 LLM 없이)

    Args:
        message: 사용자 메시지
        emotion_result: 감정 분석 결과
        safety_result: 안전 체크 결과

    Returns:
        str: 생성된 응답
    """
    primary_emotion = emotion_result["primary_emotion"]
    intensity = emotion_result["intensity"]

    # 감정별 공감 응답
    empathy_responses = {
        "우울": "많이 우울하시군요. 그 마음이 느껴집니다.",
        "불안": "불안한 마음이 크시네요. 충분히 이해합니다.",
        "분노": "화가 많이 나신 것 같아요. 그 감정을 표현해주셔서 고마워요.",
        "슬픔": "많이 슬프시군요. 힘든 시간이시겠어요.",
        "기쁨": "기쁜 마음이 느껴져요. 좋은 일이 있으셨나봐요.",
        "두려움": "두려운 마음이 드시는군요. 그 불안감을 이해합니다.",
        "한": "한스러운 마음이 느껴져요. 그 응어리진 감정이 얼마나 힘드실지...",
        "서러움": "서러운 마음이 크시네요. 그 감정을 함께 나눠봐요.",
        "외로움": "많이 외로우시군요. 혼자라는 느낌이 힘드시죠."
    }

    empathy = empathy_responses.get(primary_emotion, "그런 감정을 느끼시는군요.")

    # 강도에 따른 추가 응답
    if intensity >= 8:
        intensity_comment = "정말 많이 힘드신 것 같아요."
    elif intensity >= 6:
        intensity_comment = "힘든 시간을 보내고 계시네요."
    else:
        intensity_comment = "그런 감정을 느끼고 계시는군요."

    # 기본 응답 구성
    response = f"{empathy} {intensity_comment}\n\n조금 더 말씀해주시겠어요? 어떤 상황에서 그렇게 느끼셨나요?"

    return response


def format_emotion_status(emotion_result: Dict) -> str:
    """
    감정 상태 포맷팅

    Args:
        emotion_result: 감정 분석 결과

    Returns:
        str: 포맷된 감정 상태
    """
    primary = emotion_result["primary_emotion"]
    intensity = emotion_result["intensity"]

    # 이모지 매핑
    emotion_emojis = {
        "기쁨": "😊",
        "슬픔": "😢",
        "분노": "😠",
        "두려움": "😰",
        "놀람": "😲",
        "역겨움": "😖",
        "우울": "😔",
        "불안": "😟",
        "한": "😞",
        "서러움": "😥",
        "외로움": "😪",
        "중립": "😐"
    }

    emoji = emotion_emojis.get(primary, "💭")

    # 강도 바
    bar_length = 10
    filled = int((intensity / 10) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)

    status = f"""**현재 감정 상태**

{emoji} **{primary}**

강도: {intensity:.1f}/10
{bar}

"""

    # 부가 감정
    if emotion_result.get("secondary_emotions"):
        secondary = ", ".join(emotion_result["secondary_emotions"][:2])
        status += f"부가 감정: {secondary}\n"

    # 연령대
    if emotion_result.get("age_group_estimated"):
        status += f"추정 연령대: {emotion_result['age_group_estimated']}\n"

    # 문화적 마커
    if emotion_result.get("cultural_markers"):
        markers = ", ".join(emotion_result["cultural_markers"][:2])
        status += f"문화적 특징: {markers}\n"

    return status


def format_crisis_warning(safety_result: Dict) -> str:
    """
    위기 경고 포맷팅

    Args:
        safety_result: 안전 체크 결과

    Returns:
        str: 포맷된 위기 경고
    """
    risk_level = safety_result["risk_level"]

    if risk_level == RiskLevel.CRITICAL:
        return """⚠️ **긴급 상황 감지**

당신의 안전이 가장 중요합니다.
지금 즉시 도움을 받으세요.

🆘 **긴급 연락처**
• 자살예방상담전화: **1393** (24시간)
• 정신건강위기상담전화: **1577-0199**
• 응급: **119**
"""

    elif risk_level == RiskLevel.HIGH:
        return """⚠️ **위기 상황 감지**

전문가의 도움이 필요합니다.

📞 **연락처**
• 정신건강위기상담전화: **1577-0199**
• 자살예방상담전화: **1393**
"""

    return ""


def create_emotion_graph(emotion_history: List[Dict]) -> Dict:
    """
    감정 그래프 생성

    Args:
        emotion_history: 감정 이력

    Returns:
        Dict: Plotly 그래프 데이터
    """
    if not emotion_history:
        return {}

    # 최근 10개만
    recent = emotion_history[-10:]

    emotions = [e["emotion"] for e in recent]
    intensities = [e["intensity"] for e in recent]
    timestamps = [e.get("timestamp", "") for e in recent]

    # 시간 레이블 생성
    labels = [f"#{i+1}" for i in range(len(recent))]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=labels,
        y=intensities,
        mode='lines+markers',
        name='감정 강도',
        line=dict(color='#7C93C3', width=3),
        marker=dict(size=10),
        text=emotions,
        hovertemplate='<b>%{text}</b><br>강도: %{y:.1f}/10<extra></extra>'
    ))

    fig.update_layout(
        title="감정 변화 추이",
        xaxis_title="대화 순서",
        yaxis_title="강도",
        yaxis_range=[0, 10],
        template="plotly_white",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig


def start_assessment(assessment_type: str, session_id: str) -> Tuple[str, str, str]:
    """
    심리검사 시작

    Args:
        assessment_type: 검사 유형 (PHQ-9, GAD-7, K-10)
        session_id: 세션 ID

    Returns:
        Tuple: (도입 메시지, 첫 질문, 업데이트된 세션 ID)
    """
    session = session_manager.get_session(session_id)

    if not session:
        session_id = create_new_session()
        session = session_manager.get_session(session_id)

    # 검사 생성
    assessment = assessment_manager.create_assessment(assessment_type)

    session["current_assessment"] = {
        "type": assessment_type,
        "instance": assessment,
        "started_at": datetime.now().isoformat()
    }

    # 도입부
    intro = assessment.get_conversational_intro()

    # 첫 질문
    first_question = assessment.get_next_question()

    if first_question:
        question_text = f"{intro}\n\n{first_question[1]}"
    else:
        question_text = intro

    return question_text, "", session_id


def clear_chat(session_id: str) -> Tuple[None, str, str, str]:
    """
    채팅 초기화

    Args:
        session_id: 세션 ID

    Returns:
        Tuple: (빈 히스토리, 빈 감정 상태, 빈 경고, 새 세션 ID)
    """
    new_session_id = create_new_session()

    greeting = """안녕하세요, **마음이**입니다. 🤗

오늘은 어떤 이야기를 나누고 싶으신가요?
편안하게 마음속 이야기를 나눠주세요.

당신의 감정은 모두 소중하고 존중받을 가치가 있습니다."""

    return [[None, greeting]], "", "", new_session_id


def show_emergency_resources() -> str:
    """긴급 자원 정보 표시"""
    return """# 🆘 긴급 도움이 필요하신가요?

당신의 생명은 매우 소중합니다.
혼자 감당하지 마시고, 지금 즉시 도움을 받으세요.

## 📞 24시간 긴급 연락처

### 자살예방상담전화
**1393** (24시간 무료)
- 자살 위기 상담
- 정서적 지지
- 전문가 연결

### 정신건강위기상담전화
**1577-0199** (24시간)
- 정신건강 위기 상담
- 정신과 진료 안내
- 지역 자원 연결

### 청소년전화
**1388** (24시간)
- 청소년 상담
- 학교폭력 상담
- 가족 문제 상담

### 여성긴급전화
**1366** (24시간)
- 가정폭력 상담
- 성폭력 상담
- 긴급 보호

### 응급상황
**119**
- 즉각적인 생명 위협 시
- 응급 의료 지원

## 🏥 방문 가능한 기관

- **정신건강복지센터**: 지역 보건소 내 위치
- **정신건강의학과**: 가까운 병원 정신과
- **대학 상담센터**: 재학생 무료 이용

## 💬 온라인 상담

- **카카오톡 상담**: "상담톡109" 검색
- **블루터치 앱**: 우울증 자가관리 앱
- **마음이음**: 정신건강 정보 포털

---

**기억하세요**: 도움을 요청하는 것은 용기있는 행동입니다.
당신은 혼자가 아닙니다. 💙
"""


# ============================================================================
# Gradio 인터페이스 구축
# ============================================================================

def build_interface():
    """Gradio 인터페이스 구축"""

    with gr.Blocks(css=CUSTOM_CSS, title="마음이 - AI 심리상담 도우미", theme=gr.themes.Soft()) as app:

        # 세션 상태
        session_id_state = gr.State(value=create_new_session())

        # ====================================================================
        # 헤더
        # ====================================================================

        with gr.Row():
            gr.HTML("""
                <div class="header-container">
                    <div class="header-title">🤗 마음이</div>
                    <div class="header-subtitle">AI 심리상담 도우미</div>
                </div>
            """)

        # 면책조항
        with gr.Row():
            gr.Markdown("""
                <div class="disclaimer">
                    ⚠️ <b>안내사항</b>: 마음이는 보조 도구이며 전문 의료 서비스를 대체할 수 없습니다.
                    심각한 정신건강 문제는 반드시 전문가와 상담하세요.
                    대화 내용은 세션 동안만 임시 저장되며, 개인정보는 수집하지 않습니다.
                </div>
            """, elem_classes=["disclaimer"])

        # ====================================================================
        # 메인 영역
        # ====================================================================

        with gr.Row():

            # 왼쪽: 채팅 영역 (70%)
            with gr.Column(scale=7):

                chatbot = gr.Chatbot(
                    value=[[None, "안녕하세요, **마음이**입니다. 🤗\n\n오늘은 어떤 이야기를 나누고 싶으신가요?\n편안하게 마음속 이야기를 나눠주세요."]],
                    height=500,
                    elem_classes=["chatbot"],
                    label="대화"
                )

                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="여기에 메시지를 입력하세요...",
                        label="메시지",
                        lines=3,
                        scale=4
                    )
                    with gr.Column(scale=1):
                        send_btn = gr.Button("전송 📤", variant="primary")
                        clear_btn = gr.Button("초기화 🔄")

            # 오른쪽: 사이드바 (30%)
            with gr.Column(scale=3):

                # 감정 상태
                with gr.Accordion("💭 현재 감정 상태", open=True):
                    emotion_status = gr.Markdown("대화를 시작하면 감정 상태가 표시됩니다.")

                # 위기 경고
                crisis_warning = gr.Markdown(visible=False)

                # 감정 그래프
                with gr.Accordion("📊 감정 변화 추이", open=True):
                    emotion_graph = gr.Plot(label="감정 그래프")

                # 위기 자원
                with gr.Accordion("🆘 긴급 도움", open=False):
                    gr.Markdown(show_emergency_resources())

                    emergency_btn = gr.Button(
                        "🆘 긴급 연락처 보기",
                        variant="stop",
                        elem_classes=["emergency-button"]
                    )

        # ====================================================================
        # 하단 도구 모음
        # ====================================================================

        gr.Markdown("---")

        with gr.Row():
            gr.Markdown("### 🧪 심리검사 도구")

        with gr.Row():
            phq9_btn = gr.Button("📋 PHQ-9 (우울증 검사)", variant="secondary")
            gad7_btn = gr.Button("📋 GAD-7 (불안 검사)", variant="secondary")
            k10_btn = gr.Button("📋 K-10 (정신건강 선별)", variant="secondary")

        # ====================================================================
        # 이벤트 핸들러
        # ====================================================================

        # 메시지 전송
        msg.submit(
            chat_response,
            inputs=[msg, chatbot, session_id_state],
            outputs=[msg, chatbot, emotion_status, crisis_warning, session_id_state, emotion_graph]
        )

        send_btn.click(
            chat_response,
            inputs=[msg, chatbot, session_id_state],
            outputs=[msg, chatbot, emotion_status, crisis_warning, session_id_state, emotion_graph]
        )

        # 초기화
        clear_btn.click(
            clear_chat,
            inputs=[session_id_state],
            outputs=[chatbot, emotion_status, crisis_warning, session_id_state]
        )

        # 긴급 연락처 버튼
        emergency_btn.click(
            lambda: gr.Info("긴급 도움이 필요하면 1393으로 전화하세요. (24시간 무료)"),
            inputs=None,
            outputs=None
        )

        # 심리검사 시작 (간단한 안내만)
        phq9_btn.click(
            lambda: gr.Info("PHQ-9 검사는 전문가와 함께 진행하는 것을 권장합니다. 정신건강복지센터(1577-0199)로 문의하세요."),
            inputs=None,
            outputs=None
        )

        gad7_btn.click(
            lambda: gr.Info("GAD-7 검사는 전문가와 함께 진행하는 것을 권장합니다. 정신건강복지센터(1577-0199)로 문의하세요."),
            inputs=None,
            outputs=None
        )

        k10_btn.click(
            lambda: gr.Info("K-10 검사는 전문가와 함께 진행하는 것을 권장합니다. 정신건강복지센터(1577-0199)로 문의하세요."),
            inputs=None,
            outputs=None
        )

        # ====================================================================
        # 푸터
        # ====================================================================

        gr.Markdown("""
            ---
            <div style="text-align: center; color: #666; font-size: 0.9rem;">
                Made with ❤️ for Korean Mental Health | Version 3.0<br>
                <b>긴급 상황</b>: 자살예방상담전화 <b>1393</b> (24시간 무료)
            </div>
        """)

    return app


# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    logger.info("마음이 - AI 심리상담 도우미 시작")

    app = build_interface()

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None
    )
