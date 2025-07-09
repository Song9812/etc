import streamlit as st
import pandas as pd
from wordcloud import WordCloud
from collections import Counter
from konlpy.tag import Okt
import matplotlib.pyplot as plt
import io
import os # os 모듈 임포트 확인

# --- Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="설문조사 워드클라우드 생성기",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🌈 설문조사 워드클라우드 생성기 ✨")
st.write("네이버 폼 등에서 다운로드한 설문조사 파일로 워드클라우드를 만들어 보세요!")
st.markdown("---")

# --- 폰트 파일 경로 설정 ---
# 네이버 나눔고딕 Bold 폰트 파일명 (반드시 이 파일을 Streamlit 앱 파일과 같은 폴더에 넣어주세요!)
NANUM_FONT_FILE = "NanumGothicBold.ttf"

# 현재 스크립트가 실행되는 디렉토리 경로
current_dir = os.path.dirname(__file__)
# 폰트 파일의 전체 경로
font_path_in_app_folder = os.path.join(current_dir, NANUM_FONT_FILE)

# 폰트 파일 존재 여부 확인 (사용자에게 안내하기 위함)
if not os.path.exists(font_path_in_app_folder):
    st.warning(f"**경고**: '{NANUM_FONT_FILE}' 폰트 파일을 찾을 수 없습니다.")
    st.warning(f"'{os.path.basename(__file__)}' 파일과 같은 폴더에 '{NANUM_FONT_FILE}' 파일을 넣어주세요.")
    st.markdown("[네이버 나눔글꼴 다운로드 링크](https://hangeul.naver.com/font/nanum)")
    st.info("폰트 파일이 없으면 워드클라우드의 한글이 깨지거나 오류가 발생할 수 있습니다.")
    final_font_path = None # 폰트 경로를 None으로 설정하여 생성 시 오류 유도
else:
    final_font_path = font_path_in_app_folder
    st.success(f"'{NANUM_FONT_FILE}' 폰트 파일을 성공적으로 찾았습니다.")


# --- 1. 파일 업로드 ---
st.header("1. 설문조사 파일 업로드")
uploaded_file = st.file_uploader("엑셀 (.xlsx) 또는 CSV (.csv) 파일을 업로드해주세요.", type=["xlsx", "csv"])

df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            # CSV 파일 인코딩 자동 감지 시도 (가장 흔한 인코딩부터 시도)
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    uploaded_file.seek(0) # 파일 포인터 초기화
                    df = pd.read_csv(uploaded_file, encoding='cp949')
                except UnicodeDecodeError:
                    uploaded_file.seek(0) # 파일 포인터 초기화
                    df = pd.read_csv(uploaded_file, encoding='euc-kr')
            except Exception as e:
                st.error(f"CSV 파일을 읽는 중 알 수 없는 인코딩 오류가 발생했습니다: {e}")
                st.info("CSV 파일을 메모장으로 열어 '다른 이름으로 저장' > '인코딩'을 UTF-8로 변경 후 다시 시도해보세요.")
        else: # .xlsx
            df = pd.read_excel(uploaded_file)
        
        st.success("파일 업로드 및 읽기 성공! 데이터 미리보기:")
        st.dataframe(df.head()) # 데이터 미리보기
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        st.info("업로드한 파일이 손상되었거나, CSV 파일의 경우 인코딩 문제일 수 있습니다. 파일을 다시 저장해 보세요.")

# --- 2. 텍스트 컬럼 선택 ---
if df is not None:
    st.header("2. 워드클라우드를 만들 텍스트 컬럼 선택")
    # 문자열 또는 object 타입의 컬럼만 선택 (텍스트 데이터일 가능성 높음)
    text_columns = df.select_dtypes(include=['object', 'string']).columns.tolist() 
    
    if not text_columns:
        st.warning("워드클라우드를 만들 수 있는 텍스트(문자열) 컬럼이 없습니다. 파일 내용을 확인해주세요.")
    else:
        selected_column = st.selectbox("워드클라우드를 만들 컬럼을 선택해주세요:", text_columns)

        # --- 3. 불용어(Stopwords) 입력 ---
        st.header("3. 불용어(Stopwords) 입력 (선택 사항)")
        st.info("워드클라우드에서 제외하고 싶은 단어들을 쉼표(,)로 구분하여 입력해주세요. (예: 그리고, 그래서, 저는, 정말, 했어요)")
        # 기본 불용어 목록을 좀 더 상세하게 추가
        default_stopwords = "우리, 친구, 선생님, 정말, 했어요, 같아요, 입니다, 입니다만, 같습니다, 그리고, 그래서, 저는, 것, 게, 수, 점, 후, 때, 동안, 이번, 안, 듯, 제, 가장, 하다, 되다, 이다, 있다, 없다, 같은, 에서, 에서도, 으로, 으로도, 과, 와, 에게, 한, 인, 를, 을, 은, 는, 이, 가, 도, 만"
        stopwords_input = st.text_area("불용어 목록:", value=default_stopwords)
        
        # 불용어 리스트 생성 (공백 제거 후 쉼표로 분리)
        custom_stopwords = [word.strip() for word in stopwords_input.split(',') if word.strip()]

        # --- 4. 워드클라우드 생성 설정 및 버튼 ---
        st.header("4. 워드클라우드 생성")
        
        # 워드클라우드 생성 버튼
        if st.button("워드클라우드 생성하기"):
            if final_font_path is None:
                st.error("폰트 파일을 찾을 수 없어 워드클라우드를 생성할 수 없습니다. 위 경고 메시지를 확인해주세요.")
            else:
                with st.spinner("워드클라우드를 생성 중입니다... 잠시만 기다려주세요!"):
                    try:
                        # 모든 텍스트 응답 합치기 (NaN 값은 빈 문자열로 처리)
                        text_content = df[selected_column].astype(str).str.cat(sep=' ')
                        
                        # KoNLPy 형태소 분석기 초기화
                        okt = Okt()
                        # 형태소 분석: 명사만 추출
                        nouns = okt.nouns(text_content) 
                        
                        # 불용어 제거 및 한 글자 단어 제거
                        filtered_nouns = [
                            n for n in nouns 
                            if n not in custom_stopwords and len(n) > 1 # 불용어 제거 & 한 글자 단어 제거
                        ]
                        
                        # 단어 빈도수 계산
                        word_counts = Counter(filtered_nouns)

                        # 워드클라우드 객체 생성
                        wc = WordCloud(
                            font_path=final_font_path, # 나눔고딕 폰트 경로 사용
                            width=800,
                            height=400,
                            background_color='white',
                            max_words=150, # 표시 단어 수를 조금 더 늘려봤습니다
                            prefer_horizontal=0.9, # 가로 단어 비율 높게
                            colormap='viridis' # 색상 팔레트
                        )
                        
                        # 워드클라우드 생성
                        wc.generate_from_frequencies(word_counts)
                        
                        # 이미지로 변환하여 Streamlit에 표시
                        img_buffer = io.BytesIO()
                        plt.figure(figsize=(12, 6)) # 이미지 크기 조정
                        plt.imshow(wc, interpolation='bilinear')
                        plt.axis('off') # 축 제거
                        plt.title(f"'{selected_column}' 워드클라우드", fontsize=18) # 제목 추가
                        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
                        img_buffer.seek(0) # 버퍼 시작으로 이동

                        st.success("워드클라우드 생성 완료!")
                        st.image(img_buffer, caption=f"'{selected_column}' 워드클라우드", use_column_width=True)

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
                        st.info("데이터에 문제가 있거나, KoNLPy 관련 오류(Java JDK 설치 등)가 아닌지 확인해주세요.")
else:
    st.info("먼저 설문조사 파일을 업로드해주세요.")

st.markdown("---")
st.markdown("Made with ❤️ by Your AI Assistant")
