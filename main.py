import streamlit as st
import fitz  # PyMuPDF 라이브러리
import io
from PIL import Image # 이미지 처리를 위해 Pillow 라이브러리 필요

def main():
    st.title("PDF를 이미지로 변환 ✨")
    st.markdown("---")
    st.write("PDF 파일을 업로드하시면 각 페이지를 고품질 이미지로 변환하여 보여드려요.")

    uploaded_file = st.file_uploader("여기에 PDF 파일을 드래그하거나 클릭해서 업로드해주세요", type="pdf")

    if uploaded_file is not None:
        st.success("PDF 파일이 성공적으로 업로드되었습니다!")
        st.spinner("PDF를 이미지로 변환 중...")

        try:
            # PyMuPDF로 PDF 문서 열기
            # uploaded_file.read()는 BytesIO 객체를 반환하므로, stream 인자에 직접 전달 가능
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            images = []

            # 각 페이지를 이미지로 변환
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # 이미지 해상도 조절 (zoom 팩터)
                # 2.0은 기본 해상도의 2배, 즉 DPI를 약 144 -> 288로 높이는 효과
                # 숫자를 높일수록 이미지가 선명해지지만, 변환 시간이 길어지고 파일 크기가 커져요.
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # Pixmap을 PIL Image (Pillow 이미지 객체)로 변환
                # JPEG는 알파 채널이 없으므로 RGB로 변환 (투명도 지원 안함)
                # PNG는 알파 채널을 지원하므로 RGBA로 변환 가능
                if pix.n - pix.alpha > 3: # CMYK 등 다른 색상 공간 처리 (PNG 다운로드 시)
                    img = Image.frombytes("CMYK", [pix.width, pix.height], pix.samples)
                else: # RGB 또는 RGBA
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


                images.append(img)

            doc.close() # 문서 사용이 끝났으면 닫아줍니다.

            st.success(f"총 **{len(images)} 페이지**를 이미지로 변환 완료했습니다!")
            st.markdown("---")

            # 각 이미지를 Streamlit에 표시하고 다운로드 버튼 제공
            for i, image in enumerate(images):
                st.subheader(f"🖼️ 페이지 {i+1}")
                st.image(image, caption=f"변환된 페이지 {i+1}", use_column_width=True) # 컬럼 너비에 맞춰 이미지 표시

                # 이미지 다운로드를 위한 준비 (PNG 형식)
                buf = io.BytesIO()
                image.save(buf, format="PNG") # 이미지를 PNG 형식의 바이트로 저장
                byte_im = buf.getvalue() # 저장된 바이트 데이터 가져오기

                st.download_button(
                    label=f"⬇️ 페이지 {i+1} 이미지 다운로드 (PNG)",
                    data=byte_im,
                    file_name=f"{uploaded_file.name.replace('.pdf', '')}_page_{i+1}.png",
                    mime="image/png"
                )
                st.markdown("---") # 각 이미지 사이에 구분선 추가

        except Exception as e:
            st.error(f"PDF를 이미지로 변환하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요: {e}")
            st.warning("혹시 PDF 파일이 손상되었거나 암호화되어 있을 수 있습니다.")

if __name__ == "__main__":
    main()
