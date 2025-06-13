import streamlit as st
import fitz  # PyMuPDF 라이브러리
import io
from PIL import Image # 이미지 처리를 위해 Pillow 라이브러리 필요
import zipfile
from streamlit_drawable_canvas import st_canvas # 캔버스 라이브러리

def main():
    st.title("📄 PDF 질문 영역 추출기 (클릭으로 영역 설정)")
    st.markdown("---")
    st.write("PDF 파일을 업로드하고, **첫 페이지 미리보기에서 질문 영역의 좌상단과 우하단을 각각 클릭**해주세요. 해당 영역만 모든 페이지에서 잘라내어 이미지로 저장합니다.")
    st.warning("⚠️ **중요:** 모든 페이지의 질문 영역이 동일한 위치에 있어야 합니다.")

    uploaded_file = st.file_uploader("여기에 PDF 파일을 드래그하거나 클릭해서 업로드해주세요", type="pdf")

    if uploaded_file is not None:
        st.success("PDF 파일이 성공적으로 업로드되었습니다!")
        st.spinner("PDF 로딩 중...")

        # PDF 첫 페이지 로드 및 캔버스 준비
        doc_preview = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        if len(doc_preview) > 0:
            first_page = doc_preview.load_page(0)
            
            # 미리보기를 위한 해상도 설정 (캔버스에 표시될 이미지)
            # 너무 높은 DPI는 웹 페이지 로딩을 느리게 합니다.
            preview_zoom = 1.5 # 1.0은 72 DPI, 1.5는 108 DPI 정도
            preview_matrix = fitz.Matrix(preview_zoom, preview_zoom)
            pix_preview = first_page.get_pixmap(matrix=preview_matrix)
            img_preview = Image.frombytes("RGB", [pix_preview.width, pix_preview.height], pix_preview.samples)
            
            # 캔버스에 표시할 이미지의 너비를 Streamlit 컬럼 너비에 맞춥니다.
            # 이 너비를 기준으로 클릭 좌표를 스케일링해야 합니다.
            canvas_width = st.session_state.get('canvas_width', pix_preview.width) # 세션 스테이트에 저장된 너비가 있으면 사용
            st.session_state['canvas_width'] = canvas_width # 없으면 현재 너비 저장

            st.subheader("💡 질문 영역의 좌상단과 우하단을 클릭해주세요.")
            st.info("미리보기 이미지에서 **첫 번째 클릭은 좌상단**, **두 번째 클릭은 우하단**이 됩니다. 영역이 선택되면 자동으로 추출을 시작합니다.")

            # st_canvas를 사용하여 이미지 위에 클릭 영역 설정
            # drawing_mode="point"로 설정하여 클릭 지점을 얻습니다.
            # key를 다르게 하여 여러 번 클릭 가능하도록 합니다.
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",  # 채우기 색상 (주황색, 투명도 30%)
                stroke_width=2,
                stroke_color="rgba(255, 0, 0, 1)", # 선 색상 (빨간색)
                background_image=img_preview,
                height=pix_preview.height,
                width=canvas_width, # 캔버스 너비
                drawing_mode="point", # 클릭 모드
                key="canvas_select_area",
                display_toolbar=True # 툴바 표시 (포인터 선택 가능)
            )
            
            doc_preview.close() # 미리보기용 문서 닫기

            # 클릭 좌표 추출 및 크롭 로직
            # st_canvas는 'points' 키를 통해 클릭된 지점들을 리스트로 반환합니다.
            if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
                points = []
                for obj in canvas_result.json_data["objects"]:
                    if obj["type"] == "point":
                        # 캔버스상의 클릭 좌표를 실제 이미지 픽셀 좌표로 변환
                        # 캔버스 너비와 원본 이미지 너비 비율로 스케일링
                        scale_factor_x = pix_preview.width / canvas_result.width if canvas_result.width else 1
                        scale_factor_y = pix_preview.height / canvas_result.height if canvas_result.height else 1
                        points.append({
                            "x": int(obj["left"] * scale_factor_x),
                            "y": int(obj["top"] * scale_factor_y)
                        })

                if len(points) >= 2:
                    # 첫 번째 클릭은 좌상단, 두 번째 클릭은 우하단으로 간주
                    x0 = min(points[0]["x"], points[1]["x"])
                    y0 = min(points[0]["y"], points[1]["y"])
                    x1 = max(points[0]["x"], points[1]["x"])
                    y1 = max(points[0]["y"], points[1]["y"])

                    st.write(f"선택된 영역: 좌상단 ({x0}, {y0}), 우하단 ({x1}, {y1})")
                    st.success("영역이 선택되었습니다. 아래 버튼을 클릭하여 추출을 시작하세요!")

                    st.markdown("---")
                    
                    if st.button("🚀 선택된 영역 추출 및 ZIP으로 다운로드"):
                        if x1 <= x0 or y1 <= y0:
                            st.error("❌ 오류: 유효한 영역이 선택되지 않았습니다. 좌상단과 우하단을 정확히 클릭해주세요.")
                            return

                        st.spinner("질문 영역을 추출 중입니다. 잠시만 기다려 주세요...")

                        try:
                            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                            cropped_images = []
                            image_names = []
                            
                            # 추출 해상도 설정 (높을수록 좋음)
                            render_zoom = 4.0 # 4.0은 약 288 DPI로 렌더링
                            render_matrix = fitz.Matrix(render_zoom, render_zoom)

                            # 렌더링된 픽셀맵 기준으로 크롭할 영역 계산
                            # 입력받은 좌표(preview_zoom 기준)를 render_zoom 기준으로 스케일링합니다.
                            # 즉, (원본 72DPI 기준 x0, y0) -> (preview_zoom 기준 x0, y0) -> (render_zoom 기준 scaled_x0, scaled_y0)
                            # -> PyMuPDF의 픽셀맵 좌표는 기본적으로 72 DPI 기준입니다.
                            # -> preview_zoom이 1.5일 때의 x0, y0이므로, 72DPI 기준 좌표로 다시 역변환하여 fitz.Rect에 넣고,
                            # -> 이후 get_pixmap에서 render_matrix를 사용하면 fitz가 알아서 최종 픽셀맵을 만들 때 스케일링합니다.
                            # 정확한 방법: 클릭으로 얻은 좌표는 `preview_zoom`이 적용된 이미지의 좌표입니다.
                            # 이 좌표를 `preview_zoom`으로 나누어 원본 PDF의 72DPI 기준 좌표로 되돌린 후,
                            # 이 좌표를 `fitz.Rect`에 넣어 `get_pixmap`의 `clip` 인자에 사용하고,
                            # `get_pixmap`의 `matrix` 인자로는 `render_matrix`를 사용하면 됩니다.
                            
                            original_x0 = x0 / preview_zoom
                            original_y0 = y0 / preview_zoom
                            original_x1 = x1 / preview_zoom
                            original_y1 = y1 / preview_zoom

                            clip_rect = fitz.Rect(original_x0, original_y0, original_x1, original_y1)

                            for page_num in range(len(doc)):
                                page = doc.load_page(page_num)
                                # 지정된 영역만 고해상도로 렌더링 (clip과 matrix 동시에 사용)
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
                            st.warning("선택한 영역이 너무 작거나 PDF 파일에 문제가 있을 수 있습니다. 다시 시도해주세요.")

        else: # 파일 업로드 후 아직 캔버스 클릭 전
            st.info("PDF 파일을 업로드하시면 첫 페이지 미리보기가 나타납니다. 그 위에서 마우스로 영역을 클릭해주세요.")

if __name__ == "__main__":
    main()
