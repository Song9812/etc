import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os

st.set_page_config(layout="wide")

st.title("우리 반 친구 관계 맵")
st.write("설문조사 CSV 파일을 업로드하고, 이름 및 관계 열을 선택하여 친구 관계도를 시각화하세요.")

# 1. 데이터 업로드
uploaded_file = st.file_uploader("설문조사 결과를 담은 CSV 파일을 업로드해주세요.", type="csv")

df = None
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.subheader("업로드된 데이터 미리보기")
        st.dataframe(df.head())

        # 2. 열 선택
        all_columns = df.columns.tolist()

        st.sidebar.header("관계도 설정 옵션")

        # 노드 크기 조절 슬라이더 추가
        node_size = st.sidebar.slider(
            "노드(점)의 기본 크기 조절:",
            min_value=5, max_value=50, value=15, step=1
        )

        # 엣지 굵기 조절 슬라이더 추가 (기본 굵기)
        edge_width = st.sidebar.slider(
            "엣지(선)의 기본 굵기 조절:",
            min_value=0.5, max_value=5.0, value=1.0, step=0.1
        )

        name_column = st.sidebar.selectbox( # 사이드바에 위치 변경
            "학생 이름이 있는 열을 선택하세요:",
            all_columns
        )

        st.sidebar.subheader("관계도를 그릴 열을 선택하세요 (최대 3개):")
        relation_columns = []
        for i in range(1, 4): # 최대 3개 선택
            col = st.sidebar.selectbox( # 사이드바에 위치 변경
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
        
        G = nx.Graph()
        
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
            # 노드 크기 여기에 적용
            G.add_node(student, title=student, size=node_size)

        # 관계 데이터 추가
        # 각 관계 유형에 고유한 색상과 초기 엣지 굵기를 할당합니다.
        relation_configs = {
            # 예시 색상. 필요에 따라 변경 가능
            relation_columns[0]: {'color': '#FF6347', 'title_prefix': '관계1'}, # Tomato
            relation_columns[1]: {'color': '#4682B4', 'title_prefix': '관계2'}, # SteelBlue
            relation_columns[2]: {'color': '#32CD32', 'title_prefix': '관계3'}, # LimeGreen
        }


        for rel_col in relation_columns:
            config = relation_configs.get(rel_col, {'color': 'gray', 'title_prefix': '기타관계'}) # 기본값 설정

            for _, row in df.iterrows():
                source = str(row[name_column]).strip()
                if pd.notna(row[rel_col]):
                    targets = [t.strip() for t in str(row[rel_col]).split(',') if t.strip()]
                    
                    for target in targets:
                        if source != target and source in all_students and target in all_students:
                            if G.has_edge(source, target):
                                # 기존 엣지의 굵기 증가 (기본 굵기에 추가)
                                G[source][target]['value'] = G[source][target].get('value', 0) + edge_width
                                # 툴팁에 관계 추가
                                G[source][target]['title'] += f", {config['title_prefix']}: {rel_col}"
                            else:
                                # 새로운 엣지 추가 (기본 굵기 적용)
                                G.add_edge(source, target, title=f"{config['title_prefix']}: {rel_col}", 
                                           color=config['color'], 
                                           value=edge_width)

        if G.number_of_nodes() > 0:
            net = Network(notebook=True, height="750px", width="100%", 
                          directed=False, 
                          bgcolor="#222222", font_color="white",
                          cdn_resources='remote')
            
            # 노드 추가 (슬라이더에서 조절된 노드 크기 적용)
            for node in G.nodes(data=True):
                net.add_node(node[0], label=node[0], title=node[1].get('title', node[0]), size=node[1].get('size', node_size))

            # 엣지 추가 (슬라이더에서 조절된 엣지 굵기 적용)
            for edge in G.edges(data=True):
                # 엣지 굵기가 value에 누적되도록 설정
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
    st.info("CSV 파일을 업로드하고 이름 및 관계 열을 선택하여 우리 반 친구 관계도를 볼 수 있습니다.")

st.markdown("---")
st.markdown("이 서비스는 학급 내 친구 관계를 이해하고, 학생들이 서로 긍정적인 관계를 형성하도록 돕기 위해 개발되었습니다.")
