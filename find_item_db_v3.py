from pathlib import Path

GAME_DIR = Path(r"C:\Program Files (x86)\CTRacer")

print("📁 CTRacer 폴더 구조 탐색:\n")
if GAME_DIR.exists():
    for p in GAME_DIR.glob("*"):
        if p.is_dir():
            print(f"📂 [{p.name}]")
            for sub in p.glob("*"):
                if sub.is_dir():
                    print(f"   └── 📂 [{sub.name}]")