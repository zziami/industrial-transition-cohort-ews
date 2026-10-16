import os
import dash
import numpy as np
from dash import dash_table
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma

# ============================================================
# PART 1. 지도용 코호트-위경도 데이터 매칭
# ============================================================
# 회색 → 코호트 미포함 전체 공장 (~208,000개)
# 노란색 → 코호트 Y=0 (ICR<1 진입했다가 3년 연속 안 된 기업, 8,496개)
# 빨간색 → 코호트 Y=1 (ICR<1 3년 연속 → 한계기업 확정, 3,379개)
# 한국은행/KDB 공식 한계기업 정의 기준

코호트_필요컬럼 = 코호트[['거래소코드', '시도명', 'Y', '산단_최종분류']]
df = 위경도.merge(코호트_필요컬럼, on='거래소코드', how='left')
print(df.shape)
print(f"null 체크 - 시도명: {df['시도명'].isna().sum()}, Y: {df['Y'].isna().sum()}")


# ============================================================
# PART 2. RAG 벡터DB 구축 (최초 1회 실행)
# ============================================================
DOC_DIR = r""
DB_DIR  = r""

files = [
    (f"{DOC_DIR}\\ _KDB_ ),
    (f"{DOC_DIR}\\ _사업재편_종합지원가이드 "),
    (f"{DOC_DIR}\\ _중기부_  "),
    (f"{DOC_DIR}\\ _산업부 ),
]

docs = []
for path, ftype in files:
    print(f"로드 중: {path}")
    if ftype == "pdf":
        loader = PyPDFLoader(path)
    else:
        loader = UnstructuredHTMLLoader(path)
    docs.extend(loader.load())
    print(f"  → {len(docs)}개 페이지 누적")

print(f"\n전체 문서 수: {len(docs)}")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,   # 청크숫자 500일때 벡터 132개로 너무 적어서 줄임
    chunk_overlap=30,
    length_function=len,
)
chunks = splitter.split_documents(docs)
print(f"청크 수: {len(chunks)}")

print("\nChromaDB 저장 중...")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_DIR,
)
print(f"저장 완료! 경로: {DB_DIR}")
print(f"총 벡터 수: {vectordb._collection.count()}")


# ============================================================
# PART 3. Dash 대시보드 실행 (벡터DB 재사용)
# ============================================================


# ── RAG 초기화 ──────────────────────────────────
DB_DIR =  
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def search_policy(시도명):
    query = f"{시도명} 지역 한계기업 또는 제조업 기업이 활용할 수 있는 정책금융 지원사업을 알려줘"
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    context = "\n".join([d.page_content for d in docs])
    result = llm.invoke(f"다음 정책 문서를 참고해서 질문에 답해줘:\n{context}\n\n질문: {query}")
    return result.content



# ── 데이터 로드 ─────────────────────────────────
with open(r'           , encoding='utf-8') as f:
    geojson = json.load(f)

산단집계_df   =  
시도별_전체공장 =  
코호트_지도_df  = 
코호트_연도_df  = 
                                usecols=['회계년도', '시도명', 'Y'])



# ── OOS 검증 코호트 (앱용 파일) ───────────────────
OOS_FILE = r'파일명'
THRESH = 0.480

oos = pd.read_excel(OOS_FILE, dtype={'거래소코드': str})
print(oos.columns.tolist())
oos['점수'] = (oos['xgb_prob'] * 100).round(1)
oos['경보'] = oos['xgb_prob'] >= THRESH
_y, _t1, _t2 = oos['y_actual'], oos['icr_lt1_2024'], oos['icr_lt1_2025']
oos['결과'] = np.select([_y == 1, _t1.isna(), (_t1 == 1) & _t2.isna()],
                      ['지속', '자료 미공개분', '진입 주의'], default='회복')
oos['판정'] = np.select([oos['경보'] & (_y == 1), ~oos['경보'] & (_y == 1), oos['경보'] & (_y == 0)],
                      ['적중', '놓침', '오경보'], default='표시 없음')



시도_df =  파일명
시도_df = 시도_df.drop(columns=['시도']).rename(columns={'시도_GeoJSON': '시도'})
시도_df['한계기업비율'] = (시도_df['한계기업수'] / 시도_df['전체기업수'] * 100).round(1)



# ── 색상 ────────────────────────────────────────
BG     = '#0a0e1a'
CARD   = '#0f1528'
BORDER = '#1e2d4a'
TEXT   = '#e0e8f0'
TEXT2  = '#8899aa'
BLUE   = '#00b4d8'
GREEN  = '#00f5a0'
ORANGE = '#ff9f43'
RED    = '#ff4757'

GEO_매핑 = {
    '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
    '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
    '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
    '강원도': '강원', '충청북도': '충북', '충청남도': '충남',
    '전라북도': '전북', '전라남도': '전남', '경상북도': '경북',
    '경상남도': '경남', '제주특별자치도': '제주'
}


# ── 앱 ──────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css'
])


# ── 헬퍼 ────────────────────────────────────────
def kpi_card(title, value, color=BLUE):
    return html.Div([
        html.P(title, style={'fontSize': '11px', 'color': TEXT2, 'marginBottom': '4px'}),
        html.H4(value, style={'fontSize': '18px', 'fontWeight': '700', 'color': color, 'margin': '0'}),
    ], style={'background': CARD, 'border': f'1px solid {BORDER}',
              'borderRadius': '8px', 'padding': '12px'})

def card_header(text, id=None):
    style = {'padding': '8px 12px', 'fontSize': '13px', 'fontWeight': '700',
             'color': TEXT, 'borderBottom': f'1px solid {BORDER}'}
    if id:
        return html.Div(id=id, children=text, style=style)
    return html.Div(text, style=style)


def card_wrap(children, mb=True, flex=None):
    style = {
        'background': CARD, 'border': f'1px solid {BORDER}',
        'borderRadius': '8px', 'overflow': 'hidden',
        'marginBottom': '12px' if mb else '0'
    }
    if flex:
        style['flex'] = flex
    return html.Div(children, style=style)  

RESULT_COLORS = {'지속': RED, '진입 주의': ORANGE, '자료 미공개분': TEXT2, '회복': GREEN}


def oos_subset(clickData):
    """시도를 클릭했으면 그 시도의 OOS 코호트, 아니면 전체"""
    if not clickData:
        return oos, '전국'
    geo = clickData['points'][0]['location']
    sido = GEO_매핑.get(geo, geo)
    return oos[oos['시도'] == sido], sido


def fmt_icr(v):
    return '—' if pd.isna(v) else f'{v:.2f}'


def _txt(v):
    return '—' if pd.isna(v) else str(v)


def mini_icr_fig(r):
    """카드 안의 작은 ICR 추이 그래프 (2023~2025, 기준 1.0)"""
    years = [2023, 2024, 2025]
    vals = [r['icr_2023'], r['icr_2024'], r['icr_2025']]
    have = [v for v in vals if pd.notna(v)]
    lo, hi = min(have + [1]), max(have + [1])
    pad = (hi - lo) * 0.3 or 0.5
    fig = go.Figure()
    fig.add_hline(y=1, line_dash='dot', line_color='#ff8a95', line_width=1)
    for i in range(2):
        a, b = vals[i], vals[i + 1]
        if pd.notna(a) and pd.notna(b):
            danger = b < 1
            fig.add_trace(go.Scatter(
                x=years[i:i + 2], y=[a, b], mode='lines', showlegend=False, hoverinfo='skip',
                line=dict(color=RED if danger else BLUE, width=2.5, dash='solid' if danger else 'dash')))
    pts = [(y, v) for y, v in zip(years, vals) if pd.notna(v)]
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pts], y=[p[1] for p in pts], mode='markers+text', showlegend=False,
        text=[f'{p[1]:.2f}' for p in pts], textposition='top center', hoverinfo='skip',
        marker=dict(size=8, color=[RED if p[1] < 1 else BLUE for p in pts]),
        textfont=dict(color=TEXT, size=10)))
    for y, v in zip(years, vals):
        if pd.isna(v):
            fig.add_annotation(x=y, y=1, text='자료 없음', showarrow=False, yshift=-14,
                               font=dict(color=TEXT2, size=10))
    fig.update_layout(
        margin=dict(t=10, b=22, l=8, r=8),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickmode='array', tickvals=years, range=[2022.6, 2025.4], color=TEXT2,
                   showgrid=False, fixedrange=True, tickfont=dict(size=10)),
        yaxis=dict(visible=False, range=[lo - pad, hi + pad * 1.6], fixedrange=True),
    )
    return fig


def icr_card(r):
    """기업별 ICR 추이 카드 한 장"""
    last_y, last_v = next(((y, r[c]) for y, c in ((2025, 'icr_2025'), (2024, 'icr_2024'), (2023, 'icr_2023'))
                           if pd.notna(r[c])), (None, None))
    alarm_color = ORANGE if r['경보'] else TEXT2
    pill = {'fontSize': '11px', 'borderRadius': '10px', 'padding': '2px 8px', 'whiteSpace': 'nowrap'}
    return html.Div([
        html.Div([
            html.Div(r['회사명'], style={'fontSize': '14px', 'fontWeight': '700', 'color': TEXT,
                                       'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis'}),
            html.Span(f"{r['점수']:.1f}점", style={**pill, 'color': alarm_color, 'border': f'1px solid {alarm_color}'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'gap': '8px'}),
        html.Div(f"{_txt(r['입지유형'])} · {_txt(r['시도'])} {_txt(r['시군구'])} · {_txt(r['산업명'])}",
                 style={'fontSize': '11px', 'color': TEXT2, 'margin': '2px 0 4px', 'whiteSpace': 'nowrap',
                        'overflow': 'hidden', 'textOverflow': 'ellipsis'}),
        dcc.Graph(figure=mini_icr_fig(r), config={'displayModeBar': False, 'staticPlot': True},
                  style={'height': '150px'}),
        html.Div([
            html.Span(f'최근 ICR ({last_y})', style={'fontSize': '12px', 'color': TEXT2}),
            html.Span(f'{last_v:.2f}배', style={'fontSize': '16px', 'fontWeight': '700',
                                               'color': RED if last_v < 1 else BLUE}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                  'borderTop': f'1px solid {BORDER}', 'paddingTop': '6px'}),
        html.Div(html.Span(r['결과'], style={**pill, 'color': RESULT_COLORS[r['결과']],
                                           'border': f"1px solid {RESULT_COLORS[r['결과']]}"}),
                 style={'marginTop': '6px'}),
    ], style={'background': '#111827', 'border': f'1px solid {BORDER}', 'borderRadius': '8px',
              'padding': '10px', 'minWidth': '0'})


# ── 레이아웃 ────────────────────────────────────
app.layout = html.Div([

    # 타이틀
    html.Div([
        html.Span('한계기업 조기예측',
                  style={'fontSize': '25px', 'fontWeight': '700', 'color': TEXT}),
        html.Span(' | 산업구조전환기 비상장 외감 제조업 현황판',
                  style={'fontSize': '18px', 'color': TEXT2, 'marginLeft': '10px'}),
    ], style={'padding': '14px 20px', 'borderBottom': f'1px solid {BORDER}'}),

    html.Div([

        # ── 좌측 (flex 7) ────────────────────────
        html.Div([

            # KPI 4개
            html.Div([
                html.Div(kpi_card('전체 기업수 (2010~2025)', '219,835개', TEXT), style={'flex': '1'}),
                html.Div(kpi_card('한계기업수', '3,379개 (전체대비 1.5%)', RED), style={'flex': '1'}),
                html.Div(kpi_card('계획입지 (산단)', '85,956개', BLUE), style={'flex': '1'}),
                html.Div(kpi_card('개별입지 (비산단)', '133,879개', ORANGE), style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '12px'}),
                        # OOS 검증 코호트 KPI (콜백에서 채움)10/14추가
            html.Div(id='oos-kpi', style={'marginBottom': '12px'}),





            # 지도 두 개 나란히
            html.Div([
                card_wrap([
                    card_header('전국 한계기업 분포'),
                    dcc.Graph(id='choropleth-map', style={'height': '550px'},
                              config={'displayModeBar': False})
                ], mb=False,flex='1'),
                card_wrap([
                    card_header('시도를 클릭하세요', id='detail-map-title'),
                    dcc.Graph(id='detail-map', style={'height': '550px'},
                              config={'displayModeBar': False})
                ], mb=False,flex='1'),
            ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '12px'}),

            # 정책 추천 (좌측 하단)
            card_wrap([
                card_header('정책 추천'),
                html.Div(id='policy-content', children=[
                    html.P('시도를 클릭하면 관련 정책이 표시됩니다.',
                           style={'color': TEXT2, 'fontSize': '13px',
                                  'marginTop': '20px', 'textAlign': 'center'})
                ], style={'padding': '12px'})
            ]),

        ], style={'flex': '7', 'marginRight': '12px'}),

        # ── 우측 (flex 5) ────────────────────────
        html.Div([

            # 상세패널 (도넛 + KPI 2x2)
            card_wrap([
                card_header('시도를 클릭하세요', id='panel-title'),
                html.Div(id='panel-content', children=[
                    html.P('지도에서 시도를 클릭하면 상세 정보가 표시됩니다.',
                           style={'color': TEXT2, 'fontSize': '13px',
                                  'marginTop': '40px', 'textAlign': 'center'})
                ], style={'background': CARD,'padding': '12px','flex': '1', 'marginBottom': '120px'})
            ]),

            # 연도별 막대차트 (우측 하단)
            card_wrap([
                card_header('연도별 한계기업 추이', id='risk-title'),
                dcc.Graph(id='risk-chart', style={'height': '500px'},
                          config={'displayModeBar': False})
            ], mb=False),

        ], style={'flex': '5','display': 'flex', 'flexDirection': 'column'}),

    ], style={'display': 'flex', 'padding': '12px', 'alignItems': 'flex-start'}),


     
    # ── 하단: 기업별 ICR 추이 카드 + OOS 코호트 기업 목록 ──10/15추가
    html.Div([
        card_wrap([
            card_header('기업별 이자보상배율(ICR) 추이', id='oos-cards-title'),
            html.P('분홍 점선: 경고 기준(ICR 1.0) · 빨간 실선: 1 미만 구간 · 파란 점선: 1 이상 구간',
                   style={'fontSize': '11px', 'color': TEXT2, 'margin': '8px 12px 0'}),
            html.Div(id='oos-cards', style={'display': 'grid',
                                            'gridTemplateColumns': 'repeat(4, minmax(0, 1fr))',
                                            'gap': '12px', 'padding': '12px'}),
        ]),
        card_wrap([
            card_header('필터링 기업 목록 (OOS 2023 검증 코호트)', id='oos-table-title'),
            html.Div(dash_table.DataTable(
                id='oos-table',
                columns=[
                    {'name': '기업명', 'id': '기업명'}, {'name': '산업군', 'id': '산업군'},
                    {'name': '입지유형', 'id': '입지유형'}, {'name': '시도', 'id': '시도'},
                    {'name': '시군구', 'id': '시군구'},
                    {'name': '위험 점수', 'id': '위험 점수', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': '경보', 'id': '경보'}, {'name': '결과 분류', 'id': '결과 분류'},
                    {'name': '판정', 'id': '판정'},
                    {'name': '진입연도 ICR', 'id': '진입연도 ICR', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                ],
                data=[], page_size=12, sort_action='native',
                style_header={'backgroundColor': '#111827', 'color': TEXT, 'fontWeight': '700',
                              'border': f'1px solid {BORDER}'},
                style_cell={'backgroundColor': CARD, 'color': TEXT, 'border': f'1px solid {BORDER}',
                            'fontSize': '12px', 'padding': '6px', 'textAlign': 'left'},
                style_data_conditional=[
                    {'if': {'filter_query': '{경보} = "주의"', 'column_id': '경보'},
                     'color': ORANGE, 'fontWeight': '700'},
                    {'if': {'filter_query': '{결과 분류} = "지속"', 'column_id': '결과 분류'},
                     'color': RED, 'fontWeight': '700'},
                    {'if': {'filter_query': '{결과 분류} = "진입 주의"', 'column_id': '결과 분류'},
                     'color': ORANGE},
                    {'if': {'filter_query': '{결과 분류} = "회복"', 'column_id': '결과 분류'},
                     'color': GREEN},
                ],
            ), style={'padding': '12px'}),
        ], mb=False),
    ], style={'padding': '0 12px 12px 12px'}),
], style={'background': CARD,'backgroundColor': BG, 'minHeight': '100vh',
          'fontFamily': 'Pretendard, sans-serif', 'color': TEXT, 'overflowX': 'hidden','flex': '1',
          'paddingLeft': 'max(0px, calc((100vw - 1400px) / 2))',
          'paddingRight': 'max(0px, calc((100vw - 1400px) / 2))'})



# ── 콜백: 지도 렌더링 ────────────────────────────
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('choropleth-map', 'id')
)
def render_map(_):
    fig = px.choropleth_map(
        시도_df, geojson=geojson, locations='시도',
        featureidkey='properties.name', color='한계기업비율',
        color_continuous_scale=[[0, '#1e2d4a'], [1, '#00b4d8']],
        range_color=[10, 40],
        hover_data={'전체기업수': True, '한계기업수': True, '한계기업비율': True},
        labels={'한계기업비율': '한계기업비율(%)'},
        zoom=6.5, center={'lat': 36.5, 'lon': 127.8},
    )
    fig.update_layout(
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        paper_bgcolor='rgba(0,0,0,0)',
        coloraxis_colorbar={'title': '한계기업<br>비율(%)', 'thickness': 10,
                            'len': 0.5, 'tickfont': {'color': TEXT}},
        map=dict(style='carto-darkmatter'),
    )
    return fig


# ── 콜백: 시도 클릭 → 상세 패널 ──────────────────
@app.callback(
    Output('panel-title', 'children'),
    Output('panel-content', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_panel(clickData):
    if not clickData:
        return '시도를 클릭하세요', html.P(
            '지도에서 시도를 클릭하면 상세 정보가 표시됩니다.',
            style={'color': TEXT2, 'fontSize': '13px', 'marginTop': '40px', 'textAlign': 'center'})

    시도명 = clickData['points'][0]['location']
    시도명_단순 = GEO_매핑.get(시도명, 시도명)
    row = 시도_df[시도_df['시도'] == 시도명].iloc[0]
    시도_산단 = 산단집계_df[산단집계_df['시도명'] == 시도명_단순]
    전체공장_row = 시도별_전체공장[시도별_전체공장['시도'] == 시도명_단순]
    전체공장수 = int(전체공장_row.iloc[0]['전체공장수']) if len(전체공장_row) > 0 else int(row['전체기업수'])
    한계기업비율_전체 = round(row['한계기업수'] / 전체공장수 * 100, 1)

    def get_val(그룹):
        r = 시도_산단[시도_산단['산단그룹'] == 그룹]['한계기업비율'].values
        return float(r[0]) if len(r) > 0 else 0

    노후_v = get_val('노후산단')
    스마트_v = get_val('스마트산단')
    일반_v = get_val('일반+국가산단')
    비산단_v = get_val('비산단')

    도넛_fig = go.Figure(go.Pie(
        values=[노후_v, 스마트_v, 일반_v, 비산단_v],
        labels=['노후산단', '스마트산단', '일반+국가산단', '비산단'],
        hole=0.65,
        marker_colors=[RED, BLUE, GREEN, ORANGE],
        textinfo='none',
    ))
    도넛_fig.update_layout(
        margin=dict(t=10, b=10, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(font=dict(color=TEXT, size=11), bgcolor='rgba(0,0,0,0)',
                    orientation='v', x=1, y=0.1),
        annotations=[dict(text=f'{시도명_단순}<br>{한계기업비율_전체}%',
                  x=0.5, y=0.5, font_size=13, showarrow=False,
                  font=dict(color=TEXT))]
    )

    kpi_style = {'background': '#111827', 'border': f'1px solid {BORDER}',
                 'borderRadius': '6px', 'padding': '10px', 'flex': '1'}

    content = html.Div([
        # 도넛 + KPI 2x2 나란히
        html.Div([
            # 도넛
            html.Div([
                dcc.Graph(figure=도넛_fig, style={'height': '300px'},
                          config={'displayModeBar': False})
            ], style={'flex': '1'}),
            # KPI 2x2
            html.Div([
                html.Div([
                    html.Div([
                        html.P('전체 기업수', style={'fontSize': '11px', 'color': TEXT2, 'margin': '0'}),
                        html.P(f"{전체공장수:,}개",
                               style={'fontSize': '16px', 'fontWeight': '700', 'color': TEXT, 'margin': '0'}),
                    ], style=kpi_style),
                    html.Div([
                        html.P('산단수', style={'fontSize': '11px', 'color': TEXT2, 'margin': '0'}),
                        html.P(f"{row['산단수']}개",
                               style={'fontSize': '16px', 'fontWeight': '700', 'color': BLUE, 'margin': '0'}),
                    ], style=kpi_style),
                ], style={'display': 'flex', 'gap': '8px', 'marginBottom': '8px'}),
                html.Div([
                    html.Div([
                        html.P('한계기업수', style={'fontSize': '11px', 'color': TEXT2, 'margin': '0'}),
                        html.P(f"{row['한계기업수']:,}개",
                               style={'fontSize': '16px', 'fontWeight': '700', 'color': RED, 'margin': '0'}),
                    ], style=kpi_style),
                    html.Div([
                        html.P('한계기업비율', style={'fontSize': '11px', 'color': TEXT2, 'margin': '0'}),
                        html.P(f"{한계기업비율_전체}%",
                               style={'fontSize': '16px', 'fontWeight': '700', 'color': ORANGE, 'margin': '0'}),
                    ], style=kpi_style),
                ], style={'display': 'flex', 'gap': '8px'}),
            ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center'}),
        ], style={'display': 'flex', 'gap': '12px', 'padding': '12px'}),
    ])

    return f'{시도명_단순} 상세 현황', content

# ── 콜백: 정책 추천 ──────────────────────────────
@app.callback(
    Output('policy-content', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_policy(clickData):
    if not clickData:
        return html.P('시도를 클릭하면 관련 정책이 표시됩니다.',
                      style={'color': TEXT2, 'fontSize': '13px',
                             'marginTop': '20px', 'textAlign': 'center'})

    시도명 = clickData['points'][0]['location']
    시도명_단순 = GEO_매핑.get(시도명, 시도명)
    결과 = search_policy(시도명_단순)

    return html.Div([
        html.Div([
            html.A('🔗 KDB 산업은행', href='https://www.kdb.co.kr', target='_blank',
                   style={'fontSize': '13px', 'fontWeight': '700', 'color': BLUE,
                          'marginRight': '16px', 'textDecoration': 'none'}),
            html.A('🔗 대한상공회의소', href='https://www.korcham.net', target='_blank',
                   style={'fontSize': '13px', 'fontWeight': '700', 'color': BLUE,
                          'marginRight': '16px', 'textDecoration': 'none'}),
            html.A('🔗 산업통상자원부', href='https://www.motie.go.kr', target='_blank',
                   style={'fontSize': '13px', 'fontWeight': '700', 'color': BLUE,
                          'marginRight': '16px', 'textDecoration': 'none'}),
            html.A('🔗 중소벤처기업부', href='https://www.mss.go.kr', target='_blank',
                   style={'fontSize': '13px', 'fontWeight': '700', 'color': BLUE,
                          'textDecoration': 'none'}),
        ], style={'marginBottom': '10px'}),
        html.Div(결과, style={
            'fontSize': '13px', 'color': TEXT2, 'lineHeight': '1.8',
            'maxHeight': '320px','whiteSpace': 'pre-wrap', 'border': f'1px solid {BORDER}',
            'overflowY': 'auto','padding': '10px', 'borderRadius': '6px', 'background': '#111827'
        })
    ])



 
# ── 콜백: 우측 하단 차트 (클릭 전: 연도별 추이 / 클릭 후: 코호트 위험 점수) ──10/14 변경추가
@app.callback(
    Output('risk-chart', 'figure'),
    Output('risk-title', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_risk_chart(clickData):
    common = dict(
        margin={'r': 10, 't': 30, 'l': 10, 'b': 10},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT, size=11), title_font=dict(color=TEXT, size=12),
    )
    if clickData:
        sub, 시도 = oos_subset(clickData)
        top = sub.sort_values('점수', ascending=False).head(20)
        if top.empty:
            fig = go.Figure()
            fig.add_annotation(text=f'{시도}에는 OOS 코호트 기업이 없습니다', showarrow=False,
                               font=dict(color=TEXT2, size=13))
            fig.update_layout(**common, xaxis_visible=False, yaxis_visible=False)
            return fig, f'{시도} 코호트 기업 위험 점수'
        fig = px.bar(top, x='회사명', y='점수', color='결과', color_discrete_map=RESULT_COLORS,
                     hover_data={'경보': True, '판정': True, 'icr_2023': ':.2f'},
                     labels={'점수': '위험 점수', '회사명': ''})
        fig.add_hline(y=THRESH * 100, line_dash='dash', line_color=RED,
                      annotation_text='모델 임계값 48.0', annotation_position='top left',
                      annotation_font_color=TEXT2)
        fig.update_layout(
            **common,
            yaxis=dict(range=[0, 100], gridcolor=BORDER, color=TEXT2),
            xaxis=dict(tickangle=-45, color=TEXT2),
            legend=dict(title='', font=dict(color=TEXT, size=10), orientation='h', y=1.12),
        )
        fig.update_xaxes(categoryorder='array', categoryarray=top['회사명'].tolist())
        return fig, f'{시도} 코호트 기업 위험 점수 (상위 {len(top)}개 / 전체 {len(sub):,}개)'

    df = 코호트_연도_df.groupby('회계년도')['Y'].sum().reset_index()
    fig = px.bar(df, x='회계년도', y='Y',
                 labels={'회계년도': '연도', 'Y': '한계기업 진입수'},
                 title='전국 연도별 한계기업 진입수', color_discrete_sequence=[BLUE])
    fig.update_layout(
        **common,
        xaxis=dict(dtick=1, tickangle=-45, gridcolor=BORDER, color=TEXT2),
        yaxis=dict(gridcolor=BORDER, color=TEXT2),
    )
    return fig, '연도별 한계기업 추이'




# ── 콜백: 확대지도 ───────────────────────────────
@app.callback(
    Output('detail-map', 'figure'),
    Output('detail-map-title', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_detail_map(clickData):
    if not clickData:
        return go.Figure().update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            map=dict(style='carto-darkmatter', center=dict(lat=36.5, lon=127.8), zoom=5)
        ), '시도를 클릭하세요'

    시도명_geo = clickData['points'][0]['location']
    시도명 = GEO_매핑.get(시도명_geo, 시도명_geo)
    시도_data = 코호트_지도_df[코호트_지도_df['시도명'] == 시도명]
    center_lat = 시도_data['lat'].mean()
    center_lon = 시도_data['lon'].mean()

    fig = go.Figure()
    정상 = 시도_data[시도_data['Y'] == 0]
    fig.add_trace(go.Scattermap(
        lat=정상['lat'], lon=정상['lon'], mode='markers',
        marker=dict(size=6, color=GREEN, opacity=0.5), name='정상기업'
    ))
    한계 = 시도_data[시도_data['Y'] == 1]
    fig.add_trace(go.Scattermap(
        lat=한계['lat'], lon=한계['lon'], mode='markers',
        marker=dict(size=8, color=RED, opacity=0.8), name='한계기업'
    ))
    fig.update_layout(
        map=dict(style='carto-darkmatter',
                 center=dict(lat=center_lat, lon=center_lon), zoom=8),
        margin=dict(r=0, t=0, l=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0.01, y=0.99, font=dict(color=TEXT, size=11),
                    bgcolor='rgba(0,0,0,0)'),
    )
    return fig, f'{시도명} 기업 분포'




# ── 콜백: OOS 코호트 KPI ─────────────────────────
@app.callback(
    Output('oos-kpi', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_oos_kpi(clickData):
    sub, 시도 = oos_subset(clickData)
    n = len(sub)
    alarm = int(sub['경보'].sum())
    persist = int((sub['y_actual'] == 1).sum())
    hit = int((sub['판정'] == '적중').sum())
    pct = lambda a: f'{a / n * 100:.1f}%' if n else '—'
    detect = f'{hit / persist * 100:.1f}%' if persist else '—'

    def chip(label, color):
        c = int((sub['판정'] == label).sum())
        return html.Span(f'{label} {c:,}개', style={
            'fontSize': '12px', 'color': color, 'border': f'1px solid {BORDER}',
            'borderRadius': '12px', 'padding': '3px 10px', 'marginRight': '8px'})

    return html.Div([
        html.P(f'OOS 2023 검증 코호트 · {시도} · XGBoost(SMOTE) · 모델 임계값 48.0 (OOS 성능 기준으로 조정)',
               style={'fontSize': '12px', 'color': TEXT2, 'margin': '0 0 6px 2px'}),
        html.Div([
            html.Div(kpi_card('코호트 기업 수', f'{n:,}개', TEXT), style={'flex': '1'}),
            html.Div(kpi_card("경보 '주의' 기업", f'{alarm:,}개 ({pct(alarm)})', ORANGE), style={'flex': '1'}),
            html.Div(kpi_card('실제 한계기업 지속', f'{persist:,}개 ({pct(persist)})', RED), style={'flex': '1'}),
            html.Div(kpi_card('탐지율', detect, BLUE), style={'flex': '1'}),
            html.Div(kpi_card('진입연도(2023) ICR 중앙값', f"{fmt_icr(sub['icr_2023'].median())}배", TEXT),
                     style={'flex': '1'}),
        ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '8px'}),
        html.Div([chip('적중', GREEN), chip('놓침', RED), chip('오경보', ORANGE), chip('표시 없음', TEXT2)]),
    ])


# ── 콜백: 필터링 기업 목록 ───────────────────────
@app.callback(
    Output('oos-table', 'data'),
    Output('oos-table-title', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_oos_table(clickData):
    sub, 시도 = oos_subset(clickData)
    sub = sub.sort_values('점수', ascending=False)
    rows = pd.DataFrame({
        'id': sub['거래소코드'], '기업명': sub['회사명'], '산업군': sub['산업명'],
        '입지유형': sub['입지유형'], '시도': sub['시도'], '시군구': sub['시군구'],
        '위험 점수': sub['점수'], '경보': np.where(sub['경보'], '주의', '해당 없음'),
        '결과 분류': sub['결과'], '판정': sub['판정'], '진입연도 ICR': sub['icr_2023'].round(2),
    })
    rows = rows.astype(object).where(rows.notna(), None)
    return rows.to_dict('records'), f'필터링 기업 목록 — {시도} ({len(sub):,}개)'


# ── 콜백: 기업별 ICR 추이 카드 (위험 점수 상위 8개) ── 10/15
@app.callback(
    Output('oos-cards', 'children'),
    Output('oos-cards-title', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_oos_cards(clickData):
    sub, 시도 = oos_subset(clickData)
    top = sub.sort_values('점수', ascending=False).head(8)
    title = f'기업별 이자보상배율(ICR) 추이 — {시도} 위험 점수 상위 {len(top)}개'
    if top.empty:
        return html.P(f'{시도}에는 OOS 코호트 기업이 없습니다',
                      style={'color': TEXT2, 'fontSize': '13px', 'gridColumn': '1 / -1',
                             'textAlign': 'center', 'margin': '20px 0'}), title
    return [icr_card(r) for _, r in top.iterrows()], title


if __name__ == '__main__':
    app.run(debug=True)
