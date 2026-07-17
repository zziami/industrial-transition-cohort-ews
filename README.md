# industrial-transition-cohort-ews
# 산업구조 전환기 비상장 외감 제조업의 한계기업 조기예측(EWS)
---------------------------------------------------------------

**비상장 외부감사대상 제조기업을 대상으로, 산업구조 전환기 코호트(2010~2023) 데이터를 활용해 이자보상배율(ICR) 기준 한계기업(3년 연속 ICR<1)을 조기 예측하는 머신러닝 프로젝트입니다.**



## 1. Data Collection

- 출처: TS2000, DART(기업개황·업종코드), FACTORYON, KICOX 전국산업단지현황통계(산단 매칭), KOMIS, ECOS, Kakao API Geocoding(공간 매칭)
- 코호트기간: '2010 ~ 2023' (2009년은 YoY 파생변수용 lag 기준년도, ICR<1 최초 진입 연도 기준 코호트 구성), OOS 검증 2023년 ('2024 ~ 2025' 최신 실측치 대조 추가 검증 수행)
- 규모: 157,541행(패널정렬 후), 19,790개 기업(비상장 외감 제조업) 

## 2. EDA (Cohort Analysis)

- 코호트 정의: 이자보상배율(ICR) 1 미만으로 최초 진입한 연도를 기준으로 기업을 그룹화하여 추적하는 분석 방법. 진입 후 2년치 재무데이터로 3년 연속 한계상태 지속 여부를 조기 예측
- 산업단지 매칭: 전국 산단 1,435개 중 필터링을 거쳐 최종 751개 단지 분석 대상 확보. 비상장 외감 제조업 19,790社 중 계획입지(산단 내) 14,895개사(75.3%), 개별입지 4,895개사(24.7%)로 분류
- Y 라벨 분포전체 : 전체 11,875행 (Y=1 한계기업 3,379행 / Y=0 회복 8,496행, Y=1 비율 28.4%) — 기업(회사코드) 단위 그룹 분할(Train/Val/Test/OOS), 데이터 누수 방지

 
## 3. Preprocessing & Feature Engineering

- 전처리 파이프라인: 결측치 처리(lag 연속성 보존을 위해 일부 NaN 유지) → StratifiedGroupKFold(기업 단위 그룹 분리) → Train-only SMOTE
- Feature Selection:
  - 초기 81개 변수 → 분산0 제거·상관계수 제거·Welch T-test·VIF 제거·Lasso 등 통계·이론 기반 선택 → 35개로 1차 모델링 → SHAP+Feature Importance 반영해 재선택 → 최종 25개로 2차 모델링 확정
- 변수 레이어 구조
  - Layer 1: 재무계정 (62개)
  - Layer 2: 산업구조 전환 신호 (8개)
  - Layer 3: 입지 및 기업구조 특성 (11개, 계획입지여부 등)
  - Layer 4: 거시변수 (10개, 최종 모델 미적용)

## 4. Model & Algorithms

- 1차 모델링: 35개 피처, 7개 모델(LR/RF/XGBoost/LGBM/CatBoost/MLP/TabNet), SMOTE·CT-GAN 1:1, Threshold 0.5
- 2차 모델링: 25개 피처, 5개 모델(LR/RF/XGBoost/LGBM/CatBoost), SMOTE 1:1, Threshold 0.5 → XGBoost가 F2·AUC 균형 우위로 최종 후보 선정
- 앙상블 검증: Soft Voting, Weighted Voting, Stacking 시도 → Recall·F2 저하 확인 (Stacking은 Recall 0.170까지 급락, 실무 활용 불가) → 단독 XGBoost 모델이 최종 선택
- 최종 모델: XGBoost + SMOTE 단독모델, Threshold 0.480 (Recall·F2 손실 최소화 기준)


## 5. Report (OOS 2023 기준, Threshold 0.480)

| 지표 | 값 |
|---|---|
| Accuracy | 0.601 |
| Precision | 0.416 |
| Recall | 0.549 |
| F1 | 0.473 |
| F2 Score | 0.516 |
| AUC-ROC | 0.625 |
| 최종 Feature 수 | 25개 (81개 중 다단계 선택) |

- 임계값 선정 기준: 한계기업 미탐지(FN) 비용이 오탐(FP)보다 치명적 → Recall·F2 우선, AUC로 모델 간 변별력 비교, ACC 0.6을 최소 실용 기준으로 설정 → Threshold 0.480에서 Recall·F2·AUC 최우선 균형점 확인
- SHAP 분석 결과, 산업단지 입지 유형(계획입지여부) 이 변수중요도 2위로 확인됨 → 재무 지표만으로는 포착 못하는 공간적/산업구조적 리스크 신호 존재


## 6. Review

- 한계: 일부 통계 가정(정규성·등분산성) 미충족 구간 존재, 경향성 참고 지표로 해석
- 향후 과제: 변수 정교화 → 집단 확장 → 실무 적용
- 
### Notable Attempts (시도했으나 통합하지 않은 것)
- **지특법 78조 리스크 신호**: 산단 입주기업의 취득세·재산세 감면 요건 위반 이력을 조기경보 신호로 검토했으나, 완료신고일 등 공공데이터의 처분 이력 미제공으로 검증 불가 → 의도적 제외 (자세한 내용은 `99.부록`)

 
  


