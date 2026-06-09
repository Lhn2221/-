import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="강원도 레저 & 축제 데이터 대시보드",
    page_icon="🏔️",
    layout="wide"
)

# 2. 데이터베이스 연결 함수 (캐싱 적용으로 속도 향상)
@st.cache_data
def run_query(query, params=None):
    """
    SQLite 데이터베이스에 쿼리를 실행하고 그 결과를 Pandas DataFrame으로 반환합니다.
    """
    try:
        with sqlite3.connect("강원도 축제.db") as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"데이터베이스 연결 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 3. 메인 타이틀 및 소개
st.title("🏔️ 강원도 레저 및 지역 축제 분석 대시보드")
st.markdown("""
이 대시보드는 강원도 내 기상, 방문자수, 지출 비율, 관광 소비 및 축제 데이터를 바탕으로 
레저 및 축제 산업의 현황을 분석하고 가설을 검증하기 위해 제작되었습니다.
""")
st.divider()

# 4. 탭 구성
tab1, tab2, tab3 = st.tabs([
    "📍 가설 1: 기후 변화와 실외 레저", 
    "🔥 가설 2: 지출 상위 지역과 액티비티", 
    "🍔 가설 3: 주제별 관광소비 분석"
])

# -------------------------------------------------------------
# TAB 1: 기후 변화와 방문자수 상관관계
# -------------------------------------------------------------
with tab1:
    st.header("1. 특정 계절에 편중된 실외형 레저일수록 기후 변화에 따른 매출 변동이 클 것이다.")
    
    st.subheader("💡 가설 검증 프로세스")
    st.markdown("""
    - **가설 배경**: 기온이나 강수량 등 기후 변화가 실외 레저가 중심이 되는 지역의 방문자수에 직접적인 영향을 줄 것이다.
    - **시각화 방식**: 선택한 지역의 월별 방문자수(막대)를 좌측 축에 표시하고, 우측 축에 평균기온(주황색 실선), 최고/최저기온(점), 그리고 **강수량(보라색 실선)**을 함께 시각화하여 비교합니다.
    """)

    target_regions = ["화천", "홍천", "춘천", "인제"]
    selected_region = st.selectbox("분석할 지역을 선택해 주세요:", target_regions, index=2)

    # 기상.월별에서 '월' 글자를 제거하고 정수형으로 변환하여 올바르게 정렬합니다.
    query_1 = """
    SELECT
        기상.지역,
        기상.월별,
        기상.평균기온,
        기상.최고기온,
        기상.최저기온,
        기상.강수량,
        방문자.방문자수
    FROM 기상개황 AS 기상
    LEFT JOIN 방문자수 AS 방문자
        ON 기상.지역 = 방문자.지역
        AND 기상.월별 = 방문자.월별
    WHERE 기상.지역 = ?
    ORDER BY CAST(REPLACE(기상.월별, '월', '') AS INTEGER);
    """
    
    df1 = run_query(query_1, (selected_region,))

    if not df1.empty:
        # 이중 축(Dual Y-Axis) 차트 생성
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])

        # 1) 방문자수 (막대그래프 - 왼쪽 Y축)
        fig1.add_trace(
            go.Bar(
                x=df1['월별'], 
                y=df1['방문자수'], 
                name='방문자수 (명)', 
                marker_color='rgba(135, 206, 250, 0.5)'
            ),
            secondary_y=False,
        )

        # 2) 평균 기온 (실선 - 오른쪽 Y축)
        fig1.add_trace(
            go.Scatter(
                x=df1['월별'], 
                y=df1['평균기온'], 
                name='평균기온 (℃)', 
                mode='lines+markers',
                line=dict(color='orange', width=3)
            ),
            secondary_y=True,
        )

        # 3) 최고 기온 (점 - 오른쪽 Y축)
        fig1.add_trace(
            go.Scatter(
                x=df1['월별'], 
                y=df1['최고기온'], 
                name='최고기온 (℃)', 
                mode='markers',
                marker=dict(color='red', size=8, symbol='triangle-up')
            ),
            secondary_y=True,
        )

        # 4) 최저 기온 (점 - 오른쪽 Y축)
        fig1.add_trace(
            go.Scatter(
                x=df1['월별'], 
                y=df1['최저기온'], 
                name='최저기온 (℃)', 
                mode='markers',
                marker=dict(color='blue', size=8, symbol='triangle-down')
            ),
            secondary_y=True,
        )

        # 5) 강수량 (실선 - 오른쪽 Y축) ★ 수정 및 추가된 부분 ★
        fig1.add_trace(
            go.Scatter(
                x=df1['월별'], 
                y=df1['강수량'], 
                name='강수량 (mm)', 
                mode='lines+markers',
                line=dict(color='purple', width=3, dash='solid') # 보라색 실선으로 기온과 구별
            ),
            secondary_y=True,
        )

        # 레이아웃 설정 (우측 Y축 단위를 기온/강수량 통합 표기)
        fig1.update_layout(
            title_text=f"📊 {selected_region} 지역 기상 개황 및 방문자수 추이",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig1.update_yaxes(title_text="<b>방문자수</b> (명)", secondary_y=False)
        fig1.update_yaxes(title_text="<b>기온 (℃) / 강수량 (mm)</b>", secondary_y=True)

        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("조회된 기상 및 방문자수 데이터가 없습니다.")

    # 사용된 SQL과 인사이트 화면 출력
    with st.expander("🔍 사용된 SQL 보기"):
        st.code(query_1, language="sql")

    st.success("""
    📝 **인사이트**  
    호수문화권(춘천, 홍천, 화천, 인제, 양구) 중 네 지역의 강수량에 따른 방문자수 증감을 확인하고자 했습니다. 
    그러나, 레저스포츠 재단별 운영정책과 투자현황, 마케팅, 실내형/계절별 레저스포츠 차이 등 매우 다양한 변수가 혼재하기에 
    지역별 기상개황과 방문자수의 유의미한 상관관계를 확인하기 어려웠습니다. 
    다만, 이를 통해 상대적으로 지자체별 투자 컨트롤이 수월한 **지역축제**의 장점을 제고할 수 있는 계기가 되었습니다.
    """)

# -------------------------------------------------------------
# TAB 2: 지출 상위 지역 연도별 도넛 차트 가로 배치 (다양성 확보 버전)
# -------------------------------------------------------------
with tab2:
    st.header("2. 방문객수 상위 축제는 액티비티형으로, 호수문화권에 밀접할 것이다.")
    
    st.subheader("💡 가설 검증 프로세스")
    st.markdown("""
    - **가설 배경**: 주요 인기 축제들이 액티비티 요소를 담고 있으며, 호수문화권과 깊은 연관이 있을 것으로 추정했습니다.
    - **시각화 방식**: 매년 지출 상위 4위를 차지한 고정 멤버들의 지분 변화를 **3개의 도넛 차트**로 나란히 비교하여 독점 구조와 시각적 다양성을 동시에 확보합니다.
    """)

    # [강조 가시성 패널]
    st.info("""
    📢 **핵심 발견 (3개년 부동의 철옹성)**  
    분석 대상 기간(**2023년 ~ 2025년**) 동안 지출 상위 4개 지역은 **[강릉, 속초, 춘천, 평창]**으로 완벽히 고정되어 있습니다. 
    아래 도넛 차트의 범례와 조각들을 보시면 매년 동일한 4개 지역이 강원도 지출 파이를 나누어 갖고 있음을 직관적으로 확인하실 수 있습니다.
    """)

    query_2 = """
    SELECT 연도, 지역, 비율, 순위
    FROM (
        SELECT 
            연도,
            지역,
            비율,
            RANK() OVER (PARTITION BY 연도 ORDER BY 비율 DESC) AS 순위
        FROM "지역별 지출"
    )
    WHERE 순위 <= 4
    ORDER BY 연도, 순위;
    """

    df2 = run_query(query_2)

    if not df2.empty:
        # 3개의 열(Column)을 생성하여 가로로 나란히 배치
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        years = [2023, 2024, 2025]
        
        # 각 연도별로 동일한 색상을 매핑하기 위한 고정 컬러맵 정의 (일관성 유지)
        color_map = {
            "강릉": "#FF6B6B",  # 연한 빨강
            "속초": "#4D96FF",  # 연한 파랑
            "춘천": "#6BCB77",  # 연한 초록
            "평창": "#FFD93D"   # 연한 노랑
        }
        
        for i, year in enumerate(years):
            # 해당 연도의 데이터만 필터링
            df_year = df2[df2['연도'] == year]
            
            fig = px.pie(
                df_year,
                values='비율',
                names='지역',
                hole=0.4,  # 가운데 구멍을 뚫어 도넛 형태로 변환
                color='지역',
                color_discrete_map=color_map,
                title=f"📅 {year}년 지출 비율 구성"
            )
            
            # 도넛 내부 텍스트 설정
            # (단순 조각 비율 계산이 아닌, 실제 데이터베이스의 % 값을 그대로 표시하여 정보 왜곡을 방지합니다)
            fig.update_traces(
                textinfo='label+value',
                texttemplate='%{label}<br><b>%{value:.1f}%</b>',
                textfont_size=13
            )
            
            # 디자인 다듬기 (마지막 차트에만 범례를 표시하여 화면을 아주 깔끔하게 만듭니다)
            fig.update_layout(
                showlegend=(i == 2), 
                margin=dict(t=50, b=10, l=10, r=10)
            )
            
            cols[i].plotly_chart(fig, use_container_width=True)
            
    else:
        st.info("조회된 지출 데이터가 없습니다.")

    with st.expander("🔍 사용된 SQL 보기"):
        st.code(query_2, language="sql")

    st.success("""
    📝 **인사이트**  
    호수문화권의 인기도를 확인하기 위해 세운 가설로, 2023~2025년 모두 강릉, 속초, 춘천, 평창이 지출 상위 4개 지역으로 확인되었습니다. 
    비록 춘천을 제외한 3개 지역은 호수문화권에 해당하지 않으나, 전반적으로 해변과 산악권 등 강원도의 지리적 요소가 크게 반영된 지역에 속합니다. 
    레저스포츠와 축제 모두 액티비티 요소를 통한 결합 가능성이 크므로, 해당 4개 지역에 대한 축제 기획 시너지는 매우 긍정적으로 평가할 수 있습니다.
    """)

# -------------------------------------------------------------
# TAB 3: 주제별 관광소비 분석 (선그래프 + 테이블)
# -------------------------------------------------------------
with tab3:
    st.header("3. 음식, 액티비티, 포토스팟 등 통용성이 높은 주제일수록 외국인 방문객 수가 높을 것이다.")
    
    st.subheader("💡 가설 검증 프로세스")
    st.markdown("""
    - **가설 배경**: 대중적인 주제를 다루는 시기에 소비 활성화가 더 뚜렷할 것임을 검증하기 위해 월별 관광총소비액 추이를 분석합니다.
    - **시각화 방식**: 
        - **(A) 선 그래프**: 월별 관광총소비액의 흐름을 연도별로 비교합니다.
        - **(B) 하단 매칭 표**: 각 연도별로 소비액이 가장 높았던 상위 3개 달과 축제 시기가 겹치는 축제들을 추출하여 보여줍니다.
    """)

    query_3_A = """
    SELECT 
        연도,
        월별,
        분류,
        소비액
    FROM 관광소비
    WHERE 분류 = '관광총소비'
    ORDER BY 연도, CAST(REPLACE(월별, '월', '') AS INTEGER);
    """
    df3_A = run_query(query_3_A)

    query_3_B = """
    SELECT 
        소비.연도,
        소비.월별,
        소비.소비액,
        축제.축제명,
        축제.지역,
        축제.분야,
        축제.월별 AS 축제시기
    FROM (
        SELECT 
            연도,
            월별,
            소비액,
            RANK() OVER (PARTITION BY 연도 ORDER BY 소비액 DESC) AS 순위
        FROM 관광소비
        WHERE 분류 = '관광총소비'
    ) AS 소비
    LEFT JOIN 축제
        ON CAST(REPLACE(축제.월별, '월', '') AS INTEGER) = CAST(REPLACE(소비.월별, '월', '') AS INTEGER)
    WHERE 소비.순위 <= 3
    ORDER BY 소비.연도, 소비.소비액 DESC;
    """
    df3_B = run_query(query_3_B)

    if not df3_A.empty:
        fig3 = px.line(
            df3_A, 
            x='월별', 
            y='소비액', 
            color='연도', 
            markers=True,
            title="📈 연도별/월별 관광총소비액 추이",
            labels={"소비액": "소비액 (원)", "월별": "기준 월"}
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("조회된 관광소비 데이터가 없습니다.")

    st.subheader("🏆 연도별 최고 소비액 Top 3 해당 월의 개최 축제 목록")
    if not df3_B.empty:
        st.dataframe(df3_B, use_container_width=True)
    else:
        st.info("소비액 상위 달에 매칭되는 축제 데이터가 없습니다.")

    with st.expander("🔍 사용된 SQL 보기 (수정 내용 포함)"):
        st.code(query_3_B, language="sql")

    st.success("""
    📝 **인사이트**  
    관광 총소비액을 기준으로, 월별 수치 중 상위 3개인 달과 축제시기가 동일한 축제를 확인했습니다. 
    해당 축제들의 전체적인 테마(축제 분야)와 지역을 확인하여 투자가치가 높은 분야를 도출하고자 했습니다. 
    
    분석에 따르면, 모든 해에 공통적으로 소비가 급증하는 달은 **10월**로, 식음료 분야 축제가 특히 많이 개최되고 있음을 확인할 수 있습니다. 
    1월과 8월, 12월에는 **자연과 액티비티 분야**가 우세합니다. 
    강원도의 지리적 이점상 '자연'은 모든 축제의 밑바탕이 되므로, 이를 제외한다면 **10월에는 식음료 요소**, **그 외 집중 소비 월에는 액티비티 요소**가 활약할 수 있는 기획을 선택하는 쪽이 성공률이 높습니다.
    """)