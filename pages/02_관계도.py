import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os # 임시 파일 삭제를 위해 추가

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

        name_column = st.selectbox(
            "학생 이름이 있는 열을 선택하세요:",
            all_columns
        )

        st.subheader("관계도를 그릴 열을 선택하세요 (최대 3개):")
        relation_columns = []
        for i in range(1, 4): # 최대 3개 선택
            col = st.selectbox(
                f"관계 열 {i} 선택 (선택 사항):",
                ['선택 안 함'] + [c for c in all_columns if c != name_column and c not in relation_columns],
                key=f'rel_col_{i}'
            )
            if col != '선택 안 함':
                relation_columns.append(col)
        
        if not relation_columns:
            st.warning("관계도를 그릴 열을 최소 하나 이상 선택해주세요.")
            df = None # 관계 열이 없으면 그래프를 그리지 않음

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
                    # 쉼표로 구분된 여러 이름 처리
                    targets = [t.strip() for t in str(row[rel_col]).split(',') if t.strip()]
                    for target in targets:
                        all_students.add(target)
        
        for student in all_students:
            G.add_node(student, title=student, size=15) # 기본 노드 크기 설정

        # 관계 데이터 추가
        relation_colors = ['#FF6347', '#4682B4', '#32CD32'] # 관계별 색상 (빨강, 파랑, 초록)
        relation_idx = 0

        for rel_col in relation_columns:
            current_color = relation_colors[relation_idx % len(relation_colors)]
            relation_idx += 1

            for _, row in df.iterrows():
                source = str(row[name_column]).strip()
                if pd.notna(row[rel_col]):
                    targets = [t.strip() for t in str(row[rel_col]).split(',') if t.strip()]
                    
                    for target in targets:
                        if source != target and source in all_students and target in all_students:
                            # 이미 존재하는 엣지라면 속성 업데이트 (예: 굵기 증가)
                            if G.has_edge(source, target):
                                G[source][target]['value'] = G[source][target].get('value', 1) + 1 # 엣지 굵기
                                G[source][target]['title'] += f", {rel_col}" # 툴팁에 관계 추가
                            else:
                                G.add_edge(source, target, title=rel_col, color=current_color, value=1) # value는 엣지 굵기에 사용

        if G.number_of_nodes() > 0:
            net = Network(notebook=True, height="750px", width="100%", 
                          directed=False, # 관계의 방향성 (지목한 사람 -> 지목당한 사람)을 표시하려면 True로 변경
                          bgcolor="#222222", font_color="white",
                          cdn_resources='remote') # CDN 리소스 사용 (로컬 설치 불필요)
            
            # 노드 추가
            for node in G.nodes(data=True):
                net.add_node(node[0], label=node[0], title=node[1].get('title', node[0]), size=node[1].get('size', 15))

            # 엣지 추가
            for edge in G.edges(data=True):
                net.add_edge(edge[0], edge[1], title=edge[2].get('title', ''), color=edge[2].get('color', 'gray'), width=edge[2].get('value', 1))

            # 물리 시뮬레이션 설정 (노드들이 서로 밀고 당기며 적절한 위치를 찾음)
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

            # HTML 파일로 저장하고 Streamlit에 표시
            html_file_path = "temp_graph.html"
            net.save_graph(html_file_path)
            
            with open(html_file_path, "r", encoding="utf-8") as f:
                html_code = f.read()
            components.html(html_code, height=800)
            
            # 임시 파일 삭제
            if os.path.exists(html_file_path):
                os.remove(html_file_path)

        else:
            st.warning("관계도를 그릴 데이터가 없습니다. 선택한 열과 CSV 파일 내용을 확인해주세요.")

else:
    st.info("CSV 파일을 업로드하고 이름 및 관계 열을 선택하여 우리 반 친구 관계도를 볼 수 있습니다.")

st.markdown("---")
st.markdown("이 서비스는 학급 내 친구 관계를 이해하고, 학생들이 서로 긍정적인 관계를 형성하도록 돕기 위해 개발되었습니다.")
