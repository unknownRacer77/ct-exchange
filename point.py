import pyautogui

print("=== 실시간 좌표 추출기 (종료: Ctrl + C) ===")
print("마우스로 원하는 위치를 클릭해 보세요.\n")

try:
    while True:
        # 마우스 왼쪽 버튼을 누를 때의 좌표 감지
        if pyautogui.mouseInfo(): # 대기
            pass
except KeyboardInterrupt:
    print("\n종료합니다.")