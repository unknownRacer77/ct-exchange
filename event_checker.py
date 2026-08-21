import os
import json
import time
import cv2
import numpy as np
import pyautogui

# 1. 감지 좌표 설정 (X, Y, 가로W, 세로H)
ROI_X, ROI_Y, ROI_W, ROI_H = 10, 331, 340, 129

# 2. 템플릿 이미지 불러오기 함수
def load_templates(file_list):
    templates = []
    for filename in file_list:
        if os.path.exists(filename):
            img = cv2.imread(filename)
            if img is not None:
                templates.append(img)
    return templates

# 3. 템플릿 매칭 검사 함수 (유사도 80% 이상 판정)
def check_active(roi, templates, threshold=0.8):
    for tpl in templates:
        res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val >= threshold:
            return True
    return False

# 템플릿 이미지 파일 로드 (스크립트와 같은 폴더에 위치)
fokju_templates = load_templates(['fokju1.png', 'fokju2.png'])
golden_templates = load_templates(['golden1.png', 'golden2.png'])

print("⚡ 이벤트 감지 모니터링 시작 (10초 주기)")

while True:
    try:
        # 지정 좌표 화면 캡처
        screenshot = pyautogui.screenshot(region=(ROI_X, ROI_Y, ROI_W, ROI_H))
        roi_frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 폭주타임 & 골든타임 상태 확인
        is_fokju = check_active(roi_frame, fokju_templates)
        is_golden = check_active(roi_frame, golden_templates)

        # JSON 데이터 생성 및 저장
        event_data = {
            "fokju": is_fokju,
            "golden": is_golden,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open('event.json', 'w', encoding='utf-8') as f:
            json.dump(event_data, f, ensure_ascii=False, indent=2)

        print(f"[{event_data['updated_at']}] 폭주: {is_fokju} | 골든: {is_golden}")

    except Exception as e:
        print(f"오류 발생: {e}")

    time.sleep(10)