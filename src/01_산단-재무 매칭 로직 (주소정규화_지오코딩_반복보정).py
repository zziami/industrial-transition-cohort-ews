
# 원본 코드에서 일부 발췌 


# ==================================
# kakao_geocode     
# **지오코딩 매칭**: 표준 주소 API 단독 매칭 시 산단 밀집지역에서 실패율이 높아, 시군구 대표좌표 기반 단계적 보완 로직을 추가해 매칭률을 끌어올림
# ==================================
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

# ── 1차 지오코딩: 공장주소 우선, 실패 시 본사주소 fallback ──
df = pd.read_excel(INPUT_FILE)
if os.path.exists(OUTPUT_FILE):
    done = pd.read_csv(OUTPUT_FILE, encoding='utf-8-sig')
    done_codes = set(done['거래소코드'].astype(str))
else:
    done = pd.DataFrame()
    done_codes = set()

results = []
targets = df[~df['거래소코드'].astype(str).isin(done_codes)].copy()

for i, row in targets.iterrows():
    code, addr1, addr2 = row['거래소코드'], row.get('공장주소'), row.get('본사 주소')
    lat, lon, used = None, None, None
    if pd.notna(addr1) and str(addr1).strip():
        lat, lon = kakao_geocode(str(addr1).strip(), KAKAO_API_KEY)
        if lat: used = '공장주소'
    if lat is None and pd.notna(addr2) and str(addr2).strip():
        lat, lon = kakao_geocode(str(addr2).strip(), KAKAO_API_KEY)
        if lat: used = '본사주소'
    results.append({'거래소코드': code, '회사명': row.get('회사명', ''),
                     'lat': lat, 'lon': lon, '주소출처': used})
    if (len(results) % 100) == 0:
        temp = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
        temp.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    time.sleep(0.05)

final = pd.concat([done, pd.DataFrame(results)], ignore_index=True)

# ── 지오코딩 실패 케이스 반복 보정 (수차례 이상 반복 수행) ──
# Kakao API 주소 검색이 실패하는 케이스(신축 산단, 표기 불일치 주소 등)를
# 시군구 단위 대표좌표로 순차 보완. 실패 지역 분포를 확인 → 대표좌표 테이블 보강 →
# 재적용 → 잔여 실패 재확인을 반복하며 매칭률을 단계적으로 끌어올림.
#
# 1차 보완 (안산/화성/시흥 등 산단 밀집 시군구 20개 대표좌표 매핑):
실패 = 위경도[위경도['lat'].isna()][['거래소코드']]
실패df = 실패.merge(코호트[['거래소코드','시도명','시군구명']], on='거래소코드', how='left')

시군구_좌표 = {
    ('경기', '안산시'): (37.3219, 126.8309),
    ('경기', '화성시'): (37.1996, 126.8317),
    # ... (총 20개)
}

def fill_coords(row):
    key = (row['시도명'], row['시군구명'])
    if key in 시군구_좌표:
        return pd.Series({'lat': 시군구_좌표[key][0], 'lon': 시군구_좌표[key][1], '주소출처': '시군구중심'})
    return pd.Series({'lat': None, 'lon': None, '주소출처': None})

filled = 실패df.apply(fill_coords, axis=1)
위경도.loc[실패idx, ['lat','lon','주소출처']] = filled.values
# 기존 성공 8,658건(72.9%) → 1차 보완 후 잔여 실패 확인

# 2차 보완 (수원/안양/청주 등 추가 29개 시군구 대표좌표 매핑) 이후
# 3~5차 반복: [실제 라운드별 감소 건수 채워주시면 여기 반영]
#
# 최종 결과: 공장/본사주소 정확 지오코딩 8,658개(72.9%) +
#            시군구 중심좌표 보완 3,217개(27.1%) + 시도 중심좌표 보완 221개 = 실패 0건


#============================================================================
# 실패 케이스 보정 — 시군구 중심좌표 fallback (수차례 걸쳐 딥다이브, 원본 그대로)
#=============================================================================


# 실패한 코호트 기업들 주요지역 뽑아보기
실패 = 위경도[위경도['lat'].isna()][['거래소코드']]
실패df = 실패.merge(코호트[['거래소코드','시도명','시군구명']], on='거래소코드', how='left')

print(f"실패 건수: {len(실패df)}")
print(실패df[['시도명','시군구명']].value_counts().head(20))
# 주요산단지역들이 실패함. 안산 화성 시흥 남동 등 시군구 중심좌표 채워주기

# 시군구 대표 좌표 테이블
시군구_좌표 = {
    ('경기', '안산시'): (37.3219, 126.8309),
    ('경기', '화성시'): (37.1996, 126.8317),
    ('경기', '시흥시'): (37.3800, 126.8030),
    # ... (총 20개 시군구, 산단 밀집지역 우선)
}

def fill_coords(row):
    key = (row['시도명'], row['시군구명'])
    if key in 시군구_좌표:
        return pd.Series({'lat': 시군구_좌표[key][0],
                         'lon': 시군구_좌표[key][1],
                         '주소출처': '시군구중심'})
    return pd.Series({'lat': None, 'lon': None, '주소출처': None})

filled = 실패df.apply(fill_coords, axis=1)
위경도.loc[실패idx, ['lat','lon','주소출처']] = filled.values

print(f"기존 성공: 8658")
print(f"시군구 보완: {filled['lat'].notna().sum()}")
print(f"여전히 실패: {위경도['lat'].isna().sum()}")


#============================================================================
# 최종 매칭 품질
#=============================================================================

'''
주소출처별 품질 정리하면:
공장/본사주소 정확 geocoding: 8,658개 (72.9%)
시군구 중심좌표 보완: 3,217개 (27.1%)
시도 중심좌표 보완: 221개
실패: 0개
'''


#============================================================================
# 시도별 집계 (대시보드 연결용)
#=============================================================================


df = 코호트.merge(위경도[['거래소코드','lat','lon','주소출처']], on='거래소코드', how='left')

시도집계 = df.groupby('시도명').agg(
    전체기업수=('거래소코드', 'count'),
    한계기업수=('Y', 'sum'),
    산단수=('산단_단지명', 'nunique')
).reset_index()
시도집계['한계기업비율'] = (시도집계['한계기업수'] / 시도집계['전체기업수'] * 100).round(1)
시도집계.columns = ['시도', '전체기업수', '한계기업수', '산단수', '한계기업비율']

# 시도명 매핑 테이블 (GeoJSON 연결용)
시도명_매핑 = {
    '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시',
    '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시',
    '울산': '울산광역시', '세종': '세종특별자치시', '경기': '경기도',
    '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
    '전북': '전라북도', '전남': '전라남도', '경북': '경상북도',
    '경남': '경상남도', '제주': '제주특별자치도'
}
시도집계['시도_GeoJSON'] = 시도집계['시도'].map(시도명_매핑)


