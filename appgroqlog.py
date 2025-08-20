import streamlit as st
import groq
from PIL import Image
import os
import time
import base64

# Impor library yang dibutuhkan
import markdown2
from xhtml2pdf import pisa
from io import BytesIO, StringIO

# Tambahan untuk Excel
import pandas as pd
import re

# --- 1. Konfigurasi Halaman Web ---
st.set_page_config(
    page_title="Alfa Threat Model Expert Analysis",
    page_icon="⚡️",
    layout="centered"
)

# =========================
# ====== PDF UTILS ========
# =========================
def create_pdf_with_xhtml2pdf(markdown_content, filename="alfa_threat_analysis.pdf"):
    """
    Mengubah konten Markdown menjadi PDF yang rapi menggunakan xhtml2pdf.
    Solusi ini murni Python dan tidak memerlukan packages.txt.
    """
    try:
        # 1. Ubah Markdown ke HTML
        html_string = markdown2.markdown(
            markdown_content,
            extras=["tables", "fenced-code-blocks", "code-friendly"]
        )

        # 2. Tambahkan CSS untuk memastikan tabel dan format lainnya rapi
        full_html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{ margin: 2cm; }}
                    body {{ font-family: 'Helvetica', sans-serif; font-size: 10pt; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #000; padding: 5px; text-align: left; vertical-align: top; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    pre, code {{
                        background-color: #f4f4f4; padding: 2px 4px;
                        border: 1px solid #ddd; border-radius: 3px;
                        font-family: 'Courier New', monospace; white-space: pre-wrap;
                    }}
                    h1, h2, h3, h4 {{ margin-top: 12px; }}
                    p {{ line-height: 1.35; }}
                </style>
            </head>
            <body>
                {html_string}
            </body>
        </html>
        """

        # 3. Buat PDF di memori
        result_file = BytesIO()
        pisa_status = pisa.CreatePDF(
            BytesIO(full_html.encode("UTF-8")), # source HTML
            dest=result_file,                   # destination file
            encoding='UTF-8'
        )

        # 4. Jika pembuatan PDF gagal, tampilkan error
        if pisa_status.err:
            st.error(f"Gagal membuat PDF: {pisa_status.err}")
            return ""

        # 5. Siapkan tautan unduhan
        result_file.seek(0)
        b64_pdf = base64.b64encode(result_file.read()).decode()

        href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{filename}" style="display: inline-block; padding: 8px 12px; background-color: #FF4B4B; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">💾 Unduh Analisis (PDF)</a>'
        return href

    except Exception as e:
        st.error(f"Terjadi kesalahan tak terduga saat membuat PDF: {e}")
        return ""


# =========================
# ===== EXCEL UTILS =======
# =========================
def _autofit_and_style_excel(writer, sheet_name, df):
    """Styling ringan agar Excel rapi pada engine openpyxl/xlsxwriter."""
    try:
        # Engine openpyxl
        if hasattr(writer, 'book') and getattr(writer, 'engine', None) in ('openpyxl',):
            ws = writer.sheets[sheet_name]
            from openpyxl.styles import Font, Alignment
            header_font = Font(bold=True)
            # Header: bold + wrap
            for cell in ws[1]:
                cell.font = header_font
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            # Data: wrap + top
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=ws.max_column):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
            # Freeze header
            ws.freeze_panes = "A2"
            # Auto width sederhana
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        max_len = max(max_len, len(str(cell.value)) if cell.value is not None else 0)
                    except:
                        pass
                ws.column_dimensions[col_letter].width = min(max(12, max_len + 2), 60)

        # Engine xlsxwriter
        elif hasattr(writer, 'book') and getattr(writer, 'engine', None) in ('xlsxwriter',):
            workbook  = writer.book
            worksheet = writer.sheets[sheet_name]
            wrap = workbook.add_format({'text_wrap': True, 'valign': 'top'})
            header_fmt = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top'})
            # Header format
            for col_num, _ in enumerate(df.columns.values):
                worksheet.write(0, col_num, df.columns[col_num], header_fmt)
            # Wrap semua sel data + lebar awal
            worksheet.set_column(0, len(df.columns) - 1, 12, wrap)
            # Freeze header
            worksheet.freeze_panes(1, 0)
            # Auto width sederhana per kolom
            for i, col in enumerate(df.columns):
                max_len = max([len(str(x)) if x is not None else 0 for x in [col] + df[col].tolist()])
                worksheet.set_column(i, i, min(max(12, max_len + 2), 60))
    except Exception:
        # Styling opsional—biarkan lewat jika gagal
        pass


def _parse_markdown_tables_simple(md_text):
    """
    Fallback sederhana: parse tabel Markdown (| col | ...).
    Kembalikan list DataFrame.
    """
    lines = md_text.strip().splitlines()
    tables = []
    i = 0
    while i < len(lines):
        if '|' in lines[i]:
            # Header separator (---|---)
            if i + 1 < len(lines) and re.search(r'^\s*\|?\s*:?-{3,}.*\|.*-+', lines[i+1]):
                start = i
                j = i
                # ambil blok hingga baris non-tabel/kode
                while j < len(lines) and '|' in lines[j] and not lines[j].strip().startswith('```'):
                    j += 1
                block = lines[start:j]

                def split_row(row):
                    row = row.strip()
                    if row.startswith('|'): row = row[1:]
                    if row.endswith('|'): row = row[:-1]
                    return [c.strip() for c in row.split('|')]

                if len(block) >= 2:
                    header = split_row(block[0])
                    data_rows = [split_row(r) for r in block[2:]]  # lewati separator
                    max_cols = len(header)
                    norm = []
                    for r in data_rows:
                        if len(r) < max_cols:
                            r = r + ['']*(max_cols-len(r))
                        elif len(r) > max_cols:
                            r = r[:max_cols]
                        norm.append(r)
                    try:
                        df = pd.DataFrame(norm, columns=header)
                        tables.append(df)
                    except Exception:
                        pass
                i = j
                continue
        i += 1
    return tables


def create_excel_from_markdown(markdown_content: str, filename: str = "alfa_threat_analysis.xlsx"):
    """
    Mengubah output markdown asisten menjadi file Excel yang rapi.
    - Deteksi semua tabel; tiap tabel jadi sheet sendiri (Table1, Table2, …).
    - Jika tidak ada tabel, seluruh teks dimasukkan ke satu sheet 'Output' kolom A.
    Mengembalikan bytes Excel untuk dipakai di st.download_button.
    """
    try:
        # 1) Coba via pandas.read_html dari HTML hasil markdown2
        html_string = markdown2.markdown(
            markdown_content,
            extras=["tables", "fenced-code-blocks", "code-friendly"]
        )
        tables = []
        try:
            tables = pd.read_html(StringIO(html_string))
        except Exception:
            tables = []

        # 2) Fallback parser sederhana jika tidak ada tabel
        if not tables:
            tables = _parse_markdown_tables_simple(markdown_content)

        # 3) Jika tetap tidak ada tabel → masukkan teks apa adanya
        only_text_mode = False
        if not tables:
            only_text_mode = True
            tables = [pd.DataFrame({"Output": [markdown_content]})]

        # 4) Tulis Excel ke memori
        output = BytesIO()

        # Pilih engine yang tersedia
        engine = None
        try:
            import openpyxl  # noqa
            engine = "openpyxl"
        except Exception:
            try:
                import xlsxwriter  # noqa
                engine = "xlsxwriter"
            except Exception:
                engine = None

        if engine:
            with pd.ExcelWriter(output, engine=engine) as writer:
                for idx, df in enumerate(tables, start=1):
                    sheet_name = "Output" if (only_text_mode and idx == 1) else f"Table{idx}"
                    # Bersihkan kolom object agar tidak ada newline berlebihan
                    df = df.applymap(lambda x: str(x).strip() if pd.notna(x) else x)
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
                    _autofit_and_style_excel(writer, sheet_name, df)
        else:
            st.error("Tidak ditemukan engine Excel (openpyxl/xlsxwriter). Tambahkan salah satunya ke environment.")
            return None

        output.seek(0)
        return output.read()  # bytes
    except Exception as e:
        st.error(f"Gagal membuat Excel: {e}")
        return None


# =========================
# ====== MAIN APP =========
# =========================
def main_app():
    """Fungsi ini berisi seluruh aplikasi utama Anda setelah login berhasil."""
    st.session_state.last_activity = time.time()

    st.title("⚡️ Alfa Threat Model Expert Analysis")
    st.write("Deskripsikan Flow aplikasi maka alfathreat akan menganalisa nya dengan mudah dan akurat ")
    st.markdown("---")

    # --- SYSTEM PROMPT ---
    SYSTEM_PROMPT_CONTENT = """
    Anda adalah pakar keamanan siber dengan pengalaman 30 tahun, yang mahir dalam mengidentifikasi dan menganalisis potensi ancaman keamanan siber berdasarkan ASVS dan CWE. Jika ada pertanyaan di luar cyber security jangan berikan jawaban.
    Peran Anda adalah membuat kajian/report dalam tabel yang rapi serta up to date dengan perkembangan cyber security atas poin berikut:
    1. Gambarkan threat modelling diagram DFD menggunakan arrow.

    2. Berikan dalam tabel dan mapping nomor CWE-nya berdasarkan threat.

    3. Berikan list kerentanan dalam satu tabel pada Confidentiality, Integrity, Authentication, Availability, Non-repudiation atas threat tersebut termasuk dalam threat apa (contoh: SQLi, XSS, IDOR, DDoS). Lalu pada kolom sampingnya berikan Scenario serangan, lalu pada kolom sampingnya berikan rekomendasi keamanannya (minimal 5 rekomendasi).
       Format tabel contoh:
       | FLOW PROSES            | THREAT                    | C | I | Au | Av | N | SCENARIO                                                     | REKOMENDASI PENGAMANAN             |
       ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
       | contoh flow: user login | contoh threat: injection A06:01 | v |   | v  |   | v | fraudster menyerang dengan cara injeksi form login           | implementasikan parameterized queries |

    4. Berikan penilaian DREAD (INFORMATIONAL=1, LOW=2, MEDIUM=3, HIGH=4, CRITICAL=5). Beri nilai masing-masing komponen dalam satu kolom, contoh: Discoverability=3, Reproducibility=2, dst. Rata-rata dari 5 komponen adalah skornya.

    5. Gunakan standar industri (OWASP, ASVS, NIST, Gartner) untuk analisis teknis.

    6. Batasi jawaban hanya dalam lingkup keamanan siber.

    7. Semua output Bahasa Indonesia dan jangan buang makna serapan Inggrisnya.
    """

    # --- Sidebar untuk Unggah File dan Kontrol ---
    with st.sidebar:
        st.subheader(f"Selamat datang, {st.session_state['username']}!")

        # **Disarankan** ambil dari secrets. Fallback ke session:
        if 'GROQ_API_KEY' not in st.session_state:
            st.session_state.GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "").strip()

        st.subheader("Unggah File")
        st.markdown("Unggah file untuk dianalisis.")
        uploaded_file = st.file_uploader(
            "Pilih file",
            type=["jpeg", "jpg", "png", "pdf", "txt"]
        )

        st.subheader("Model")
        model_option = st.selectbox(
            'Pilih model yang akan digunakan:',
            ('llama-3.3-70b-versatile', 'qwen/qwen3-32b', 'deepseek-r1-distill-llama-70b')
        )

        if uploaded_file:
            st.success(f"File '{uploaded_file.name}' siap dianalisis.")

        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Inisialisasi Klien Groq
    client = None
    if st.session_state.GROQ_API_KEY:
        try:
            client = groq.Groq(api_key=st.session_state.GROQ_API_KEY)
        except Exception as e:
            st.error(f"Gagal menginisialisasi klien Groq. Pastikan kunci API Anda valid. Error: {e}")
    else:
        st.warning("Kunci API Groq tidak ditemukan. Tambahkan di Secrets Streamlit: GROQ_API_KEY.")

    # Inisialisasi riwayat chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Menampilkan riwayat chat dan tombol unduh
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                # PDF
                pdf_download_link = create_pdf_with_xhtml2pdf(
                    message["content"],
                    f"analisis_{message['content'][:20].replace(' ', '_')}.pdf"
                )
                st.markdown(pdf_download_link, unsafe_allow_html=True)

                # EXCEL
                excel_bytes = create_excel_from_markdown(
                    message["content"],
                    "alfa_threat_analysis.xlsx"
                )
                if excel_bytes:
                    st.download_button(
                        "📥 Unduh Analisis (Excel)",
                        data=excel_bytes,
                        file_name="alfa_threat_analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # Menerima Input Pengguna dan Proses
    if prompt := st.chat_input("Deskripsikan skenario atau ajukan pertanyaan keamanan..."):
        if not client:
            st.error("Tidak dapat melanjutkan. Klien Groq belum terinisialisasi.")
        else:
            with st.chat_message("user"):
                st.markdown(prompt)

            final_prompt = prompt
            if uploaded_file is not None:
                st.info(f"Menganalisis file: **{uploaded_file.name}**...")
                if uploaded_file.type in ["image/jpeg", "image/png"]:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=f"File gambar: {uploaded_file.name}", use_column_width=True)
                final_prompt = f"Berdasarkan sebuah file bernama '{uploaded_file.name}', jawab pertanyaan ini dari sudut pandang keamanan siber: {prompt}"
                st.success("Konteks file berhasil ditambahkan ke dalam prompt.")

            st.session_state.messages.append({"role": "user", "content": final_prompt})

            try:
                system_message = {"role": "system", "content": SYSTEM_PROMPT_CONTENT}
                messages_to_send = [system_message] + st.session_state.messages

                with st.spinner("Alfa Threat sedang menganalisis... 🤔"):
                    chat_completion = client.chat.completions.create(
                        messages=messages_to_send,
                        model=model_option,
                    )

                    response_text = chat_completion.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                    with st.chat_message("assistant"):
                        st.markdown(response_text)

                        # PDF
                        if response_text:
                            pdf_download_link = create_pdf_with_xhtml2pdf(response_text)
                            st.markdown(pdf_download_link, unsafe_allow_html=True)

                        # EXCEL
                        excel_bytes = create_excel_from_markdown(response_text, "alfa_threat_analysis.xlsx")
                        if excel_bytes:
                            st.download_button(
                                "📥 Unduh Analisis (Excel)",
                                data=excel_bytes,
                                file_name="alfa_threat_analysis.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

            except Exception as e:
                st.error(f"Terjadi kesalahan saat berkomunikasi dengan API Groq. Detail: {e}")
                # Hapus pesan user terakhir agar state tetap konsisten
                if st.session_state.messages and st.session_state.messages[-1].get("role") == "user":
                    st.session_state.messages.pop()


# =========================
# ====== LOGIN PAGE =======
# =========================
def login_page():
    st.title("Login Alfa Threat Model")
    st.write("Silakan masukkan kredensial Anda untuk melanjutkan.")
    VALID_CREDENTIALS = {
        "admin": "password123",
        "putri": "putri",
        "jeremy": "jeremy"
    }
    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in VALID_CREDENTIALS and password == VALID_CREDENTIALS[username]:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.last_activity = time.time()
                st.rerun()
            else:
                st.error("Username atau password salah.")


# =========================
# ====== APP FLOW =========
# =========================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = 0

# Auto-logout 30 menit idle
if st.session_state.authenticated:
    if time.time() - st.session_state.last_activity > 1800:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.warning("Sesi Anda telah berakhir karena tidak aktif. Silakan login kembali.")
        time.sleep(1.5)
        st.rerun()

if st.session_state.authenticated:
    main_app()
else:
    login_page()
