"""
Conversation Logging System with Privacy Compliance
Complies with Korean Personal Information Protection Act (개인정보보호법)
"""

import logging
import json
import hashlib
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
import uuid

logger = logging.getLogger(__name__)


class PrivacyMasker:
    """
    Mask personally identifiable information (PII) in conversations
    Korean Personal Information Protection Act compliance
    """

    # PII patterns for Korean context
    PII_PATTERNS = {
        # Phone numbers
        "phone": [
            r"01[0-9]-\d{3,4}-\d{4}",  # 010-1234-5678
            r"01[0-9]\d{7,8}",  # 01012345678
            r"\d{2,3}-\d{3,4}-\d{4}"  # 02-123-4567
        ],
        # Korean resident registration number (주민등록번호)
        "rrn": [
            r"\d{6}-[1-4]\d{6}",  # 123456-1234567
            r"\d{13}"  # 1234561234567 (when without hyphen)
        ],
        # Email
        "email": [
            r"[\w\.-]+@[\w\.-]+\.\w+"
        ],
        # Credit card
        "credit_card": [
            r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"
        ],
        # Address (Korean)
        "address": [
            r"[가-힣]+[시도]\s+[가-힣]+[구시군]\s+[가-힣]+[동읍면]",
            r"[가-힣]+[로길]\s+\d+"
        ],
        # Names (Korean - heuristic, be careful)
        "name": [
            r"(?:성명|이름|환자명)[\s:]+([가-힣]{2,4})",
        ]
    }

    @classmethod
    def mask_pii(cls, text: str) -> str:
        """
        Mask all PII in text

        Args:
            text: Original text

        Returns:
            Text with masked PII
        """
        masked = text

        # Mask phone numbers
        for pattern in cls.PII_PATTERNS["phone"]:
            masked = re.sub(pattern, "[전화번호]", masked)

        # Mask RRN
        for pattern in cls.PII_PATTERNS["rrn"]:
            masked = re.sub(pattern, "[주민등록번호]", masked)

        # Mask email
        for pattern in cls.PII_PATTERNS["email"]:
            masked = re.sub(pattern, "[이메일]", masked)

        # Mask credit card
        for pattern in cls.PII_PATTERNS["credit_card"]:
            masked = re.sub(pattern, "[카드번호]", masked)

        # Mask address (partial - keep general area)
        for pattern in cls.PII_PATTERNS["address"]:
            masked = re.sub(pattern, "[주소]", masked)

        return masked

    @classmethod
    def anonymize_session_id(cls, session_id: str) -> str:
        """
        Create anonymized hash of session ID

        Args:
            session_id: Original session ID

        Returns:
            Hashed session ID
        """
        return hashlib.sha256(session_id.encode()).hexdigest()[:16]


class ConversationLogger:
    """
    Secure conversation logger with encryption and automatic retention management

    Features:
    - PII masking
    - Encryption at rest
    - Automatic retention policy (default: 90 days)
    - Audit trail
    - GDPR/PIPA compliance
    """

    def __init__(
        self,
        log_dir: Path,
        encryption_key: Optional[bytes] = None,
        retention_days: int = 90,
        enable_encryption: bool = True
    ):
        """
        Args:
            log_dir: Directory for log storage
            encryption_key: Fernet encryption key (generated if None)
            retention_days: Days to retain logs before auto-deletion
            enable_encryption: Whether to encrypt logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.retention_days = retention_days
        self.enable_encryption = enable_encryption

        # Encryption setup
        if enable_encryption:
            if encryption_key is None:
                encryption_key = Fernet.generate_key()
                # Save key securely (in production, use key management service)
                key_file = self.log_dir / ".encryption_key"
                if not key_file.exists():
                    key_file.write_bytes(encryption_key)
                else:
                    encryption_key = key_file.read_bytes()

            self.fernet = Fernet(encryption_key)
        else:
            self.fernet = None

        # Audit log
        self.audit_log_path = self.log_dir / "audit.log"
        self._setup_audit_logging()

        logger.info(f"ConversationLogger initialized (encryption: {enable_encryption}, retention: {retention_days} days)")

    def _setup_audit_logging(self):
        """Setup audit trail logging"""
        audit_logger = logging.getLogger("conversation_audit")
        audit_logger.setLevel(logging.INFO)

        handler = logging.FileHandler(self.audit_log_path, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)

        self.audit_logger = audit_logger

    def log_conversation(
        self,
        session_id: str,
        turn_data: Dict[str, Any],
        mask_pii: bool = True
    ) -> str:
        """
        Log a conversation turn with privacy protection

        Args:
            session_id: Session identifier
            turn_data: Conversation turn data
                {
                    "user_message": str,
                    "assistant_response": str,
                    "timestamp": datetime,
                    "crisis_detected": bool,
                    "metadata": dict
                }
            mask_pii: Whether to mask PII (default: True)

        Returns:
            Log entry ID
        """
        # Generate log entry ID
        entry_id = str(uuid.uuid4())

        # Anonymize session ID
        anon_session_id = PrivacyMasker.anonymize_session_id(session_id)

        # Mask PII if enabled
        user_message = turn_data.get("user_message", "")
        assistant_response = turn_data.get("assistant_response", "")

        if mask_pii:
            user_message = PrivacyMasker.mask_pii(user_message)
            assistant_response = PrivacyMasker.mask_pii(assistant_response)

        # Create log entry
        log_entry = {
            "entry_id": entry_id,
            "session_id": anon_session_id,  # Anonymized
            "timestamp": turn_data.get("timestamp", datetime.now()).isoformat(),
            "user_message": user_message,
            "assistant_response": assistant_response,
            "crisis_detected": turn_data.get("crisis_detected", False),
            "crisis_level": turn_data.get("crisis_level"),
            "metadata": turn_data.get("metadata", {}),
            "logged_at": datetime.now().isoformat()
        }

        # Encrypt if enabled
        log_content = json.dumps(log_entry, ensure_ascii=False, indent=2)

        if self.enable_encryption:
            log_content = self.fernet.encrypt(log_content.encode()).decode()

        # Write to file (one file per day)
        log_file = self._get_log_file(datetime.now())
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_content + "\n")

        # Audit trail
        self.audit_logger.info(f"Logged conversation turn: session={anon_session_id}, entry={entry_id}, crisis={turn_data.get('crisis_detected', False)}")

        return entry_id

    def _get_log_file(self, date: datetime) -> Path:
        """Get log file path for given date"""
        filename = f"conversations_{date.strftime('%Y%m%d')}.log"
        return self.log_dir / filename

    def read_conversation(
        self,
        entry_id: str,
        date: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Read a specific conversation entry

        Args:
            entry_id: Entry ID to read
            date: Date of entry (searches all if None)

        Returns:
            Conversation entry or None
        """
        if date:
            log_files = [self._get_log_file(date)]
        else:
            log_files = sorted(self.log_dir.glob("conversations_*.log"))

        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Decrypt if needed
                    if self.enable_encryption:
                        try:
                            line = self.fernet.decrypt(line.encode()).decode()
                        except Exception as e:
                            logger.error(f"Decryption failed: {e}")
                            continue

                    try:
                        entry = json.loads(line)
                        if entry.get("entry_id") == entry_id:
                            return entry
                    except json.JSONDecodeError:
                        continue

        return None

    def get_session_history(
        self,
        session_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get all entries for a session

        Args:
            session_id: Session ID (will be anonymized for search)
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)

        Returns:
            List of conversation entries
        """
        anon_session_id = PrivacyMasker.anonymize_session_id(session_id)

        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        entries = []

        # Iterate through date range
        current_date = start_date
        while current_date <= end_date:
            log_file = self._get_log_file(current_date)
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        # Decrypt if needed
                        if self.enable_encryption:
                            try:
                                line = self.fernet.decrypt(line.encode()).decode()
                            except Exception:
                                continue

                        try:
                            entry = json.loads(line)
                            if entry.get("session_id") == anon_session_id:
                                entries.append(entry)
                        except json.JSONDecodeError:
                            continue

            current_date += timedelta(days=1)

        return entries

    def cleanup_old_logs(self, dry_run: bool = False) -> int:
        """
        Remove logs older than retention period

        Args:
            dry_run: If True, only simulate deletion

        Returns:
            Number of files deleted/would be deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        for log_file in self.log_dir.glob("conversations_*.log"):
            # Extract date from filename
            try:
                date_str = log_file.stem.split("_")[1]  # conversations_YYYYMMDD
                file_date = datetime.strptime(date_str, "%Y%m%d")

                if file_date < cutoff_date:
                    if not dry_run:
                        log_file.unlink()
                        self.audit_logger.info(f"Deleted old log file: {log_file.name}")
                    deleted_count += 1
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse date from {log_file.name}: {e}")

        logger.info(f"Cleanup: {deleted_count} files {'would be' if dry_run else ''} deleted")
        return deleted_count

    def export_logs(
        self,
        output_path: Path,
        start_date: datetime,
        end_date: datetime,
        anonymize: bool = True
    ) -> None:
        """
        Export logs for a date range (for legal/compliance requests)

        Args:
            output_path: Output file path
            start_date: Start date
            end_date: End date
            anonymize: Keep anonymization (default: True)
        """
        all_entries = []

        current_date = start_date
        while current_date <= end_date:
            log_file = self._get_log_file(current_date)
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        if self.enable_encryption:
                            try:
                                line = self.fernet.decrypt(line.encode()).decode()
                            except Exception:
                                continue

                        try:
                            entry = json.loads(line)
                            all_entries.append(entry)
                        except json.JSONDecodeError:
                            continue

            current_date += timedelta(days=1)

        # Export
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_entries": len(all_entries),
            "anonymized": anonymize,
            "entries": all_entries
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        self.audit_logger.info(f"Exported logs: {len(all_entries)} entries to {output_path}")
        logger.info(f"Logs exported to {output_path}")

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get logging statistics

        Args:
            start_date: Start date (default: 7 days ago)
            end_date: End date (default: today)

        Returns:
            Statistics dictionary
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        total_entries = 0
        crisis_count = 0
        unique_sessions = set()

        current_date = start_date
        while current_date <= end_date:
            log_file = self._get_log_file(current_date)
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        if self.enable_encryption:
                            try:
                                line = self.fernet.decrypt(line.encode()).decode()
                            except Exception:
                                continue

                        try:
                            entry = json.loads(line)
                            total_entries += 1
                            if entry.get("crisis_detected"):
                                crisis_count += 1
                            unique_sessions.add(entry.get("session_id"))
                        except json.JSONDecodeError:
                            continue

            current_date += timedelta(days=1)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_entries": total_entries,
            "unique_sessions": len(unique_sessions),
            "crisis_detections": crisis_count,
            "crisis_rate": round(crisis_count / total_entries * 100, 2) if total_entries > 0 else 0
        }


# Global logger instance
_conversation_logger: Optional[ConversationLogger] = None


def get_conversation_logger() -> ConversationLogger:
    """Get or create global conversation logger"""
    global _conversation_logger
    if _conversation_logger is None:
        _conversation_logger = ConversationLogger(
            log_dir=Path("logs"),
            retention_days=90,
            enable_encryption=True
        )
    return _conversation_logger


def init_conversation_logger(
    log_dir: Path,
    encryption_key: Optional[bytes] = None,
    retention_days: int = 90,
    enable_encryption: bool = True
) -> ConversationLogger:
    """
    Initialize global conversation logger

    Args:
        log_dir: Directory for logs
        encryption_key: Encryption key
        retention_days: Retention period
        enable_encryption: Enable encryption

    Returns:
        ConversationLogger instance
    """
    global _conversation_logger
    _conversation_logger = ConversationLogger(
        log_dir=log_dir,
        encryption_key=encryption_key,
        retention_days=retention_days,
        enable_encryption=enable_encryption
    )
    return _conversation_logger
