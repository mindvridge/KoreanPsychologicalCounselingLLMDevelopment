# Windows 실행파일 빌드 가이드

## 개요
이 가이드는 마음챗 애플리케이션을 Windows 실행파일(.exe)로 빌드하는 방법을 설명합니다.

## 사전 요구사항

1. **Python 3.10 이상** 설치
2. **모든 의존성 패키지** 설치:
   ```bash
   pip install -r requirements.txt
   ```
3. **PyInstaller** 설치 (자동 설치됨):
   ```bash
   pip install pyinstaller
   ```

## 빌드 방법

### 방법 1: 배치 파일 사용 (권장)
```bash
build_exe.bat
```

### 방법 2: Python 스크립트 직접 실행
```bash
python build_exe.py
```

### 방법 3: PyInstaller 직접 사용
```bash
pyinstaller 마음챗.spec
```

## 빌드 결과

빌드가 완료되면 다음 위치에 실행파일이 생성됩니다:
```
dist/마음챗.exe
```

## 실행 방법

1. `dist` 폴더로 이동
2. `마음챗.exe` 더블클릭 또는 명령줄에서 실행:
   ```bash
   dist\마음챗.exe
   ```

**중요**: `마음챗.exe`를 실행하면 `start_all.py`와 동일하게 작동합니다:
- ✅ 기존 서버 프로세스 자동 종료 (포트 8000, 8001)
- ✅ 메인 API 서버 시작 (포트 8000)
- ✅ 음성 API 서버 시작 (포트 8001)
- ✅ 브라우저 자동 열기 (http://localhost:8000)
- ✅ 모든 초기화 과정 수행

## 주의사항

### 필수 파일
- `.env` 파일: API 키 등 환경 변수가 포함되어 있어야 합니다
- `configs/` 폴더: 설정 파일들이 포함되어야 합니다
- `frontend/` 폴더: 프론트엔드 파일들이 포함되어야 합니다

### 시스템 요구사항
- **espeak-ng**: TTS 기능을 위해 필요합니다
  - 설치: `choco install espeak-ng -y` (관리자 권한)
- **CUDA**: GPU 가속을 위해 필요합니다 (선택사항)
- **인터넷 연결**: OpenAI API 사용 시 필요합니다

### 빌드 크기
- 실행파일 크기는 약 500MB~1GB 정도입니다 (모든 의존성 포함)
- 빌드 시간은 시스템 성능에 따라 5~15분 정도 소요됩니다

## 문제 해결

### 빌드 오류
1. **모듈을 찾을 수 없음**: `hiddenimports`에 모듈 추가
2. **데이터 파일 누락**: `datas`에 파일/폴더 경로 추가
3. **메모리 부족**: 빌드 중 다른 프로그램 종료

### 실행 오류
1. **DLL 오류**: Visual C++ Redistributable 설치 필요
2. **경로 오류**: 상대 경로 문제일 수 있음
3. **권한 오류**: 관리자 권한으로 실행 시도

## 고급 설정

### 아이콘 추가
`마음챗.spec` 파일에서 `icon=None` 부분을 수정:
```python
icon='path/to/icon.ico',
```

### 콘솔 창 숨기기
`마음챗.spec` 파일에서 `console=True`를 `console=False`로 변경

### 단일 파일 vs 폴더
현재 설정은 단일 실행파일로 빌드됩니다. 폴더 형태로 빌드하려면:
```python
exe = EXE(
    ...
    onefile=True,  # False로 변경
)
```

## 배포

빌드된 실행파일을 배포할 때:
1. `dist/마음챗.exe` 파일
2. `.env` 파일 (또는 환경 변수 설정 가이드)
3. `README.md` (사용 가이드)

이 세 가지를 함께 배포하세요.

