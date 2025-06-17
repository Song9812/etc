import streamlit as st
import fitz  # PyMuPDF 라이브러리
import io
from PIL import Image, ImageDraw, ImageFont # Pillow 라이브러리 (ImageDraw, ImageFont 추가)
import zipfile

# Pillow에서 사용할 기본 폰트 설정
# 시스템 폰트 경로를 지정하지 않아도 되므로 SyntaxError 발생 가능성이 줄어듭니다.
# 단, 숫자의 가독성이 다소 떨어질 수 있습니다.
font = ImageFont.load_default()

# 세션 상태 초기화 (업로드 플래그)
if 'pdf_uploaded_flag' not in st.session_state:
    st.session_state.pdf_uploaded_flag = False

def main():
    st.title("📄 PDF 질문 영역 추출기 (좌표축 표시 버전)")
    st.markdown("---")
    st.write("PDF 파일을 업로드하고, 미리보기 이미지의 좌표축을 참고하여 질문 영역의 좌표를 입력해주세요.")
    st.warning("⚠️ **중요:** 모든 페이지의 질문 영역이 동일한 위치에 있어야 합니다.")

    uploaded_file = st.file_uploader("여기에 PDF 파일을 드래그하거나 클릭해서 업로드해주세요", type="pdf", key="pdf_uploader")

    # 파일이 새로 업로드되거나 변경되면 상태 초기화
    if uploaded_file is not None and st.session_state.pdf_uploaded_flag == False:
        st.session_state.pdf_uploaded_flag = True
        st.session_state.x0 = 0 # 좌표 입력값 초기화
        st.session_state.y0 = 0
        st.session_state.x1 = 0
        st.session_state.y1 = 0
        st.rerun() # 재실행하여 UI 초기화
    elif uploaded_file is None:
        st.session_state.pdf_uploaded_flag = False

    if uploaded_file is not None:
        st.success("PDF 파일이 성공적으로 업로드되었습니다!")
        st.spinner("PDF 로딩 중...")

        try:
            doc_preview = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            if len(doc_preview) > 0:
                first_page = doc_preview.load_page(0)
                
                # 미리보기를 위한 해상도 설정 (그리드를 그릴 이미지)
                preview_zoom = 1.5 # 1.0은 72 DPI, 1.5는 108 DPI 정도
                preview_matrix = fitz.Matrix(preview_zoom, preview_zoom)
                pix_preview = first_page.get_pixmap(matrix=preview_matrix)
                img_preview = Image.frombytes("RGB", [pix_preview.width, pix_preview.height], pix_preview.samples)
                
                doc_preview.close() # 미리보기용 문서 닫기

                # --- 이미지에 좌표 그리드 그리기 ---
                draw = ImageDraw.Draw(img_preview)
                grid_spacing = 50 # 그리드 간격 (픽셀)
                text_color = (0, 0, 255) # 파란색 텍스트
                line_color = (150, 150, 150, 128) # 회색 선, 반투명
                line_color_bold = (0, 0, 0, 200) # 진한 검정색 선

                # 가로선 그리기
                for y in range(0, img_preview.height, grid_spacing):
                    line_thick = 1 if (y / grid_spacing) % 2 != 0 else 2 # 짝수 간격마다 더 굵게
                    draw.line([(0, y), (img_preview.width, y)], fill=line_color if line_thick==1 else line_color_bold, width=line_thick)
                    draw.text((5, y + 2), str(int(y / preview_zoom)), fill=text_color, font=font) # 실제 PDF 좌표 표시

                # 세로선 그리기
                for x in range(0, img_preview.width, grid_spacing):
                    line_thick = 1 if (x / grid_spacing) % 2 != 0 else 2 # 짝수 간격마다 더 굵게
                    draw.line([(x, 0), (x, img_preview.height)], fill=line_color if line_thick==1 else line_color_bold, width=line_thick)
                    # 텍스트가 겹치지 않게 약간 아래로
                    if x > 0: # 0은 표시 안함
                        draw.text((x + 2, 5), str(int(x / preview_zoom)), fill=text_color, font=font) # 실제 PDF 좌표 표시

                st.subheader("💡 크롭할 영역의 좌표를 입력해주세요.")
                st.info("아래 첫 페이지 미리보기의 좌표축을 참고하여 질문이 있는 직사각형 영역의 **좌상단 (X, Y)** 과 **우하단 (X, Y)** 좌표를 입력해주세요.")
                st.caption(f"미리보기 이미지 크기: 가로 {img_preview.width}px, 세로 {img_preview.height}px (확대율 {preview_zoom:.1f}x)")
                st.caption("표시된 숫자는 PDF 원본(72 DPI 기준)의 좌표입니다.")

                st.image(img_preview, caption="PDF 첫 페이지 미리보기 (좌표축 표시)", use_column_width=True)

                st.markdown("---")

                # 사용자로부터 크롭 좌표 입력 받기
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### 좌상단 좌표 (시작점)")
                    # 세션 상태에 저장된 값 사용 또는 기본값 설정
                    x0 = st.number_input("X0 (왼쪽에서 시작)", min_value=0, value=st.session_state.get('x0', 50), step=10, key="x0_input")
                    y0 = st.number_input("Y0 (위에서 시작)", min_value=0, value=st.session_state.get('y0', 50), step=10, key="y0_input")
                with col2:
                    st.write("### 우하단 좌표 (끝점)")
                    x1 = st.number_input("X1 (왼쪽에서 시작)", min_value=0, value=st.session_state.get('x1', 750), step=10, key="x1_input")
                    y1 = st.number_input("Y1 (위에서 시작)", min_value=0, value=st.session_state.get('y1', 200), step=10, key="y1_input")
                
                # 입력된 좌표 세션 상태에 저장
                st.session_state.x0 = x0
                st.session_state.y0 = y0
                st.session_state.x1 = x1
                st.session_state.y1 = y1

                st.markdown("---")

                if st.button("🚀 질문 영역 추출 및 ZIP으로 다운로드 시작"):
                    if x1 <= x0 or y1 <= y0:
                        st.error("❌ 오류: X1은 X0보다 커야 하고, Y1은 Y0보다 커야 합니다. 유효한 좌표를 입력해주세요.")
                        return

                    st.spinner("질문 영역을 추출 중입니다. 잠시만 기다려 주세요...")

                    try:
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        cropped_images = []
                        image_names = []
                        
                        render_zoom = 4.0 
                        render_matrix = fitz.Matrix(render_zoom, render_zoom)

                        # 그리드에서 사용자가 본 원본 PDF 좌표(72 DPI 기준) 그대로 사용
                        clip_rect = fitz.Rect(x0, y0, x1, y1)

                        for page_num in range(len(doc)):
                            page = doc.load_page(page_num)
                            # 지정된 영역만 고해상도로 렌더링
                            cropped_pix = page.get_pixmap(matrix=render_matrix, clip=clip_rect)

                            if cropped_pix.n - cropped_pix.alpha > 3:
                                img = Image.frombytes("CMYK", [cropped_pix.width, cropped_pix.height], cropped_pix.samples)
                            else:
                                img = Image.frombytes("RGB", [cropped_pix.width, cropped_pix.height], cropped_pix.samples)

                            cropped_images.append(img)
                            image_names.append(f"{uploaded_file.name.replace('.pdf', '')}_Q_page_{page_num+1}.png")

                        doc.close()

                        st.success(f"✔️ 총 **{len(cropped_images)} 페이지**에서 질문 영역을 추출 완료했습니다!")
                        st.markdown("---")

                        if cropped_images:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                                for i, image in enumerate(cropped_images):
                                    img_byte_arr = io.BytesIO()
                                    image.save(img_byte_arr, format="PNG")
                                    zip_file.writestr(image_names[i], img_byte_arr.getvalue())

                            st.download_button(
                                label="⬇️ 추출된 질문 영역 이미지 ZIP 파일로 다운로드",
                                data=zip_buffer.getvalue(),
                                file_name=f"{uploaded_file.name.replace('.pdf', '')}_questions.zip",
                                mime="application/zip"
                            )
                            st.markdown("---")

                            st.subheader("미리보기 (처음 5장)")
                            for i, image in enumerate(cropped_images[:min(5, len(cropped_images))]):
                                st.image(image, caption=f"페이지 {i+1} 질문 영역", use_column_width=True)
                                if i < len(cropped_images) -1:
                                    st.markdown("---")
                            if len(cropped_images) > 5:
                                st.write(f"... 외 {len(cropped_images) - 5} 페이지")

                    except Exception as e:
                        st.error(f"⚠️ 오류가 발생했습니다: {e}")
                        st.warning("입력한 좌표가 이미지 크기를 벗어나거나 PDF 파일에 문제가 있을 수 있습니다.")
            else:
                st.error("⚠️ 오류: PDF 파일에서 페이지를 찾을 수 없습니다.")

    else:
        st.info("PDF 파일을 업로드하시면 첫 페이지 미리보기가 나타납니다. 좌표축을 참고하여 영역을 입력해주세요.")

if __name__ == "__main__":
    main()
