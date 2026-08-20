from pathlib import Path

# 게임이 설치된 폴더 경로로 수정하세요
GAME_DIR = Path(r"C:\Program Files (x86)\CTRacer")


def main():
    if not GAME_DIR.exists():
        print("❌ 지정한 경로가 존재하지 않습니다. GAME_DIR 경로를 확인해 주세요.")
        return

    print(f"📁 [{GAME_DIR}] 파일 구조 탐색 중...\n")

    ext_counter = {}
    sample_files = []

    for file_path in GAME_DIR.rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix.lower() or "(확장자 없음)"
            ext_counter[ext] = ext_counter.get(ext, 0) + 1

            # 데이터 파일 가능성이 높은 파일 모음
            if ext in [".dat", ".bin", ".tbl", ".pak", ".db", ".xml", ".txt", ".csv"]:
                sample_files.append((ext, file_path.name))

    print("📊 **확장자별 파일 개수**")
    for ext, count in sorted(ext_counter.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {ext}: {count}개")

    print("\n🔍 **주요 데이터 후보 파일 (상위 15개)**")
    for ext, name in sample_files[:15]:
        print(f"  - [{ext}] {name}")


if __name__ == "__main__":
    main()