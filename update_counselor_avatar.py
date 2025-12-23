"""
상담사 아바타 이미지 업데이트 스크립트
사용자가 제공한 이미지 파일을 상담사 아바타로 교체합니다.
"""
import sys
from pathlib import Path
from PIL import Image
import shutil

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def update_counselor_avatar(image_path):
    """
    상담사 아바타 이미지를 업데이트합니다.
    
    Args:
        image_path: 새 이미지 파일 경로
    """
    # 경로 설정
    target_dir = Path('frontend/images')
    target_file = target_dir / 'counselor_avatar.png'
    
    # 디렉토리 생성
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 이미지 파일 확인
    source_path = Path(image_path)
    if not source_path.exists():
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        print("\n사용 방법:")
        print("1. 이미지 파일을 프로젝트 루트에 복사하세요")
        print("2. 다음 명령을 실행하세요:")
        print(f"   python update_counselor_avatar.py <이미지_파일_경로>")
        return False
    
    try:
        # 이미지 열기 및 리사이즈
        print(f"📷 이미지 로드 중: {source_path}")
        img = Image.open(source_path)
        
        # 원본 크기 확인
        print(f"   원본 크기: {img.size[0]}x{img.size[1]}px")
        
        # 원형 아바타로 변환 (정사각형으로 리사이즈 후 원형 마스크 적용)
        size = 200  # 최종 크기
        img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # 원형 마스크 생성
        from PIL import ImageDraw
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        # 원형 이미지 생성
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        if img_resized.mode == 'RGBA':
            output.paste(img_resized, (0, 0), mask)
        else:
            img_rgba = img_resized.convert('RGBA')
            output.paste(img_rgba, (0, 0), mask)
        
        # 저장
        output.save(target_file, 'PNG', optimize=True)
        print(f"✅ 상담사 아바타 이미지 업데이트 완료: {target_file}")
        print(f"   최종 크기: {size}x{size}px (원형)")
        
        # 백업 생성
        backup_file = target_dir / 'counselor_avatar_backup.png'
        if target_file.exists() and not backup_file.exists():
            shutil.copy2(target_file, backup_file)
            print(f"📦 기존 이미지 백업: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 70)
        print("상담사 아바타 이미지 업데이트")
        print("=" * 70)
        print("\n사용 방법:")
        print("  python update_counselor_avatar.py <이미지_파일_경로>")
        print("\n예시:")
        print("  python update_counselor_avatar.py counselor.jpg")
        print("  python update_counselor_avatar.py C:/Users/username/Pictures/counselor.png")
        print("\n지원 형식: JPG, PNG, JPEG, WEBP")
        print("\n이미지가 자동으로 200x200px 원형 아바타로 변환됩니다.")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = update_counselor_avatar(image_path)
    sys.exit(0 if success else 1)

