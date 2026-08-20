from pathlib import Path

GAME_DIR = Path(r"C:\Program Files (x86)\CTRacer")

# 아이템, 차량, 상점 등 DB 가능성이 높은 키워드
KEYWORDS = ["item", "car", "shop", "part", "script", "data", "tbl"]


def search_item_files():
    print("🔍 아이템/DB 관련 핵심 파일 검색 중...\n")

    found_files = []
    for file_path in GAME_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [
            ".ss",
            ".si",
            ".dat",
        ]:
            name_lower = file_path.name.lower()
            if any(kw in name_lower for kw in KEYWORDS):
                found_files.append(file_path)

    print(f"🎯 총 {len(found_files)}개의 핵심 후보 파일 발견!\n")

    for file_path in found_files[:10]:
        rel_path = file_path.relative_to(GAME_DIR)
        print(f"📄 파일명: [{file_path.name}] (경로: {rel_path})")

        # 파일 헤더 (첫 32바이트) 16진수로 읽기
        try:
            with open(file_path, "rb") as f:
                header = f.read(32)
                hex_bytes = " ".join(f"{b:02X}" for b in header)
                print(f"  └ Hex Header: {hex_bytes}")
        except Exception as e:
            print(f"  └ 읽기 실패: {e}")
        print("-" * 65)


if __name__ == "__main__":
    search_item_files()