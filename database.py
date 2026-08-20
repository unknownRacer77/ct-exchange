import sqlite3

def init_db(db_path="market.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 아이템 마스터 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS item_master (
        item_id TEXT PRIMARY KEY,
        item_name TEXT NOT NULL,
        phash TEXT
    )
    """)
    
    # 2. 실시간 매물 수집 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        listing_id TEXT PRIMARY KEY,
        item_id TEXT,
        price INTEGER,
        remaining_time TEXT,
        scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES item_master (item_id)
    )
    """)
    
    # 3. 일자별 시세 스냅샷 테이블 (그래프 데이터용)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT,
        item_id TEXT,
        min_price INTEGER,
        max_price INTEGER,
        median_price REAL,
        avg_price REAL,
        volume INTEGER,
        UNIQUE(snapshot_date, item_id)
    )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    