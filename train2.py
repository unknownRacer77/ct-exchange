import os
from paddleocr import PaddleOCR

# 1. OCR 엔진 초기화 (한국어 설정)
ocr = PaddleOCR(use_angle_cls=True, lang='ko')

# 2. 폴더 경로 설정
folder_path = './item_dataset'
files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# 3. 10개만 테스트
for filename in files[:10]:
    img_path = os.path.join(folder_path, filename)
    
    # PaddleOCR 실행
    result = ocr.ocr(img_path, cls=True)
    
    # 텍스트 추출 (결과값에서 글자만 뽑아냄)
    texts = [line[1][0] for line in result[0]] if result[0] else []
    item_name = ' '.join(texts)
    
    print(f'{filename}\t{item_name}')