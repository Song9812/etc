import streamlit as st
from pypdf import PdfReader, PdfWriter
import io

st.set_page_config(layout="centered")
st.title("스캔 문서 병합 서비스 (앞면/뒷면)")
st.write("앞면 스캔본(정순)과 뒷면 스캔본(역순)을 업로드하여 올바른 순서로 병합합니다.")

# --- 1. 파일 업로드 ---
front_file = st.file_uploader("앞면 PDF 파일 업로드 (예: Page1-33)", type="pdf")
back_file = st.file_uploader("뒷면 PDF 파일 업로드 (예: Page33-1)", type="pdf")

# --- 2. 파일명 입력 필드 추가 ---
# 기본 파일명 제안
default_filename = "merged_document.pdf"
if front_file and back_file:
    # 업로드된 파일명에서 확장자를 제외하고 조합하여 기본값 제공
    front_name = front_file.name.rsplit('.', 1)[0]
    back_name = back_file.name.rsplit('.', 1)[0]
    default_filename = f"{front_name}_{back_name}_merged.pdf"

output_filename = st.text_input(
    "저장할 병합 PDF 파일명을 입력하세요:", 
    value=default_filename # 초기값 설정
)

# 파일명에 .pdf 확장자가 없으면 자동으로 추가
if output_filename and not output_filename.endswith(".pdf"):
    output_filename += ".pdf"
elif not output_filename: # 파일명이 비어있으면 기본값으로 대체
    output_filename = "merged_document.pdf"


if front_file and back_file:
    try:
        front_reader = PdfReader(front_file)
        back_reader = PdfReader(back_file)

        front_num_pages = len(front_reader.pages)
        back_num_pages = len(back_reader.pages)

        # --- 3. 페이지 수 확인 및 경고 ---
        if front_num_pages != back_num_pages:
            st.warning(
                f"경고: 앞면 PDF({front_num_pages} 페이지)와 뒷면 PDF({back_num_pages} 페이지)의 페이지 수가 다릅니다. "
                "병합 결과가 예상과 다를 수 있습니다."
            )
            proceed = st.button("계속 진행")
            if not proceed:
                st.stop()
        
        st.success(f"앞면 PDF: {front_num_pages} 페이지, 뒷면 PDF: {back_num_pages} 페이지")

        pdf_writer = PdfWriter()

        # --- 4. 페이지 짝 맞추어 병합 ---
        max_pages = max(front_num_pages, back_num_pages)

        for i in range(max_pages):
            # 앞면 페이지 추가 (순방향)
            if i < front_num_pages:
                pdf_writer.add_page(front_reader.pages[i])
            else:
                st.info(f"앞면 PDF에 더 이상 추가할 페이지가 없습니다. 뒷면만 계속 추가합니다.")

            # 뒷면 페이지 추가 (역방향)
            if i < back_num_pages:
                pdf_writer.add_page(back_reader.pages[back_num_pages - 1 - i])
            else:
                if i < front_num_pages:
                    st.info(f"뒷면 PDF에 더 이상 추가할 페이지가 없습니다. 앞면만 계속 추가합니다.")


        # --- 5. 결과 PDF 다운로드 ---
        output_pdf_bytes = io.BytesIO()
        pdf_writer.write(output_pdf_bytes)
        output_pdf_bytes.seek(0)

        st.download_button(
            label="병합된 PDF 다운로드",
            data=output_pdf_bytes,
            file_name=output_filename, # 사용자 입력 파일명 사용
            mime="application/pdf"
        )
        st.success(f"PDF 병합이 완료되었습니다. '{output_filename}' 이름으로 다운로드하세요.")

    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        st.warning("업로드된 파일이 유효한 PDF 파일인지, 그리고 파일이 손상되지 않았는지 확인해주세요.")

else:
    st.info("앞면 PDF와 뒷면 PDF 파일을 모두 업로드해주세요.")
