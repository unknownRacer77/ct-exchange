import re
from rapidfuzz import process, fuzz

class HybridMatcher:
    def __init__(self, master_items: list[dict]):
        """
        master_items 예시 구조:
        [
            {"item_id": "ITEM_001", "item_name": "AVT-S-DR", "phash": "a1b2c3d4"},
            {"item_id": "ITEM_002", "item_name": "AVT-C7-FA", "phash": "a1b2c3d4"}
        ]
        """
        self.master_items = master_items

    def clean_text(self, raw_text: str) -> str:
        # 영문, 숫자, 하이픈(-) 제외 특수문자 및 한글 모두 제거
        return re.sub(r'[^a-zA-Z0-9-]', '', raw_text)

    def match(self, ocr_text: str, cropped_image_hash: str = None) -> dict:
        cleaned_ocr = self.clean_text(ocr_text)
        
        # 1단계: 아이콘 이미지 해시 비교로 후보군 압축
        candidates = self.master_items
        if cropped_image_hash:
            matched_by_hash = [
                item for item in self.master_items 
                if item.get("phash") == cropped_image_hash
            ]
            if matched_by_hash:
                candidates = matched_by_hash

        # 2단계: 후보군 범위 내에서만 정제된 OCR 텍스트 유사도 매칭
        candidate_names = [item["item_name"] for item in candidates]
        best_match = process.extractOne(cleaned_ocr, candidate_names, scorer=fuzz.ratio)
        
        if best_match and best_match[1] >= 60:  # 유사도 60% 이상 시 승인
            matched_name = best_match[0]
            for item in candidates:
                if item["item_name"] == matched_name:
                    return item
                    
        return {"item_id": "UNKNOWN", "item_name": cleaned_ocr}