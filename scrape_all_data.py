import json
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

base_url = 'https://ctr.domi.kr/itemlist/'
headers = {'User-Agent': 'Mozilla/5.0'}

all_data = []
seen_urls = set()

print('파싱 시작...')

page = 1
while True:
    url = f'{base_url}?parts=all&page={page}'
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'
        if res.status_code != 200: break
        
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find_all('tr')
        if len(rows) <= 1: break

        count = 0
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 7: continue

            name_tag = cols[1].find('a')
            if not name_tag: continue

            detail_url = urljoin('https://ctr.domi.kr', name_tag['href'])
            if detail_url in seen_urls: continue
            seen_urls.add(detail_url)

            name = name_tag.get_text(strip=True)
            img_tag = cols[0].find('img')
            img_src = urljoin('https://ctr.domi.kr', img_tag['src']) if img_tag else ''

            # 차량 클래스 파싱 (이미지 alt 또는 파일명)
            car_class = '-'
            class_img = cols[4].find('img')
            if class_img:
                alt_txt = class_img.get('alt', '').strip()
                if alt_txt in ['S', 'A', 'B', 'C', 'R', 'G']:
                    car_class = alt_txt
                else:
                    src = class_img.get('src', '')
                    fn = src.split('/')[-1].split('.')[0].upper()
                    car_class = fn[-1] if fn and fn[-1] in 'SABCRG' else '-'
            else:
                txt = cols[4].get_text(strip=True)
                if txt and txt != '전체': car_class = txt

            item = {
                'name': name,
                'image': img_src,
                'parts': cols[2].get_text(strip=True),
                'shopgroup': cols[3].get_text(strip=True),
                'carclass': car_class,
                'tp': cols[5].get_text(strip=True),
                'price': cols[6].get_text(strip=True),
                'details': {}
            }

            # 상세 페이지 표 정보 파싱
            try:
                d_res = requests.get(detail_url, headers=headers)
                d_res.encoding = 'utf-8'
                d_soup = BeautifulSoup(d_res.text, 'html.parser')
                for tr in d_soup.find_all('tr'):
                    tds = tr.find_all(['th', 'td'])
                    if len(tds) >= 2:
                        k = tds[0].get_text(strip=True)
                        v = tds[1].get_text(strip=True)
                        if k and v: item['details'][k] = v
            except:
                pass

            all_data.append(item)
            count += 1

        if count == 0: break
        print(f'{page}페이지 파싱 완료 ({count}개)')
        page += 1
    except:
        break

with open('ctr_items_db.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print(f'총 {len(all_data)}개 파싱 완료!')