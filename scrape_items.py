import requests
from bs4 import BeautifulSoup
import json
import time

base_url = "https://ctr.domi.kr/itemlist/?parts=all&shopgroup=all&carclass=all&itemname=&page="
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

items = []
page = 1

while True:
    url = f"{base_url}{page}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.select('tbody tr')
    if not rows:
        break

    parsed = 0
    for row in rows:
        name_td = row.find('td', class_='name')
        if not name_td:
            continue
        
        name = name_td.text.strip()
        img_td = row.find('td', class_='img')
        image_src = img_td.find('img')['src'] if img_td and img_td.find('img') else ""

        tds = row.find_all('td')
        
        class_td = row.find('td', class_='classimg')
        car_class = ""
        if class_td and class_td.find('img'):
            src = class_td.find('img')['src']
            car_class = src.split('class_')[-1].replace('.png', '').upper()

        texts = [td.text.strip() for td in tds]
        
        items.append({
            "image": image_src,
            "name": name,
            "parts": texts[2] if len(texts) > 2 else "",
            "shopgroup": texts[3] if len(texts) > 3 else "",
            "carclass": car_class,
            "torque": texts[5] if len(texts) > 5 else "",
            "weight": texts[6] if len(texts) > 6 else "",
            "tp": texts[7] if len(texts) > 7 else "",
            "price": texts[-1] if len(texts) > 0 else ""
        })
        parsed += 1

    if parsed == 0:
        break
    print(f"{page}페이지 수집 완료")
    page += 1
    time.sleep(0.1)

with open('ctr_items_db.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=4)

print(f"총 {len(items)}개 수집 완료!")