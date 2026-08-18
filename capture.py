import os
import sys
import time
import keyboard
import pyautogui
import pydirectinput

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

def main():
    # 1. 스크린샷 저장용 폴더 생성
    save_folder = 'screenshots'
    os.makedirs(save_folder, exist_ok=True)
    
    keyboard.add_hotkey('ctrl+5', stop_program)

    print('=== 거래소 화면 자동 캡쳐기 실행 (종료: Ctrl + 5) ===')
    print('⏳ 3초 뒤에 시작됩니다. 시티레이서 창을 맨 앞으로 가져다 놓으세요!')
    for i in range(3, 0, -1):
        print(f'  {i}초 전...')
        time.sleep(1)

    page = 1
    while is_running:
        # 2. 현재 화면 전체 캡쳐 및 파일 저장
        screen = pyautogui.screenshot()
        file_path = os.path.join(save_folder, f'page_{page:03d}.png')
        screen.save(file_path)
        print(f'[{page} 페이지] 캡쳐 완료 -> {file_path}')

        # 3. 다음 페이지 클릭 후 마우스 치우기
        click_pos(*COORDS['next_btn'])
        pydirectinput.moveTo(10, 10)

        # 4. 화면 전환 대기 (1.5초)
        time.sleep(1.5)
        page += 1

if __name__ == '__main__':
    main()