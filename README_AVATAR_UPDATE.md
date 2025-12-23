# 상담사 아바타 이미지 업데이트 가이드

## 개요
AI 상담사 채팅 아이콘을 사용자가 제공한 이미지로 교체하는 방법입니다.

## 사용 방법

### 1. 이미지 파일 준비
- 지원 형식: JPG, PNG, JPEG, WEBP
- 권장 크기: 최소 200x200px 이상
- 이미지 파일을 프로젝트 루트 디렉토리에 복사하세요

### 2. 스크립트 실행
```bash
python update_counselor_avatar.py <이미지_파일_경로>
```

### 예시
```bash
# 프로젝트 루트에 있는 이미지
python update_counselor_avatar.py counselor.jpg

# 절대 경로 사용
python update_counselor_avatar.py C:/Users/username/Pictures/counselor.png
```

### 3. 결과
- 이미지가 자동으로 200x200px 원형 아바타로 변환됩니다
- `frontend/images/counselor_avatar.png`에 저장됩니다
- 기존 이미지는 `counselor_avatar_backup.png`로 백업됩니다

## 적용 위치
다음 위치에서 상담사 아바타가 표시됩니다:
- 채팅 헤더 (상담사 정보)
- 채팅 메시지 (봇 메시지 아바타)
- "생각중" 메시지 아바타
- 홈 화면 상담사 정보

## 주의사항
- Pillow 라이브러리가 설치되어 있어야 합니다: `pip install Pillow`
- 이미지 파일 경로에 한글이나 특수문자가 포함되지 않도록 주의하세요
- 브라우저 캐시를 지우고 새로고침하면 변경된 이미지가 표시됩니다

