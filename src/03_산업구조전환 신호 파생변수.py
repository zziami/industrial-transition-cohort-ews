
# 산단_최종분류 → 4개 그룹으로 분류
def 산단분류(x):
    if x == '0':
        return '비산단'
    elif '노후' in str(x):
        return '노후산단'
    elif '스마트' in str(x):
        return '스마트산단'
    else:
        return '일반+국가산단'

코호트['산단그룹'] = 코호트['산단_최종분류'].astype(str).apply(산단분류)

# 시도별 산단그룹별 집계
산단집계 = 코호트.groupby(['시도명', '산단그룹']).agg(
    기업수=('거래소코드', 'count'),
    한계기업수=('Y', 'sum')
).reset_index()
산단집계['한계기업비율'] = (산단집계['한계기업수'] / 산단집계['기업수'] * 100).round(1)
