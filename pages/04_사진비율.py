import streamlit as st
from PIL import Image, ImageOps
import io

def get_target_dimensions(original_width, original_height, target_ratio):
    """
    원본 이미지 크기와 목표 비율을 기반으로 레터박스를 추가하기 전의
    최대 가로/세로 길이를 결정합니다.
    """
    if target_ratio == "1:1":
        return 1000, 1000 # 고정된 1000x1000 캔버스
    elif target_ratio == "4:3":
        # 목표 비율 (가로:세로)에 맞춰 최대 1000px 기준 계산
        if original_width / original_height > 4/3: # 원본이 4:3보다 가로가 길면
            return 1000, int(1000 * (3/4))
        else: # 원본이 4:3보다 세로가 길거나 같으면
            return int(1000 * (4/3)), 1000
    elif target_ratio == "16:9":
        # 목표 비율 (가로:세로)에 맞춰 최대 1000px 기준 계산
        if original_width / original_height > 16/9: # 원본이 16:9보다 가로가 길면
            return 1000, int(1000 * (9/16))
        else: # 원본이 16:9보다 세로가 길거나 같으면
            return int(1000 * (16/9)), 1000
    else: # "원본 비율"
        # 이 경우에는 레터박스를 추가하지 않고, 이미지 자체를 1000px 기준으로 리사이즈
        if original_width > original_height:
            new_width = 1000
            new_height = int(original_height * (1000 / original_width))
        else:
            new_height = 1000
            new_width = int(original_width * (1000 / original_height))
        return new_width, new_height


def add_letterbox(image, target_ratio, letterbox_color):
    """
    이미지에 레터박스를 추가하여 지정된 비율의 캔버스에 맞춥니다.
    """
    original_width, original_height = image.size

    # 목표 캔버스 크기 결정 (최대 1000x1000 범위 내에서)
    if target_ratio == "원본 비율":
        # 원본 비율을 유지하면서 최대 1000x1000으로 리사이즈
        if original_width > original_height:
            max_size = (1000, int(1000 * original_height / original_width))
        else:
            max_size = (int(1000 * original_width / original_height), 1000)
        
        resized_image = image.resize(max_size, Image.Resampling.LANCZOS)
        return resized_image # 원본 비율 선택 시에는 레터박스 없음

    # 목표 비율에 따른 최종 캔버스 크기 (1000x1000)
    final_canvas_width, final_canvas_height = 1000, 1000 
    
    # 이미지 스케일링하여 목표 비율 캔버스에 최대한 맞추기
    # 레터박스를 그릴 공간 확보 (원본 비율을 유지하며 최대 크기로 조절)
    width_ratio = final_canvas_width / original_width
    height_ratio = final_canvas_height / original_height
    
    scale_factor = min(width_ratio, height_ratio)
    
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)

    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 새로운 비율의 캔버스 생성 (선택된 색상 배경)
    letterbox_color_rgb = tuple(int(letterbox_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) # HEX -> RGB
    new_image = Image.new("RGB", (final_canvas_width, final_canvas_height), letterbox_color_rgb)

    # 조절된 이미지를 새 캔버스의 중앙에 붙여넣기
    paste_x = (final_canvas_width - new_width) // 2
    paste_y = (final_canvas_height - new_height) // 2
    new_image.paste(resized_image, (paste_x, paste_y))

    return new_image


st.set_page_config(layout="centered", page_title="커스텀 이미지 변환기")

st.title("📸 이미지 레터박스 추가 & 비율 변환기")
st.write("이미지를 업로드하고 원하는 레터박스 색상과 비율을 선택하여 변환합니다.")

# 사이드바 설정
st.sidebar.header("설정")
selected_ratio = st.sidebar.selectbox(
    "원하는 이미지 비율을 선택하세요:",
    ("1:1", "4:3", "16:9", "원본 비율"),
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
