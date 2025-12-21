"""
GPU 감지 및 검증 유틸리티
GPU가 감지되지 않으면 상세한 에러 로그와 함께 예외를 발생시킵니다.
"""

import logging
import sys
import subprocess
import platform

logger = logging.getLogger(__name__)

# GPU 감지 결과 캐시 (중복 로그 방지)
_gpu_cache = {
    "checked": False,
    "result": None
}


def check_gpu_availability(raise_on_failure: bool = True, log_info: bool = True) -> dict:
    """
    GPU 사용 가능 여부를 확인하고, 실패 시 상세한 에러 정보를 로그로 출력합니다.
    
    Args:
        raise_on_failure: GPU가 없을 때 예외를 발생시킬지 여부
        log_info: 로그 출력 여부 (기본값: True, 첫 호출만 출력)
        
    Returns:
        dict: GPU 정보
        
    Raises:
        RuntimeError: GPU가 감지되지 않고 raise_on_failure=True인 경우
    """
    global _gpu_cache
    
    # 캐시된 결과가 있으면 재사용 (로그 중복 방지)
    if _gpu_cache["checked"] and _gpu_cache["result"] is not None:
        result = _gpu_cache["result"]
        if not result["available"] and raise_on_failure:
            raise RuntimeError(result.get("error", "GPU를 찾을 수 없습니다."))
        return result
    
    import torch
    
    gpu_info = {
        "available": False,
        "device_count": 0,
        "device_name": None,
        "cuda_version": None,
        "driver_version": None,
        "error": None
    }
    
    try:
        # PyTorch CUDA 사용 가능 여부 확인
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["device_count"] = torch.cuda.device_count()
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            gpu_info["cuda_version"] = torch.version.cuda
            
            # GPU 속성 정보
            if gpu_info["device_count"] > 0:
                device_props = torch.cuda.get_device_properties(0)
                gpu_info["total_memory"] = device_props.total_memory / (1024**3)  # GB
                gpu_info["major"] = device_props.major
                gpu_info["minor"] = device_props.minor
                
            # 첫 호출 시에만 로그 출력
            if log_info and not _gpu_cache["checked"]:
                logger.info(f"✓ GPU 감지 성공: {gpu_info['device_name']}")
                logger.info(f"  - CUDA 버전: {gpu_info['cuda_version']}")
                logger.info(f"  - GPU 개수: {gpu_info['device_count']}")
                if 'total_memory' in gpu_info:
                    logger.info(f"  - GPU 메모리: {gpu_info['total_memory']:.1f} GB")
            
            # 결과 캐싱
            _gpu_cache["checked"] = True
            _gpu_cache["result"] = gpu_info
            
            return gpu_info
        else:
            # GPU가 감지되지 않은 경우 상세한 원인 분석
            error_details = []
            error_details.append("=" * 70)
            error_details.append("❌ GPU 감지 실패 - 상세 원인 분석")
            error_details.append("=" * 70)
            
            # 1. PyTorch 정보
            error_details.append(f"\n[1] PyTorch 정보:")
            error_details.append(f"  - PyTorch 버전: {torch.__version__}")
            error_details.append(f"  - CUDA 사용 가능: {torch.cuda.is_available()}")
            
            # 2. PyTorch 빌드 정보 확인
            if hasattr(torch.version, 'cuda'):
                error_details.append(f"  - PyTorch CUDA 버전: {torch.version.cuda or 'N/A'}")
            else:
                error_details.append(f"  - PyTorch CUDA 버전: N/A (CPU 전용 빌드 가능성)")
            
            # PyTorch가 CPU 전용인지 확인
            if '+cpu' in torch.__version__:
                error_details.append(f"  ⚠️  CPU 전용 PyTorch가 설치되어 있습니다!")
                error_details.append(f"     해결 방법: CUDA 버전의 PyTorch를 설치하세요.")
                error_details.append(f"     예: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
            
            # 3. NVIDIA 드라이버 확인 (Windows)
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        driver_version = result.stdout.strip().split('\n')[0]
                        error_details.append(f"\n[2] NVIDIA 드라이버:")
                        error_details.append(f"  - 드라이버 버전: {driver_version}")
                        gpu_info["driver_version"] = driver_version
                    else:
                        error_details.append(f"\n[2] NVIDIA 드라이버:")
                        error_details.append(f"  ⚠️  nvidia-smi 명령을 실행할 수 없습니다.")
                        error_details.append(f"     NVIDIA 드라이버가 설치되지 않았거나 PATH에 없을 수 있습니다.")
                except FileNotFoundError:
                    error_details.append(f"\n[2] NVIDIA 드라이버:")
                    error_details.append(f"  ⚠️  nvidia-smi를 찾을 수 없습니다.")
                    error_details.append(f"     NVIDIA 드라이버가 설치되지 않았을 수 있습니다.")
                except subprocess.TimeoutExpired:
                    error_details.append(f"\n[2] NVIDIA 드라이버:")
                    error_details.append(f"  ⚠️  nvidia-smi 응답 시간 초과")
                except Exception as e:
                    error_details.append(f"\n[2] NVIDIA 드라이버:")
                    error_details.append(f"  ⚠️  확인 실패: {e}")
            else:
                # Linux/Mac
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        driver_version = result.stdout.strip().split('\n')[0]
                        error_details.append(f"\n[2] NVIDIA 드라이버:")
                        error_details.append(f"  - 드라이버 버전: {driver_version}")
                        gpu_info["driver_version"] = driver_version
                except Exception:
                    pass
            
            # 4. CUDA 라이브러리 확인
            error_details.append(f"\n[3] CUDA 라이브러리:")
            try:
                import ctypes.util
                cuda_lib = ctypes.util.find_library('cudart')
                if cuda_lib:
                    error_details.append(f"  - CUDA 런타임 라이브러리: {cuda_lib}")
                else:
                    error_details.append(f"  ⚠️  CUDA 런타임 라이브러리를 찾을 수 없습니다.")
            except Exception as e:
                error_details.append(f"  ⚠️  CUDA 라이브러리 확인 실패: {e}")
            
            # 5. 하드웨어 확인
            error_details.append(f"\n[4] 하드웨어:")
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "name"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        gpus = [line.strip() for line in result.stdout.split('\n') if line.strip() and line.strip() != 'Name']
                        if gpus:
                            error_details.append(f"  - 감지된 GPU:")
                            for gpu in gpus:
                                error_details.append(f"    • {gpu}")
                        else:
                            error_details.append(f"  ⚠️  GPU 하드웨어를 찾을 수 없습니다.")
                except Exception:
                    error_details.append(f"  ⚠️  하드웨어 정보를 확인할 수 없습니다.")
            
            # 6. 환경 변수 확인
            error_details.append(f"\n[5] 환경 변수:")
            cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', 'N/A')
            error_details.append(f"  - CUDA_VISIBLE_DEVICES: {cuda_visible}")
            if cuda_visible != 'N/A' and cuda_visible != '':
                error_details.append(f"  ⚠️  CUDA_VISIBLE_DEVICES가 설정되어 있어 GPU가 숨겨져 있을 수 있습니다.")
            
            # 7. 해결 방법 제시
            error_details.append(f"\n[6] 해결 방법:")
            error_details.append(f"  1. NVIDIA 드라이버가 최신인지 확인: https://www.nvidia.com/Download/index.aspx")
            error_details.append(f"  2. CUDA 버전의 PyTorch 설치:")
            error_details.append(f"     pip uninstall torch torchvision torchaudio")
            error_details.append(f"     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
            error_details.append(f"  3. CUDA_VISIBLE_DEVICES 환경 변수 확인")
            error_details.append(f"  4. 시스템 재시작 후 다시 시도")
            error_details.append("=" * 70)
            
            error_message = "\n".join(error_details)
            gpu_info["error"] = error_message
            
            # 로그에 상세 정보 출력
            logger.error(error_message)
            
            # raise_on_failure이 True이면 예외 발생
            if raise_on_failure:
                raise RuntimeError(
                    "GPU가 감지되지 않습니다. GPU가 필요합니다.\n"
                    "상세한 원인 분석은 위의 로그를 참조하세요."
                )
            
            return gpu_info
            
    except ImportError:
        error_msg = "PyTorch가 설치되지 않았습니다. pip install torch를 실행하세요."
        logger.error(error_msg)
        gpu_info["error"] = error_msg
        if raise_on_failure:
            raise RuntimeError(error_msg)
        return gpu_info
    except Exception as e:
        error_msg = f"GPU 확인 중 오류 발생: {e}"
        logger.error(error_msg, exc_info=True)
        gpu_info["error"] = error_msg
        if raise_on_failure:
            raise RuntimeError(error_msg)
        return gpu_info


def require_gpu(device: str = "cuda") -> str:
    """
    GPU가 필요한 경우 사용 가능한지 확인하고, 없으면 예외를 발생시킵니다.
    
    Args:
        device: 요청한 디바이스 ("cuda"인 경우 GPU 필수)
        
    Returns:
        str: 실제 사용할 디바이스
        
    Raises:
        RuntimeError: device가 "cuda"인데 GPU가 감지되지 않은 경우
    """
    if device == "cuda":
        # 캐시를 사용하여 중복 로그 방지
        gpu_info = check_gpu_availability(raise_on_failure=True, log_info=True)
        if not gpu_info["available"]:
            raise RuntimeError("GPU가 필요하지만 감지되지 않았습니다.")
        return "cuda"
    else:
        return device

