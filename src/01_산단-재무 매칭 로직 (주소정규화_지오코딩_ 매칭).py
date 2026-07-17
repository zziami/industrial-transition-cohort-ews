
# 원본 코드에서 일부 발췌 


def kakao_geocode(address, api_key):
    """주소 → 위경도 변환"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": address}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])  # lat, lon
    except:
        pass
    return None, None

# ── 데이터 로드 ────────────────────────────────
df = pd.read_excel(INPUT_FILE)
print(f"전체 행수: {len(df)}")

# ── 이어서 돌리기 위한 기존 결과 로드 ──────────────
if os.path.exists(OUTPUT_FILE):
    done = pd.read_csv(OUTPUT_FILE, encoding='utf-8-sig')
    done_codes = set(done['거래소코드'].astype(str))
    print(f"기존 완료: {len(done_codes)}건 스킵")
else:
    done = pd.DataFrame()
    done_codes = set()

# ── geocoding 실행 ─────────────────────────────
results = []
targets = df[~df['거래소코드'].astype(str).isin(done_codes)].copy()
print(f"신규 처리 대상: {len(targets)}건")

for i, row in targets.iterrows():
    code  = row['거래소코드']
    addr1 = row.get('공장주소', None)
    addr2 = row.get('본사 주소', None)

    lat, lon, used = None, None, None

    # 공장주소 우선
    if pd.notna(addr1) and str(addr1).strip():
        lat, lon = kakao_geocode(str(addr1).strip(), KAKAO_API_KEY)
        if lat: used = '공장주소'

    # fallback: 본사주소
    if lat is None and pd.notna(addr2) and str(addr2).strip():
        lat, lon = kakao_geocode(str(addr2).strip(), KAKAO_API_KEY)
        if lat: used = '본사주소'

    results.append({
        '거래소코드': code,
        '회사명': row.get('회사명', ''),
        'lat': lat,
        'lon': lon,
        '주소출처': used,
    })

    # 100건마다 저장 + 진행상황 출력
    if (len(results) % 100) == 0:
        temp = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
        temp.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        success = sum(1 for r in results if r['lat'])
        print(f"진행: {len(results)}/{len(targets)} | 성공: {success}건")

    time.sleep(0.05)  # API 호출 간격

# ── 최종 저장 ──────────────────────────────────
final = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
