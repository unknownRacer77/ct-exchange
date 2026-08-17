import os
import ctypes
import json
import sys
import time
import subprocess
import asyncio
import re
import difflib

import keyboard
import pyautogui
import pydirectinput
import cv2
import numpy as np
from PIL import Image

# Windows OCR 모듈
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.globalization import Language
from winsdk.windows.storage import StorageFile
from winsdk.windows.graphics.imaging import BitmapDecoder

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

# 거래소 주요 아이템 DB (items.txt 파일에서 자동 로드)
def load_item_db():
    if os.path.exists("items.txt"):
        with open("items.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

ITEM_DB = load_item_db()

COORDS = {
    'buy_tab': (946, 361),
    'sell_tab': (1299, 361),
    'refresh': (1985, 492),
    'next_btn': (1594, 1798),
}

SLOTS = {
    1: {
        "item_image": (817, 550, 1012, 738),
        "item_name": (1016, 555, 1616, 608),
        "nickname": (1648, 556, 2034, 608),
        "time_remaining": (1017, 622, 1462, 672),
        "price": (1018, 676, 1458, 726),
    },
    2: {
        "item_image": (817, 750, 1012, 938),
        "item_name": (1016, 755, 1616, 808),
        "nickname": (1648, 756, 2034, 808),
        "time_remaining": (1017, 822, 1462, 872),
        "price": (1018, 876, 1458, 926),
    },
    3: {
        "item_image": (819, 948, 1012, 1138),
        "item_name": (1017, 954, 1616, 1009),
        "nickname": (1648, 954, 2027, 1007),
        "time_remaining": (1017, 1022, 1465, 1073),
        "price": (1019, 1076, 1460, 1125),
    },
    4: {
        "item_image": (817, 1149, 1013, 1336),
        "item_name": (1016, 1155, 1617, 1208),
        "nickname": (1646, 1153, 2035, 1206),
        "time_remaining": (1018, 1221, 1461, 1270),
        "price": (1018, 1276, 1459, 1322),
    },
    5: {
        "item_image": (820, 1351, 1012, 1537),
        "item_name": (1018, 1356, 1613, 1409),
        "nickname": (1647, 1354, 2036, 1408),
        "time_remaining": (1017, 1422, 1461, 1473),
        "price": (1018, 1476, 1461, 1524),
    },
    6: {
        "item_image": (817, 1549, 1012, 1737),
        "item_name": (1016, 1555, 1616, 1608),
        "nickname": (1648, 1556, 2034, 1608),
        "time_remaining": (1017, 1622, 1462, 1672),
        "price": (1018, 1676, 1458, 1726),
    },
}

all_items_data = []
is_running = True

def stop_program():
    global is_running
    print('\n[!!] 크롤링 중단 (Ctrl + 5)')
    is_running = False
    sys.exit(0)

def click_pos(x, y):
    pyautogui.moveTo(x, y, duration=0.1)
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.mouseUp()

async def _extract_text_winocr(image_path):
    lang = Language("ko-KR")
    engine = OcrEngine.try_create_from_language(lang)
    
    file = await StorageFile.get_file_from_path_async(os.path.abspath(image_path))
    stream = await file.open_async(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    
    result = await engine.recognize_async(bitmap)
    return result.text.strip()

def read_text(crop_img):
    img_np = np.array(crop_img)
    if len(img_np.shape) == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_np
        
    resized = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
    _, thresh = cv2.threshold(resized, 170, 255, cv2.THRESH_BINARY)
    padded = cv2.copyMakeBorder(thresh, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=255)
    
    temp_path = "temp_ocr.png"
    cv2.imwrite(temp_path, padded)
    
    try:
        return asyncio.run(_extract_text_winocr(temp_path))
    except Exception:
        return ""

def clean_item_name(name):
    if not name:
        return ""
    
    # 1. 고정 정규 치환
    name = name.replace('UCIS', 'UC1S').replace('SPIF', 'SP1F').replace('UCI', 'UC1')
    name = name.replace('아EI쿡바', '안티롤바').replace('아EI', '안티').replace('EX1 R', 'EX1R')
    
    # 2. DB 내 단어와 유사도 비교 (자동 교정)
    matches = difflib.get_close_matches(name, ITEM_DB, n=1, cutoff=0.55)
    if matches:
        return matches[0]
    
    # 3. DB에 없는 단어는 unknown_items.txt에 자동 기록
    if name and len(name) > 1:
        with open("unknown_items.txt", "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
            
    return name

def clean_price(raw_text):
    text = raw_text.replace('가격', '').replace('간격', '').replace('CT', '').replace(',', '').replace(' ', '')
    text = text.replace('이', '0').replace('O', '0').replace('o', '0').replace('Q', '0')
    numbers = re.findall(r'\d+', text)
    if numbers:
        val = "".join(numbers)
        return f"{int(val):,}" + "CT"
    return raw_text

def clean_time(raw_text):
    text = raw_text.replace('남은시간', '').replace(' ', '')
    text = text.replace('빕', '일').replace('간', '시간')
    return text

def parse_slots(screen, page_num):
    page_items = []
    os.makedirs('item_images', exist_ok=True)

    for slot_num, pos in SLOTS.items():
        thumb_path = f'item_images/p{page_num}_s{slot_num}.png'
        try:
            screen.crop(pos["item_image"]).save(thumb_path)
        except Exception:
            thumb_path = ''

        try:
            raw_name = read_text(screen.crop(pos["item_name"]))
            name_text = clean_item_name(raw_name)
        except Exception:
            name_text = ""

        try:
            nick_text = read_text(screen.crop(pos["nickname"]))
        except Exception:
            nick_text = ""

        try:
            time_raw = read_text(screen.crop(pos["time_remaining"]))
            time_text = clean_time(time_raw)
        except Exception:
            time_text = ""

        try:
            price_raw = read_text(screen.crop(pos["price"]))
            price_text = clean_price(price_raw)
        except Exception:
            price_text = ""

        if name_text or price_text or nick_text:
            item_data = {
                'name': name_text,
                'nickname': nick_text,
                'time': time_text,
                'price': price_text,
                'image_path': thumb_path
            }
            page_items.append(item_data)
            print(f"  [슬롯 {slot_num}] 이름: {name_text} | 닉네임: {nick_text} | 가격: {price_text} | 남은시간: {time_text}")

    return page_items

def save_and_push():
    print('\n>> 크롤링 완료: json 저장 및 웹 전송(Git Push) 진행...')
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_items_data, f, ensure_ascii=False, indent=4)

    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Update market crawling data'], check=True)
        subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print('>> 웹사이트 업로드(Git Push) 완료!')
    except subprocess.CalledProcessError as e:
        print(f'>> Git 업로드 실패: {e}')

    all_items_data.clear()

def main():
    print('=== 시티레이서 거래소 데이터 크롤러 실행 (종료: Ctrl + 5) ===')
    print('⏳ 5초 뒤에 시작됩니다. 시티레이서 창을 맨 앞으로 가져다 놓으세요!')
    
    for i in range(5, 0, -1):
        print(f'  {i}초 전...')
        time.sleep(1)
        
    keyboard.add_hotkey('ctrl+5', stop_program)

    cycle = 1
    while is_running:
        print(f'\n--- [크롤링 사이클 {cycle}] 시작 ---')

        click_pos(*COORDS['sell_tab'])
        time.sleep(0.3)
        click_pos(*COORDS['buy_tab'])
        time.sleep(0.3)

        for _ in range(3):
            if not is_running: break
            click_pos(*COORDS['refresh'])
            time.sleep(0.2)

        page = 1
        prev_page_signature = ""
        same_page_count = 0

        while is_running:
            print(f'\n[{page} 페이지 크롤링 중]')
            screen = pyautogui.screenshot()
            items = parse_slots(screen, page)
            
            # 6개 슬롯 전체 데이터 조합으로 고유 시그니처 생성
            current_signature = "".join([f"{item['name']}_{item['price']}_{item['nickname']}" for item in items])

            all_items_data.append({
                'page': page,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'items': items
            })

            click_pos(*COORDS['next_btn'])
            pydirectinput.moveTo(10, 10)
            time.sleep(3.5)

            if current_signature and current_signature == prev_page_signature:
                same_page_count += 1
                if same_page_count >= 2:
                    print('\n>> 마지막 페이지 도달 확인')
                    save_and_push()
                    break
            else:
                same_page_count = 0

            prev_page_signature = current_signature
            page += 1

        cycle += 1
        time.sleep(1)

if __name__ == '__main__':
    main()