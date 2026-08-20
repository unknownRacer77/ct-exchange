import json
import os
import statistics
from datetime import datetime

class CrawlerService:
    def __init__(self, history_file="raw_history.json", output_data_file="data.json"):
        self.history_file = history_file
        self.output_data_file = output_data_file

    def _load_history(self) -> dict:
        """기존 누적 데이터 불러오기 (점검 후 재가동 시 이전 데이터 유지)"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_history(self, history: dict):
        """누적 데이터 저장"""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def process_and_update(self, new_scraped_data: list):
        """
        crawler.py에서 수집한 데이터를 받아 기존 데이터와 합산 후 통계 산출
        new_scraped_data 형식: [{"name": "아이템명", "price": 100000}, ...]
        """
        # 1. 이전 누적 데이터 로드
        history = self._load_history()

        # 2. 신규 데이터 합산
        for item in new_scraped_data:
            name = item.get("name")
            price = item.get("price")
            if not name or price is None:
                continue

            if name not in history:
                history[name] = []

            history[name].append({
                "price": int(price),
                "timestamp": datetime.now().isoformat()
            })

        # 누적 파일 저장
        self._save_history(history)

        # 3. 통계(최저, 최고, 평균, 중앙값) 계산
        result_list = []
        for name, records in history.items():
            prices = [r["price"] for r in records if isinstance(r.get("price"), (int, float))]
            if not prices:
                continue

            result_list.append({
                "item_name": name,
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": round(statistics.mean(prices)),
                "median_price": round(statistics.median(prices)),
                "count": len(prices),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # 4. 웹 UI 표시용 data.json 저장
        with open(self.output_data_file, "w", encoding="utf-8") as f:
            json.dump(result_list, f, ensure_ascii=False, indent=2)

        return result_list