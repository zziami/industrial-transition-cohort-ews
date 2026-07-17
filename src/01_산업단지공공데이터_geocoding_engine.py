
# 원본 코드에서 일부 발췌 


import pandas as pd
import requests
import time
import os

# 1. API 호출 함수 (Exception Handling)
def kakao_geocode(address, api_key):
    """주소 → 위경도 변환 (네트워크 예외 방어)"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": address}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception as e:
        print(f"Error: {e}")
    return None, None

# 2. 데이터 로드 및 중복 제거
INPUT_FILE = 'data.xlsx'
OUTPUT_FILE = 'geocoding_result.xlsx'
KAKAO_API_KEY = 'YOUR_API_KEY'

df = pd.read_excel(INPUT_FILE)
# 고유 공장주소만 추출하여 API 호출 효율 극대화
unique_addrs = df[['공장주소']].drop_duplicates().reset_index(drop=True)

# 3. 체크포인트 로드 (이어서 작업하기)
if os.path.exists(OUTPUT_FILE):
    done = pd.read_excel(OUTPUT_FILE)
    done_addrs = set(done['공장주소'].astype(str))
    print(f"기존 완료: {len(done_addrs)}건 스킵")
else:
    done = pd.DataFrame()
    done_addrs = set()

# 4. Geocoding 실행 (신규 대상 처리)
targets = unique_addrs[~unique_addrs['공장주소'].astype(str).isin(done_addrs)]
results = []

for i, row in targets.iterrows():
    addr = str(row['공장주소']).strip()
    lat, lon = kakao_geocode(addr, KAKAO_API_KEY)
    results.append({'공장주소': addr, 'lat': lat, 'lon': lon})

    # 100건마다 중간 저장 (데이터 유실 방지)
    if (len(results) % 100) == 0:
        temp = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
        temp.to_excel(OUTPUT_FILE, index=False)
        print(f"진행: {len(results)}건 처리 완료")

    time.sleep(0.05) # API 부하 방지

# 5. 최종 저장
final = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
final.to_excel(OUTPUT_FILE, index=False)
print(f"완료! 전체: {len(final)}건")
