원본코드에서 일부 발췌 

# =================================
# 그래서 산단에 입주해서 망한다는거야??
# 계획입지여부: Y=0: 0.4773, Y=1: 0.4813 → 차이 0.004로 거의 동일 산단/비산단 비율이 한계기업이나 정상기업이나 비슷.
→ "산단이 망한다"가 아님. 모델이 계획입지여부를 중요하게 쓰는 건 다른 변수들과의 상호작용 때문. 단독으로 보면 차이가 없음.
# =================================


top10 = ['계획입지여부', '자본잠식여부', '대표이사변경여부', '총자산_LOG',
         '매출액영업이익률', 'WC_Stress', '총자본회전율', '총자본증가율', '세전이익률', 'CFO']

print("=== 변수별 Y=0 vs Y=1 평균 비교 ===")
for col in top10:
    y0 = oos[oos['Y']==0][col].mean()
    y1 = oos[oos['Y']==1][col].mean()
    print(f"{col:20s} | Y=0: {y0:.4f} | Y=1: {y1:.4f} | 차이: {y1-y0:.4f}")




# =================================
#  자산분위별 카이제곱/피셔 정확검정
# ===================================

import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

# OOS 데이터 로드 (819개사)
df = pd.read_csv(r"D:\2차현황\260612새로하기\기본데이터스플릿\260612_OOS.csv")

# 자산 4분위 구분
df["자산분위"] = pd.qcut(df["총자산_LOG"], q=4, labels=["소규모","중소","중대","대규모"])

for grp in ["소규모", "중소", "중대", "대규모"]:
    sub = df[df["자산분위"] == grp]
    ct = pd.crosstab(sub["계획입지여부"], sub["Y"])
    ratio = sub.groupby("계획입지여부")["Y"].mean()
    chi2, p_chi2, dof, expected = chi2_contingency(ct)
    fisher_odds, fisher_p = fisher_exact(ct)

# 검정 결과 및 해석은 별도 문의 시 안내


# =============
# 시각화 
# =============

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_pickle(r"D:\2차현황\260612새로하기\기본데이터스플릿\260612_Train.pkl")

ratio = df.groupby('계획입지여부')['Y'].mean()
labels = ['개별입지(0)', '계획입지(1)']
values = ratio.values
colors = ['#a0b4cc', '#1f3f6e']

fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(labels, values, color=colors)

for bar in bars:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
             f'{bar.get_height():.1%}', ha='center', fontsize=11, fontweight='bold')

ax.set_ylabel('한계기업 비율 (Y=1)', fontsize=11)
ax.set_title('입지별 한계기업 비율\n(Train 기준)', fontsize=13, fontweight='bold')
ax.set_ylim(0, max(values) * 1.4)
plt.tight_layout()


 

