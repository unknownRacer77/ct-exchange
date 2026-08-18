import os
import sys
import time
import keyboard
import pyautogui
import pydirectinput
import pandas as pd
from difflib import get_close_matches

COORDS = {
    'buy_tab': (946, 361),
    'sell_tab': (1299, 361),
    'refresh': (1985, 492),
    'next_btn': (1594, 1798),
}

is_running = True

def stop_program():
    global is_running
    print('\n[!!] 캡쳐 중단 (Ctrl + 5)')
    is_running = False
    sys.exit(0)

def click_pos(x, y):
    pyautogui.moveTo(x, y, duration=0.1)
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.mouseUp()

def load_valid_items():
    """market_items.csv에서 정상 아이템 이름 목록 불러오기"""
    if os.path.exists('market_items.csv'):
        try:
            df = pd.read_csv('market_items.csv')
            if 'item_name' in df.columns:
                return df['item_name'].dropna().astype(str).tolist()
        except Exception:
            pass
    return []

def correct_item_name(text, valid_items):
    """OCR 오인식 텍스트를 market_items.csv 기준으로 자동 보정"""
    if not valid_items:
        return text
    match = get_close_matches(text, valid_items, n=1, cutoff=0.6)
    return match[0] if match else text

def main():
    save_folder = 'screenshots'
    os.makedirs(save_folder, exist_ok=True)
    
    keyboard.add_hotkey('ctrl+5', stop_program)

    # 정상 아이템 목록 미리 로드
    valid_items = load_valid_items()

    print('=== 거래소 화면 자동 캡쳐기 실행 (종료: Ctrl + 5) ===')
    print('⏳ 3초 뒤에 시작됩니다. 시티레이서 창을 맨 앞으로 가져다 놓으세요!')
    for i in range(3, 0, -1):
        print(f'  {i}초 전...')
        time.sleep(1)

    page = 1
    while is_running:
        screen = pyautogui.screenshot()
        file_path = os.path.join(save_folder, f'page_{page:03d}.png')
        screen.save(file_path)
        print(f'[{page} 페이지] 캡쳐 완료 -> {file_path}')

        # 예시: OCR 추출 후 보정 과정이 필요할 때 아래 함수 사용 가능
        # corrected_name = correct_item_name("인식된텍스트", valid_items)

        click_pos(*COORDS['next_btn'])
        pydirectinput.moveTo(10, 10)

        time.sleep(1.5)
        page += 1

if __name__ == '__main__':
    main()