"""
유틸리티 함수 모듈
Utility Functions Module

공통으로 사용되는 헬퍼 함수들을 제공합니다.
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    로깅 시스템 설정

    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 콘솔만 출력)
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler()]

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def load_json(file_path: str) -> Dict[str, Any]:
    """
    JSON 파일 로드

    Args:
        file_path: JSON 파일 경로

    Returns:
        Dict: JSON 데이터
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        return {}


def save_json(data: Dict[str, Any], file_path: str) -> bool:
    """
    JSON 파일 저장

    Args:
        data: 저장할 데이터
        file_path: 저장 경로

    Returns:
        bool: 성공 여부
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"JSON 저장 오류: {e}")
        return False


def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    YAML 파일 로드

    Args:
        file_path: YAML 파일 경로

    Returns:
        Dict: YAML 데이터
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"YAML 파싱 오류: {e}")
        return {}


def truncate_conversation_history(
    history: List[Dict[str, str]],
    max_turns: int = 10
) -> List[Dict[str, str]]:
    """
    대화 기록 자르기 (최근 N턴만 유지)

    Args:
        history: 대화 기록 리스트
        max_turns: 최대 턴 수

    Returns:
        List: 잘린 대화 기록
    """
    if len(history) <= max_turns * 2:  # user + assistant = 1 turn
        return history

    # 최근 대화만 유지
    return history[-(max_turns * 2):]


def format_conversation_for_model(
    history: List[Dict[str, str]],
    system_prompt: str
) -> str:
    """
    대화 기록을 모델 입력 형식으로 변환

    Args:
        history: 대화 기록
        system_prompt: 시스템 프롬프트

    Returns:
        str: 포맷된 대화 문자열
    """
    formatted = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"

    for i, turn in enumerate(history):
        role = turn.get("role", "")
        content = turn.get("content", "")

        if role == "user":
            if i == 0:
                formatted += f"{content} [/INST]"
            else:
                formatted += f"<s>[INST] {content} [/INST]"
        elif role == "assistant":
            formatted += f" {content} </s>"

    return formatted


def extract_response_from_generation(generated_text: str) -> str:
    """
    생성된 텍스트에서 응답 부분만 추출

    Args:
        generated_text: 모델이 생성한 전체 텍스트

    Returns:
        str: 추출된 응답
    """
    # </s> 태그 이후 텍스트 제거
    if "</s>" in generated_text:
        generated_text = generated_text.split("</s>")[0]

    # [/INST] 이후의 텍스트만 추출
    if "[/INST]" in generated_text:
        parts = generated_text.split("[/INST]")
        response = parts[-1].strip()
    else:
        response = generated_text.strip()

    return response


def clean_text(text: str) -> str:
    """
    텍스트 정제

    Args:
        text: 입력 텍스트

    Returns:
        str: 정제된 텍스트
    """
    # 앞뒤 공백 제거
    text = text.strip()

    # 연속된 공백을 하나로
    import re
    text = re.sub(r'\s+', ' ', text)

    # 특수 토큰 제거
    special_tokens = ['<s>', '</s>', '[INST]', '[/INST]', '<<SYS>>', '<</SYS>>']
    for token in special_tokens:
        text = text.replace(token, '')

    return text.strip()


def get_timestamp() -> str:
    """
    현재 타임스탬프 반환

    Returns:
        str: ISO 형식의 타임스탬프
    """
    return datetime.now().isoformat()


def check_gpu_availability() -> Dict[str, Any]:
    """
    GPU 사용 가능 여부 확인

    Returns:
        Dict: GPU 정보
    """
    import torch

    gpu_info = {
        "available": torch.cuda.is_available(),
        "device_count": 0,
        "devices": []
    }

    if torch.cuda.is_available():
        gpu_info["device_count"] = torch.cuda.device_count()

        for i in range(torch.cuda.device_count()):
            device_props = torch.cuda.get_device_properties(i)
            gpu_info["devices"].append({
                "id": i,
                "name": device_props.name,
                "total_memory_gb": round(device_props.total_memory / (1024**3), 2),
                "compute_capability": f"{device_props.major}.{device_props.minor}"
            })

    return gpu_info


def estimate_model_memory(model_name: str, quantization_bits: int = 16) -> float:
    """
    모델 메모리 사용량 추정

    Args:
        model_name: 모델 이름
        quantization_bits: 양자화 비트 (4, 8, 16)

    Returns:
        float: 예상 메모리 사용량 (GB)
    """
    # SOLAR-Ko-10.7B 기준
    base_params = 10.7  # billion parameters

    # 파라미터당 바이트 수
    bytes_per_param = quantization_bits / 8

    # 모델 가중치 메모리
    model_memory = base_params * bytes_per_param

    # 추가 오버헤드 (약 20%)
    total_memory = model_memory * 1.2

    return round(total_memory, 2)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    설정 파일 유효성 검사

    Args:
        config: 설정 딕셔너리

    Returns:
        bool: 유효성 여부
    """
    required_keys = ["model", "generation", "conversation", "safety"]

    for key in required_keys:
        if key not in config:
            logger.error(f"필수 설정 키 누락: {key}")
            return False

    return True


def create_default_config() -> Dict[str, Any]:
    """
    기본 설정 생성

    Returns:
        Dict: 기본 설정
    """
    return {
        "model": {
            "name": "beomi/OPEN-SOLAR-KO-10.7B",
            "quantization": {
                "enabled": True,
                "bits": 4
            }
        },
        "generation": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_new_tokens": 512
        },
        "conversation": {
            "max_turns": 10
        },
        "safety": {
            "enable_crisis_detection": True
        }
    }


def sanitize_user_input(text: str) -> str:
    """
    사용자 입력 정제 (보안)

    Args:
        text: 사용자 입력

    Returns:
        str: 정제된 입력
    """
    # HTML 태그 제거
    import re
    text = re.sub(r'<[^>]+>', '', text)

    # 과도한 반복 문자 제한
    text = re.sub(r'(.)\1{10,}', r'\1\1\1', text)

    # 최대 길이 제한
    max_length = 2000
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


if __name__ == "__main__":
    # 테스트 코드
    setup_logging("INFO")
    logger.info("Utility module loaded successfully")

    # GPU 확인
    gpu_info = check_gpu_availability()
    logger.info(f"GPU Info: {gpu_info}")

    # 메모리 추정
    memory_4bit = estimate_model_memory("SOLAR-Ko-10.7B", 4)
    logger.info(f"Estimated 4-bit model memory: {memory_4bit} GB")
