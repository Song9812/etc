import streamlit as st
from PIL import Image, ImageOps
import io

def add_letterbox(image, target_size=(1000, 1000), color=(0, 0, 0)):
    """
    이미지에 레터박스를 추가하여 지정된 크기의 정사각형으로 만듭니다.
    """
    original_width, original_height = image.size

    # 이미지 비율에 따라 레터박스를 추가할지 결정
    if original_width > original_height:
        # 가로가 더 길면 세로를 늘려야 함 (위/아래 레터박스)
        scale_factor = target_size[0] / original_width
        new_width = target_size[0]
        new_height = int(original_height * scale_factor)
    else:
        # 세로가 더 길거나 같으면 가로를 늘려야 함 (양옆 레터박스)
        scale_factor = target_size[1] / original_height
        new_height = target_size[1]
        new_width = int(original_width * scale_factor)

    # 이미지 크기 조절
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 새로운 1:1 비율의 캔버스 생성 (검은색 배경)
    new_image = Image.new("RGB", target_size, color)

    # 조절된 이미지를 새 캔버스의 중앙에 붙여넣기
    paste_x = (target_size[0] - new_width) // 2
    paste_y = (target_size[1] - new_height) // 2
    new_image.paste(resized_image, (paste_x, paste_y))

    return new_image

st.set_page_config(layout="centered", page_title="1:1 이미지 변환기")

st.title("📸 1:1 이미지 변환기")
st.write("이미지를 업로드하여 자동으로 1:1 비율로 만들고 레터박스를 추가합니다.")

uploaded_file = st.file_uploader("이미지 파일을 업로드하세요...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 이미지 로드
    image = Image.open(uploaded_file)
    st.image(image, caption="원본 이미지", use_column_width=True)

    st.subheader("변환된 이미지 미리보기:")

    # 레터박스 추가 함수 호출
    processed_image = add_letterbox(image)

    # 변환된 이미지 표시
    st.image(processed_image, caption="1:1 비율 변환 이미지", use_column_width=True)

    # 이미지 다운로드 버튼
    buf = io.BytesIO()
    processed_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="변환된 이미지 다운로드",
        data=byte_im,
        file_name="1x1_converted_image.png",
        mime="image/png"
    )

st.markdown("---")
st.markdown("Made with ❤️ by Streamlit")
