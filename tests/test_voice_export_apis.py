"""
Voice and Export API Integration Tests
Tests for voice interface and data export functionality
"""

import pytest
import sys
import io
import base64
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestVoiceService:
    """Test voice service functionality"""

    def test_voice_service_initialization(self):
        """Test voice service can be initialized"""
        from src.voice_service import VoiceService

        service = VoiceService()
        assert service is not None
        assert service.sample_rate == 16000
        assert service.max_audio_duration == 300

    def test_audio_format_validation(self):
        """Test audio format validation"""
        from src.voice_service import VoiceService

        service = VoiceService()

        # Valid WAV file signature
        wav_data = b'RIFF\x00\x00\x00\x00WAVE'
        is_valid, format_type = service.validate_audio_format(wav_data)
        assert is_valid == True
        assert format_type == "wav"

        # Valid MP3 file signature
        mp3_data = b'ID3\x03\x00\x00\x00'
        is_valid, format_type = service.validate_audio_format(mp3_data)
        assert is_valid == True
        assert format_type == "mp3"

        # Invalid format
        invalid_data = b'INVALID\x00\x00'
        is_valid, format_type = service.validate_audio_format(invalid_data)
        assert is_valid == False

    def test_tts_duration_estimation(self):
        """Test TTS duration estimation"""
        from src.voice_service import VoiceService

        service = VoiceService()

        # Korean text (3.5 chars/second)
        korean_text = "안녕하세요" * 10  # 50 characters
        duration = service._estimate_duration(korean_text, "ko")
        assert 13 < duration < 15  # ~14.3 seconds

        # English text (15 chars/second)
        english_text = "Hello World!" * 10  # 120 characters
        duration = service._estimate_duration(english_text, "en")
        assert 7 < duration < 9  # ~8 seconds

    def test_cache_key_generation(self):
        """Test TTS cache key generation"""
        from src.voice_service import VoiceService

        service = VoiceService()

        key1 = service._generate_cache_key("안녕하세요", "ko", False)
        key2 = service._generate_cache_key("안녕하세요", "ko", False)
        key3 = service._generate_cache_key("안녕하세요", "ko", True)  # Different (slow=True)

        assert key1 == key2  # Same parameters = same key
        assert key1 != key3  # Different parameters = different key

    def test_emotion_aware_voice_service(self):
        """Test emotion-aware voice service initialization"""
        from src.voice_service import EmotionAwareVoiceService

        service = EmotionAwareVoiceService()
        assert hasattr(service, 'emotion_speech_params')
        assert 'sadness' in service.emotion_speech_params
        assert 'happiness' in service.emotion_speech_params

        # Check sadness uses slow speech
        assert service.emotion_speech_params['sadness']['slow'] == True
        # Check happiness uses normal speech
        assert service.emotion_speech_params['happiness']['slow'] == False


class TestExportService:
    """Test export service functionality"""

    def test_export_service_initialization(self):
        """Test export service can be initialized"""
        from src.export_service import ExportService

        service = ExportService()
        assert service is not None
        assert service.export_dir.exists()

    def test_csv_export(self):
        """Test CSV export functionality"""
        from src.export_service import ExportService

        service = ExportService()

        conversation_history = [
            {"role": "user", "content": "안녕하세요", "time": "2025-11-18T10:00:00"},
            {"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?", "time": "2025-11-18T10:00:05"}
        ]

        csv_data = service.export_conversation_to_csv(
            conversation_history=conversation_history,
            session_id="test_session",
            include_metadata=True
        )

        assert csv_data is not None
        assert len(csv_data) > 0

        # Decode and check content
        csv_text = csv_data.decode('utf-8-sig')
        assert "안녕하세요" in csv_text
        assert "user" in csv_text
        assert "assistant" in csv_text

    def test_json_export(self):
        """Test JSON export functionality"""
        from src.export_service import ExportService

        service = ExportService()

        data = {
            "session_id": "test_session",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }

        json_data = service.export_to_json(data, pretty=True)

        assert json_data is not None
        assert b'"session_id"' in json_data
        assert b'"test_session"' in json_data

    def test_assessment_interpretation(self):
        """Test assessment score interpretation"""
        from src.export_service import ExportService

        service = ExportService()

        # PHQ-9 interpretations
        interpretation = service._get_assessment_interpretation("PHQ-9", 2)
        assert "최소한" in interpretation  # Minimal

        interpretation = service._get_assessment_interpretation("PHQ-9", 7)
        assert "경도" in interpretation  # Mild

        interpretation = service._get_assessment_interpretation("PHQ-9", 20)
        assert "중증" in interpretation  # Severe

        # GAD-7 interpretations
        interpretation = service._get_assessment_interpretation("GAD-7", 3)
        assert "최소한" in interpretation

        interpretation = service._get_assessment_interpretation("GAD-7", 16)
        assert "중증" in interpretation

    def test_user_stats_csv_export(self):
        """Test user statistics CSV export"""
        from src.export_service import ExportService

        service = ExportService()

        stats_data = {
            "total_conversations": 10,
            "total_messages": 50,
            "crisis_count": 2,
            "preferences": {
                "persona_favorite": "warm_mother",
                "interaction_count": 5
            }
        }

        csv_data = service.export_user_stats_to_csv(
            user_id="test_user",
            stats_data=stats_data
        )

        assert csv_data is not None
        csv_text = csv_data.decode('utf-8-sig')
        assert "total_conversations" in csv_text
        assert "10" in csv_text


class TestVoiceAPIEndpoints:
    """Test voice API endpoints (mocked)"""

    @patch('src.api.get_voice_service_instance')
    def test_transcribe_endpoint_validation(self, mock_voice_service):
        """Test transcribe endpoint validates input"""
        # This would require FastAPI TestClient
        # Placeholder for actual API testing
        pass

    @patch('src.api.get_voice_service_instance')
    def test_synthesize_endpoint_validation(self, mock_voice_service):
        """Test synthesize endpoint validates input"""
        # This would require FastAPI TestClient
        # Placeholder for actual API testing
        pass


class TestExportAPIEndpoints:
    """Test export API endpoints (mocked)"""

    def test_export_csv_endpoint(self):
        """Test CSV export endpoint"""
        # This would require FastAPI TestClient
        # Placeholder for actual API testing
        pass

    def test_export_pdf_endpoint(self):
        """Test PDF export endpoint"""
        # This would require FastAPI TestClient
        # Placeholder for actual API testing
        pass


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""

    def test_full_voice_conversation_flow(self):
        """Test complete voice conversation workflow"""
        # This would test:
        # 1. Audio upload
        # 2. STT transcription
        # 3. Message processing
        # 4. TTS synthesis
        # 5. Audio response
        pass

    def test_full_export_workflow(self):
        """Test complete export workflow"""
        # This would test:
        # 1. Have a conversation
        # 2. Export to CSV
        # 3. Export to JSON
        # 4. Generate PDF report
        # 5. Verify all exports contain correct data
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
