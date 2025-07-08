import streamlit as st
import groq
from PIL import Image
import time
from fpdf import FPDF

# --- 1. Konfigurasi Halaman Web ---
st.set_page_config(
    page_title="Alfa Threat Model Expert Analysis",
    page_icon="⚡️",
    layout="centered"
)

# --- FUNGSI HELPER UNTUK MEMBUAT PDF ---
def create_pdf(text):
    """
    Membuat file PDF dari sebuah string teks.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    encoded_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=encoded_text)
    return pdf.output(dest='S').encode('latin-1')

# --- FUNGSI UNTUK HALAMAN APLIKASI UTAMA ---
def main_app():
    """Fungsi ini berisi seluruh aplikasi utama setelah login berhasil."""
    
    st.session_state.last_activity = time.time()
    
    st.title("⚡️ Alfa Threat Model Expert Analysis")
    st.write("Deskripsikan alur aplikasi, maka AlfaThreat akan menganalisisnya dengan mudah dan akurat.")
    st.markdown("---")

    # --- SYSTEM PROMPT UNTUK AI ---
    SYSTEM_PROMPT_CONTENT = """
    Anda adalah pakar keamanan siber dengan pengalaman 30 tahun...
    (System prompt Anda tetap sama, tidak saya tampilkan di sini agar ringkas)
    """

    # --- SIDEBAR ---
    with st.sidebar:
        st.subheader(f"Selamat datang, {st.session_state['username']}!")
        
        # --- BARU: Kolom input untuk API Key ---
        st.subheader("Konfigurasi API Key")
        groq_api_key = st.text_input(
            "Masukkan Groq API Key Anda", 
            type="password",
            help="API Key Anda tidak akan disimpan. Diperlukan untuk setiap sesi."
        )

        # DIHAPUS: Logika yang mengambil dari st.secrets
        # if 'GROQ_API_KEY' not in st.session_state:
        #     st.session_state.GROQ_API_KEY = st.secrets.get("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")
        
        st.subheader("Unggah File")
        st.markdown("Unggah file untuk dianalisis (opsional).")
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
    # --- BARU: Logika menggunakan API Key dari input pengguna ---
    if groq_api_key:
        try:
            client = groq.Groq(api_key=groq_api_key)
        except Exception as e:
            st.error(f"Gagal menginisialisasi klien Groq. Pastikan kunci API Anda valid. Error: {e}")
    else:
        # Peringatan jika API key belum dimasukkan
        st.warning("Silakan masukkan Groq API Key Anda di sidebar untuk memulai.")

    # Inisialisasi riwayat pesan jika belum ada
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Tampilkan riwayat pesan
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Terima input dari pengguna
    if prompt := st.chat_input("Deskripsikan skenario atau ajukan pertanyaan keamanan..."):
        if not client:
            st.error("Tidak dapat melanjutkan. Harap masukkan Groq API Key yang valid di sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            final_prompt = prompt
            if uploaded_file:
                st.info(f"Menambahkan konteks dari file: **{uploaded_file.name}**...")
                final_prompt = f"Berdasarkan file bernama '{uploaded_file.name}', jawab pertanyaan ini: {prompt}"

            try:
                system_message = {"role": "system", "content": SYSTEM_PROMPT_CONTENT}
                messages_to_send = [system_message, {"role": "user", "content": final_prompt}]

                with st.spinner("AlfaThreat sedang menganalisis... 🤔"):
                    chat_completion = client.chat.completions.create(
                        messages=messages_to_send,
                        model=model_option,
                    )
                    response_text = chat_completion.choices[0].message.content

                st.session_state.messages.append({"role": "assistant", "content": response_text})
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    pdf_bytes = create_pdf(response_text)
                    st.download_button(
                        label="📄 Simpan Hasil sebagai PDF",
                        data=pdf_bytes,
                        file_name="hasil_analisis_alfathreat.pdf",
                        mime="application/pdf"
                    )
            
            except Exception as e:
                st.error(f"Terjadi kesalahan saat berkomunikasi dengan API Groq. Detail: {e}")
                st.session_state.messages.pop()

# --- FUNGSI UNTUK HALAMAN LOGIN ---
def login_page():
    st.title("Login ke Alfa Threat Model")
    st.write("Silakan masukkan kredensial Anda untuk melanjutkan.")
    
    VALID_CREDENTIALS = {
        "admin": "password123", "user": "U$3R",
        "jeremy": "jeremy", "bambang": "hermanto"
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

# --- KONTROL ALUR APLIKASI ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = 0

SESSION_TIMEOUT = 1800 
if st.session_state.authenticated and (time.time() - st.session_state.last_activity > SESSION_TIMEOUT):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.warning("Sesi Anda telah berakhir karena tidak aktif. Silakan login kembali.")
    time.sleep(3)
    st.rerun()

if st.session_state.authenticated:
    main_app()
else:
    login_page()
