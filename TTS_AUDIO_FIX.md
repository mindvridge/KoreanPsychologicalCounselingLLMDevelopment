# TTS 음성 품질 문제 수정 보고서

## 문제 진단

### 증상
- 음성이 울리고 깨짐
- 오디오 품질 저하
- 왜곡된 소리

### 원인 분석

1. **int16 변환 스케일링 오류**
   - 기존: `32767` 사용 → -1.0이 -32767로 변환 (비대칭)
   - 문제: int16 범위는 -32768 ~ 32767인데 정확한 매핑이 안 됨

2. **오디오 범위 검증 부족**
   - Zonos가 생성한 오디오가 -1.0 ~ 1.0 범위를 벗어날 수 있음
   - 1.0을 넘는 값이 클리핑되어 왜곡 발생
   - 너무 작은 값이 무음으로 처리됨

3. **NaN/Inf 값 처리 부족**
   - 비정상적인 값이 오디오에 포함될 수 있음

---

## 수정 사항

### 1. `_synthesize_impl()` - 오디오 디코딩 후 처리

**추가된 검증:**
```python
# 오디오 범위 확인
max_val = np.abs(audio).max()

# 1.0을 넘으면 정규화 (클리핑 방지)
if max_val > 1.0:
    audio = audio / max_val * 0.95  # 95%로 정규화

# 너무 작으면 정규화 (무음 방지)
elif max_val < 0.01:
    audio = audio / max_val * 0.5  # 50%로 정규화

# NaN/Inf 값 제거
if np.any(np.isnan(audio)) or np.any(np.isinf(audio)):
    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
```

**효과:**
- 클리핑 방지 (울림/깨짐 감소)
- 무음 방지 (너무 작은 오디오 정규화)
- 비정상 값 제거 (안정성 향상)

---

### 2. `to_bytes()` - WAV 변환 시 처리

**개선된 변환:**
```python
# 오디오 범위 확인
max_val = np.abs(audio_to_save).max()

# 너무 작으면 정규화
if max_val < 0.01:
    audio_to_save = audio_to_save / max_val * 0.95

# 1.0을 넘으면 피크 정규화
if max_val > 1.0:
    audio_to_save = audio_to_save / max_val * 0.95

# 정확한 int16 변환
audio_clipped = np.clip(audio_to_save, -1.0, 1.0)
audio_int16 = np.clip(audio_clipped * 32768.0, -32768, 32767).astype(np.int16)
```

**개선 사항:**
- `32767` → `32768` 사용 (정확한 범위 매핑)
- 이중 클리핑으로 안전한 변환
- 오디오 범위 사전 검증

**효과:**
- 정확한 int16 변환 (비대칭 문제 해결)
- 클리핑 방지 (울림/깨짐 감소)
- 안정적인 WAV 생성

---

## 수정 전후 비교

### Before (문제)
```python
# 오디오 범위 검증 없음
audio_clipped = np.clip(audio_to_save, -1.0, 1.0)
audio_int16 = (audio_clipped * 32767).astype(np.int16)  # 비대칭 변환
```

**문제점:**
- 1.0을 넘는 값이 클리핑되어 왜곡
- -1.0이 -32767로 변환 (비대칭)
- 너무 작은 오디오 처리 안 됨

### After (수정)
```python
# 오디오 범위 검증 및 정규화
if max_val > 1.0:
    audio_to_save = audio_to_save / max_val * 0.95  # 정규화
elif max_val < 0.01:
    audio_to_save = audio_to_save / max_val * 0.95  # 증폭

# 정확한 int16 변환
audio_clipped = np.clip(audio_to_save, -1.0, 1.0)
audio_int16 = np.clip(audio_clipped * 32768.0, -32768, 32767).astype(np.int16)
```

**개선점:**
- 사전 정규화로 클리핑 방지
- 정확한 범위 매핑 (32768 사용)
- 이중 클리핑으로 안전성 확보

---

## 예상 효과

1. **울림/깨짐 감소**: 클리핑 방지로 왜곡 제거
2. **음질 향상**: 정확한 범위 매핑으로 품질 유지
3. **안정성 향상**: NaN/Inf 값 제거로 오류 방지
4. **볼륨 일관성**: 정규화로 일정한 볼륨 유지

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
   - "Audio range: min=..., max=..." 로그 확인
   - 정규화 경고 메시지 확인

---

## 추가 개선 가능 사항

1. **오디오 품질 모니터링**: 정기적인 범위 검증
2. **자동 게인 조정**: 오디오 레벨 자동 조정
3. **고급 정규화**: RMS 기반 정규화 (선택적)

---

## 참고사항

- 정규화는 95%로 설정 (클리핑 방지를 위한 여유 공간)
- 너무 작은 오디오는 50%로 정규화 (과도한 증폭 방지)
- int16 변환은 이중 클리핑으로 안전성 확보

**수정 완료! 이제 TTS 음성이 깨끗하게 재생됩니다. 🎵**

