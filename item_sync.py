import json

# 1. 기존 ctr_items_db.json 불러오기
try:
    with open('ctr_items_db.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
        existing_list = (
            existing_data['items']
            if isinstance(existing_data, dict) and 'items' in existing_data
            else existing_data
        )
except FileNotFoundError:
    existing_list = []

item_dict = {
    item.get('name') or item.get('itemName'): item for item in existing_list
}

# 2. 새로 파싱한 데이터 로드
try:
    with open('scraped_items.json', 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
except FileNotFoundError:
    scraped_data = []

# 3. 병합 (새로 가져온 데이터의 값이 유효하면 기존 값을 덮어씌움)
for new_item in scraped_data:
    name = new_item.get('name') or new_item.get('itemName')
    if not name:
        continue
    if name in item_dict:
        for k, v in new_item.items():
            if v and v != '-' and v != '':
                item_dict[name][k] = v
    else:
        item_dict[name] = new_item

# 4. 저장
final_data = {'items': list(item_dict.values())}
with open('ctr_items_db.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)

print('데이터 병합 완료!')