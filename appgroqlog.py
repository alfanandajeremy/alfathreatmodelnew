import streamlit as st
import groq
from PIL import Image
import os
import time
import base64
from fpdf import FPDF

# --- 1. Konfigurasi Halaman Web ---
st.set_page_config(
    page_title="Alfa Threat Model Expert Analysis",
    page_icon="⚡️",
    layout="centered"
)

# --- FUNGSI UNTUK MEMBUAT PDF (VERSI FINAL) ---
def create_pdf_download_link_fpdf2(text_content, filename="alfa_threat_analysis.pdf"):
    """
    Mengubah konten teks menjadi PDF menggunakan FPDF2 dan menghasilkan tautan unduhan.
    Kode ini sudah memperbaiki error 'bytearray' dan masalah path file font.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Membuat path absolut ke file font agar andal di lingkungan cloud
        script_dir = os.path.dirname(__file__)
        font_path = os.path.join(script_dir, "DejaVuSans.ttf")

        try:
            # Menambahkan font yang mendukung karakter Unicode
            pdf.add_font('DejaVu', '', font_path, uni=True)
            pdf.set_font('DejaVu', '', 11)
        except RuntimeError:
            st.error(f"Font tidak ditemukan di path: {font_path}. Pastikan 'DejaVuSans.ttf' ada di repositori GitHub Anda.")
            pdf.set_font("Arial", size=11) # Fallback jika font tidak ditemukan

        # Menulis konten teks ke PDF
        pdf.multi_cell(0, 5, text_content)
        
        # PERBAIKAN: .output() sudah menghasilkan bytes, jadi .encode() dihapus
        pdf_output = pdf.output()
        
        # Meng-encode PDF ke format base64 untuk membuat tautan unduhan
        b64_pdf = base64.b64encode(pdf_output).decode()
        
        # Membuat tautan unduhan dalam format HTML
        href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{filename}" style="display: inline-block; padding: 8px 12px; background-color: #FF4B4B; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">💾 Unduh Analisis (PDF)</a>'
        return href
    except Exception as e:
        st.error(f"Gagal membuat PDF dengan FPDF2: {e}")
        return ""

# --- FUNGSI UTAMA APLIKASI ---
def main_app():
    """Fungsi ini berisi seluruh aplikasi utama Anda setelah login berhasil."""
    
    st.session_state.last_activity = time.time()
    
    st.title("⚡️ Alfa Threat Model Expert Analysis")
    st.write("Deskripsikan Flow aplikasi maka alfathreat akan menganalisa nya dengan mudah dan akurat ")
    st.markdown("---")

    # --- SYSTEM PROMPT (Tidak ada perubahan) ---
    SYSTEM_PROMPT_CONTENT = """
    Anda adalah pakar keamanan siber dengan pengalaman 30 tahun, yang mahir dalam mengidentifikasi dan menganalisis potensi ancaman keamanan siber lebih dari 30 tahun. jika ada pertanyaan diluar cyber security jangan berikan jawaban.
    Peran Anda adalah membuat kajian/report dalam tabel yang rapih serta up to date dengan perkembangan cyber security atas poin berikut :
    1. gambarkan threat modelling diagram dfd menggunakan arrow
    
    2. berikan dalam tabel T01, C01, A01 nya dan code threat pada asvs attack code nya nomor berapa.

    3. berikan list kerentanan dalam satu tabel pada Confidentiallity,Integrity, Authentication, Availability, Non repudiation atas threat tersebut termasuk dalam threat apa (misalkan contoh serangan sql,xss, idor, ddos) lalu pada kolom sampingnya berikan Scenario serangan, lalu pada kolom sampingnya serta rekomendasi keamananya pada tabel minimal 5 rekomendasi.
      contoh format output tabel harus seperti dibawah:
      | FLOW PROSES            | THREAT                    | C | I | A | A | N | SCENARIO                                                     | REKOMENDASI PENGAMANAN             |
      ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
      | contoh flow: user login  | contoh threat :injection A06:01  | v |   | v |   | v | fraudster menyerang dengan cara masuk ke sistem dan injeksi form login   | implementasikan parameterize queries   |      
      
    4. memberikan penilaian DREAD dalam penilaian ancaman dimana kategorinya (INFORMATIONAL=1, LOW RISK=2, MEDIUM=3, HIGH RISK=4, CRITICAL =5.) berikan nilai pada masing masing komponen dalam satu kolom. misalkan : Discoverability = 3 , reproducibility = 2, nanti dari nilai semuanya dibagi 5 itu merupakan score nya.
    
    5. Menggunakan standar industri dan praktik terbaik dari OWASP, ASVS, Gartner, NIST, serta standar keamanan siber internasional lainnya untuk memberikan analisis teknis.
    
    6. Selalu batasi jawaban Anda hanya dalam lingkup keamanan siber. Jangan menjawab pertanyaan di luar topik ini.
    
    7. semua outputnya bahasa indonesia dan jangan buang makna serapan bahasa inggrisnya.
    """

    # --- Sidebar untuk Unggah File dan Kontrol ---
    with st.sidebar:
        st.subheader(f"Selamat datang, {st.session_state['username']}!")
        
        if 'GROQ_API_KEY' not in st.session_state:
            st.session_state.GROQ_API_KEY = "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" # Ganti dengan kunci Anda jika perlu
        
        st.subheader("Unggah File")
        st.markdown("Unggah file untuk dianalisis.")
        uploaded_file = st.file_uploader(
            "Pilih file",
            type=["jpeg", "jpg", "png", "pdf", "txt"]
        )
        
        st.subheader("Model")
        model_option = st.selectbox(
            'Pilih model yang akan digunakan:',
            ('llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768', 'gemma-7b-it')
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
        st.warning("Kunci API Groq tidak ditemukan. Harap pastikan sudah diatur.")

    # Inisialisasi riwayat chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Menampilkan riwayat chat dan tombol unduh
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                pdf_download_link = create_pdf_download_link_fpdf2(message["content"], f"analisis_{message['content'][:20].replace(' ', '_')}.pdf")
                st.markdown(pdf_download_link, unsafe_allow_html=True)

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

                with st.spinner(f"Alfa Threat sedang menganalisis tunggu ya!!! ... 🤔"):
                    chat_completion = client.chat.completions.create(
                        messages=messages_to_send,
                        model=model_option,
                    )
                
                    response_text = chat_completion.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                    with st.chat_message("assistant"):
                        st.markdown(response_text)
                        
                        # Membuat dan menampilkan link download PDF untuk respons baru
                        if response_text:
                            pdf_download_link = create_pdf_download_link_fpdf2(response_text)
                            st.markdown(pdf_download_link, unsafe_allow_html=True)
                            
            except Exception as e:
                st.error(f"Terjadi kesalahan saat berkomunikasi dengan API Groq. Detail: {e}")
                st.session_state.messages.pop()

# --- FUNGSI UNTUK HALAMAN LOGIN (Tidak ada perubahan) ---
def login_page():
    st.title("Login ke Alfa Threat Model")
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

# --- KONTROL ALUR APLIKASI (Tidak ada perubahan) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = 0

# Logika untuk memeriksa sesi timeout
if st.session_state.authenticated:
    if time.time() - st.session_state.last_activity > 1800: # Timeout 30 menit
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.warning("Sesi Anda telah berakhir karena tidak aktif. Silakan login kembali.")
        time.sleep(3)
        st.rerun()

# Menentukan halaman mana yang akan ditampilkan
if st.session_state.authenticated:
    main_app()
else:
    login_page()
