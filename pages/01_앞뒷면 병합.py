import streamlit as st
from pypdf import PdfReader, PdfWriter # PyPDF2 대신 pypdf 임포트
import io

st.set_page_config(layout="centered") # 페이지 레이아웃 설정 (선택 사항)
st.title("스캔 문서 병합 서비스 (앞면/뒷면)")
st.write("앞면 스캔본(정순)과 뒷면 스캔본(역순)을 업로드하여 올바른 순서로 병합합니다.")

# --- 1. 파일 업로드 ---
front_file = st.file_uploader("앞면 PDF 파일 업로드 (예: Page1-33)", type="pdf")
back_file = st.file_uploader("뒷면 PDF 파일 업로드 (예: Page33-1)", type="pdf")

if front_file and back_file:
    try:
        front_reader = PdfReader(front_file)
        back_reader = PdfReader(back_file)

        front_num_pages = len(front_reader.pages)
        back_num_pages = len(back_reader.pages)

        # --- 2. 페이지 수 확인 및 경고 ---
        if front_num_pages != back_num_pages:
            st.warning(
                f"경고: 앞면 PDF({front_num_pages} 페이지)와 뒷면 PDF({back_num_pages} 페이지)의 페이지 수가 다릅니다. "
                "병합 결과가 예상과 다를 수 있습니다."
            )
            proceed = st.button("계속 진행")
            if not proceed:
                st.stop() # '계속 진행' 버튼을 누르지 않으면 여기서 앱 실행 중지
        
        st.success(f"앞면 PDF: {front_num_pages} 페이지, 뒷면 PDF: {back_num_pages} 페이지")

        pdf_writer = PdfWriter()

        # --- 3. 페이지 짝 맞추어 병합 ---
        # 뒷면 페이지는 역순으로 접근해야 합니다.
        # 앞면과 뒷면 중 페이지 수가 적은 쪽에 맞춰서 반복합니다.
        max_pages = max(front_num_pages, back_num_pages)

        for i in range(max_pages):
            # 앞면 페이지 추가 (순방향)
            if i < front_num_pages:
                pdf_writer.add_page(front_reader.pages[i])
            else:
                st.info(f"앞면 PDF에 더 이상 추가할 페이지가 없습니다. 뒷면만 계속 추가합니다.")

            # 뒷면 페이지 추가 (역방향)
            # 뒷면의 마지막 페이지부터 앞면의 첫 페이지와 짝을 이룹니다.
            if i < back_num_pages:
                pdf_writer.add_page(back_reader.pages[back_num_pages - 1 - i])
            else:
                if i < front_num_pages: # 앞면 페이지가 남아있는데 뒷면이 없는 경우에만 경고
                    st.info(f"뒷면 PDF에 더 이상 추가할 페이지가 없습니다. 앞면만 계속 추가합니다.")


        # --- 4. 결과 PDF 다운로드 ---
        output_pdf_bytes = io.BytesIO()
        pdf_writer.write(output_pdf_bytes)
        output_pdf_bytes.seek(0) # 스트림의 시작으로 이동

        st.download_button(
            label="병합된 PDF 다운로드",
            data=output_pdf_bytes,
            file_name="merged_document.pdf",
            mime="application/pdf"
        )
        st.success("PDF 병합이 완료되었습니다. 위 버튼을 눌러 다운로드하세요.")

    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        st.warning("업로드된 파일이 유효한 PDF 파일인지, 그리고 파일이 손상되지 않았는지 확인해주세요.")

else:
    st.info("앞면 PDF와 뒷면 PDF 파일을 모두 업로드해주세요.")
