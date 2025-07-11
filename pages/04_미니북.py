import streamlit as st
import fitz  # PyMuPDF
import io

# --- 페이지 레이아웃 정의 (A4 기준) ---
# A4 사이즈: 210mm x 297mm -> 픽셀 단위 (예: 72 DPI 기준)
# 1포인트 = 1/72 인치 (약 0.3528mm)
# A4는 약 595 x 842 포인트 (Portrait)
# A4 Landscape: 842 x 595 포인트

A4_LANDSCAPE_WIDTH = 842
A4_LANDSCAPE_HEIGHT = 595

# 미니북 레이아웃 (A4 가로 방향 기준, 페이지 순서와 회전 각도 중요!)
# 아래 배열은 A4 한 장에 8페이지가 들어갈 때, 인쇄 후 접었을 때 올바른 순서가 되도록 설계된 예시입니다.
# 실제 접는 방법에 따라 이 부분은 수정되어야 합니다.
# (원본 페이지 번호, X 위치, Y 위치, 회전 각도)
# (0-indexed: 0=1페이지, 1=2페이지, ..., 7=8페이지)

# 예시 레이아웃: A4를 가로로 놓고, 왼쪽 절반에 8,1, 오른쪽 절반에 2,7
# 아래쪽 절반에 6,3, 4,5 가 되도록
# 이 레이아웃은 A4를 가로로 놓고, 세로로 반 접고, 그 상태에서 가로로 반 접고, 다시 세로로 반 접어서
# 칼집을 낸 후 펼쳐서 만드는 방식 중 하나를 가정한 것입니다.
# (원본 페이지 인덱스, x_offset, y_offset, rotation_degrees)
PAGE_LAYOUT = [
    # 상단 왼쪽 (인쇄면 기준)
    {'page_idx': 7, 'x_offset': 0, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 180}, # 8페이지 (거꾸로)
    {'page_idx': 0, 'x_offset': A4_LANDSCAPE_WIDTH / 4, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 0}, # 1페이지
    {'page_idx': 1, 'x_offset': A4_LANDSCAPE_WIDTH / 2, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 0}, # 2페이지
    {'page_idx': 6, 'x_offset': A4_LANDSCAPE_WIDTH * 3 / 4, 'y_offset': A4_LANDSCAPE_HEIGHT / 2, 'rotation': 180}, # 7페이지 (거꾸로)

    # 하단 왼쪽 (인쇄면 기준)
    {'page_idx': 5, 'x_offset': 0, 'y_offset': 0, 'rotation': 180}, # 6페이지 (거꾸로)
    {'page_idx': 2, 'x_offset': A4_LANDSCAPE_WIDTH / 4, 'y_offset': 0, 'rotation': 0}, # 3페이지
    {'page_idx': 3, 'x_offset': A4_LANDSCAPE_WIDTH / 2, 'y_offset': 0, 'rotation': 0}, # 4페이지
    {'page_idx': 4, 'x_offset': A4_LANDSCAPE_WIDTH * 3 / 4, 'y_offset': 0, 'rotation': 0}  # 5페이지
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

        # 새로운 A4 가로 방향 PDF 생성
        output_pdf = fitz.open()
        new_page = output_pdf.new_page(width=A4_LANDSCAPE_WIDTH, height=A4_LANDSCAPE_HEIGHT)

        # 각 원본 페이지를 새로운 페이지에 배치
        for page_info in PAGE_LAYOUT:
            original_page_idx = page_info['page_idx']
            x_offset = page_info['x_offset']
            y_offset = page_info['y_offset']
            rotation = page_info['rotation']

            if original_page_idx >= len(input_pdf):
                st.warning(f"경고: 원본 PDF에 {original_page_idx + 1} 페이지가 없습니다. 레이아웃 설정을 확인하세요.")
                continue

            # 원본 페이지 가져오기
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

            scaled_width = orig_page_width * scale
            scaled_height = orig_page_height * scale

            # 삽입할 사각형 (x0, y0, x1, y1)
            # x0, y0는 삽입될 페이지의 왼쪽 하단 좌표
            # PyMuPDF의 insert_pdf_page는 x_offset, y_offset이 왼쪽 상단 기준
            # 그러나 회전 시 기준점은 달라지므로 transform 매트릭스를 사용하는 것이 안정적

            # 변환 매트릭스 생성
            # 1. 크기 조절
            matrix = fitz.Matrix(scale, scale)

            # 2. 회전 (중심 기준 회전이 아니므로, 나중에 translate로 위치 조정)
            if rotation == 90:
                matrix = matrix.pre_rotate(90)
            elif rotation == 180:
                matrix = matrix.pre_rotate(180)
            elif rotation == 270:
                matrix = matrix.pre_rotate(270)

            # 3. 위치 이동
            # rotate된 페이지의 새로운 크기 계산
            rotated_bbox = fitz.Rect(0, 0, orig_page_width, orig_page_height).transform(matrix)
            rotated_width = rotated_bbox.width
            rotated_height = rotated_bbox.height

            # 중앙 정렬을 위한 추가 오프셋 계산 (각 칸의 중앙에 오도록)
            center_x_offset = (target_width - rotated_width) / 2
            center_y_offset = (target_height - rotated_height) / 2


            # 최종 삽입 위치 (페이지 레이아웃의 x,y_offset + 중앙 정렬 오프셋)
            # PyMuPDF의 insert_pdf_page는 rect가 아닌, point (x,y)로 삽입 시작점을 받음.
            # 이 시작점은 회전된 페이지의 좌측 상단이 될 것임.
            final_x = x_offset + center_x_offset
            final_y = y_offset + center_y_offset

            # 페이지 삽입
            # insert_pdf(from_pdf, from_page_num, to_page_num, from_x, from_y, to_x, to_y, rotate)는 복잡
            # 더 간단한 방법은 새 페이지에 draw_pdf_page를 사용하는 것.
            # draw_pdf_page(rect, page, matrix, overlay)
            # rect: 새 페이지 내에서 원본 페이지가 그려질 영역
            # page: 원본 페이지
            # matrix: 변환 매트릭스 (스케일, 회전, 이동)

            # 새 페이지에 원본 페이지 그리기 (매트릭스 사용)
            # PyMuPDF의 Matrix는 post-multiply 방식으로 적용됨.
            # 따라서 이동(translate)은 마지막에 적용되어야 함.
            # rotate된 페이지를 최종 위치로 옮기기 위한 translate 매트릭스 추가
            final_matrix = fitz.Matrix(scale, scale)
            if rotation == 90:
                final_matrix = final_matrix.pre_rotate(90)
            elif rotation == 180:
                final_matrix = final_matrix.pre_rotate(180)
            elif rotation == 270:
                final_matrix = final_matrix.pre_rotate(270)

            # 최종 위치로 이동 (x, y)
            final_matrix = final_matrix.pre_translate(final_x, final_y)

            # 원본 페이지의 내용을 새 페이지에 그립니다.
            # draw_pdf_page는 첫 번째 인자로 사각형을 받지만, 실제로는 matrix로 모든 변환을 제어하는 것이 일반적
            # 여기서는 전체 A4 페이지를 rect로 주고, matrix로 페이지를 그릴 위치를 조정.
            new_page.show_pdf_page(fitz.Rect(0, 0, A4_LANDSCAPE_WIDTH, A4_LANDSCAPE_HEIGHT), input_pdf, original_page_idx, matrix=final_matrix)


        # 결과 PDF를 메모리에 저장
        output_buffer = io.BytesIO()
        output_pdf.save(output_buffer)
        output_pdf.close()
        input_pdf.close()
        return output_buffer.getvalue()

    except Exception as e:
        st.error(f"PDF 변환 중 오류가 발생했습니다: {e}")
        return None

# --- Streamlit 앱 UI ---
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
