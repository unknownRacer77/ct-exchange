import os
os.environ['USERPROFILE'] = 'C:\\p_cache'
import ctypes
import json
import sys
import time
import subprocess
import re
import difflib

import keyboard
import pyautogui
import pydirectinput
import cv2
import numpy as np
from PIL import Image

# PaddleOCR 모듈
from paddleocr import PaddleOCR

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

# PaddleOCR 엔진 초기화 (한국어, PP-OCRv3 버전 지정)
ocr_engine = PaddleOCR(use_angle_cls=False, lang='korean', show_log=False, ocr_version='PP-OCRv4')

# 거래소 주요 아이템 DB (items.txt 파일에서 자동 로드)
def load_item_db():
    if os.path.exists("items.txt"):
        with open("items.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

ITEM_DB = load_item_db()

# ==========================================
# 사용자 정의 오답 노트 (1:1 강제 교정)
# ==========================================
REPLACEMENTS = {
    "SCI c": "SC1C",
    "SCI B": "SC1B",
    "SCIB": "SC1B",
    "EXI F": "EX1F",
    "로터 EXIG": "로터 EX1G",
    "제작실피1 바디경량화 GI": "제작실패 바디경량화 G1",
    "제작실표H 바디경량화 GI": "제작실패 바디경량화 G1",
    "바디 강성화 듀랄루민c": "바디 강성화 듀랄루민C",
    "오일쿨러 EX3 설계도c": "오일쿨러 EX3 설계도C",
    "로터 Type UC1 F": "로터 Type UC1F",
    "인테이크파이프 UC1": "인테이크파이프 UC1S",
    "바디 경량화 듀랄루민s": "바디 경량화 듀랄루민S",
    "CTR-S5 DR엔진S5": "CTR-S5 DR엔진",
    "독립쓰로틀 SP1": "독립쓰로틀 SP1S",
    "오일쿨러 C": "오일쿨러 SC1C",
    "인터쿨러 SCIC": "오일쿨러 SC1C",
    "에어클리너 SCI c": "오일쿨러 SC1C",
    "인테이크파이프 SCI B": "인테이크파이프 SC1B",
    "인테이크파이프 SCI": "인테이크파이프 SC1S",
    "인터쿨러 SCIB": "인터쿨러 SC1B",
    "인터쿨러 SCIA": "인터쿨러 SC1A",
    "독립쓰로를 SCI A": "독립쓰로틀 SC1A",
    "트윈터보 EXI R": "트윈터보 EX1R",
    "오일쿨러 UC1": "오일쿨러 UC1S",
    "패드 Type UC1 R": "패드 Type UC1R",
    "패드 Type UC1 F": "패드 Type UC1F",
    "오일쿨러 SCIS": "오일쿨러 SC1S",
    "에어클리너 SCI B": "에어클리너 SC1B",
    "0`7幽 EX2A": "하이캠 EX2A",
    "타이어 Type SP1 F": "타이어 Type SP1F",
    "0`캣 SCIB": "하이캠 SC1B",
    "하이캠 SCIB": "하이캠 SC1B",
    "오일쿨러 SCI B": "오일쿨러 SC1B",
    "독립쓰로를 EXI R": "독립쓰로틀 EX1R",
    "로터 Type SP1 F": "로터 Type SP1F",
    "제작실피1 트윈터보 G3": "제작실패 트윈터보 G3",
    "제작실표H 트윈터보 G3": "제작실패 트윈터보 G3",
    "제작실패 트윈터보 GI": "제작실패 트윈터보 G1",
    "바디경량화듀랄루민 SP1": "바디경량화 듀랄루민 SP1",
    "트윈터보 Type SCI": "트윈터보 Type SC1S",
    "트윈터보 Type SCI A": "트윈터보 Type SC1A",
    "하이캠 EXIR": "하이캠 EX1R",
    "대용량라디에이터 EXI R": "대용량라디에이터 EX1R",
    "커플지옥 솔로해골s": "커플지옥 솔로해골S",
    "독립쓰로틀 EXI R": "독립쓰로틀 EX1R",
    "빅보어 EXIR": "빅보어 EX1R",
    "오일쿨러 EXI R": "오일쿨러 EX1R",
    "TRN-G PX 트윈 터보(T4)": "TRN-GPX 트윈터보 (T4)",
    "마이 티 파워": "마이티파워",
    "빅보어": "빅보어 UC1S",
    "어 SCIA": "빅보어 SC1A",
    "량화 듀랄루민A": "바디 경량화 듀랄루민A",
    "독립쓰로들 EXI A": "독립쓰로틀 EX1A",
    "인터쿨러 EXIA": "인터쿨러 EX1A",
    "하이캠 EXIA": "하이캠 EX1A",
    "트윈터보 Type SP1 5": "트윈터보 Type SP1S",
    "익스원샷": "믹스원샷",
    "인테이크파이프 UC1 G": "인테이크파이프 UC1G",
    "타이어 Type EXI": "타이어 Type EX1",
    "안티를바 Type UC1": "안티롤바 Type UC1",
    "쇼비 Soft Type UC1": "쇼바 Soft Type UC1",
    "CTR-RI DR엔진": "CTR-R1 DR엔진",
    "QUESTZ이": "QUEST훈이",
    "1 QUESTE이": "QUEST훈이"
}

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
        "nickname": (1650, 556, 2031, 608),
        "time_remaining": (1274, 621, 1463, 670),
        "price": (1018, 676, 1458, 726),
    },
    2: {
        "item_image": (817, 750, 1012, 938),
        "item_name": (1016, 755, 1616, 808),
        "nickname": (1650, 756, 2031, 808),
        "time_remaining": (1271, 823, 1461, 870),
        "price": (1018, 876, 1458, 926),
    },
    3: {
        "item_image": (819, 948, 1012, 1138),
        "item_name": (1017, 954, 1616, 1009),
        "nickname": (1650, 954, 2031, 1007),
        "time_remaining": (1274, 1024, 1461, 1070),
        "price": (1019, 1076, 1460, 1125),
    },
    4: {
        "item_image": (817, 1149, 1013, 1336),
        "item_name": (1016, 1155, 1617, 1208),
        "nickname": (1650, 1153, 2031, 1206),
        "time_remaining": (1275, 1223, 1461, 1272),
        "price": (1018, 1276, 1459, 1322),
    },
    5: {
        "item_image": (820, 1351, 1012, 1537),
        "item_name": (1018, 1356, 1613, 1409),
        "nickname": (1650, 1354, 2031, 1408),
        "time_remaining": (1271, 1423, 1461, 1470),
        "price": (1018, 1476, 1461, 1524),
    },
    6: {
        "item_image": (817, 1549, 1012, 1737),
        "item_name": (1016, 1555, 1616, 1608),
        "nickname": (1648, 1556, 2029, 1608),
        "time_remaining": (1269, 1625, 1462, 1672),
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

def clean_nickname(raw_text):
    if not raw_text:
        return ""
    text = raw_text.replace('!', '1').replace(']', '').replace('[', '').replace('\\', '').replace('|', '').replace('l', 'I')
    text = text.replace('훈O', '훈이').replace('훈0', '훈이').replace('훈O이', '훈이')
    text = text.strip()
    return REPLACEMENTS.get(text, text)

def clean_item_name(name):
    if not name:
        return ""
    
    name = name.upper()
    name = REPLACEMENTS.get(name, name)
    name = re.sub(r'([A-Za-z0-9]+)[I!\|Li]*진', r'\1엔진', name)
    name = name.replace('UCIS', 'UC1S').replace('SPIF', 'SP1F').replace('UCI', 'UC1')
    name = name.replace('SPI', 'SP1').replace('SPl', 'SP1').replace('EXl', 'EX1')
    name = name.replace('아EI쿡바', '안티롤바').replace('아EI', '안티').replace('EX1 R', 'EX1R')
    
    matches = difflib.get_close_matches(name, ITEM_DB, n=1, cutoff=0.45)
    if matches:
        return matches[0]
    
    if name and len(name) > 1:
        with open("unknown_items.txt", "a", encoding="utf-8") as f:
            f.write(f"{name}\n")
            
    return name

def clean_price(raw_text):
    if not raw_text:
        return ""
    text = raw_text.replace('가격', '').replace('간격', '').replace('CT', '').replace(',', '').replace(' ', '')
    text = text.replace('I', '1').replace('l', '1').replace('!', '1').replace('|', '1').replace('i', '1')
    text = text.replace(']', '1').replace('[', '1').replace('/', '1').replace('\\', '1').replace('?', '1').replace('}', '1')
    text = text.replace('이', '0').replace('O', '0').replace('o', '0').replace('Q', '0')
    numbers = re.findall(r'\d+', text)
    if numbers:
        val = "".join(numbers)
        return f"{int(val):,}" + "CT"
    return raw_text

def clean_time(raw_text):
    if not raw_text:
        return ""
    
    text = raw_text.replace('남은시간', '').strip()
    
    day_match = re.search(r'(\d+)\s*일\s*(\d+)', text)
    if day_match:
        return f"{day_match.group(1)}일 {int(day_match.group(2))}시간"

    hour_match = re.search(r'(\d+)\s*시[간]*\s*(\d+)', text)
    if hour_match:
        return f"{hour_match.group(1)}시간 {int(hour_match.group(2))}분"

    only_hour_match = re.search(r'(\d+)\s*시[간]*', text)
    if only_hour_match:
        return f"{only_hour_match.group(1)}시간"

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
            nick_text = clean_nickname(read_text(screen.crop(pos["nickname"])))
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
            
            current_signature = "".join([f"{item['name']}_{item['price']}_{item['nickname']}" for item in items])

            all_items_data.append({
                'page': page,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'items': items
            })

            click_pos(*COORDS['next_btn'])
            pydirectinput.moveTo(10, 10)
            
            time.sleep(1)

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