import os
import re

# 한글 계정명 경로 오류 방지
os.environ["HOME"] = "C:/paddle_cache"
os.environ["USERPROFILE"] = "C:/paddle_cache"

import cv2
import numpy as np
from paddleocr import PaddleOCR

# OCR 엔진 초기화
ocr_engine = PaddleOCR(use_angle_cls=False, lang='korean', show_log=False, ocr_version='PP-OCRv3', det=False)

# 윈도우 탐색기 방식 정렬 키 (숫자 인식 정렬)
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def read_text(crop_img):
    img_np = np.array(crop_img)
    if len(img_np.shape) == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_np
        
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    resized = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    padded = cv2.copyMakeBorder(resized, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
    inverted = cv2.bitwise_not(padded)
    img_final = cv2.cvtColor(inverted, cv2.COLOR_GRAY2BGR)
    
    try:
        result = ocr_engine.ocr(img_final, cls=False)
        if not result or not result[0]:
            return ""
        return " ".join([line[1][0] for line in result[0]]).strip()
    except Exception:
        return ""

def auto_label_dataset(base_dir):
    label_file_path = os.path.join(base_dir, "train_list.txt")
    
    if not os.path.exists(base_dir):
        return
        
    # 윈도우 탐색기와 동일한 자연 정렬 적용
    raw_files = [f for f in os.listdir(base_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    files = sorted(raw_files, key=natural_sort_key)
    
    print(f"[{base_dir}] 총 {len(files)}개 이미지 탐색기 동일 순서로 라벨링 시작...")
    
    with open(label_file_path, "w", encoding="utf-8") as f:
        for idx, img_name in enumerate(files):
            img_path = os.path.join(base_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
                
            text = read_text(img)
            if text:
                f.write(f"{img_name}\t{text}\n")
                
            if (idx + 1) % 100 == 0:
                print(f"  - {idx + 1}/{len(files)} 진행 중...")
                
    print(f">> 완료: {label_file_path}\n")

if __name__ == '__main__':
    auto_label_dataset("nick_dataset")
    auto_label_dataset("item_dataset")