import streamlit as st
from PIL import Image, ImageOps
import io

def add_letterbox(image, target_ratio, letterbox_color):
    """
    이미지에 레터박스를 추가하여 지정된 비율의 캔버스에 맞춥니다.
    """
    original_width, original_height = image.size

    # 원본 비율 선택 시에는 리사이즈만 수행하고 레터박스 없음
    if target_ratio == "원본 비율":
        if original_width > original_height:
            max_size = (1000, int(1000 * original_height / original_width))
        else:
            max_size = (int(1000 * original_width / original_height), 1000)
        
        resized_image = image.resize(max_size, Image.Resampling.LANCZOS)
        return resized_image

    # 1:1, 4:3, 3:4, 16:9, 9:16 비율의 경우 1000x1000 캔버스에 맞춤
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
    # Streamlit color_picker는 HEX 코드를 반환하므로 RGB로 변환
    letterbox_color_rgb = tuple(int(letterbox_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
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
