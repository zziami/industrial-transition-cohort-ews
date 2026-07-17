




import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma





# ── RAG 초기화 ─────────────────────────────────
DB_DIR = r"D:\2차현황\대시보드\chroma_db"
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# qa_chain = RetrievalQA.from_chain_type(
#     llm=llm,
#     retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
#)

# def search_policy(시도명):
#     query = f"{시도명} 지역 한계기업 또는 제조업 기업이 활용할 수 있는 정책금융 지원사업을 알려줘"
#     result = qa_chain.invoke({"query": query})
#     return result["result"]
def search_policy(시도명):
    query = f"{시도명} 지역 한계기업 또는 제조업 기업이 활용할 수 있는 정책금융 지원사업을 알려줘"
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    context = "\n".join([d.page_content for d in docs])
    result = llm.invoke(f"다음 정책 문서를 참고해서 질문에 답해줘:\n{context}\n\n질문: {query}")
    return result.content



# ── 데이터 로드 백터파일 ────────────────────────────────
with open(r'', encoding='utf-8') as f:
    geojson = json.load(f)

산단집계_df = pd.read_excel(r'')
시도별_전체공장 = pd.read_excel(r'')

# ── 더미 데이터 (geocoding 완료 후 교체) ──────────
시도_더미 = pd.read_excel(r'')
시도_더미 = 시도_더미.drop(columns=['시도']).rename(columns={'시도_GeoJSON': '시도'})
시도_더미['한계기업비율'] = (시도_더미['한계기업수'] / 시도_더미['전체기업수'] * 100).round(1)


# ── 문서 경로 ──────────────────────────────────
DOC_DIR = r""
DB_DIR  = r""

files = [
    (f"{DOC_DIR}\\20260607_KDB_사업구조전환.pdf",                    "pdf"),
    (f"{DOC_DIR}\\20260607_사업재편_종합지원가이드.pdf",              "pdf"),
    (f"{DOC_DIR}\\20260607_중기부_정책자금융자계획.pdf",              "pdf"),
    (f"{DOC_DIR}\\20260607_산업부_산단_친환경_설비_인프라지원공고.html", "html"),
]

# ── 문서 로드 ──────────────────────────────────
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

# ── 청킹 ───────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,   # 청크숫자 500일때 백터 132개로 너무 적어서 줄임
    chunk_overlap=30,
    length_function=len,
)
chunks = splitter.split_documents(docs)
print(f"청크 수: {len(chunks)}")

# ── 임베딩 + ChromaDB 저장 ─────────────────────
print("\nChromaDB 저장 중...")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_DIR,
)
print(f"저장 완료! 경로: {DB_DIR}")
print(f"총 벡터 수: {vectordb._collection.count()}")





# ── 앱 초기화 ──────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css'
])

# ── 색상 팔레트 ────────────────────────────────
NAVY   = "#0A1B33"
BLUE   = '#2563a8'
LIGHT  = '#e8eef5'
WHITE  = '#ffffff'
ORANGE = '#e67e22'
RED    = '#c0392b'






# ── KPI 카드 컴포넌트 ──────────────────────────
def kpi_card(title, value, color=NAVY):
    return dbc.Card([
        dbc.CardBody([
            html.P(title, style={'fontSize': '15px', 'color': '#555', 'marginBottom': '4px','fontWeight': '600'}),
            html.H4(value, style={'fontSize': '22px', 'fontWeight': '700', 'color': color, 'margin': '0'}),
        ])
    ], style={'borderRadius': '4px', 'border': f'1px solid {LIGHT}', 'padding': '4px'})

# ── 레이아웃 ───────────────────────────────────
app.layout = dbc.Container([

    # 상단 타이틀 바
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span('한계기업 조기예측', style={'fontSize': '25px', 'fontWeight': '700', 'color': WHITE}),
                html.Span(' | 산업구조전환기 비상장 외감 제조업 현황판',
                          style={'fontSize': '14px', 'color': '#aac4e8', 'marginLeft': '10px'}),
            ], style={'padding': '14px 20px', 'background': NAVY})
        ])
    ], className='mb-3'),

    # KPI 카드 행
    dbc.Row([
        dbc.Col(kpi_card('전체 기업수 (2010~2025)', '219,835개'), width=3),
        dbc.Col(kpi_card('한계기업수', '3,379개 (전체기업수 대비 1.5%)', RED), width=3),
        dbc.Col(kpi_card('계획입지 (산단\n국가·일반·농공·스마트)', '85,956개', ORANGE), width=3),
        dbc.Col(kpi_card('개별입지 (비산단)', '133,879개', BLUE), width=3),
    ], className='mb-3'),

#    지도 + 상세 패널
    dbc.Row([


  

        # 좌측 지도
dbc.Col([
    dbc.Row([
        # 전국 지도
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('전국 한계기업 분포', style={'background': NAVY, 'color': WHITE, 'fontSize': '15px', 'fontWeight': '700'}),
                dbc.CardBody([
                    dcc.Graph(id='choropleth-map', style={'height': '650px'},
                              config={'displayModeBar': False})
                ], style={'padding': '8px'})
            ]),
        ], width=6),

        # 시도 확대지도
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(id='detail-map-title', children='시도를 클릭하세요',
                               style={'background': NAVY, 'color': WHITE, 'fontSize': '15px', 'fontWeight': '700'}),
                dbc.CardBody([
                    dcc.Graph(id='detail-map', style={'height': '650px'},
                              config={'displayModeBar': False})
                ], style={'padding': '8px'})
            ]),
        ], width=6),
    ], className='mb-3'),

    # 리스크 차트
    dbc.Card([
        dbc.CardHeader('연도별 한계기업 추이',
                       style={'background': NAVY, 'color': WHITE, 'fontSize': '15px', 'fontWeight': '700'}),
        dbc.CardBody([
            dcc.Graph(id='risk-chart', style={'height': '300px'},
                      config={'displayModeBar': False})
        ], style={'padding': '8px'})
    ]),

], width=7),

        # 우측 패널
        dbc.Col([

            # 우측 상단 상세패널
            dbc.Card([
                dbc.CardHeader(id='panel-title', children='시도를 클릭하세요',
                               style={'background': NAVY, 'color': WHITE, 'fontSize': '20px', 'fontWeight': '700'}),
                dbc.CardBody([
                    html.Div(id='panel-content', children=[
                        html.P('지도에서 시도를 클릭하면 상세 정보가 표시됩니다.',
                               style={'color': '#888', 'fontSize': '13px', 'marginTop': '20px', 'textAlign': 'center'})
                    ])
                ], style={'padding': '12px'})
            ], className='mb-3'),

            # 우측 하단 정책추천
            dbc.Card([
                dbc.CardHeader('정책 추천',
                               style={'background': NAVY, 'color': WHITE, 'fontSize': '20px', 'fontWeight': '700'}),
                dbc.CardBody([
                    html.Div(id='policy-content', children=[
                        html.P('시도를 클릭하면 관련 정책이 표시됩니다.',
                               style={'color': '#888', 'fontSize': '13px', 'marginTop': '20px', 'textAlign': 'center'})
                    ], style={'fontSize': '12px', 'color': '#333', 'lineHeight': '1.8', 'whiteSpace': 'pre-wrap'})
                ], style={'padding': '12px'})
            ]),

        ], width=5),

    ]),
    ], fluid=True, style={'backgroundColor': '#f4f6fa', 'minHeight': '100vh', 'padding': '0','fontFamily': 'Pretendard, sans-serif','overflowX': 'hidden'})


def get_donut_values(시도_산단, 그룹명):
    row = 시도_산단[시도_산단['산단그룹'] == 그룹명]
    if len(row) == 0:
        return [0, 100], '0%'
    비율 = row.iloc[0]['한계기업비율']
    return [비율, 100-비율], f'{비율}%'



# ── 콜백: 지도 렌더링 ──────────────────────────
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('choropleth-map', 'id')
)
def render_map(_):
    fig = px.choropleth_map(
        시도_더미,
        geojson=geojson,
        locations='시도',
        featureidkey='properties.name',
        color='한계기업비율',
        color_continuous_scale='Blues',
        range_color=[10, 40],
        hover_data={'전체기업수': True, '한계기업수': True, '한계기업비율': True, '산단수': True},
        labels={'한계기업비율': '한계기업비율(%)'},
        zoom=5.5,
        center={'lat': 36.5, 'lon': 127.8},
    )
    fig.update_layout(
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        coloraxis_colorbar={'title': '한계기업<br>비율(%)', 'thickness': 12, 'len': 0.6},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig
 
# ── 콜백: 시도 클릭 → 상세 패널 ────────────────
@app.callback(
    Output('panel-title', 'children'),
    Output('panel-content', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_panel(clickData):
    if not clickData:
        return '시도를 클릭하세요', html.P('지도에서 시도를 클릭하면 상세 정보가 표시됩니다.',
                                          style={'color': '#888', 'fontSize': '13px', 'marginTop': '20px', 'textAlign': 'center'})

    시도명 = clickData['points'][0]['location']
    row = 시도_더미[시도_더미['시도'] == 시도명].iloc[0]

    매핑 = {
        '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
        '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
        '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
        '강원도': '강원', '충청북도': '충북', '충청남도': '충남',
        '전라북도': '전북', '전라남도': '전남', '경상북도': '경북',
        '경상남도': '경남', '제주특별자치도': '제주'
    }
    시도명_단순 = 매핑.get(시도명, 시도명)
    시도_산단 = 산단집계_df[산단집계_df['시도명'] == 시도명_단순]

    전체공장_row = 시도별_전체공장[시도별_전체공장['시도'] == 시도명_단순]
    전체공장수 = 전체공장_row.iloc[0]['전체공장수'] if len(전체공장_row) > 0 else row['전체기업수']

    # 도넛차트 데이터 뽑기
    노후_values, 노후_pct = get_donut_values(시도_산단, '노후산단')
    스마트_values, 스마트_pct = get_donut_values(시도_산단, '스마트산단')
    일반_values, 일반_pct = get_donut_values(시도_산단, '일반+국가산단')
    비산단_values, 비산단_pct = get_donut_values(시도_산단, '비산단')
    
    한계기업비율_전체 = round(row['한계기업수'] / 전체공장수 * 100, 1)

    content = html.Div([
        dbc.Row([
            dbc.Col(kpi_card('전체 기업수', f"{전체공장수:,}개"), width=6),
            dbc.Col(kpi_card('산단수', f"{row['산단수']}개", BLUE), width=6),
        ], className='mb-4'),
        dbc.Row([
            dbc.Col(kpi_card('한계기업수', f"{row['한계기업수']:,}개", RED), width=6),
            #dbc.Col(kpi_card('한계기업비율', f"{row['한계기업비율']}%", ORANGE), width=6),
            dbc.Col(kpi_card('한계기업비율', f"{한계기업비율_전체}%", ORANGE), width=6),
        ], className='mb-4'),

        html.Hr(style={'borderColor': "#4E4E4D", 'marginTop': '20px', 'marginBottom': '12px'}),
        html.P('산단 유형별 현황', style={'fontWeight': '900', 'fontSize': '18px', 'color': NAVY, 'marginBottom': '6px', 'marginTop': '30px'}),
        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=go.Figure(go.Pie(
                        values=[30, 70], labels=['한계기업', '정상기업'],
                        hole=0.6, marker_colors=[RED, LIGHT], textinfo='none'
                    )).update_layout(
                        title=dict(text='노후산단', font=dict(size=13), x=0.5),
                        showlegend=False, margin=dict(t=40, b=0, l=0, r=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        annotations=[dict(text=노후_pct, x=0.5, y=0.5, font_size=14, showarrow=False)]
                    ),
                    style={'height': '130px'}, config={'displayModeBar': False}
                )
            ], width=6),
            dbc.Col([
                dcc.Graph(
                    figure=go.Figure(go.Pie(
                        values=[20, 80], labels=['한계기업', '정상기업'],
                        hole=0.6, marker_colors=[RED, LIGHT], textinfo='none'
                    )).update_layout(
                        title=dict(text='스마트산단', font=dict(size=13), x=0.5),
                        showlegend=False, margin=dict(t=40, b=0, l=0, r=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        annotations=[dict(text=스마트_pct, x=0.5, y=0.5, font_size=14, showarrow=False)]
                    ),
                    style={'height': '130px'}, config={'displayModeBar': False}
                )
            ], width=6),
        ], className='mb-2'),
        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    figure=go.Figure(go.Pie(
                        values=[25, 75], labels=['한계기업', '정상기업'],
                        hole=0.6, marker_colors=[RED, LIGHT], textinfo='none'
                    )).update_layout(
                        title=dict(text='일반+국가산단', font=dict(size=13), x=0.5),
                        showlegend=False, margin=dict(t=40, b=0, l=0, r=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        annotations=[dict(text=일반_pct, x=0.5, y=0.5, font_size=14, showarrow=False)]
                    ),
                    style={'height': '130px'}, config={'displayModeBar': False}
                )
            ], width=6),
            dbc.Col([
                dcc.Graph(
                    figure=go.Figure(go.Pie(
                        values=[28, 72], labels=['한계기업', '정상기업'],
                        hole=0.6, marker_colors=[RED, LIGHT], textinfo='none'
                    )).update_layout(
                        title=dict(text='비산단(개별입지)', font=dict(size=13), x=0.5),
                        showlegend=False, margin=dict(t=40, b=0, l=0, r=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        annotations=[dict(text=비산단_pct, x=0.5, y=0.5, font_size=14, showarrow=False)]
                    ),
                    style={'height': '130px'}, config={'displayModeBar': False}
                )
            ], width=6),
        ], className='mb-2'),
    ])

    return f'{시도명} 상세 현황', content 

# ── 콜백: 시도 클릭 → 정책 추천 ────────────────
@app.callback(
    Output('policy-content', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_policy(clickData):
    if not clickData:
        return html.P('시도를 클릭하면 관련 정책이 표시됩니다.',
                    style={'color': '#888', 'fontSize': '13px', 'marginTop': '20px', 'textAlign': 'center'})

    시도명 = clickData['points'][0]['location']
    결과 = search_policy(시도명)

    return html.Div([
        html.Div([
            html.A('🔗 KDB 산업은행(사업구조전환)', 
                   href='https://www.kdb.co.kr',
                   target='_blank',
                   style={'fontSize': '15px', 'fontWeight': '700', 'color': BLUE, 'marginRight': '20px'}),
            html.A('🔗 대한상공회의소(기업지원)', 
                   href='https://www.korcham.net',
                   target='_blank',
                   style={'fontSize': '15px', 'fontWeight': '700', 'color': BLUE, 'marginRight': '20px'}),
            html.A('🔗 산업통상자원부(친환경설비인프라)', 
                   href='https://www.motie.go.kr',
                   target='_blank',
                   style={'fontSize': '15px', 'fontWeight': '700', 'color': BLUE, 'marginRight': '20px'}),
            html.A('🔗 중소벤처기업부(정책자금융자계획)', 
                   href='https://www.mss.go.kr',
                   target='_blank',
                   style={'fontSize': '15px', 'fontWeight': '700', 'color': BLUE}),
        ], style={'marginBottom': '12px'}),
        html.Div(
            결과,
            style={
                'fontSize': '15px',
                'color': '#333',
                'lineHeight': '1.8',
                'whiteSpace': 'pre-wrap',
                'border': '1px solid #e0e0d8',
                'padding': '8px',
                'borderRadius': '4px',
                'background': '#fafaf8'
            }
        ),
    ])
# ── 전역 데이터: 연도별 추이용 ─────────────────
코호트_df = pd.read_excel(r'D:\2차현황\대시보드\20260606_코호트_정제완료.xlsx',
                        usecols=['회계년도', '시도명', 'Y'])

# ── 콜백: 연도별 한계기업 추이 차트 ──────────────
@app.callback(
    Output('risk-chart', 'figure'),
    Input('choropleth-map', 'clickData')
)
def update_risk_chart(clickData):
    if not clickData:
        # 전국 기본 차트
        df = 코호트_df.groupby('회계년도')['Y'].sum().reset_index()
        title = '전국 연도별 한계기업 진입수'
    else:
        시도명_geo = clickData['points'][0]['location']
        # GeoJSON 시도명 → 우리 데이터 시도명 변환
        매핑 = {
            '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
            '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
            '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
            '강원도': '강원', '충청북도': '충북', '충청남도': '충남',
            '전라북도': '전북', '전라남도': '전남', '경상북도': '경북',
            '경상남도': '경남', '제주특별자치도': '제주'
        }
        시도명 = 매핑.get(시도명_geo, 시도명_geo)
        df = 코호트_df[코호트_df['시도명'] == 시도명].groupby('회계년도')['Y'].sum().reset_index()
        title = f'{시도명} 연도별 한계기업 진입수'

    fig = px.line(
        df,
        x='회계년도',
        y='Y',
        markers=True,
        labels={'회계년도': '연도', 'Y': '한계기업 진입수'},
        title=title,
    )
    fig.update_traces(line_color=NAVY, marker_color=RED)
    fig.update_layout(
        margin={'r': 10, 't': 40, 'l': 10, 'b': 10},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(dtick=1, tickangle=-45),
        yaxis_title='한계기업 진입수',
        xaxis_title='연도',
        font=dict(size=11),
    )
    return fig

# ── 콜백: 시도 클릭 → 확대지도 ──────────────────
@app.callback(
    Output('detail-map', 'figure'),
    Output('detail-map-title', 'children'),
    Input('choropleth-map', 'clickData')
)
def update_detail_map(clickData):
    if not clickData:
        return go.Figure(), '시도를 클릭하세요'

    시도명_geo = clickData['points'][0]['location']
    매핑 = {
        '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
        '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
        '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
        '강원도': '강원', '충청북도': '충북', '충청남도': '충남',
        '전라북도': '전북', '전라남도': '전남', '경상북도': '경북',
        '경상남도': '경남', '제주특별자치도': '제주'
    }
    시도명 = 매핑.get(시도명_geo, 시도명_geo)

    # 코호트 데이터 로드
    코호트_지도 = pd.read_excel(r'D:\2차현황\대시보드\20260608_코호트_위경도_완성.xlsx')
    시도_df = 코호트_지도[코호트_지도['시도명'] == 시도명]

    # 중심좌표
    center_lat = 시도_df['lat'].mean()
    center_lon = 시도_df['lon'].mean()

    fig = go.Figure()

    # 회색 - 정상기업 (Y=0)
    정상 = 시도_df[시도_df['Y'] == 0]
    fig.add_trace(go.Scattermap(
        lat=정상['lat'], lon=정상['lon'],
        mode='markers',
        marker=dict(size=6, color='gray', opacity=0.5),
        name='정상기업'
    ))

    # 빨강 - 한계기업 (Y=1)
    한계 = 시도_df[시도_df['Y'] == 1]
    fig.add_trace(go.Scattermap(
        lat=한계['lat'], lon=한계['lon'],
        mode='markers',
        marker=dict(size=8, color='red', opacity=0.8),
        name='한계기업'
    ))

    fig.update_layout(
        map=dict(
            style='carto-positron',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=8
        ),
        margin=dict(r=0, t=0, l=0, b=0),
        legend=dict(x=0.01, y=0.99),
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig, f'{시도명} 기업 분포'


if __name__ == '__main__':
    app.run(debug=True)
