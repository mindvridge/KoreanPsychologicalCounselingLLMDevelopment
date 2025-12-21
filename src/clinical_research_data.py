"""
임상 연구 데이터 수집 시스템 (Clinical Research Data Collection System)
IRB 준수 및 연구 윤리를 고려한 데이터 수집/관리

기능:
- 연구 참여 동의 관리 (Informed Consent)
- 익명화/가명화 처리 (Anonymization/Pseudonymization)
- 연구 데이터 수집 및 저장
- 데이터 품질 관리
- 연구 데이터 내보내기 (IRB 승인 형식)
- 감사 추적 (Audit Trail)
- 데이터 보존 정책 관리
"""

import logging
import hashlib
import uuid
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


# =============================================================================
# Enums & Constants
# =============================================================================

class ConsentStatus(Enum):
    """동의 상태"""
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    CONSENTED = "consented"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


class DataCategory(Enum):
    """데이터 카테고리"""
    DEMOGRAPHIC = "demographic"           # 인구통계학적 정보
    CLINICAL = "clinical"                  # 임상 데이터
    ASSESSMENT = "assessment"              # 평가/검사 데이터
    CONVERSATION = "conversation"          # 대화 데이터
    OUTCOME = "outcome"                    # 결과/효과 데이터
    SAFETY = "safety"                      # 안전 관련 데이터
    FEEDBACK = "feedback"                  # 피드백 데이터


class PIIType(Enum):
    """개인식별정보 유형"""
    NAME = "name"
    PHONE = "phone"
    EMAIL = "email"
    RRN = "rrn"  # 주민등록번호
    ADDRESS = "address"
    IP = "ip"
    DEVICE_ID = "device_id"


class AuditAction(Enum):
    """감사 추적 행동"""
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    ACCESS_GRANTED = "access_granted"
    ACCESS_REVOKED = "access_revoked"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class InformedConsent:
    """연구 참여 동의"""
    consent_id: str
    participant_id: str
    study_id: str
    consent_version: str
    status: ConsentStatus
    consent_date: Optional[datetime]
    withdrawal_date: Optional[datetime]
    consent_elements: Dict[str, bool]  # 개별 동의 항목
    electronic_signature: Optional[str]
    ip_hash: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ResearchParticipant:
    """연구 참여자"""
    participant_id: str  # 익명화된 ID
    original_user_hash: str  # 원본 사용자 ID의 해시
    study_ids: List[str]
    consent_records: List[str]
    enrollment_date: datetime
    status: str  # active, withdrawn, completed
    demographic_data: Dict[str, Any]  # 익명화된 인구통계
    created_at: datetime
    updated_at: datetime


@dataclass
class ResearchDataRecord:
    """연구 데이터 레코드"""
    record_id: str
    participant_id: str
    study_id: str
    session_id: str
    category: DataCategory
    data_type: str
    data_content: Dict[str, Any]
    collection_timestamp: datetime
    quality_flags: List[str]
    anonymized: bool
    created_at: datetime


@dataclass
class AuditLog:
    """감사 로그"""
    log_id: str
    timestamp: datetime
    action: AuditAction
    actor_id: str  # 누가 (연구자/시스템)
    target_type: str  # 대상 유형
    target_id: str  # 대상 ID
    details: Dict[str, Any]
    ip_hash: Optional[str]


@dataclass
class StudyProtocol:
    """연구 프로토콜"""
    study_id: str
    study_name: str
    irb_approval_number: str
    irb_approval_date: datetime
    irb_expiry_date: datetime
    principal_investigator: str
    data_retention_years: int
    consent_version: str
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    data_collection_points: List[str]
    status: str  # active, completed, suspended


# =============================================================================
# Anonymization Service
# =============================================================================

class AnonymizationService:
    """익명화/가명화 서비스"""

    def __init__(self, salt: str = None):
        self.salt = salt or self._generate_salt()
        self.pii_patterns = self._init_pii_patterns()

    def _generate_salt(self) -> str:
        """솔트 생성"""
        return uuid.uuid4().hex

    def _init_pii_patterns(self) -> Dict[PIIType, List[str]]:
        """PII 패턴 정의"""
        return {
            PIIType.PHONE: [
                r'01[0-9]-?\d{3,4}-?\d{4}',
                r'\d{2,3}-\d{3,4}-\d{4}'
            ],
            PIIType.EMAIL: [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ],
            PIIType.RRN: [
                r'\d{6}-?[1-4]\d{6}'
            ],
            PIIType.IP: [
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
            ]
        }

    def create_participant_id(self, user_id: str) -> Tuple[str, str]:
        """
        사용자 ID를 익명화된 참여자 ID로 변환

        Returns:
            Tuple[participant_id, user_hash]
        """
        # 원본 해시 생성 (복구 불가능)
        user_hash = hashlib.sha256(
            f"{user_id}{self.salt}".encode()
        ).hexdigest()

        # 참여자 ID 생성 (P + 랜덤)
        participant_id = f"P{uuid.uuid4().hex[:12].upper()}"

        return participant_id, user_hash

    def anonymize_text(self, text: str) -> Tuple[str, List[Dict]]:
        """
        텍스트에서 PII 익명화

        Returns:
            Tuple[anonymized_text, detected_pii_list]
        """
        anonymized = text
        detected_pii = []

        replacements = {
            PIIType.PHONE: "[전화번호]",
            PIIType.EMAIL: "[이메일]",
            PIIType.RRN: "[주민등록번호]",
            PIIType.IP: "[IP주소]"
        }

        for pii_type, patterns in self.pii_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    detected_pii.append({
                        "type": pii_type.value,
                        "position": text.find(match),
                        "length": len(match)
                    })
                anonymized = re.sub(
                    pattern,
                    replacements.get(pii_type, "[개인정보]"),
                    anonymized
                )

        # 이름 패턴 (한글 2-4자)
        # 주의: 단순 패턴이므로 실제로는 더 정교한 NER 필요
        name_pattern = r'[가-힣]{2,4}(?:씨|님|선생님|박사님)?'

        return anonymized, detected_pii

    def anonymize_demographic(self, data: Dict) -> Dict:
        """인구통계학적 데이터 익명화/일반화"""
        anonymized = {}

        # 나이 → 연령대
        if "age" in data:
            age = data["age"]
            if age < 20:
                anonymized["age_group"] = "10대"
            elif age < 30:
                anonymized["age_group"] = "20대"
            elif age < 40:
                anonymized["age_group"] = "30대"
            elif age < 50:
                anonymized["age_group"] = "40대"
            elif age < 60:
                anonymized["age_group"] = "50대"
            else:
                anonymized["age_group"] = "60대 이상"

        # 성별 유지
        if "gender" in data:
            anonymized["gender"] = data["gender"]

        # 지역 → 대분류만
        if "region" in data:
            region = data["region"]
            if "서울" in region:
                anonymized["region"] = "수도권"
            elif any(city in region for city in ["경기", "인천"]):
                anonymized["region"] = "수도권"
            elif any(city in region for city in ["부산", "울산", "경남"]):
                anonymized["region"] = "영남권"
            elif any(city in region for city in ["대구", "경북"]):
                anonymized["region"] = "영남권"
            elif any(city in region for city in ["광주", "전남", "전북"]):
                anonymized["region"] = "호남권"
            elif any(city in region for city in ["대전", "충남", "충북"]):
                anonymized["region"] = "충청권"
            else:
                anonymized["region"] = "기타"

        # 직업 → 대분류
        if "occupation" in data:
            occupation = data["occupation"]
            if any(job in occupation for job in ["학생", "대학생", "고등학생"]):
                anonymized["occupation_category"] = "학생"
            elif any(job in occupation for job in ["회사원", "직장인"]):
                anonymized["occupation_category"] = "직장인"
            elif any(job in occupation for job in ["자영업", "사업"]):
                anonymized["occupation_category"] = "자영업"
            elif any(job in occupation for job in ["주부", "가사"]):
                anonymized["occupation_category"] = "가정관리"
            elif any(job in occupation for job in ["무직", "구직"]):
                anonymized["occupation_category"] = "무직/구직"
            else:
                anonymized["occupation_category"] = "기타"

        return anonymized

    def hash_ip(self, ip: str) -> str:
        """IP 주소 해싱"""
        return hashlib.sha256(f"{ip}{self.salt}".encode()).hexdigest()[:16]


# =============================================================================
# Consent Management
# =============================================================================

class ConsentManager:
    """동의 관리"""

    def __init__(self):
        self.consent_templates = self._init_templates()
        self.consents: Dict[str, InformedConsent] = {}

    def _init_templates(self) -> Dict[str, Dict]:
        """동의서 템플릿"""
        return {
            "research_participation": {
                "version": "1.0",
                "title": "연구 참여 동의서",
                "elements": {
                    "purpose": {
                        "title": "연구 목적",
                        "content": "본 연구는 AI 기반 심리상담 시스템의 효과성을 평가하기 위한 것입니다.",
                        "required": True
                    },
                    "procedures": {
                        "title": "연구 절차",
                        "content": "참여자는 AI 상담 시스템을 사용하고, 정기적으로 설문에 응답하게 됩니다.",
                        "required": True
                    },
                    "data_collection": {
                        "title": "수집 데이터",
                        "content": "대화 내용(익명화), 심리검사 결과, 만족도 등을 수집합니다.",
                        "required": True
                    },
                    "privacy": {
                        "title": "개인정보 보호",
                        "content": "모든 데이터는 익명화되어 저장되며, 연구 목적으로만 사용됩니다.",
                        "required": True
                    },
                    "voluntary": {
                        "title": "자발적 참여",
                        "content": "참여는 자발적이며, 언제든지 철회할 수 있습니다.",
                        "required": True
                    },
                    "risks": {
                        "title": "위험 및 이익",
                        "content": "심리적 불편감이 발생할 수 있으며, 필요시 전문가에게 연결됩니다.",
                        "required": True
                    },
                    "contact": {
                        "title": "연구진 연락처",
                        "content": "문의사항은 연구책임자에게 연락하세요.",
                        "required": True
                    },
                    "audio_recording": {
                        "title": "음성 녹음 동의",
                        "content": "음성 상담의 경우 녹음될 수 있습니다.",
                        "required": False
                    },
                    "future_research": {
                        "title": "향후 연구 활용 동의",
                        "content": "익명화된 데이터가 향후 관련 연구에 활용될 수 있습니다.",
                        "required": False
                    }
                }
            }
        }

    def get_consent_form(self, template_name: str) -> Dict:
        """동의서 양식 반환"""
        return self.consent_templates.get(template_name, {})

    def record_consent(
        self,
        participant_id: str,
        study_id: str,
        consent_elements: Dict[str, bool],
        ip_hash: str
    ) -> InformedConsent:
        """동의 기록"""
        template = self.consent_templates.get("research_participation", {})

        # 필수 항목 확인
        required_elements = [
            key for key, elem in template.get("elements", {}).items()
            if elem.get("required", False)
        ]

        all_required_consented = all(
            consent_elements.get(elem, False) for elem in required_elements
        )

        consent_id = str(uuid.uuid4())
        now = datetime.now()

        consent = InformedConsent(
            consent_id=consent_id,
            participant_id=participant_id,
            study_id=study_id,
            consent_version=template.get("version", "1.0"),
            status=ConsentStatus.CONSENTED if all_required_consented else ConsentStatus.DECLINED,
            consent_date=now if all_required_consented else None,
            withdrawal_date=None,
            consent_elements=consent_elements,
            electronic_signature=f"ESIG-{uuid.uuid4().hex[:8].upper()}",
            ip_hash=ip_hash,
            created_at=now,
            updated_at=now
        )

        self.consents[consent_id] = consent
        return consent

    def withdraw_consent(self, consent_id: str, reason: str = None) -> bool:
        """동의 철회"""
        if consent_id not in self.consents:
            return False

        consent = self.consents[consent_id]
        consent.status = ConsentStatus.WITHDRAWN
        consent.withdrawal_date = datetime.now()
        consent.updated_at = datetime.now()

        return True

    def check_consent(self, participant_id: str, study_id: str) -> bool:
        """동의 상태 확인"""
        for consent in self.consents.values():
            if (consent.participant_id == participant_id and
                consent.study_id == study_id and
                consent.status == ConsentStatus.CONSENTED):
                return True
        return False


# =============================================================================
# Research Data Repository
# =============================================================================

class ResearchDataRepository:
    """연구 데이터 저장소"""

    def __init__(self, storage_path: str = "./research_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.participants: Dict[str, ResearchParticipant] = {}
        self.records: Dict[str, ResearchDataRecord] = {}
        self.audit_logs: List[AuditLog] = []
        self.studies: Dict[str, StudyProtocol] = {}

    def register_study(self, protocol: StudyProtocol) -> str:
        """연구 등록"""
        self.studies[protocol.study_id] = protocol
        self._log_audit(
            AuditAction.DATA_CREATE,
            "system",
            "study",
            protocol.study_id,
            {"study_name": protocol.study_name}
        )
        return protocol.study_id

    def enroll_participant(
        self,
        participant_id: str,
        user_hash: str,
        study_id: str,
        demographic_data: Dict
    ) -> ResearchParticipant:
        """참여자 등록"""
        now = datetime.now()

        participant = ResearchParticipant(
            participant_id=participant_id,
            original_user_hash=user_hash,
            study_ids=[study_id],
            consent_records=[],
            enrollment_date=now,
            status="active",
            demographic_data=demographic_data,
            created_at=now,
            updated_at=now
        )

        self.participants[participant_id] = participant

        self._log_audit(
            AuditAction.DATA_CREATE,
            "system",
            "participant",
            participant_id,
            {"study_id": study_id}
        )

        return participant

    def store_data(
        self,
        participant_id: str,
        study_id: str,
        session_id: str,
        category: DataCategory,
        data_type: str,
        data_content: Dict,
        anonymized: bool = True
    ) -> ResearchDataRecord:
        """연구 데이터 저장"""
        record_id = str(uuid.uuid4())
        now = datetime.now()

        # 데이터 품질 검사
        quality_flags = self._check_data_quality(data_content, category)

        record = ResearchDataRecord(
            record_id=record_id,
            participant_id=participant_id,
            study_id=study_id,
            session_id=session_id,
            category=category,
            data_type=data_type,
            data_content=data_content,
            collection_timestamp=now,
            quality_flags=quality_flags,
            anonymized=anonymized,
            created_at=now
        )

        self.records[record_id] = record

        self._log_audit(
            AuditAction.DATA_CREATE,
            "system",
            "research_data",
            record_id,
            {
                "participant_id": participant_id,
                "category": category.value,
                "data_type": data_type
            }
        )

        return record

    def _check_data_quality(self, data: Dict, category: DataCategory) -> List[str]:
        """데이터 품질 검사"""
        flags = []

        # 필수 필드 확인
        if not data:
            flags.append("EMPTY_DATA")

        # 카테고리별 검사
        if category == DataCategory.ASSESSMENT:
            if "score" not in data:
                flags.append("MISSING_SCORE")
            if "assessment_type" not in data:
                flags.append("MISSING_ASSESSMENT_TYPE")

        if category == DataCategory.CONVERSATION:
            if "message_count" in data and data["message_count"] < 2:
                flags.append("SHORT_CONVERSATION")

        return flags

    def get_participant_data(
        self,
        participant_id: str,
        study_id: str,
        categories: List[DataCategory] = None
    ) -> List[ResearchDataRecord]:
        """참여자 데이터 조회"""
        records = []
        for record in self.records.values():
            if (record.participant_id == participant_id and
                record.study_id == study_id):
                if categories is None or record.category in categories:
                    records.append(record)

        self._log_audit(
            AuditAction.DATA_READ,
            "researcher",
            "participant_data",
            participant_id,
            {"study_id": study_id, "record_count": len(records)}
        )

        return records

    def export_study_data(
        self,
        study_id: str,
        format: str = "json",
        include_categories: List[DataCategory] = None
    ) -> Dict:
        """연구 데이터 내보내기"""
        export_data = {
            "study_id": study_id,
            "export_timestamp": datetime.now().isoformat(),
            "participants": [],
            "records": []
        }

        # 해당 연구의 참여자
        for p_id, participant in self.participants.items():
            if study_id in participant.study_ids:
                export_data["participants"].append({
                    "participant_id": participant.participant_id,
                    "enrollment_date": participant.enrollment_date.isoformat(),
                    "status": participant.status,
                    "demographic_data": participant.demographic_data
                })

        # 해당 연구의 데이터 레코드
        for record in self.records.values():
            if record.study_id == study_id:
                if include_categories is None or record.category in include_categories:
                    export_data["records"].append({
                        "record_id": record.record_id,
                        "participant_id": record.participant_id,
                        "session_id": record.session_id,
                        "category": record.category.value,
                        "data_type": record.data_type,
                        "data_content": record.data_content,
                        "collection_timestamp": record.collection_timestamp.isoformat(),
                        "quality_flags": record.quality_flags
                    })

        self._log_audit(
            AuditAction.DATA_EXPORT,
            "researcher",
            "study",
            study_id,
            {
                "participant_count": len(export_data["participants"]),
                "record_count": len(export_data["records"])
            }
        )

        return export_data

    def _log_audit(
        self,
        action: AuditAction,
        actor_id: str,
        target_type: str,
        target_id: str,
        details: Dict,
        ip_hash: str = None
    ):
        """감사 로그 기록"""
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            action=action,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_hash=ip_hash
        )
        self.audit_logs.append(log)

    def get_audit_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        action_type: AuditAction = None
    ) -> List[AuditLog]:
        """감사 로그 조회"""
        logs = self.audit_logs

        if start_date:
            logs = [l for l in logs if l.timestamp >= start_date]
        if end_date:
            logs = [l for l in logs if l.timestamp <= end_date]
        if action_type:
            logs = [l for l in logs if l.action == action_type]

        return logs


# =============================================================================
# Clinical Research Data Collection System
# =============================================================================

class ClinicalResearchDataSystem:
    """임상 연구 데이터 수집 시스템 통합 클래스"""

    def __init__(self, storage_path: str = "./research_data"):
        self.anonymization = AnonymizationService()
        self.consent_manager = ConsentManager()
        self.repository = ResearchDataRepository(storage_path)

        logger.info("임상 연구 데이터 수집 시스템 초기화 완료")

    def create_study(
        self,
        study_name: str,
        irb_number: str,
        principal_investigator: str,
        data_retention_years: int = 3
    ) -> StudyProtocol:
        """연구 생성"""
        study_id = f"STUDY-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()

        protocol = StudyProtocol(
            study_id=study_id,
            study_name=study_name,
            irb_approval_number=irb_number,
            irb_approval_date=now,
            irb_expiry_date=now + timedelta(days=365),
            principal_investigator=principal_investigator,
            data_retention_years=data_retention_years,
            consent_version="1.0",
            inclusion_criteria=[
                "18세 이상 성인",
                "한국어 의사소통 가능",
                "연구 참여 동의"
            ],
            exclusion_criteria=[
                "현재 정신과 입원 치료 중",
                "심각한 자살 위험",
                "인지 장애로 동의 불가"
            ],
            data_collection_points=[
                "baseline",
                "week2",
                "week4",
                "week8",
                "follow_up_3m"
            ],
            status="active"
        )

        self.repository.register_study(protocol)
        return protocol

    def enroll_participant(
        self,
        user_id: str,
        study_id: str,
        demographic_data: Dict,
        consent_elements: Dict[str, bool],
        ip_address: str
    ) -> Tuple[ResearchParticipant, InformedConsent]:
        """연구 참여자 등록"""
        # 익명화된 참여자 ID 생성
        participant_id, user_hash = self.anonymization.create_participant_id(user_id)

        # IP 해싱
        ip_hash = self.anonymization.hash_ip(ip_address)

        # 동의 기록
        consent = self.consent_manager.record_consent(
            participant_id=participant_id,
            study_id=study_id,
            consent_elements=consent_elements,
            ip_hash=ip_hash
        )

        if consent.status != ConsentStatus.CONSENTED:
            raise ValueError("필수 동의 항목이 충족되지 않았습니다.")

        # 인구통계 익명화
        anonymized_demo = self.anonymization.anonymize_demographic(demographic_data)

        # 참여자 등록
        participant = self.repository.enroll_participant(
            participant_id=participant_id,
            user_hash=user_hash,
            study_id=study_id,
            demographic_data=anonymized_demo
        )

        participant.consent_records.append(consent.consent_id)

        return participant, consent

    def collect_conversation_data(
        self,
        participant_id: str,
        study_id: str,
        session_id: str,
        messages: List[Dict],
        emotion_data: Dict = None,
        crisis_events: List[Dict] = None
    ) -> ResearchDataRecord:
        """대화 데이터 수집"""
        # 동의 확인
        if not self.consent_manager.check_consent(participant_id, study_id):
            raise ValueError("유효한 동의가 없습니다.")

        # 메시지 익명화
        anonymized_messages = []
        for msg in messages:
            anon_text, _ = self.anonymization.anonymize_text(msg.get("content", ""))
            anonymized_messages.append({
                "role": msg.get("role", ""),
                "content": anon_text,
                "timestamp": msg.get("timestamp", "")
            })

        data_content = {
            "message_count": len(messages),
            "session_duration_minutes": self._calculate_duration(messages),
            "messages": anonymized_messages,
            "emotion_summary": emotion_data,
            "crisis_events": crisis_events or []
        }

        return self.repository.store_data(
            participant_id=participant_id,
            study_id=study_id,
            session_id=session_id,
            category=DataCategory.CONVERSATION,
            data_type="counseling_session",
            data_content=data_content,
            anonymized=True
        )

    def collect_assessment_data(
        self,
        participant_id: str,
        study_id: str,
        session_id: str,
        assessment_type: str,
        responses: Dict[int, int],
        score: int,
        interpretation: str
    ) -> ResearchDataRecord:
        """평가/검사 데이터 수집"""
        if not self.consent_manager.check_consent(participant_id, study_id):
            raise ValueError("유효한 동의가 없습니다.")

        data_content = {
            "assessment_type": assessment_type,
            "responses": responses,
            "score": score,
            "interpretation": interpretation,
            "completion_time": datetime.now().isoformat()
        }

        return self.repository.store_data(
            participant_id=participant_id,
            study_id=study_id,
            session_id=session_id,
            category=DataCategory.ASSESSMENT,
            data_type=assessment_type,
            data_content=data_content,
            anonymized=True
        )

    def collect_outcome_data(
        self,
        participant_id: str,
        study_id: str,
        timepoint: str,
        outcomes: Dict
    ) -> ResearchDataRecord:
        """결과/효과 데이터 수집"""
        if not self.consent_manager.check_consent(participant_id, study_id):
            raise ValueError("유효한 동의가 없습니다.")

        data_content = {
            "timepoint": timepoint,
            "outcomes": outcomes,
            "collection_date": datetime.now().isoformat()
        }

        return self.repository.store_data(
            participant_id=participant_id,
            study_id=study_id,
            session_id=f"outcome_{timepoint}",
            category=DataCategory.OUTCOME,
            data_type="outcome_measure",
            data_content=data_content,
            anonymized=True
        )

    def _calculate_duration(self, messages: List[Dict]) -> float:
        """세션 지속 시간 계산"""
        if len(messages) < 2:
            return 0.0

        try:
            first_ts = messages[0].get("timestamp", "")
            last_ts = messages[-1].get("timestamp", "")

            if first_ts and last_ts:
                first_dt = datetime.fromisoformat(first_ts)
                last_dt = datetime.fromisoformat(last_ts)
                duration = (last_dt - first_dt).total_seconds() / 60
                return round(duration, 2)
        except Exception:
            pass

        return 0.0

    def withdraw_participant(
        self,
        participant_id: str,
        study_id: str,
        reason: str = None
    ) -> bool:
        """참여자 철회"""
        # 동의 철회
        for consent_id, consent in self.consent_manager.consents.items():
            if (consent.participant_id == participant_id and
                consent.study_id == study_id):
                self.consent_manager.withdraw_consent(consent_id, reason)

        # 참여자 상태 업데이트
        if participant_id in self.repository.participants:
            participant = self.repository.participants[participant_id]
            participant.status = "withdrawn"
            participant.updated_at = datetime.now()
            return True

        return False

    def export_for_analysis(
        self,
        study_id: str,
        include_categories: List[DataCategory] = None,
        format: str = "json"
    ) -> Dict:
        """분석용 데이터 내보내기"""
        return self.repository.export_study_data(
            study_id=study_id,
            format=format,
            include_categories=include_categories
        )

    def get_study_statistics(self, study_id: str) -> Dict:
        """연구 통계 조회"""
        participants = [
            p for p in self.repository.participants.values()
            if study_id in p.study_ids
        ]

        records = [
            r for r in self.repository.records.values()
            if r.study_id == study_id
        ]

        active_count = len([p for p in participants if p.status == "active"])
        withdrawn_count = len([p for p in participants if p.status == "withdrawn"])
        completed_count = len([p for p in participants if p.status == "completed"])

        category_counts = {}
        for r in records:
            cat = r.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "study_id": study_id,
            "total_participants": len(participants),
            "active_participants": active_count,
            "withdrawn_participants": withdrawn_count,
            "completed_participants": completed_count,
            "total_records": len(records),
            "records_by_category": category_counts,
            "report_date": datetime.now().isoformat()
        }

    def get_module_summary(self) -> Dict:
        """모듈 요약"""
        return {
            "name": "임상 연구 데이터 수집 시스템",
            "version": "1.0.0",
            "components": {
                "anonymization": "익명화/가명화 서비스 (PII 탐지, 해싱)",
                "consent_manager": "동의 관리 (전자 동의서, 철회)",
                "data_repository": "연구 데이터 저장소 (CRUD, 내보내기)",
                "audit_logging": "감사 추적 (모든 접근 기록)"
            },
            "data_categories": [cat.value for cat in DataCategory],
            "compliance": [
                "개인정보보호법 (PIPA)",
                "생명윤리법",
                "IRB 연구윤리"
            ],
            "active_studies": len(self.repository.studies),
            "total_participants": len(self.repository.participants),
            "total_records": len(self.repository.records)
        }


# =============================================================================
# Factory & Test
# =============================================================================

def get_research_system(storage_path: str = "./research_data") -> ClinicalResearchDataSystem:
    """임상 연구 데이터 시스템 인스턴스 생성"""
    return ClinicalResearchDataSystem(storage_path)


if __name__ == "__main__":
    # 테스트
    system = get_research_system()

    print("=" * 60)
    print("임상 연구 데이터 수집 시스템 테스트")
    print("=" * 60)

    # 모듈 요약
    summary = system.get_module_summary()
    print(f"\n모듈: {summary['name']} v{summary['version']}")
    print("\n구성요소:")
    for key, value in summary['components'].items():
        print(f"  - {key}: {value}")

    # 연구 생성
    print("\n\n--- 연구 생성 테스트 ---")
    study = system.create_study(
        study_name="AI 심리상담 효과성 연구",
        irb_number="IRB-2025-001",
        principal_investigator="홍길동 교수",
        data_retention_years=5
    )
    print(f"연구 ID: {study.study_id}")
    print(f"연구명: {study.study_name}")
    print(f"IRB 번호: {study.irb_approval_number}")

    # 참여자 등록
    print("\n\n--- 참여자 등록 테스트 ---")
    consent_elements = {
        "purpose": True,
        "procedures": True,
        "data_collection": True,
        "privacy": True,
        "voluntary": True,
        "risks": True,
        "contact": True,
        "audio_recording": False,
        "future_research": True
    }

    participant, consent = system.enroll_participant(
        user_id="user123",
        study_id=study.study_id,
        demographic_data={"age": 28, "gender": "여성", "region": "서울"},
        consent_elements=consent_elements,
        ip_address="192.168.1.100"
    )
    print(f"참여자 ID: {participant.participant_id}")
    print(f"동의 상태: {consent.status.value}")

    # 익명화 테스트
    print("\n\n--- 익명화 테스트 ---")
    test_text = "안녕하세요, 제 전화번호는 010-1234-5678이고 이메일은 test@example.com입니다."
    anon_text, detected = system.anonymization.anonymize_text(test_text)
    print(f"원본: {test_text}")
    print(f"익명화: {anon_text}")

    # 통계
    print("\n\n--- 연구 통계 ---")
    stats = system.get_study_statistics(study.study_id)
    print(f"총 참여자: {stats['total_participants']}")
    print(f"활성 참여자: {stats['active_participants']}")

    print("\n\n테스트 완료!")
