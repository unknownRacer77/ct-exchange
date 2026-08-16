import ctypes
import json
import os
import sys
import time
import subprocess
import keyboard
import pyautogui
import pydirectinput
import pygetwindow as gw
import easyocr
import cv2
import numpy as np

# Windows DPI 배율 오차 방지
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# CPU만 사용하도록 설정 (gpu=False)
reader = easyocr.Reader(['en', 'ko'], gpu=False)

# 4K 전체화면 기준 버튼 좌표
COORDS = {
    'buy_tab': (953, 388),
    'sell_tab': (1316, 386),
    'refresh': (1994, 509),
    'next_btn': (1592, 1779),
}

all_items_data = []
is_running = True

def stop_program():
    global is_running
    print('\n[!!] Ctrl + 5 입력 감지: 크롤러를 종료합니다.')
    is_running = False
    sys.exit(0)

def get_game_window():
    windows = gw.getWindowsWithTitle('CTRacer') or gw.getWindowsWithTitle('시티레이서')
    if windows:
        win = windows[0]
        if win.isMinimized:
            win.restore()
        win.activate()
        time.sleep(0.1)
        hwnd = win._hWnd
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0040)
        time.sleep(0.1)
        return win
    return None

def click_coord(btn_name):
    x, y = COORDS[btn_name]
    pydirectinput.moveTo(x, y)
    time.sleep(0.03)
    pydirectinput.mouseDown()
    time.sleep(0.03)
    pydirectinput.mouseUp()

def get_game_screenshot(win):
    if win:
        return pyautogui.screenshot(region=(win.left, win.top, win.width, win.height))
    return pyautogui.screenshot()

def get_item_list_screenshot(win):
    full_img = get_game_screenshot(win)
    crop_img = full_img.crop((436, 167, 1831, 1218))
    return crop_img

def is_same_screen(img1, img2, threshold=3.0):
    arr1 = np.array(img1.convert('L'), dtype=np.float32)
    arr2 = np.array(img2.convert('L'), dtype=np.float32)
    diff = np.mean(np.abs(arr1 - arr2))
    return diff < threshold

def check_last_page_pixel():
    pydirectinput.moveTo(10, 10)
    time.sleep(0.05)
    x, y = COORDS['next_btn']
    try:
        r, g, b = pyautogui.pixel(x, y)
        if r <= 35 and g <= 35 and b <= 35:
            return True
    except Exception:
        pass
    return False

# 이미지 전처리 최적화 (배율 왜곡 방지를 위해 스케일 축소 및 이진화 적용)
def preprocess_crop(crop_img):
    img = np.array(crop_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # 이미지 확대 배율을 낮추어 글자 깨짐 현상 방지
    h, w = img.shape[:2]
    img = cv2.resize(img, (int(w * 1.5), int(h * 1.5)), interpolation=cv2.INTER_LINEAR)
    # Otsu 이진화로 글자와 배경을 선명하게 분리
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

# 아이템명 보정 및 대문자 변환
def clean_item_name(text):
    if not text: 
        return ""
    text = text.upper()
    replacements = {
        '오일물러': '오일쿨러', '인터론러': '인터쿨러', '언진': '엔진', 
        '로러': '로터', '드리쓰로틀': '독립쓰로틀', '드리쓰로든': '독립쓰로틀', 
        '대뼈라디에이터': '대용량라디에이터', '대뼈': '대용량', '하이객': '하이캠',
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong.upper(), right.upper())
    return text.strip()

def extract_current_page_items(win):
    screenshot = get_game_screenshot(win)
    page_items = []
    
    # 6개 슬롯의 Y축 오프셋을 개별 지정하여 밀림 현상 원천 차이 차단
    # (기존 간격 오차 누적 문제 해결)
    slot_y_offsets = [0, 193, 386, 579, 772, 965]

    os.makedirs('item_images', exist_ok=True)

    for i, dy in enumerate(slot_y_offsets):
        # 1. 아이템 썸네일 이미지 저장
        try:
            img_box = (822, 559 + dy, 1010, 730 + dy)
            img_crop = screenshot.crop(img_box)
            image_filename = f'item_images/item_{i+1}.png'
            img_crop.save(image_filename)
        except Exception:
            image_filename = ''

        # 2. 아이템 이름
        try:
            name_crop = screenshot.crop((1015, 561 + dy, 1614, 608 + dy))
            name_text = clean_item_name(" ".join(reader.readtext(preprocess_crop(name_crop), detail=0)))
        except Exception:
            name_text = ""

        # 3. 판매자 닉네임
        try:
            nick_crop = screenshot.crop((1676, 563 + dy, 2038, 608 + dy))
            nickname_text = " ".join(reader.readtext(preprocess_crop(nick_crop), detail=0)).strip()
        except Exception:
            nickname_text = ""

        # 4. 남은 시간
        try:
            time_crop = screenshot.crop((1279, 626 + dy, 1461, 665 + dy))
            raw_time = " ".join(reader.readtext(preprocess_crop(time_crop), allowlist='0123456789시간분초 ', detail=0)).strip()
            time_text = raw_time.replace('간', '시간').replace(' ', '')
        except Exception:
            time_text = ""

        # 5. 가격
        try:
            price_crop = screenshot.crop((1116, 680 + dy, 1457, 720 + dy))
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
    
    win = get_game_window()

    cycle_count = 1
    while is_running:
        print(f'\n--- [사이클 {cycle_count}] 시작 ---')
        win = get_game_window()

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
            items = extract_current_page_items(win)
            all_items_data.append({
                'page': page,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'items': items,
            })

            prev_screen = get_item_list_screenshot(win)

            click_coord('next_btn')
            pydirectinput.moveTo(10, 10)
            time.sleep(1.2)

            current_screen = get_item_list_screenshot(win)

            if check_last_page_pixel() or is_same_screen(prev_screen, current_screen):
                time.sleep(0.8)
                retry_screen = get_item_list_screenshot(win)
                if is_same_screen(prev_screen, retry_screen):
                    print("\n>> 마지막 페이지 도달 확인!")
                    upload_to_domain()
                    break

            page += 1

        cycle_count += 1
        time.sleep(1)

if __name__ == '__main__':
    run_crawler()