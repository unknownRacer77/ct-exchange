import ctypes
import json
import os
import sys
import time
import subprocess
import keyboard
import pyautogui
import pydirectinput
import easyocr
import cv2
import numpy as np
from PIL import Image
from mss import mss

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

reader = easyocr.Reader(['en', 'ko'], gpu=False)

COORDS = {
    'buy_tab': (1900, 770),
    'sell_tab': (2630, 770),
    'refresh': (3980, 1010),
    'next_btn': (3180, 3550),
}

all_items_data = []
is_running = True

def stop_program():
    global is_running
    print('\n[!!] Ctrl + 5 입력 감지: 크롤러를 종료합니다.')
    is_running = False
    sys.exit(0)

def click_coord(btn_name):
    x, y = COORDS[btn_name]
    pydirectinput.moveTo(x, y)
    time.sleep(0.03)
    pydirectinput.mouseDown()
    time.sleep(0.03)
    pydirectinput.mouseUp()

def get_game_screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

def get_item_list_screenshot():
    full_img = get_game_screenshot()
    return full_img.crop((870, 330, 3660, 2430))

def is_same_screen(img1, img2, threshold=3.0):
    arr1 = np.array(img1.convert('L'), dtype=np.float32)
    arr2 = np.array(img2.convert('L'), dtype=np.float32)
    return np.mean(np.abs(arr1 - arr2)) < threshold

def check_last_page_pixel():
    pydirectinput.moveTo(10, 10)
    time.sleep(0.05)
    return False

def preprocess_crop(crop_img, scale=2.0):
    img = np.array(crop_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)

def extract_current_page_items():
    screenshot = get_game_screenshot()
    page_items = []
    slot_y_offsets = [0, 386, 772, 1158, 1544, 1930]

    os.makedirs('item_images', exist_ok=True)

    for i, dy in enumerate(slot_y_offsets):
        try:
            img_box = (1644, 1118 + dy, 2020, 1460 + dy)
            image_filename = f'item_images/item_{i+1}.png'
            screenshot.crop(img_box).save(image_filename)
        except Exception:
            image_filename = ''

        try:
            name_crop = screenshot.crop((2030, 1122 + dy, 3228, 1216 + dy))
            name_text = " ".join(reader.readtext(preprocess_crop(name_crop), detail=0)).strip()
        except Exception:
            name_text = ""

        try:
            nick_crop = screenshot.crop((3352, 1126 + dy, 4076, 1216 + dy))
            nickname_text = " ".join(reader.readtext(preprocess_crop(nick_crop), detail=0)).strip()
        except Exception:
            nickname_text = ""

        try:
            time_crop = screenshot.crop((2558, 1252 + dy, 2922, 1330 + dy))
            raw_time = " ".join(reader.readtext(preprocess_crop(time_crop), allowlist='0123456789시간분초 ', detail=0)).strip()
            time_text = raw_time.replace('간', '시간').replace(' ', '')
        except Exception:
            time_text = ""

        try:
            price_crop = screenshot.crop((2232, 1360 + dy, 2914, 1440 + dy))
            raw_price = " ".join(reader.readtext(preprocess_crop(price_crop), allowlist='0123456789,CTO', detail=0)).strip()
            price_text = raw_price.replace('O', '0').replace('o', '0').replace(' ', '')
        except Exception:
            price_text = ""

        if name_text or price_text or nickname_text:
            item_data = {
                'name': name_text,
                'nickname': nickname_text,
                'time': time_text,
                'price': price_text,
                'image_path': image_filename
            }
            page_items.append(item_data)
            print(f"  └ [{i+1}번 슬롯] 이름: '{name_text}' | 판매자: '{nickname_text}' | 가격: '{price_text}' | 시간: '{time_text}'")

    return page_items

def upload_to_domain():
    print('\n>> [마지막 페이지 감지] 데이터 저장 및 GitHub 업로드 진행...')
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_items_data, f, ensure_ascii=False, indent=4)

    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Auto data update'], check=True)
        subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print('>> GitHub 업로드 성공!')
    except subprocess.CalledProcessError as e:
        print(f'>> [Git 오류 발생] 업로드 실패: {e}')

    all_items_data.clear()

def run_crawler():
    global is_running
    print('=== 시티레이서 크롤러 실행 (종료 키: Ctrl + 5) ===')
    keyboard.add_hotkey('ctrl+5', stop_program)

    cycle_count = 1
    while is_running:
        print(f'\n--- [사이클 {cycle_count}] 시작 ---')

        click_coord('sell_tab')
        time.sleep(0.3)

        click_coord('buy_tab')
        time.sleep(0.3)

        rx, ry = COORDS['refresh']
        pydirectinput.moveTo(rx, ry)
        for i in range(1, 6):
            if not is_running:
                break
            pydirectinput.mouseDown()
            time.sleep(0.03)
            pydirectinput.mouseUp()
            time.sleep(0.2)

        page = 1
        while is_running:
            print(f'\n[{page} 페이지] 수집 중...')
            items = extract_current_page_items()
            all_items_data.append({
                'page': page,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'items': items,
            })

            prev_screen = get_item_list_screenshot()

            click_coord('next_btn')
            pydirectinput.moveTo(10, 10)
            time.sleep(1.2)

            current_screen = get_item_list_screenshot()

            if check_last_page_pixel() or is_same_screen(prev_screen, current_screen):
                time.sleep(0.8)
                retry_screen = get_item_list_screenshot()
                if is_same_screen(prev_screen, retry_screen):
                    print("\n>> 마지막 페이지 도달 확인!")
                    upload_to_domain()
                    break

            page += 1

        cycle_count += 1
        time.sleep(1)

if __name__ == '__main__':
    run_crawler()