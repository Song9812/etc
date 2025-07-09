import streamlit as st
import pandas as pd
from wordcloud import WordCloud
from collections import Counter
from konlpy.tag import Okt
import matplotlib.pyplot as plt
import io # 바이트 스트림 처리를 위해 import

# --- Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="설문조사 워드클라우드 생성기",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🌈 설문조사 워드클라우드 생성기 ✨")
st.write("네이버 폼 등에서 다운로드한 설문조사 파일로 워드클라우드를 만들어 보세요!")
st.markdown("---")

# --- 1. 파일 업로드 ---
st.header("1. 설문조사 파일 업로드")
uploaded_file = st.file_uploader("엑셀 (.xlsx) 또는 CSV (.csv) 파일을 업로드해주세요.", type=["xlsx", "csv"])

df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            # CSV 파일 인코딩 문제 발생 시 다른 인코딩 시도 (예: 'cp949', 'euc-kr', 'utf-8-sig')
            # try:
            #     df = pd.read_csv(uploaded_file, encoding='utf-8')
            # except UnicodeDecodeError:
            #     df = pd.read_csv(uploaded_file, encoding='cp949') # 또는 'euc-kr', 'utf-8-sig'
        else: # .xlsx
            df = pd.read_excel(uploaded_file)
        
        st.success("파일 업로드 및 읽기 성공!")
        st.dataframe(df.head()) # 데이터 미리보기
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        st.info("CSV 파일의 경우 인코딩 문제일 수 있습니다. 파일을 메모장으로 열어 '다른 이름으로 저장' > '인코딩'을 UTF-8로 변경 후 다시 시도해보세요.")

# --- 2. 텍스트 컬럼 선택 ---
if df is not None:
    st.header("2. 워드클라우드를 만들 텍스트 컬럼 선택")
    text_columns = df.select_dtypes(include=['object']).columns.tolist() # 문자열 타입 컬럼만 선택
    
    if not text_columns:
        st.warning("워드클라우드를 만들 텍스트(문자열) 컬럼이 없습니다. 파일을 확인해주세요.")
    else:
        selected_column = st.selectbox("워드클라우드를 만들 컬럼을 선택해주세요:", text_columns)

        # --- 3. 불용어(Stopwords) 입력 ---
        st.header("3. 불용어(Stopwords) 입력 (선택 사항)")
        st.info("워드클라우드에서 제외하고 싶은 단어들을 쉼표(,)로 구분하여 입력해주세요. (예: 그리고, 그래서, 저는, 정말, 했어요)")
        stopwords_input = st.text_area("불용어 목록:", value="우리, 친구, 선생님, 정말, 했어요, 같아요, 입니다, 입니다만, 같습니다, 그리고, 그래서, 저는, 것, 게, 수, 점, 후, 때, 동안, 이번, 안, 듯, 제, 가장")
        
        # 불용어 리스트 생성 (공백 제거 후 쉼표로 분리)
        custom_stopwords = [word.strip() for word in stopwords_input.split(',') if word.strip()]

        # --- 4. 워드클라우드 생성 설정 및 버튼 ---
        st.header("4. 워드클라우드 생성")
        
        # 한글 폰트 경로 지정 (사용자 환경에 맞게 수정 필요)
        # Windows 예시: 'C:/Windows/Fonts/malgunbd.ttf' (맑은 고딕 볼드)
        # Mac 예시: '/Library/Fonts/AppleGothic.ttf'
        # 리눅스 예시: '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf' (나눔고딕 설치 후)
        
        # 기본 폰트 경로를 사용하고, 없으면 사용자에게 입력받도록 설정
        default_font_path = "C:/Windows/Fonts/malgunbd.ttf" # Windows 기본값, 사용자 환경에 맞게 수정 필요!
        if not os.path.exists(default_font_path):
             st.warning(f"기본 폰트 경로 '{default_font_path}'를 찾을 수 없습니다. 사용하시는 시스템에 맞는 한글 폰트 경로를 직접 입력해주세요.")
             font_path_input = st.text_input("한글 폰트 파일 경로를 입력해주세요:", value=default_font_path)
             final_font_path = font_path_input
        else:
             final_font_path = default_font_path

        # 워드클라우드 생성 버튼
        if st.button("워드클라우드 생성하기"):
            if not os.path.exists(final_font_path):
                st.error(f"지정된 폰트 경로 '{final_font_path}'에 파일이 존재하지 않습니다. 올바른 폰트 경로를 입력해주세요.")
            else:
                with st.spinner("워드클라우드를 생성 중입니다... 잠시만 기다려주세요!"):
                    try:
                        # 모든 텍스트 응답 합치기 (NaN 값은 빈 문자열로 처리)
                        text_content = df[selected_column].astype(str).str.cat(sep=' ')
                        
                        # KoNLPy 형태소 분석기 초기화
                        okt = Okt()
                        nouns = okt.nouns(text_content) # 명사 추출
                        
                        # 불용어 제거 및 한 글자 단어 제거
                        filtered_nouns = [
                            n for n in nouns 
                            if n not in custom_stopwords and len(n) > 1
                        ]
                        
                        # 단어 빈도수 계산
                        word_counts = Counter(filtered_nouns)

                        # 워드클라우드 객체 생성
                        wc = WordCloud(
                            font_path=final_font_path,
                            width=800,
                            height=400,
                            background_color='white',
                            max_words=100, # 최대 표시 단어 수
                            prefer_horizontal=0.9, # 가로 단어 비율 (조절 가능)
                            colormap='viridis' # 색상 팔레트 (다양한 옵션: 'viridis', 'plasma', 'magma', 'cividis', 'Greens', 'Blues' 등)
                        )
                        
                        # 워드클라우드 생성
                        wc.generate_from_frequencies(word_counts)
                        
                        # 이미지로 변환하여 Streamlit에 표시
                        img_buffer = io.BytesIO()
                        plt.figure(figsize=(10, 5))
                        plt.imshow(wc, interpolation='bilinear')
                        plt.axis('off')
                        plt.title(f"'{selected_column}' 워드클라우드", fontsize=16)
                        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
                        img_buffer.seek(0) # 버퍼 시작으로 이동

                        st.success("워드클라우드 생성 완료!")
                        st.image(img_buffer, caption="생성된 워드클라우드", use_column_width=True)

                        # 이미지 다운로드 버튼
                        st.download_button(
                            label="워드클라우드 이미지 다운로드 (PNG)",
                            data=img_buffer,
                            file_name=f"{selected_column}_wordcloud.png",
                            mime="image/png"
                        )
                        st.info("워드클라우드 이미지를 다운로드하여 발표 자료 등에 활용해보세요!")

                    except Exception as e:
                        st.error(f"워드클라우드 생성 중 오류 발생: {e}")
                        st.info("한글 폰트 경로가 올바른지, 또는 KoNLPy 관련 오류(Java JDK 설치 등)가 아닌지 확인해주세요.")
else:
    st.info("먼저 설문조사 파일을 업로드해주세요.")

st.markdown("---")
st.markdown("Made with ❤️ by Your AI Assistant")
