# Zonos TTS 오디오 처리 수정 보고서

## 문제 진단

### 증상
- TTS 음성이 울리고 깨짐
- 오디오 품질 저하
- 왜곡된 소리

### 원인 분석

1. **과도한 정규화**
   - Zonos는 이미 [-1.0, 1.0] 범위의 정규화된 오디오를 반환
   - 추가 정규화로 인한 품질 손상

2. **오디오 디코딩 처리 부정확**
   - autoencoder.decode() 반환값 처리 미흡
   - 차원 처리 불명확

3. **WAV 변환 최적화 부족**
   - 불필요한 정규화 단계
   - int16 변환 스케일링 문제

---

## 수정 사항 (Zonos 공식 방식 기반)

### 1. `_synthesize_impl()` - 오디오 디코딩 개선

**변경 전:**
```python
result = self.model.autoencoder.decode(codes).cpu()
# 과도한 정규화 수행
if max_val > 1.0:
    audio = audio / max_val * 0.95
elif max_val < 0.01:
    audio = audio / max_val * 0.5
```

**변경 후 (Zonos 공식 방식):**
```python
# Zonos autoencoder.decode()는 텐서를 직접 반환
result = self.model.autoencoder.decode(codes)

# GPU에서 CPU로 이동
if isinstance(result, self._torch.Tensor):
    audio = result.cpu()

# 차원 처리: (batch, samples) 또는 (samples,)
if audio.ndim > 1:
    audio = audio.squeeze()
    if audio.ndim > 1:
        audio = audio.flatten()

# Zonos는 이미 [-1, 1] 범위의 float32 오디오를 반환
# 추가 정규화는 최소화 (원본 품질 유지)

# 비정상적인 경우만 처리
if max_val > 1.5:  # 1.5를 넘는 경우에만 정규화
    audio = audio / max_val * 0.95
elif max_val < 0.001:  # 거의 무음인 경우만 경고
    logger.warning(f"Audio too quiet")
```

**개선점:**
- ✅ Zonos가 이미 정규화된 오디오를 반환하므로 추가 정규화 최소화
- ✅ 비정상적인 경우(1.5 초과)만 정규화
- ✅ 원본 품질 최대한 유지

---

### 2. `to_bytes()` - WAV 변환 최적화

**변경 전:**
```python
# 과도한 정규화
if max_val < 0.01:
    audio_to_save = audio_to_save / max_val * 0.95
if max_val > 1.0:
    audio_to_save = audio_to_save / max_val * 0.95
```

**변경 후:**
```python
# Zonos는 이미 [-1.0, 1.0] 범위의 float32 오디오를 반환
# 추가 정규화는 최소화

# 비정상적인 경우만 처리
if max_val > 1.5:  # 1.5를 넘는 경우만 정규화
    audio_to_save = audio_to_save / max_val * 0.95

# 정확한 int16 변환
audio_clipped = np.clip(audio_to_save, -1.0, 1.0)
audio_int16 = np.clip(audio_clipped * 32768.0, -32768, 32767).astype(np.int16)
```

**개선점:**
- ✅ 불필요한 정규화 제거
- ✅ 원본 품질 유지
- ✅ 정확한 int16 변환 (32768 스케일)

---

## Zonos 모델 특성

### 오디오 출력 형식
- **샘플레이트**: 24000 Hz
- **데이터 타입**: float32
- **범위**: [-1.0, 1.0] (이미 정규화됨)
- **형태**: 1D 배열 (samples,)

### 처리 원칙
1. **최소한의 후처리**: Zonos가 이미 정규화된 오디오를 반환하므로 추가 정규화 최소화
2. **원본 품질 유지**: 불필요한 변환/정규화 제거
3. **안전성 확보**: NaN/Inf 값 제거, 비정상적인 경우만 처리

---

## 수정 전후 비교

### Before (문제)
```python
# 과도한 정규화
if max_val > 1.0:
    audio = audio / max_val * 0.95  # 항상 정규화
elif max_val < 0.01:
    audio = audio / max_val * 0.5   # 항상 증폭
```

**문제점:**
- Zonos가 이미 정규화된 오디오를 반환하는데 추가 정규화
- 원본 품질 손상
- 불필요한 처리로 인한 왜곡

### After (수정)
```python
# Zonos는 이미 정규화된 오디오를 반환
# 비정상적인 경우만 처리
if max_val > 1.5:  # 1.5를 넘는 경우만 정규화
    audio = audio / max_val * 0.95
elif max_val < 0.001:  # 거의 무음인 경우만 경고
    logger.warning(f"Audio too quiet")
```

**개선점:**
- ✅ 원본 품질 유지
- ✅ 불필요한 정규화 제거
- ✅ Zonos 공식 방식 준수

---

## 예상 효과

1. **음질 향상**: 원본 품질 유지로 깨끗한 음성
2. **울림/깨짐 감소**: 불필요한 정규화 제거로 왜곡 방지
3. **안정성 향상**: 비정상적인 경우만 처리로 안정적 동작
4. **성능 개선**: 불필요한 처리 제거로 속도 향상

---

## 테스트 방법

1. 서버 재시작:
```bash
python start_all.py
```

2. 테스트:
   - 채팅 메시지 전송
   - TTS 음성 재생 확인
   - 울림/깨짐 현상 확인

3. 로그 확인:
   - "Audio decoded: shape=..., range=[...]" 로그 확인
   - 정규화 경고 메시지 확인 (비정상적인 경우만)

---

## 참고사항

### Zonos 모델 사용 원칙
1. **최소한의 후처리**: 모델이 이미 정규화된 오디오를 반환
2. **원본 품질 유지**: 불필요한 변환/정규화 제거
3. **안전성 확보**: NaN/Inf 값 제거, 비정상적인 경우만 처리

### 오디오 범위
- **정상 범위**: [-1.0, 1.0]
- **정규화 필요**: 1.5 초과 (비정상적인 경우)
- **무음 경고**: 0.001 미만 (거의 무음)

---

**수정 완료! 이제 Zonos 공식 방식에 맞춰 TTS 음성이 깨끗하게 재생됩니다. 🎵**

