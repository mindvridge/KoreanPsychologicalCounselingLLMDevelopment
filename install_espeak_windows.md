# Windows에서 espeak-ng 설치 방법

Zonos TTS가 작동하려면 `espeak-ng`가 필요합니다.

## 방법 1: Chocolatey 사용 (관리자 권한 필요)

관리자 권한으로 PowerShell을 열고:

```powershell
choco install espeak-ng -y
```

## 방법 2: 수동 설치

1. espeak-ng 다운로드:
   - https://github.com/espeak-ng/espeak-ng/releases
   - 최신 Windows 버전 다운로드

2. 설치:
   - 다운로드한 파일 실행
   - 또는 압축 해제 후 `espeak-ng.exe`를 PATH에 추가

3. PATH 확인:
   ```powershell
   espeak-ng --version
   ```

## 방법 3: WSL 사용

WSL(Windows Subsystem for Linux)을 사용하는 경우:

```bash
sudo apt-get update
sudo apt-get install espeak-ng
```

