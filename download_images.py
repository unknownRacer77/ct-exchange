import os
import json
import requests

print("JSON 파일 로딩 중...")
with open('ctr_items_db.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    items = data.get('items', data) if isinstance(data, dict) else data

print(f"총 {len(items)}개의 아이템 확인. 이미지 다운로드 시작...")

# 브라우저인 것처럼 속이는 헤더 추가
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://ctr.domi.kr/'
}

for idx, item in enumerate(items):
    img_path = item.get('image', '')
    if img_path:
        relative_path = img_path.lstrip('/')
        local_path = os.path.join('.', relative_path)
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        if not os.path.exists(local_path):
            url = f"https://ctr.domi.kr{img_path}"
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    with open(local_path, 'wb') as img_file:
                        img_file.write(res.content)
                    print(f"[{idx+1}/{len(items)}] 다운로드 성공: {local_path}")
                else:
                    print(f"[{idx+1}/{len(items)}] 실패 ({res.status_code}): {url}")
            except Exception as e:
                print(f"[{idx+1}/{len(items)}] 에러: {e}")

print("모든 이미지 처리 완료!")