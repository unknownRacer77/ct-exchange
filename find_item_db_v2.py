from pathlib import Path

GAME_DIR = Path(r"C:\Program Files (x86)\CTRacer")

# 제외할 맵/그래픽 폴더
EXCLUDE_DIRS = ["circuit", "map", "sound", "bgm", "effect"]

# 아이템/차량/상점 핵심 키워드
KEYWORDS = ["item", "car", "shop", "engine", "wheel", "tuning", "table", "db"]


def main():
    print("📁 1. 설치 폴더 내 주요 최상위/하위 디렉토리 목록:")
    for path in GAME_DIR.iterdir():
        if path.is_dir():
            print(f"  - [{path.name}]")

    print("\n" + "=" * 60 + "\n")
    print("🔍 2. 맵 폴더 제외 - 핵심 데이터 파일 탐색 중...\n")

    found_files = []
    for file_path in GAME_DIR.rglob("*"):
        if not file_path.is_file():
            continue

        # 맵/사운드 폴더 스킵
        rel_path_str = str(file_path.relative_to(GAME_DIR)).lower()
        if any(ex in rel_path_str for ex in EXCLUDE_DIRS):
            continue

        name_lower = file_path.name.lower()

        # 확장자 또는 파일명에 핵심 키워드가 포함된 경우
        if file_path.suffix.lower() in [
            ".ss",
            ".si",
            ".dat",
            ".tbl",
            ".db",
            ".bin",
            ".csv",
            ".txt",
        ]:
            if any(kw in name_lower for kw in KEYWORDS) or file_path.parent == GAME_DIR:
                found_files.append(file_path)

    print(f"🎯 후보 파일 {len(found_files)}개 발견!\n")
    for file_path in found_files[:15]:
        rel_path = file_path.relative_to(GAME_DIR)
        print(f"📄 [{file_path.name}] (경로: {rel_path})")
        try:
            with open(file_path, "rb") as f:
                header = f.read(24)
                hex_bytes = " ".join(f"{b:02X}" for b in header)
                print(f"  └ Hex Header: {hex_bytes}")
        except Exception as e:
            print(f"  └ 읽기 실패: {e}")
        print("-" * 60)


if __name__ == "__main__":
    main()