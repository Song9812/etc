import streamlit as st
from PIL import Image, ImageOps
import io

def add_letterbox(image, target_ratio, letterbox_color):
    """
    이미지에 레터박스를 추가하여 지정된 비율의 캔버스에 맞춥니다.
    """
    original_width, original_height = image.size

    # 1. 목표 비율에 따른 최종 캔버스 크기 계산 (최대 길이 1000px 기준)
    if target_ratio == "1:1":
        target_canvas_width, target_canvas_height = 1000, 1000
    elif target_ratio == "4:3":
        target_canvas_width, target_canvas_height = 1000, int(1000 * (3/4))
    elif target_ratio == "3:4":
        target_canvas_width, target_canvas_height = int(1000 * (3/4)), 1000
    elif target_ratio == "16:9":
        target_canvas_width, target_canvas_height = 1000, int(1000 * (9/16))
    elif target_ratio == "9:16":
        target_canvas_width, target_canvas_height = int(1000 * (9/16)), 1000
    else: # "원본 비율"
        # 원본 비율 선택 시에는 레터박스 없이 이미지 자체를 최대 1000px로 리사이즈
        if original_width > original_height:
            resized_width = 1000
            resized_height = int(original_height * (1000 / original_width))
        else:
            resized_height = 1000
            resized_width = int(original_width * (1000 / original_height))
        
        resized_image = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
        return resized_image # 레터박스 추가 로직 건너뛰고 바로 반환

    # 2. 원본 이미지를 목표 캔버스에 맞게 스케일링 (비율 유지)
    # 이미지의 어떤 변을 기준으로 스케일링할지 결정하여 여백을 만듦
    scale_factor_width = target_canvas_width / original_width
    scale_factor_height = target_canvas_height / original_height

    # 캔버스 안에 이미지가 다 들어가도록 더 작은 스케일 팩터 사용
    if scale_factor_width < scale_factor_height:
        # 가로에 맞추면 세로에 여백이 생김 (위/아래 레터박스)
        new_width = target_canvas_width
        new_height = int(original_height * scale_factor_width)
    else:
        # 세로에 맞추면 가로에 여백이 생김 (양옆 레터박스)
        new_height = target_canvas_height
        new_width = int(original_width * scale_factor_height)
    
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 3. 새로운 캔버스 생성 및 이미지 붙여넣기
    # Streamlit color_picker는 HEX 코드를 반환하므로 RGB 튜플로 변환
    letterbox_color_rgb = tuple(int(letterbox_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    new_image = Image.new("RGB", (target_canvas_width, target_canvas_height), letterbox_color_rgb)

    # 조절된 이미지를 새 캔버스의 중앙에 붙여넣기
    paste_x = (target_canvas_width - new_width) // 2
    paste_y = (target_canvas_height - new_height) // 2
    new_image.paste(resized_image, (paste_x, paste_y))

    return new_image


st.set_page_config(layout="centered", page_title="커스텀 이미지 변환기")

st.title("📸 이미지 레터박스 추가 & 비율 변환기")
st.write("이미지를 업로드하고 원하는 레터박스 색상과 최종 이미지 비율을 선택하여 변환합니다.")

# 사이드바 설정
st.sidebar.header("설정")
selected_ratio = st.sidebar.selectbox(
    "최종 이미지 비율을 선택하세요:",
    ("1:1", "4:3", "3:4", "16:9", "9:16", "원본 비율"),
    index=0 # 기본값 1:1
)

# 레터박스 색상 선택 (기본값 검은색)
letterbox_color = st.sidebar.color_picker(
    "레터박스 색상을 선택하세요:", "#000000" # 기본값 검은색
)

uploaded_file = st.file_uploader("이미지 파일을 업로드하세요...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 이미지 로드
    image = Image.open(uploaded_file)
    st.image(image, caption="원본 이미지", use_column_width=True)

    st.subheader("변환된 이미지 미리보기:")

    # 레터박스 추가 함수 호출
    processed_image = add_letterbox(image, selected_ratio, letterbox_color)

    # 변환된 이미지 표시
    st.image(processed_image, caption=f"{selected_ratio} 비율 변환 이미지 (레터박스 색상: {letterbox_color})", use_column_width=True)

    # 이미지 다운로드 버튼
    buf = io.BytesIO()
    processed_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="변환된 이미지 다운로드",
        data=byte_im,
        file_name=f"{selected_ratio.replace(':', 'x')}_converted_image.png",
        mime="image/png"
    )

st.markdown("---")
st.markdown("Made with ❤️ by Streamlit")
