import streamlit as st
import fitz  # PyMuPDF
import io

# --- 페이지 레이아웃 정의 (A4 기준) ---
# 기존과 동일
A4_LANDSCAPE_WIDTH = 842
A4_LANDSCAPE_HEIGHT = 595

PAGE_LAYOUT = [
    {'page_idx': 7, 'x_offset': 0, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 180},
    {'page_idx': 0, 'x_offset': A4_LANDSCAPE_WIDTH / 4, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 0},
    {'page_idx': 1, 'x_offset': A4_LANDSCAPE_WIDTH / 2, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 0},
    {'page_idx': 6, 'x_offset': A4_LANDSCAPE_WIDTH * 3 / 4, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 180},

    {'page_idx': 5, 'x_offset': 0, 'y_offset': 0, 'rotation': 180},
    {'page_idx': 2, 'x_offset': A4_LANDSCAPE_WIDTH / 4, 'y_offset': 0, 'rotation': 0},
    {'page_idx': 3, 'x_offset': A4_LANDSCAPE_WIDTH / 2, 'y_offset': 0, 'rotation': 0},
    {'page_idx': 4, 'x_offset': A4_LANDSCAPE_WIDTH * 3 / 4, 'y_offset': 0, 'rotation': 0}
]

def create_mini_book_pdf(input_pdf_bytes):
    """
    업로드된 8페이지 PDF를 A4 미니북 형태로 변환합니다.
    """
    try:
        input_pdf = fitz.open(stream=input_pdf_bytes, filetype="pdf")

        if len(input_pdf) != 8:
            st.error(f"⚠️ 업로드된 PDF는 8페이지여야 합니다. 현재 페이지 수는 {len(input_pdf)}페이지 입니다.")
            return None

        output_pdf = fitz.open()
        new_page = output_pdf.new_page(width=A4_LANDSCAPE_WIDTH, height=A4_LANDSCAPE_HEIGHT)

        for page_info in PAGE_LAYOUT:
            original_page_idx = page_info['page_idx']
            x_offset = page_info['x_offset']
            y_offset = page_info['y_offset']
            rotation = page_info['rotation']

            if original_page_idx >= len(input_pdf):
                st.warning(f"경고: 원본 PDF에 {original_page_idx + 1} 페이지가 없습니다. 레이아웃 설정을 확인하세요.")
                continue

            orig_page = input_pdf.load_page(original_page_idx)

            # 원본 페이지 크기
            orig_page_width = orig_page.rect.width
            orig_page_height = orig_page.rect.height

            # A4 한 칸에 들어갈 페이지의 목표 크기 (A4 가로의 1/4 폭, 1/2 높이)
            target_width = A4_LANDSCAPE_WIDTH / 4
            target_height = A4_LANDSCAPE_HEIGHT / 2

            # 원본 비율 유지하면서 target_width, target_height 에 맞게 스케일
            scale_x = target_width / orig_page_width
            scale_y = target_height / orig_page_height
            scale = min(scale_x, scale_y) # 종횡비 유지

            # --- 이 부분이 핵심 수정! ---
            # 1. 스케일링 매트릭스 생성
            scale_matrix = fitz.Matrix(scale, scale)

            # 2. 회전 매트릭스 생성
            rotate_matrix = fitz.Matrix(rotation=rotation)

            # 3. 이동 매트릭스 생성 (나중에 중앙 정렬 오프셋과 함께 적용)
            # 회전 후의 페이지 바운딩 박스 계산을 위해 일단 스케일 + 회전만 적용한 매트릭스
            combined_matrix_for_bbox = scale_matrix * rotate_matrix

            rotated_bbox = orig_page.rect.transform(combined_matrix_for_bbox)
            rotated_width = rotated_bbox.width
            rotated_height = rotated_bbox.height

            # 각 칸의 중앙에 오도록 추가 오프셋 계산
            center_x_offset = (target_width - rotated_width) / 2
            center_y_offset = (target_height - rotated_height) / 2

            # 4. 최종 변환 매트릭스 합성 (스케일 -> 회전 -> 이동 순서)
            # PyMuPDF의 행렬은 (x', y') = (x, y) * M 이므로,
            # (원본) * 스케일 * 회전 * 이동 순서로 곱해야 합니다.
            # translate 매트릭스는 최종 위치로 옮기는 역할을 합니다.
            translate_matrix = fitz.Matrix(1, 0, 0, 1, x_offset + center_x_offset, y_offset + center_y_offset)

            # 최종 매트릭스 = (스케일 매트릭스 * 회전 매트릭스) * 이동 매트릭스
            final_matrix = scale_matrix * rotate_matrix * translate_matrix

            # 새 페이지에 원본 페이지 그리기 (매트릭스 사용)
            # show_pdf_page는 원본 페이지를 매트릭스로 변환하여 대상 문서에 그립니다.
            new_page.show_pdf_page(new_page.rect, input_pdf, original_page_idx, matrix=final_matrix)

        # 결과 PDF를 메모리에 저장
        output_buffer = io.BytesIO()
        output_pdf.save(output_buffer)
        output_pdf.close()
        input_pdf.close()
        return output_buffer.getvalue()

    except Exception as e:
        st.error(f"PDF 변환 중 오류가 발생했습니다: {e}")
        return None

# --- Streamlit 앱 UI (이 부분은 이전과 동일) ---
st.set_page_config(layout="centered", page_title="미니북 PDF 변환기")

st.title("✂️ 8페이지 미니북 PDF 변환기")

st.markdown("""
A4 용지 한 장으로 만들 수 있는 8페이지 미니북 PDF를 생성합니다.
8페이지 PDF를 업로드하면, 인쇄 후 바로 접을 수 있도록 페이지 순서와 방향을 조절하여 하나의 A4 PDF로 만들어 드립니다.

**⚠️ 중요**: 이 도구는 특정 미니북 접는 방식을 가정하고 있습니다.
인쇄 후 올바르게 접히는지 확인하기 위해 **[미니북 접는 방법](https://www.google.com/search?q=a4+%EB%AF%B8%EB%8B%8B%EC%9B%85+%EB%A7%8C%EB%93%A4%EA%B8%B0&tbm=vid)**을 참고해주세요!
(예시 검색 링크이며, 정확한 접는 방법을 영상으로 확인하시는 것을 추천합니다.)
""")

uploaded_file = st.file_uploader("8페이지 PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None:
    st.info("PDF 파일을 읽는 중...")
    pdf_bytes = uploaded_file.read()

    with st.spinner("미니북 PDF를 생성 중입니다... 📄"):
        transformed_pdf_bytes = create_mini_book_pdf(pdf_bytes)

    if transformed_pdf_bytes:
        st.success("미니북 PDF 생성이 완료되었습니다! 🎉")
        st.download_button(
            label="미니북 PDF 다운로드",
            data=transformed_pdf_bytes,
            file_name="minibook_output.pdf",
            mime="application/pdf"
        )
        st.markdown("""
        **[다운로드]** 받은 PDF를 A4 용지에 **가로(Landscape) 방향**으로 인쇄하세요.
        """)
        st.subheader("미니북 접는 방법 (예시)")
        st.markdown("""
        1.  인쇄된 A4 용지를 가로로 놓습니다.
        2.  정확한 미니북을 만들기 위해 **[이 영상](https://www.youtube.com/watch?v=F0pYdE69y64)** (예시 유튜브 링크)을 참고하여 종이를 접고 칼집을 내세요.
        """)
    else:
        st.error("PDF 변환에 실패했습니다. 파일을 다시 확인해주세요.")

st.markdown("---")
st.markdown("Made with ❤️ by Your Name")
