import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import io
import os
from collections import Counter

# --- Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="우리 반 관계도 그래프 생성기",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("👭 우리 반 관계도 그래프 생성기 🔗✨")
st.write("설문조사 데이터를 활용하여 학생들 간의 관계망 그래프를 시각화합니다.")
st.markdown("---")

# --- 폰트 파일 경로 설정 ---
NANUM_FONT_FILE = "NanumGothicBold.ttf"
current_dir = os.path.dirname(__file__)
font_path_in_app_folder = os.path.join(current_dir, NANUM_FONT_FILE)

# 폰트 파일 존재 여부 확인 및 안내
if not os.path.exists(font_path_in_app_folder):
    st.warning(f"**경고**: '{NANUM_FONT_FILE}' 폰트 파일을 찾을 수 없습니다. 폰트가 없으면 그래프의 한글 이름이 깨지거나 오류가 발생합니다.")
    st.warning(f"'{os.path.basename(__file__)}' 파일과 같은 폴더에 '{NANUM_FONT_FILE}' 파일을 넣어주세요.")
    st.markdown("[네이버 나눔글꼴 다운로드 링크](https://hangeul.naver.com/font/nanum)")
    final_font_path = None
else:
    final_font_path = font_path_in_app_folder

# matplotlib 한글 폰트 설정
if final_font_path:
    plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.error("한글 폰트 파일을 찾을 수 없어 그래프에 한글이 깨질 수 있습니다. 폰트 파일을 준비해주세요.")


# --- 1. 파일 업로드 ---
st.header("1. 설문조사 파일 업로드")
uploaded_file = st.file_uploader("엑셀 (.xlsx) 또는 CSV (.csv) 파일을 업로드해주세요.", type=["xlsx", "csv"])

df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='cp949')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='euc-kr')
            except Exception as e:
                st.error(f"CSV 파일을 읽는 중 알 수 없는 인코딩 오류가 발생했습니다: {e}")
                st.info("CSV 파일을 메모장으로 열어 '다른 이름으로 저장' > '인코딩'을 UTF-8로 변경 후 다시 시도해보세요.")
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("파일 업로드 및 읽기 성공! 데이터 미리보기:")
        st.dataframe(df.head())
        st.session_state.df = df
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        st.info("업로드한 파일이 손상되었거나, CSV 파일의 경우 인코딩 문제일 수 있습니다. 파일을 다시 저장해 보세요.")
else:
    if 'df' in st.session_state:
        del st.session_state.df


# --- 2. 컬럼명 매핑 ---
if 'df' in st.session_state and st.session_state.df is not None:
    df = st.session_state.df

    st.header("2. 관계 설문 컬럼 매핑")
    st.write("엑셀/CSV 파일에서 **'이름' 컬럼을 응답자 이름으로 자동 설정**합니다.")
    st.write("아래에 6개 질문 각각의 1, 2, 3순위 응답 컬럼명을 **순서대로** 선택해주세요. (총 18개)")

    all_cols = df.columns.tolist()

    if '이름' in all_cols:
        respondent_col = '이름'
        st.success(f"응답자 이름 컬럼으로 **'{respondent_col}'** 이(가) 자동 설정되었습니다.")
    else:
        st.error("'이름' 컬럼을 찾을 수 없습니다. 응답자 이름 컬럼을 수동으로 선택해주세요.")
        respondent_col = st.selectbox("응답자 이름 컬럼 선택:", all_cols, index=0)

    st.markdown("**아래 순서에 맞춰 각 질문의 1, 2, 3순위 컬럼명을 드롭다운에서 선택해주세요:**")
    question_prompts = [
        "우리 반에 웃음을 주는 친구",
        "1학기 동안 나와 가장 많은 추억을 만든 친구",
        "우리 반에서 가장 따뜻하고 친절한 친구",
        "나의 비밀을 털어놓아도 안심할 수 있는 믿음직한 친구",
        "졸업식 날, 가장 먼저 눈물을 글썽일 것 같은 친구",
        "2학기에 더 가까워지고 싶은, 함께 추억을 쌓고 싶은 친구"
    ]

    selected_relation_cols = []
    for i, q_prompt in enumerate(question_prompts):
        st.subheader(f"질문 {i+1}: {q_prompt}")
        default_index_1 = next((j for j, col in enumerate(all_cols) if f'{i+5}.' in col or f'Q{i+5}_1' in col or (q_prompt in col and '1순위' in col) or (q_prompt in col and '_1' in col)), 0)
        default_index_2 = next((j for j, col in enumerate(all_cols) if f'{i+5}.' in col or f'Q{i+5}_2' in col or (q_prompt in col and '2순위' in col) or (q_prompt in col and '_2' in col)), 0)
        default_index_3 = next((j for j, col in enumerate(all_cols) if f'{i+5}.' in col or f'Q{i+5}_3' in col or (q_prompt in col and '3순위' in col) or (q_prompt in col and '_3' in col)), 0)
        
        col1 = st.selectbox(f"  └ 1순위 컬럼 (예: '{q_prompt} (1순위)'):", all_cols, key=f'rel_q{i+1}_1', index=default_index_1)
        col2 = st.selectbox(f"  └ 2순위 컬럼 (예: '{q_prompt} (2순위)'):", all_cols, key=f'rel_q{i+1}_2', index=default_index_2)
        col3 = st.selectbox(f"  └ 3순위 컬럼 (예: '{q_prompt} (3순위)'):", all_cols, key=f'rel_q{i+1}_3', index=default_index_3)
        selected_relation_cols.extend([col1, col2, col3])

    # --- 3. 그래프 생성 및 시각화 ---
    st.header("3. 관계도 그래프 생성")

    if st.button("관계도 그래프 그리기"):
        if not final_font_path:
            st.error("한글 폰트 파일을 찾을 수 없어 그래프를 생성할 수 없습니다. 폰트 파일을 준비해주세요.")
        else:
            with st.spinner("관계도 그래프를 생성 중입니다..."):
                try:
                    G = nx.DiGraph()

                    valid_students = df[respondent_col].dropna().astype(str).unique().tolist()
                    G.add_nodes_from(valid_students)

                    weights = {1: 3, 2: 2, 3: 1}

                    for idx, row in df.iterrows():
                        source = str(row[respondent_col]).strip()
                        if not source or source == 'nan' or source not in valid_students:
                            continue

                        for i_col, col_name in enumerate(selected_relation_cols):
                            rank_in_group = (i_col % 3) + 1
                            target = str(row[col_name]).strip()

                            if target and target != 'nan' and target in valid_students and source != target:
                                if G.has_edge(source, target):
                                    G[source][target]['weight'] = G[source][target].get('weight', 0) + weights[rank_in_group]
                                else:
                                    G.add_edge(source, target, weight=weights[rank_in_group])

                    in_degree_weights = Counter()
                    for u, v, data in G.edges(data=True):
                        in_degree_weights[v] += data['weight']

                    node_sizes = [in_degree_weights[node] * 100 + 300 if node in in_degree_weights else 300 for node in G.nodes()]
                    edge_widths = [d['weight'] * 0.5 for (u, v, d) in G.edges(data=True)]

                    plt.figure(figsize=(15, 12))
                    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

                    # --- 변경된 부분: nx.draw() 함수 사용 ---
                    nx.draw(
                        G, pos,
                        node_size=node_sizes,
                        node_color='skyblue',
                        alpha=0.9,
                        linewidths=1,
                        edgecolors='gray',
                        width=edge_widths,
                        alpha=0.6,
                        edge_color='gray',
                        arrows=True,
                        arrowsize=15,
                        labels={node: node for node in G.nodes()}, # 노드 라벨 직접 전달
                        font_size=10,
                        font_color='black',
                        font_family='NanumGothic' # 폰트 설정 직접 전달 (matplotlib의 rcParams와 함께 작동)
                    )
                    # --- 변경된 부분 끝 ---

                    plt.title("우리 반 친구 관계도", fontsize=20, pad=20)
                    plt.axis('off')
                    plt.tight_layout()

                    buf = io.BytesIO()
                    plt.savefig(buf, format="png", bbox_inches='tight', dpi=300)
                    buf.seek(0)
                    plt.close()

                    st.success("관계도 그래프 생성 완료!")
                    st.image(buf, caption="우리 반 친구 관계도", use_column_width=True)

                    st.download_button(
                        label="관계도 그래프 이미지 다운로드 (PNG)",
                        data=buf,
                        file_name="class_network_graph.png",
                        mime="image/png"
                    )
                    st.info("관계도 그래프 이미지를 다운로드하여 학생들과 공유해보세요!")

                except KeyError as e:
                    st.error(f"컬럼 이름을 찾을 수 없습니다. 입력하신 컬럼명: '{e}'")
                    st.warning("선택하신 컬럼 이름이 엑셀/CSV 파일에 **정확히 존재하는지 다시 확인**해주세요. 대소문자나 오타에 주의하세요.")
                except Exception as e:
                    st.error(f"그래프 생성 중 오류가 발생했습니다: {e}")
                    st.info("데이터 형식이나 내용에 문제가 있을 수 있습니다. 학생 이름에 오타가 없는지, '이름' 컬럼에 없는 이름이 응답으로 들어갔는지 확인해보세요.")
else:
    st.info("관계도 그래프를 보려면 먼저 설문 파일을 업로드해주세요.")

st.markdown("---")
st.markdown("Made with ❤️ by Your AI Assistant")
