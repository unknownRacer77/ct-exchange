import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base_url = 'https://ctr.domi.kr'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

all_data = []
seen_names = set()

print('🚀 데이터 파싱 시작...')

for shop_id in range(1, 51):
    url = f'{base_url}/itemlist/?parts=all&shopgroup={shop_id}&carclass=all&itemname='
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'
        if res.status_code != 200: continue
        
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table tr')
        if len(rows) <= 1: continue

        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) < 7: continue

            name_tag = cols[1].find('a')
            name = name_tag.get_text(strip=True) if name_tag else cols[1].get_text(strip=True)
            
            if name in seen_names: continue
            seen_names.add(name)

            # 썸네일 이미지 절대경로
            img_tag = cols[0].find('img')
            img_src = urljoin(base_url, img_tag['src']) if img_tag else ''

            # 차량 클래스 이미지 파싱 (S, A, B, C 등 알파벳 추출)
            carclass_td = cols[4]
            car_class_img = carclass_td.find('img')
            carclass = '-'
            if car_class_img:
                alt = car_class_img.get('alt', '').strip()
                if alt in ['S', 'A', 'B', 'C', 'R', 'G']:
                    carclass = alt
                else:
                    src = car_class_img.get('src', '')
                    fn = src.split('/')[-1].split('.')[0].upper()
                    carclass = fn[-1] if fn and fn[-1] in 'SABCRG' else '-'
            else:
                txt = carclass_td.get_text(strip=True)
                if txt and txt != '전체': carclass = txt

            item = {
                'name': name,
                'image': img_src,
                'parts': cols[2].get_text(strip=True),
                'shopgroup': cols[3].get_text(strip=True),
                'carclass': carclass,
                'tp': cols[5].get_text(strip=True),
                'price': cols[6].get_text(strip=True),
                'details': {}
            }

            # 상세 페이지 표 정보 파싱
            if name_tag and name_tag.has_attr('href'):
                detail_url = urljoin(base_url, name_tag['href'])
                try:
                    d_res = requests.get(detail_url, headers=headers)
                    d_res.encoding = 'utf-8'
                    d_soup = BeautifulSoup(d_res.text, 'html.parser')
                    
                    for s_row in d_soup.select('table tr'):
                        th, td = s_row.find('th'), s_row.find('td')
                        if th and td:
                            item['details'][th.get_text(strip=True)] = td.get_text(strip=True)
                except:
                    pass
                time.sleep(0.05)

            all_data.append(item)
        time.sleep(0.2)
    except Exception as e:
        pass

with open('ctr_items_db.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print(f'\n🎉 총 {len(all_data)}개 데이터 파싱 완료!')