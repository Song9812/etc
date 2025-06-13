import streamlit as st
import fitz  # PyMuPDF 라이브러리
import io
from PIL import Image # 이미지 처리를 위해 Pillow 라이브러리 필요
import zipfile # ZIP 파일 생성을 위한 라이브러리

def main():
    st.title("PDF를 이미지로 변환 ✨")
    st.markdown("---")
    st.write("PDF 파일을 업로드하시면 각 페이지를 고품질 이미지로 변환하여 보여드려요.")

    uploaded_file = st.file_uploader("여기에 PDF 파일을 드래그하거나 클릭해서 업로드해주세요", type="pdf")

    if uploaded_file is not None:
        st.success("PDF 파일이 성공적으로 업로드되었습니다!")
        st.spinner("PDF를 이미지로 변환 중...")

        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            images = []
            image_names = [] # 이미지 파일명을 저장할 리스트

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                if pix.n - pix.alpha > 3:
                    img = Image.frombytes("CMYK", [pix.width, pix.height], pix.samples)
                else:
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                images.append(img)
                # 파일명 설정 (예: original_pdf_name_page_1.png)
                image_names.append(f"{uploaded_file.name.replace('.pdf', '')}_page_{page_num+1}.png")

            doc.close()

            st.success(f"총 **{len(images)} 페이지**를 이미지로 변환 완료했습니다!")
            st.markdown("---")

            # --- 전체 페이지 ZIP 다운로드 버튼 추가 ---
            if images: # 이미지가 하나라도 있을 때만 버튼 표시
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for i, image in enumerate(images):
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format="PNG")
                        # ZIP 파일에 이미지 추가 (파일명 지정)
                        zip_file.writestr(image_names[i], img_byte_arr.getvalue())

                # ZIP 파일 다운로드 버튼
                st.download_button(
                    label="⬇️ 모든 이미지 ZIP 파일로 다운로드",
                    data=zip_buffer.getvalue(),
                    file_name=f"{uploaded_file.name.replace('.pdf', '')}_images.zip",
                    mime="application/zip"
                )
                st.markdown("---")
            # --- ZIP 다운로드 버튼 추가 끝 ---


            # 각 이미지를 Streamlit에 표시하고 개별 다운로드 버튼 제공
            st.subheader("개별 페이지 이미지 보기 및 다운로드")
            for i, image in enumerate(images):
                st.write(f"**페이지 {i+1}**")
                st.image(image, caption=f"변환된 페이지 {i+1}", use_column_width=True)

                buf = io.BytesIO()
                image.save(buf, format="PNG")
                byte_im = buf.getvalue()

                st.download_button(
                    label=f"⬇️ 페이지 {i+1} 이미지 다운로드 (PNG)",
                    data=byte_im,
                    file_name=image_names[i], # 위에 설정한 파일명 사용
                    mime="image/png"
                )
                st.markdown("---")

        except Exception as e:
            st.error(f"PDF를 이미지로 변환하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요: {e}")
            st.warning("혹시 PDF 파일이 손상되었거나 암호화되어 있을 수 있습니다.")

if __name__ == "__main__":
    main()
