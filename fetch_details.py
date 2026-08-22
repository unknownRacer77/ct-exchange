import json
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ctr.domi.kr"
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
        ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}


def get_item_detail(item_id):
    """상세 페이지(detail.php)에서 표 데이터 파싱"""
    if not item_id:
        return {}

    url = f"{BASE_URL}/itemlist/detail.php?id={item_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        detail_info = {}
        for row in soup.select("table tr"):
            cols = row.find_all(["td", "th"])
            if len(cols) == 2:
                key, val = cols[0].text.strip(), cols[1].text.strip()
                if key and val:
                    detail_info[key] = val
        return detail_info
    except Exception:
        return {}


def main():
    items = []
    page = 1

    while True:
        list_url = f"{BASE_URL}/itemlist/?parts=all&shopgroup=all&carclass=all&itemname=&page={page}"
        print(f"\n📄 {page}페이지 수집 중... ({list_url})")

        res = requests.get(list_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("tbody tr")

        if not rows:
            print(f"🛑 {page}페이지에 데이터가 없습니다. 모든 페이지 수집 완료!")
            break

        print(f"📦 {page}페이지에서 {len(rows)}개 항목 발견")

        for row in rows:
            item_id = row.get("data-id")

            name_el = row.select_one("td.name")
            name = name_el.text.strip() if name_el else ""

            img_el = row.select_one("td.img img")
            img_src = (
                urljoin(BASE_URL, img_el["src"])
                if img_el and img_el.has_attr("src")
                else ""
            )

            tds = row.find_all("td")
            parts = tds[2].text.strip() if len(tds) > 2 else ""
            shopgroup = tds[3].text.strip() if len(tds) > 3 else ""
            
            # --- 수정된 부분: Class 이미지에서 알파벳 추출 ---
            carclass = ""
            classimg_el = row.select_one("td.classimg img")
            if classimg_el and classimg_el.has_attr("src"):
                src_val = classimg_el["src"]  # 예: /assets/itemlist/class/class_b.png
                file_name = src_val.split("/")[-1]  # class_b.png
                # class_ 와 .png 를 제거하고 대문자로 변환 -> B
                carclass = file_name.replace("class_", "").replace(".png", "").upper()
            # --------------------------------------------------

            tp = tds[5].text.strip() if len(tds) > 5 else ""
            price = tds[6].text.strip() if len(tds) > 6 else ""

            print(f"  - [{name}] (ID: {item_id}) 상세 데이터 파싱")
            details = get_item_detail(item_id)

            if not tp or tp == '-':
                tp = details.get("TP") or details.get("tp") or details.get("튜닝포인트") or "-"

            items.append({
                "id": item_id,
                "name": name,
                "image": img_src,
                "parts": parts,
                "shopgroup": shopgroup,
                "carclass": carclass,
                "tp": tp,
                "price": price,
                "details": details,
            })

        page += 1

    # 웹페이지에서 동기화 에러가 나지 않도록 파일명을 ct_trade_db.json 으로 맞춤
    with open("ct_trade_db.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 총 {page - 1}개 페이지에서 총 {len(items)}개 아이템 수집 및 저장 완료!")


if __name__ == "__main__":
    main()