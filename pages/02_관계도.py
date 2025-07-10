import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os

st.set_page_config(layout="wide")

st.title("우리 반 친구 관계 맵")
st.write("설문조사 CSV 파일을 업로드하고, 옵션을 선택하여 친구 관계도를 시각화하세요.")

# 1. 데이터 업로드
uploaded_file = st.file_uploader("설문조사 결과를 담은 CSV 파일을 업로드해주세요.", type="csv")

df = None
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.subheader("업로드된 데이터 미리보기")
        st.dataframe(df.head())

        st.sidebar.header("관계도 시각화 설정")

        # 1. 테마 선택 (배경색/글자색)
        theme = st.sidebar.radio(
            "테마 선택:",
            ('어두운 테마 (검정 배경, 흰 글씨)', '밝은 테마 (하얀 배경, 검정 글씨)'),
            index=0 # 기본값은 어두운 테마
        )
        bg_color = "#222222" if theme == '어두운 테마 (검정 배경, 흰 글씨)' else "#FFFFFF"
        font_color = "white" if theme == '어두운 테마 (검정 배경, 흰 글씨)' else "black"

        # 2. 노드 크기 조절 슬라이더
        node_size = st.sidebar.slider(
            "노드(점)의 기본 크기 조절:",
            min_value=5, max_value=50, value=15, step=1
        )

        # 3. 노드 이름(라벨) 폰트 크기 조절 슬라이더
        name_font_size = st.sidebar.slider(
            "노드 이름(라벨) 폰트 크기 조절:",
            min_value=8, max_value=30, value=12, step=1
        )
        
        # 4. 엣지(선) 굵기 조절 슬라이더 (기본 굵기)
        edge_width = st.sidebar.slider(
            "엣지(선)의 기본 굵기 조절:",
            min_value=0.5, max_value=5.0, value=1.0, step=0.1
        )

        # 5. 관계 방향성 표현 방식 선택
        edge_direction_style = st.sidebar.radio(
            "관계 방향성 표현 방식:",
            ('방향성 없음', '화살표(지목 방향)'),
            index=0 # 기본값은 방향성 없음
        )
        # '굵기(지목 횟수)'는 '방향성 없음'에서도 적용되므로 별도 옵션으로 두지 않고, 항상 굵기 변화 적용
        
        is_directed = (edge_direction_style == '화살표(지목 방향)')

        # 열 선택
        all_columns = df.columns.tolist()

        name_column = st.sidebar.selectbox(
            "학생 이름이 있는 열을 선택하세요:",
            all_columns
        )

        st.sidebar.subheader("관계도를 그릴 열을 선택하세요 (최대 3개):")
        relation_columns = []
        for i in range(1, 4): # 최대 3개 선택
            col = st.sidebar.selectbox(
                f"관계 열 {i} 선택 (선택 안 함 가능):",
                ['선택 안 함'] + [c for c in all_columns if c != name_column and c not in relation_columns],
                key=f'rel_col_{i}'
            )
            if col != '선택 안 함':
                relation_columns.append(col)
        
        if not relation_columns:
            st.warning("관계도를 그릴 열을 최소 하나 이상 선택해주세요.")
            df = None

    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        df = None

# 3. 관계도 생성 및 시각화
if df is not None and name_column and relation_columns:
    if st.button("관계도 그리기"):
        st.subheader("친구 관계도")
        
        # 방향성에 따라 그래프 타입 선택
        G = nx.DiGraph() if is_directed else nx.Graph()
        
        # 모든 학생 이름을 노드로 추가 (중복 제거)
        all_students = set()
        for _, row in df.iterrows():
            if pd.notna(row[name_column]):
                all_students.add(str(row[name_column]).strip())
            for rel_col in relation_columns:
                if pd.notna(row[rel_col]):
                    targets = [t.strip() for t in str(row[rel_col]).split(',') if t.strip()]
                    for target in targets:
                        all_students.add(target)
        
        for student in all_students:
            G.add_node(student, title=student, size=node_size, 
                       font={'size': name_font_size, 'color': font_color}) # 노드 이름 폰트 크기 및 색상 적용

        # 관계 데이터 추가
        # 각 관계 유형에 고유한 색상을 할당합니다.
        relation_colors = ['#FF6347', '#4682B4', '#32CD32'] # Tomato, SteelBlue, LimeGreen (예시 색상)
        
        for idx, rel_col in enumerate(relation_columns):
            current_color = relation_colors[idx % len(relation_colors)]

            for _, row in df.iterrows():
                source = str(row[name_column]).strip()
                if pd.notna(row[rel_col]):
                    targets = [t.strip() for t in str(row[rel_col]).split(',') if t.strip()]
                    
                    for target in targets:
                        if source != target and source in all_students and target in all_students:
                            if G.has_edge(source, target):
                                # 기존 엣지의 굵기 증가 (기본 굵기에 추가)
                                # 'value'는 pyvis에서 엣지 굵기를 조절하는 속성
                                G[source][target]['value'] = G[source][target].get('value', 0) + edge_width
                                # 툴팁에 관계 추가
                                G[source][target]['title'] += f", {rel_col}"
                            else:
                                # 새로운 엣지 추가 (기본 굵기 적용)
                                G.add_edge(source, target, 
                                           title=rel_col, 
                                           color=current_color, 
                                           value=edge_width) # value는 엣지 굵기

        if G.number_of_nodes() > 0:
            net = Network(notebook=True, height="750px", width="100%", 
                          directed=is_directed, # 방향성 옵션 적용
                          bgcolor=bg_color, font_color=font_color, # 배경색/글자색 옵션 적용
                          cdn_resources='remote')
            
            # 노드 추가
            for node in G.nodes(data=True):
                net.add_node(node[0], 
                             label=node[0], 
                             title=node[1].get('title', node[0]), 
                             size=node[1].get('size', node_size),
                             font=node[1].get('font', {'size': name_font_size, 'color': font_color})) # 폰트 설정 적용

            # 엣지 추가
            for edge in G.edges(data=True):
                net.add_edge(edge[0], edge[1], 
                             title=edge[2].get('title', ''), 
                             color=edge[2].get('color', 'gray'), 
                             width=edge[2].get('value', edge_width))

            # 물리 시뮬레이션 설정 (기존과 동일)
            net.set_options("""
            var options = {
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 100,
                  "springConstant": 0.08,
                  "avoidOverlap": 0.9
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
              },
              "interaction": {
                "zoomView": true,
                "hover": true,
                "tooltipDelay": 300
              }
            }
            """)

            html_file_path = "temp_graph.html"
            net.save_graph(html_file_path)
            
            with open(html_file_path, "r", encoding="utf-8") as f:
                html_code = f.read()
            components.html(html_code, height=800)
            
            if os.path.exists(html_file_path):
                os.remove(html_file_path)

        else:
            st.warning("관계도를 그릴 데이터가 없습니다. 선택한 열과 CSV 파일 내용을 확인해주세요.")

else:
    st.info("CSV 파일을 업로드하고 이름 및 관계 열, 시각화 옵션을 선택하여 우리 반 친구 관계도를 볼 수 있습니다.")

st.markdown("---")
st.markdown("이 서비스는 학급 내 친구 관계를 이해하고, 학생들이 서로 긍정적인 관계를 형성하도록 돕기 위해 개발되었습니다.")
