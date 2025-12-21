# TTS 속도 최적화 가이드

## 개요
이 문서는 Zonos TTS의 속도를 향상시키기 위한 다양한 방법을 설명합니다.

## 1. 하드웨어 최적화

### GPU 성능
- **더 좋은 GPU**: NVIDIA RTX 3090, RTX 4090, A100 등 고성능 GPU 사용
- **VRAM**: 최소 8GB 이상 권장 (모델 로딩 및 생성 시 메모리 사용)
- **CUDA 버전**: 최신 CUDA 드라이버 및 PyTorch-CUDA 버전 사용

### 현재 GPU 확인
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
```

## 2. 소프트웨어 최적화 (이미 적용됨)

### ✅ 현재 적용된 최적화
1. **torch.compile 비활성화**: 컴파일 오버헤드 제거, eager mode 사용
2. **텍스트 청크 크기**: 100자 → 80자로 축소 (더 빠른 첫 응답)
3. **max_codes 범위 축소**: 100-500 → 80-400 (생성 시간 단축)
4. **CUDA 최적화**: cuDNN benchmark 활성화, 메모리 캐시 정리

### 추가 최적화 옵션

#### A. 모델 양자화 (INT8)
```python
# 모델을 INT8로 양자화하여 속도 향상 (품질 약간 저하 가능)
from torch.quantization import quantize_dynamic
model_int8 = quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
```

#### B. 배치 처리
```python
# 여러 문장을 한 번에 처리 (현재는 순차 처리)
# 주의: 메모리 사용량 증가
```

#### C. 샘플레이트 낮추기 (품질 저하)
```python
# 24000Hz → 16000Hz (속도 향상, 품질 저하)
# 현재는 24000Hz 사용 중
```

## 3. 설정 조정

### 현재 설정 (src/tts.py)
- **max_chunk_length**: 80자 (100에서 축소)
- **max_codes**: 80-400 (100-500에서 축소)
- **sample_rate**: 24000Hz
- **torch.compile**: 비활성화됨

### 속도 우선 설정 (더 빠르게)
```python
max_chunk_length = 60  # 더 작은 청크
max_codes = max(60, min(max_codes, 300))  # 더 작은 범위
```

### 품질 우선 설정 (더 느리지만 품질 향상)
```python
max_chunk_length = 120  # 더 큰 청크
max_codes = max(100, min(max_codes, 600))  # 더 큰 범위
```

## 4. 성능 벤치마크

### 현재 성능 측정
코드에 이미 성능 측정 로그가 추가되어 있습니다:
```
TTS generation completed in X.XXs (max_codes=XXX, text_length=XXX)
```

### 목표 성능
- **짧은 텍스트 (10-20자)**: 1-2초 이내
- **중간 텍스트 (50-100자)**: 3-5초 이내
- **긴 텍스트 (200자 이상)**: 청크 단위로 스트리밍

## 5. GPU 업그레이드 가이드

### 권장 GPU (속도 순)
1. **NVIDIA RTX 4090** (24GB VRAM) - 최고 성능
2. **NVIDIA RTX 3090** (24GB VRAM) - 우수한 성능
3. **NVIDIA RTX 3080** (10GB VRAM) - 좋은 성능
4. **NVIDIA RTX 3060** (12GB VRAM) - 기본 성능

### 예상 성능 향상
- **RTX 3060 → RTX 4090**: 약 3-4배 속도 향상
- **CPU → RTX 3060**: 약 10-20배 속도 향상

## 6. 추가 최적화 팁

### A. 시스템 최적화
- 백그라운드 프로세스 종료
- GPU 전용 모드 설정 (Windows: 전원 관리 → 고성능)
- GPU 드라이버 최신 버전 유지

### B. 메모리 관리
- 불필요한 모델 언로드
- GPU 메모리 캐시 정리 (`torch.cuda.empty_cache()`)

### C. 네트워크 최적화 (스트리밍)
- 작은 청크로 빠른 첫 응답
- 병렬 처리 (여러 문장 동시 생성)

## 7. 문제 해결

### 느린 생성 속도
1. GPU 사용 확인: `torch.cuda.is_available()`
2. GPU 메모리 확인: `nvidia-smi`
3. 텍스트 길이 확인: 너무 긴 텍스트는 청크로 분할
4. 로그 확인: `TTS generation completed in X.XXs`

### 메모리 부족
1. `max_codes` 범위 축소
2. `max_chunk_length` 축소
3. 배치 크기 축소

## 8. 코드 수정 예시

### 더 빠른 설정으로 변경
`src/tts.py` 파일에서:
```python
# Line 520: 더 작은 청크
max_chunk_length = 60  # 80에서 60으로

# Line 711: 더 작은 max_codes
max_codes = max(60, min(max_codes, 300))  # 80-400에서 60-300으로
```

주의: 너무 작은 값은 품질 저하를 일으킬 수 있습니다.

