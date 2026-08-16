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
import torch
from PIL import Image

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

# GPU 사용 가능 여부 확인 및 출력
print(f">> PyTorch CUDA 사용 가능 여부: {torch.cuda.is_available()}")
reader = easyocr.Reader(['en', 'ko'], gpu=True)

COORDS = {
    'buy_tab': (946, 361),
    'sell_tab': (1299, 361),
    'refresh': (1985, 492),
    'next_btn': (1594, 1798),
}

all_items_data = []
is_running = True

def stop_program():
    global is_running
    print('\n[!!] 프로그램 종료 (Ctrl + 5)')
    is_running = False
    sys.exit(0)

def click_pos(x, y):
    pydirectinput.moveTo(x, y)
    time.sleep(0.05)
    pydirectinput.mouseDown()
    time.sleep(0.05)
    pydirectinput.mouseUp()

def get_list_region(screen):
    return screen.crop((870, 330, 3660, 2430))

def is_same_image(img1, img2):
    arr1 = np.array(img1.convert('L'), dtype=np.float32)
    arr2 = np.array(img2.convert('L'), dtype=np.float32)
    return np.mean(np.abs(arr1 - arr2)) < 3.0

def preprocess_for_ocr(crop_img):
    img = np.array(crop_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]
    resized = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    return resized

def parse_slots(screen):
    page_items = []
    slot_offsets = [0, 196, 392, 588, 784, 980]

    os.makedirs('item_images', exist_ok=True)

    for idx, dy in enumerate(slot_offsets):
        slot_num = idx + 1
        
        try:
            thumb_box = (824, 556 + dy, 1009, 725 + dy)
            thumb_path = f'item_images/item_{slot_num}.png'
            screen.crop(thumb_box).save(thumb_path)
        except Exception:
            thumb_path = ''

        try:
            name_box = (1018, 556 + dy, 1613, 604 + dy)
            name_text = " ".join(reader.readtext(preprocess_for_ocr(screen.crop(name_box)), detail=0)).strip()
        except Exception:
            name_text = ""

        try:
            nick_box = (1649, 557 + dy, 2037, 605 + dy)
            nick_text = " ".join(reader.readtext(preprocess_for_ocr(screen.crop(nick_box)), detail=0)).strip()
        except Exception:
            nick_text = ""

        try:
            time_box = (1260, 625 + dy, 1459, 667 + dy)
            time_raw = " ".join(reader.readtext(preprocess_for_ocr(screen.crop(time_box)), allowlist='0123456789시간분초 ', detail=0)).strip()
            time_text = time_raw.replace('간', '시간').replace(' ', '')
        except Exception:
            time_text = ""

        try:
            price_box = (1146, 677 + dy, 1459, 717 + dy)
            price_raw = " ".join(reader.readtext(preprocess_for_ocr(screen.crop(price_box)), allowlist='0123456789,CTO', detail=0)).strip()
            price_text = price_raw.replace('O', '0').replace('o', '0').replace(' ', '')
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
            print(f"  [슬롯 {slot_num}] 이름: {name_text} | 가격: {price_text}")

    return page_items

def save_and_push():
    print('\n>> 데이터 저장 및 GitHub 업로드 진행...')
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_items_data, f, ensure_ascii=False, indent=4)

    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Auto data update'], check=True)
        subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print('>> GitHub 업로드 완료!')
    except subprocess.CalledProcessError as e:
        print(f'>> Git 업로드 실패: {e}')

    all_items_data.clear()

def main():
    print('=== 시티레이서 크롤러 실행 (종료: Ctrl + 5) ===')
    keyboard.add_hotkey('ctrl+5', stop_program)

    cycle = 1
    while is_running:
        print(f'\n--- [사이클 {cycle}] 시작 ---')

        click_pos(*COORDS['sell_tab'])
        time.sleep(0.3)
        click_pos(*COORDS['buy_tab'])
        time.sleep(0.3)

        for _ in range(3):
            if not is_running: break
            click_pos(*COORDS['refresh'])
            time.sleep(0.2)

        page = 1
        while is_running:
            print(f'\n[{page} 페이지 수집 중]')
            screen = pyautogui.screenshot()
            items = parse_slots(screen)
            
            all_items_data.append({
                'page': page,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'items': items
            })

            prev_img = get_list_region(screen)

            click_pos(*COORDS['next_btn'])
            pydirectinput.moveTo(10, 10)
            
            # 페이지 로딩 대기 시간을 2.0초로 늘려 화면이 완전히 바뀐 후 비교하도록 수정
            time.sleep(2.0)

            current_screen = pyautogui.screenshot()
            curr_img = get_list_region(current_screen)

            if is_same_image(prev_img, curr_img):
                time.sleep(0.5)
                retry_screen = pyautogui.screenshot()
                if is_same_image(curr_img, get_list_region(retry_screen)):
                    print('\n>> 마지막 페이지 도달 확인')
                    save_and_push()
                    break

            page += 1

        cycle += 1
        time.sleep(1)

if __name__ == '__main__':
    main()