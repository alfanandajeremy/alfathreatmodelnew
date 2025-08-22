import streamlit as st
import pytesseract
from PIL import Image
import time
import base64
import re
import groq
# =========================
# 1) Konfigurasi Halaman
# =========================
st.set_page_config(
    page_title="Alfa Threat Model Expert Analysis",
    page_icon="⚡️",
    layout="centered"
)

# =========================
# 3) File Processing Functions
# =========================

def read_image(image_file):
    """
    Fungsi untuk membaca teks dari gambar menggunakan OCR
    """
    image = Image.open(image_file)
    text = pytesseract.image_to_string(image)  # OCR untuk mengekstrak teks
    return text

def process_uploaded_file(uploaded_file):
    """
    Proses file yang diunggah berdasarkan tipe file
    """
    file_type = uploaded_file.type

    if file_type in ["image/jpeg", "image/png"]:
        image = Image.open(uploaded_file)
        st.image(image, caption=f"File gambar: {uploaded_file.name}", use_container_width=True)
        
        # Baca teks dari gambar menggunakan OCR
        extracted_text = read_image(uploaded_file)
        
        # Menampilkan teks yang diekstrak di dalam chat
        with st.chat_message("user"):
            st.markdown(f"**Teks dari gambar:**\n{extracted_text}")
        
        # Analisis sederhana: jika ada kata kunci tertentu
        if "password" in extracted_text.lower():
            response = "Gambar ini tampaknya mengandung informasi sensitif terkait kata sandi. Pastikan untuk menjaga kerahasiaannya."
        else:
            response = "Gambar berhasil diproses dan teks diekstraksi."

        return response
    
    elif file_type == "text/plain":
        text_data = uploaded_file.getvalue().decode("utf-8")
        st.text_area("File teks yang diunggah", text_data, height=300)
        return f"File teks '{uploaded_file.name}' berhasil diproses."

    else:
        st.error("File type tidak didukung. Harap unggah file gambar atau teks.")
        return f"File type '{file_type}' tidak didukung."

# =========================
# 4) Main App
# =========================
def main_app():
    st.session_state.last_activity = time.time()

    st.title("⚡️ Alfa Threat Model Expert Analysis")
    st.write("Deskripsikan Flow aplikasi maka AlfaThreat akan menganalisa-nya dengan mudah dan akurat.")
    st.markdown("---")

    SYSTEM_PROMPT_CONTENT = """
    Anda adalah pakar keamanan siber dengan pengalaman 30 tahun, yang mahir dalam mengidentifikasi dan menganalisis potensi ancaman keamanan siber berdasarkan ASVS dan CWE. Jika ada pertanyaan di luar cyber security jangan berikan jawaban.
    Peran Anda adalah membuat kajian/report dalam tabel yang rapi serta up to date dengan perkembangan cyber security atas poin berikut:
    1. Gambarkan threat modelling diagram DFD menggunakan arrow.
    2. Berikan dalam tabel dan mapping nomor CWE-nya berdasarkan threat.
    3. Berikan list kerentanan dalam satu tabel pada Confidentiality, Integrity, Authentication, Availability, Non-repudiation atas threat tersebut termasuk dalam threat apa (contoh: SQLi, XSS, IDOR, DDoS). Lalu pada kolom sampingnya berikan Scenario serangan, lalu pada kolom sampingnya berikan rekomendasi keamanannya (minimal 5 rekomendasi).
       Format tabel contoh:
       | FLOW PROSES            | THREAT                    | C | I | Au | Av | N | SCENARIO                                                     | REKOMENDASI PENGAMANAN             |
       ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
       | contoh flow: user login | contoh threat: injection A06:01 | v |   | v  |   | v | fraudster injeksi form login                                 | implementasikan parameterized queries |
    4. Berikan penilaian DREAD (INFORMATIONAL=1, LOW=2, MEDIUM=3, HIGH=4, CRITICAL=5). Beri nilai masing-masing komponen dalam satu kolom, contoh: Discoverability=3, Reproducibility=2, dst. Rata-rata dari 5 komponen adalah skornya.
    5. Gunakan standar industri (OWASP, ASVS, NIST, Gartner) untuk analisis teknis.
    6. Batasi jawaban hanya dalam lingkup keamanan siber.
    7. Semua output Bahasa Indonesia dan jangan buang makna serapan Inggrisnya.
    """

    with st.sidebar:
        st.subheader(f"Selamat datang, {st.session_state.get('username','')}!")
        
        if 'GROQ_API_KEY' not in st.session_state:
            st.session_state.GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "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").strip()

        st.subheader("Unggah File")
        st.markdown("Unggah file untuk dianalisis.")
        uploaded_file = st.file_uploader(
            "Pilih file",
            type=["jpeg", "jpg", "png", "txt"]
        )

        if uploaded_file:
            result = process_uploaded_file(uploaded_file)
            st.success(result)

        st.subheader("Model")
        model_option = st.selectbox(
            'Pilih model yang akan digunakan:',
            ('llama-3.3-70b-versatile', 'qwen/qwen3-32b', 'deepseek-r1-distill-llama-70b')
        )

        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    client = None
    if st.session_state.GROQ_API_KEY:
        try:
            client = groq.Groq(api_key=st.session_state.GROQ_API_KEY)
        except Exception as e:
            st.error(f"Gagal menginisialisasi klien Groq. Pastikan kunci API Anda valid. Error: {e}")
    else:
        st.warning("Kunci API Groq tidak ditemukan. Tambahkan di Secrets Streamlit: GROQ_API_KEY.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Input pengguna
    if prompt := st.chat_input("Deskripsikan skenario atau ajukan pertanyaan keamanan..."):
        if not client:
            st.error("Tidak dapat melanjutkan. Klien Groq belum terinisialisasi.")
        else:
            with st.chat_message("user"):
                st.markdown(prompt)

            final_prompt = prompt
            if uploaded_file is not None:
                st.info(f"Menganalisis file: **{uploaded_file.name}**...")
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
                        
            except Exception as e:
                st.error(f"Terjadi kesalahan saat berkomunikasi dengan API Groq. Detail: {e}")
                if st.session_state.messages and st.session_state.messages[-1].get("role") == "user":
                    st.session_state.messages.pop()

# =========================
# 5) Login Page
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
# 6) App Flow & Session
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

