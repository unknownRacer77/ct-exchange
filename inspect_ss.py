import os
from pathlib import Path

GAME_DIR = Path(r"C:\Program Files (x86)\CTRacer")

def inspect_ss_files():
    print("🔍 .ss / .si 파일 내부 분석 중...\n")
    
    count = 0
    for file_path in GAME_DIR.rglob("*"):
        if file_path.suffix.lower() in [".ss", ".si"]:
            count += 1
            print(f"📄 [{file_path.name}] (경로: {file_path.relative_to(GAME_DIR)})")
            
            # EUC-KR / CP949 인코딩으로 텍스트 읽기 시도
            try:
                with open(file_path, "r", encoding="cp949", errors="ignore") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    if lines:
                        print("  └ 텍스트 샘플 (상위 3줄):")
                        for line in lines[:3]:
                            print(f"     > {line[:80]}")
                    else:
                        print("  └ (빈 파일 또는 바이너리 데이터)")
            except Exception as e:
                print(f"  └ 읽기 실패: {e}")
                
            print("-" * 60)
            if count >= 10:  # 상위 10개만 확인
                break

if __name__ == "__main__":
    inspect_ss_files()