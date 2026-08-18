import os
import glob
import asyncio
import re
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import difflib

from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.globalization import Language
from winsdk.windows.storage import StorageFile
from winsdk.windows.graphics.imaging import BitmapDecoder

# 1. items.txt DB 로드 (유사도 교정용)
ITEM_DB = []
if os.path.exists("items.txt"):
    with open("items.txt", "r", encoding="utf-8") as f:
        ITEM_DB = [line.strip() for line in f if line.strip()]

# 각 슬롯별 (아이템명, 남은시간, 가격) Crop 좌표 설정 [x1, y1, x2, y2]
SLOT_BOXES = [
    {"name": (1016, 555, 1616, 608), "time": (1180, 608, 1510, 650), "price": (1180, 650, 1510, 695)},
    {"name": (1016, 755, 1616, 808), "time": (1180, 755, 1510, 850), "price": (1180, 850, 1510, 895)},
    {"name": (1017, 954, 1616, 1009), "time": (1180, 1009, 1510, 1051), "price": (1180, 1051, 1510, 1096)},
    {"name": (1016, 1155, 1617, 1208), "time": (1180, 1208, 1510, 1250), "price": (1180, 1250, 1510, 1295)},
    {"name": (1018, 1356, 1613, 1409), "time": (1180, 1409, 1510, 1451), "price": (1180, 1451, 1510, 1496)},
    {"name": (1016, 1555, 1616, 1608), "time": (1180, 1608, 1510, 1650), "price": (1180, 1650, 1510, 1695)},
]

async def do_ocr(image_path):
    lang = Language("ko-KR")
    engine = OcrEngine.try_create_from_language(lang)
    file = await StorageFile.get_file_from_path_async(os.path.abspath(image_path))
    stream = await file.open_async(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    result = await engine.recognize_async(bitmap)
    return result.text.strip()

def process_crop(img, box):
    crop = img.crop(box)
    gray = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2GRAY)
    inverted = cv2.bitwise_not(gray)
    resized = cv2.resize(inverted, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    padded = cv2.copyMakeBorder(resized, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
    temp_path = "temp_crop.png"
    cv2.imwrite(temp_path, padded)
    return temp_path

def clean_name(text):
    if not text:
        return ""
    if ITEM_DB:
        matches = difflib.get_close_matches(text, ITEM_DB, n=1, cutoff=0.5)
        if matches:
            return matches[0]
    return text

def clean_time(text):
    if not text:
        return ""
    
    # 1. 뭉개진 글자 예외 정제
    text = re.sub(r'시+', '시간', text)
    text = re.sub(r'시간+', '시간', text)
    text = re.sub(r'일+', '일', text)
    text = re.sub(r'분+', '분', text)
    
    # 2. 숫자 + 단위 패턴 추출
    days = re.findall(r'(\d+)일', text)
    hours = re.findall(r'(\d+)시간', text)
    mins = re.findall(r'(\d+)분', text)
    
    # 3. 규격 재조합
    result = []
    if days:
        result.append(f"{days[0]}일")
    if hours:
        result.append(f"{hours[0]}시간")
    if mins:
        result.append(f"{mins[0]}분")
        
    return " ".join(result) if result else text

def clean_price(text):
    digits = re.sub(r'[^0-9]', '', text)
    return f"{int(digits):,}CT" if digits else text

def main():
    image_files = sorted(glob.glob("screenshots/*.png"))
    if not image_files:
        print("screenshots 폴더에 이미지가 없습니다.")
        return

    all_data = []
    for page_idx, img_path in enumerate(image_files, start=1):
        img = Image.open(img_path)
        print(f"[{page_idx} / {len(image_files)}] 페이지 분석 중...")

        for slot_idx, slot in enumerate(SLOT_BOXES, start=1):
            raw_name = asyncio.run(do_ocr(process_crop(img, slot["name"])))
            if not raw_name:
                continue
            raw_time = asyncio.run(do_ocr(process_crop(img, slot["time"])))
            raw_price = asyncio.run(do_ocr(process_crop(img, slot["price"])))

            all_data.append({
                "페이지": page_idx,
                "슬롯": slot_idx,
                "아이템명": clean_name(raw_name),
                "남은시간": clean_time(raw_time),
                "가격": clean_price(raw_price)
            })

    # 결과 CSV 출력
    df = pd.DataFrame(all_data)
    df.to_csv("market_items.csv", index=False, encoding="utf-8-sig")
    print(f"\n완료! 총 {len(all_data)}개 매물이 market_items.csv 로 저장되었습니다.")

if __name__ == '__main__':
    main()