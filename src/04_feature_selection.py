
# 원본코드에서 일부 발췌

# =====================================================
# TimeSeriesSplit 코드 구조
#
# 산단데이터_재무데이터 파생변수 만들어서 붙이고
# 2009년 제외 (전기값 계산용이니까 학습 제외)
# Y 있는 코호트만 추출
#   (원본 코호트 파일 보존 - 분산0 제거 안 한 파일 그대로 VIF 돌렸더니
#    무한루프에 빠져서 다시 정제 → 분할 → VIF 순서로 재설계함)
#
# Train/Val/Test 분할 (2010~2017 / 2018~2019 / 2020~2022)
# 외부검증셋 분리 (t=2023)
# Expanding Window 7-Fold CV
# =====================================================

# ── 데이터 처리 흐름 (심사 대비용) ─────────────────────────────
# 원본 보존: 코호트_전처리완료.csv (불변의 기준점)
# 데이터 정제: 원본을 읽어와서 분산 0인 변수 + 필수 제거 리스트
#             (is_matched, 중분류 등)를 제거 → 코호트_정제완료.csv로 저장
# 데이터 분할: 코호트_정제완료.csv를 불러와서 Train/Val/Test/OOS로 분할
#             → 각각 .pkl 파일로 저장
# 모델링 준비: Train.pkl로 VIF 수행(핵심 피처 확정)
#             → Train.pkl 기준 스케일링 수행 후 Val/Test/OOS 변환
#
# 재현성: 원본이 그대로 보존되어 있고 정제본이 명확히 존재하므로
#        데이터 흐름(Audit Trail)이 투명함
# 오류 차단: 원본을 덮어쓰지 않으니 정제 과정 실수 시 언제든 재시작 가능
# =====================================================

# ── 코호트 필터링: 기업당 최초진입 1행만 유지 ──────────────────
# (회사코드 groupby → 같은 기업이 여러 구간에 걸치는 걸 원천 차단)
첫진입_idx = df[df['최초진입'] == 1].groupby('거래소코드')['회계년도'].idxmin()
df_cohort = df.loc[첫진입_idx].copy()
df_cohort = df_cohort[
    (df_cohort['회계년도'] >= 2010) &
    (df_cohort['회계년도'] <= 2023) &
    (df_cohort['Y'].notna())
].copy()

# ── 시계열 분할 (회계년도 = 기업당 유일한 관측 시점) ────────────
# 기업당 1행만 남은 상태이므로, 회계년도 기준 분할 = 기업 단위 분할과 동일
# → 시간 순서 보존 + 기업 단위 누수 차단을 동시에 충족
oos   = df_cohort[df_cohort['회계년도'] == 2023].copy()
df_   = df_cohort[df_cohort['회계년도'] != 2023].copy()
train = df_[df_['회계년도'] <= 2017].copy()
val   = df_[df_['회계년도'].isin([2018, 2019])].copy()
test  = df_[df_['회계년도'].isin([2020, 2021, 2022])].copy()

print(f"Train: {len(train):,}행 | Y=1 비율: {train['Y'].mean():.3f}")
print(f"Val  : {len(val):,}행 | Y=1 비율: {val['Y'].mean():.3f}")
print(f"Test : {len(test):,}행 | Y=1 비율: {test['Y'].mean():.3f}")
print(f"OOS  : {len(oos):,}행 | Y=1 비율: {oos['Y'].mean():.3f}")

# 결과: Train 6,992 / Val 1,728 / Test 2,336 / OOS 819
#       Y=1 비율: Train 0.288 / Val 0.232 / Test 0.297 / OOS 0.327





#===========================================
# 이변량 상관계수 기반 제거 (0.95 이상) ← 정정
#===========================================

# 원본에서 코호트만 필터링 (컬럼 제거 없이)
첫진입_idx = df[df['최초진입'] == 1].groupby('거래소코드')['회계년도'].idxmin()
df_corr = df.loc[첫진입_idx].copy()
df_corr = df_corr[
    (df_corr['회계년도'] >= 2010) &
    (df_corr['회계년도'] <= 2023) &
    (df_corr['Y'].notna())
].copy()

num_cols = df_corr.select_dtypes(include=[np.number]).columns.tolist()
exclude = ['거래소코드', '회계년도', 'Y', 'ICR', 'ICR_미만1', 'ICR_미만1_전기',
           'ICR_미만1_t1', 'ICR_미만1_t2', '최초진입', '연속_t1', '연속_t2',
           '회계년도_t1', '회계년도_t2']
check_cols = [c for c in num_cols if c not in exclude]

corr_matrix = df_corr[check_cols].corr().abs()
upper = corr_matrix.where(
    np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
)

high_corr = [(col, row, round(upper.loc[row, col], 4))
             for col in upper.columns
             for row in upper.index
             if upper.loc[row, col] >= 0.95]

corr_df = pd.DataFrame(high_corr, columns=['변수1', '변수2', '상관계수'])


#================================
# 제거변수
#================================

removed_corr = pd.DataFrame([
    {'제거변수': '업종대비_당좌비율', '유지변수': '업종대비_유동비율', '상관계수': 0.9863, '사유': '상관계수 0.95 이상 중복'},
    {'제거변수': '부가가치', '유지변수': 'EBITDA', '상관계수': 0.9994, '사유': '상관계수 0.95 이상 중복'},
    {'제거변수': '매출액순이익률', '유지변수': '세전이익률', '상관계수': 0.9954, '사유': '상관계수 0.95 이상 중복'},
    {'제거변수': '순부채비율', '유지변수': '부채비율', '상관계수': 0.9542, '사유': '상관계수 0.95 이상 중복'},
])


#================================
# 분산 0 제거
#================================

# Train 기준 분산0 확인
zero_var_cols = [c for c in proc_cols if train[c].var() == 0]
print(f"분산0 컬럼 ({len(zero_var_cols)}개):")
print(zero_var_cols)
# → 종업원증감율 (종업원 데이터가 매년 동일값으로 기록되어 증감률 계산 불가)



#==================
# Welch t-test
# 판단기준 35개 통계적 유의성기반 + 10개(분석가의 전문적 판단 - 분식과 부실의 피쳐 및 선행연구 기반) = 총 45개를 최종 후보군으로 확정하고 VIF 다중공선성 검사를 진행
#==================

# 이 테스트의 목적은 "부도 기업과 정상 기업의 평균이 통계적으로 유의미하게 다른가?"를 확인하여,
# 변별력이 없는(p-value가 높은) 변수를 걸러내는 것입니다.

meta_cols = ['회사명', '거래소코드', '회계년도', 'Y']
welch_exclude = ['산단_매칭여부', '제조시설면적', '건축면적',
                 '산단_분양률', '산단_가동업체', '산단_가동률']
num_cols = train.select_dtypes(include=[np.number]).columns.tolist()
ttest_cols = [c for c in num_cols if c not in meta_cols + welch_exclude]

results = []
for col in ttest_cols:
    group0 = train.loc[train['Y'] == 0, col].dropna()
    group1 = train.loc[train['Y'] == 1, col].dropna()
    t_stat, p_val = stats.ttest_ind(group0, group1, equal_var=False)
    results.append({
        'feature': col,
        'mean_Y0': group0.mean(),
        'mean_Y1': group1.mean(),
        'mean_diff': group1.mean() - group0.mean(),
        't_stat': t_stat,
        'p_value': p_val,
        'significant': p_val < 0.05
    })

ttest_df = pd.DataFrame(results).sort_values('p_value')


#================
# VIF (다중공선성)  
# 다중공선성 제거 과정의 투명성 확보. VIF > 10인 변수 목록 및 제거 순서 — 10 이상인 건 CCC만 걸림. 동태적인 변화를 보려면 CCC보다 ΔCCC가 더 적합.
#================

final_features = [
    '총자산_LOG', 'WC_Stress', '총자본회전율', '매출액영업이익률', '총자본증가율',
    '세전이익률', '유동부채비율', '영업운전자본부담률', 'CCC', '당기순이익변동성',
    '재고자산회전기간', 'AQI', '유형자산회전율', '대표이사변경여부', 'INV_Accel',
    'CFO', 'TATA', '부채비율증감', '지속적당기순손실여부', '이익잉여금증감',
    '자본잠식여부', '단기화지수', '차입금의존도', 'ΔCCC', '유동부채증감',
    '이익잉여금증감률', '매출채권회전기간', '현금비율', '업종대비_현금비율',
    'DEPI', 'GMI', 'SGI',
    '유동비율증감', '기계화집약도', 'Zombie_Density', '계획입지여부', '노동소득분배율'
]

# CCC 제거
for df_split, name in [(train,'Train'),(val,'Val'),(test,'Test'),(oos,'OOS')]:
    if 'CCC' in df_split.columns:
        df_split.drop(columns=['CCC'], inplace=True)



#======================
# Lasso (LogisticRegressionCV)
#=====================

X_train = train[final_features].replace([np.inf, -np.inf], 0).fillna(0)
y_train = train['Y']

# Lasso (LogisticRegressionCV, L1 penalty)



#============================
# 계획입지여부 강제 복구 근거
# 지속적당기순손실여부: 이미 포함된 '당기순이익변동성'이나 '세전이익률' 같은 변수들이 이 정보를 이미 반영하고 있을 가능성이 큽. 
# 계획입지는 선행연구에서 근거로 넣은 핵심변수임. LASSO가 제거했지만 이론적 근거(논문) 기반 복구
# 이론기반 강제포함 → p<0.1 경계선 방어 → SHAP 사후검증
# ===========================


# 계획입지여부 강제 복구
lasso_features = lasso_selected['feature'].tolist()
lasso_features += ['계획입지여부']
lasso_features = list(dict.fromkeys(lasso_features))

print(f"최종 피처 수: {len(lasso_features)}개")






