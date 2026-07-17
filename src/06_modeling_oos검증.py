# 원본코드 에서 일부 발췌함

# ========================
# SMOTE
# ========================

from imblearn.over_sampling import BorderlineSMOTE

train = pd.read_csv(r'D:\2차현황\260612새로하기\스케일링스플릿_25개\260613_Train_25개_scaled.csv')

X_train = train[final_features_25].values
y_train = train['Y'].values

smote = BorderlineSMOTE(random_state=42)
X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
print(f"SMOTE 완료: {X_train_res.shape}")


# ========================
# 앙상블 비교
# ========================

THRESHOLD = 0.480

def calculate_metrics(y_true, y_prob, threshold=THRESHOLD):
    y_pred = (y_prob >= threshold).astype(int)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f2 = (5 * precision * recall) / (4 * precision + recall) if (4 * precision + recall) > 0 else 0
    return {'Accuracy': accuracy_score(y_true, y_pred), 'Precision': precision,
            'Recall': recall, 'F2': f2, 'AUC_ROC': roc_auc_score(y_true, y_prob),
            'MCC': matthews_corrcoef(y_true, y_pred),
            'KS': ks_2samp(y_prob[y_true==1], y_prob[y_true==0]).statistic}

# Soft Voting
prob_rf  = rf_smote.predict_proba(X_test)[:, 1]
prob_xgb = xgb_smote.predict_proba(X_test)[:, 1]
prob_cat = cat_smote.predict_proba(X_test)[:, 1]
prob_soft = (prob_rf + prob_xgb + prob_cat) / 3
metrics_soft = calculate_metrics(y_test, prob_soft)

# Weighted Voting (XGB:0.4, CAT:0.3, RF:0.3)
prob_weighted = 0.4 * prob_xgb + 0.3 * prob_cat + 0.3 * prob_rf
metrics_weighted = calculate_metrics(y_test, prob_weighted)

# Stacking (LGBM 메타모델)
from sklearn.ensemble import StackingClassifier
from lightgbm import LGBMClassifier

estimators = [('rf', rf_smote), ('xgb', xgb_smote), ('cat', cat_smote)]
meta_model = LGBMClassifier(random_state=42, verbosity=-1)

stacking = StackingClassifier(
    estimators=estimators, final_estimator=meta_model,
    cv=5, stack_method='predict_proba', passthrough=False, n_jobs=-1
)
stacking.fit(X_train_res, y_train_res)
prob_stacking = stacking.predict_proba(X_test)[:, 1]
metrics_stacking = calculate_metrics(y_test, prob_stacking)

# ==========================================
#                    ACC          Recall      F2        AUC
# Soft Voting        0.634         0.595      0.549     0.676
# Weighted Voting    0.631         0.598      0.550     0.676
# Stacking           (Recall 급락 → 실무 활용 불가)
#
# 최종 성능 비교 (Test 세트 기준)
# XGB 단독(T=0.47): Accuracy 0.6053, Recall 0.6757, F2 0.5948 — 가장 높은 탐지력
# 앙상블 기법은 모델 간 예측 오차를 상쇄하여 안정성을 높이는 장점이 있으나,
# 부실 기업 탐지(Recall)가 최우선 목표인 경우, 특정 모델(XGBoost)의 임계값을
# 최적화한 단독 모델이 더 우수한 예측 성능을 보임
# ==========================================


# ========================
# Threshold 확정 (0.475~0.49 비교)
# ========================

for t in [0.475, 0.48, 0.485, 0.49]:
    metrics = calculate_metrics(y_oos, prob_xgb_oos, threshold=t)
    print(f"T={t}: ACC={metrics['Accuracy']:.4f}, Recall={metrics['Recall']:.4f}, F2={metrics['F2']:.4f}")


# ========================
# OOS 최종검증 (t=2023, t+1/t+2=2024~2025 실측 대조)
# ========================

model_dir = r'D:\2차현황\260612새로하기\ML_25개피처모델결과저장\모델저장'
with open(os.path.join(model_dir, 'XGB_SMOTE.pkl'), 'rb') as f:
    xgb_smote = pickle.load(f)

oos = pd.read_csv(r'D:\2차현황\260612새로하기\스케일링스플릿_25개\260613_OOS_25개_scaled.csv')
X_oos = oos[final_features_25].values
y_oos = oos['Y'].values

prob_xgb_oos = xgb_smote.predict_proba(X_oos)[:, 1]
metrics_oos = calculate_metrics(y_oos, prob_xgb_oos, threshold=0.480)

print("=== OOS 검증 결과 (XGB SMOTE, T=0.480) ===")
print(f"Accuracy: {metrics_oos['Accuracy']:.4f}")
print(f"Recall  : {metrics_oos['Recall']:.4f}")
print(f"F2      : {metrics_oos['F2']:.4f}")
print(f"AUC_ROC : {metrics_oos['AUC_ROC']:.4f}")
