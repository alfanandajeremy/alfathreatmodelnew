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
    Fungsi ini menangani teks multi-baris dan karakter dasar.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    # Menggunakan 'latin-1' encoding untuk teks agar kompatibel dengan font standar FPDF
    # dan mengganti karakter yang tidak didukung.
    encoded_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=encoded_text)
    # Mengembalikan output PDF sebagai bytes, yang dibutuhkan oleh st.download_button
    return pdf.output(dest='S').encode('latin-1')

# --- FUNGSI UNTUK HALAMAN APLIKASI UTAMA ---
def main_app():
    """Fungsi ini berisi seluruh aplikasi utama setelah login berhasil."""
    
    # Perbarui waktu aktivitas setiap kali halaman utama dimuat ulang
    st.session_state.last_activity = time.time()
    
    st.title("⚡️ Alfa Threat Model Expert Analysis")
    st.write("Deskripsikan alur aplikasi, maka AlfaThreat akan menganalisisnya dengan mudah dan akurat.")
    st.markdown("---")

    # --- SYSTEM PROMPT UNTUK AI ---
    SYSTEM_PROMPT_CONTENT = """
    Anda adalah pakar keamanan siber dengan pengalaman 30 tahun, yang mahir dalam mengidentifikasi dan menganalisis potensi ancaman keamanan siber. Jika ada pertanyaan di luar keamanan siber, jangan berikan jawaban.
    Peran Anda adalah membuat laporan dalam tabel yang rapi serta up-to-date dengan perkembangan keamanan siber atas poin berikut:
    1. Gambarkan threat modelling diagram DFD menggunakan notasi panah (misal: User -> Web Server).
    2. Berikan tabel T01, C01, A01 dan kode ancaman pada ASVS.
    3. Buat tabel kerentanan (Confidentiality, Integrity, Authentication, Availability, Non-repudiation) untuk setiap ancaman. Sertakan jenis ancaman (SQLi, XSS, IDOR, DDoS), skenario serangan (Sumber: NIST 800-30), dan minimal 5 rekomendasi keamanan.
       Contoh format tabel:
       | FLOW PROSES | ANCAMAN | C | I | A | A | N | SKENARIO SERANGAN | REKOMENDASI PENGAMANAN |
       |-------------|---------|---|---|---|---|---|-------------------|------------------------|
       | User Login  | A03:Injection | v | v | v |   | v | Penyerang memasukkan payload SQL pada form login. | Gunakan parameterized queries. |
    4. Berikan penilaian DREAD (Damage, Reproducibility, Exploitability, Affected Users, Discoverability) dengan skala: INFORMATIONAL=1, LOW=2, MEDIUM=3, HIGH=4, CRITICAL=5. Hitung skor rata-rata (Total / 5).
    5. Gunakan standar industri seperti OWASP, ASVS, Gartner, dan NIST.
    6. Batasi jawaban hanya pada lingkup keamanan siber.
    7. Gunakan Bahasa Indonesia dan pertahankan istilah teknis dalam Bahasa Inggris jika perlu.
    """

    # --- SIDEBAR ---
    with st.sidebar:
        st.subheader(f"Selamat datang, {st.session_state['username']}!")
        
        # Ambil API Key dari Streamlit secrets
        if 'GROQ_API_KEY' not in st.session_state:
            st.session_state.GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
        
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
            # Hapus semua session state untuk logout
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
        st.warning("Kunci API Groq tidak ditemukan. Harap atur di file secrets.toml.")

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
            st.error("Tidak dapat melanjutkan. Klien Groq belum terinisialisasi.")
        else:
            # Tambahkan pesan pengguna ke riwayat dan tampilkan
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Persiapkan pesan untuk dikirim ke API
            final_prompt = prompt
            if uploaded_file:
                st.info(f"Menambahkan konteks dari file: **{uploaded_file.name}**...")
                final_prompt = f"Berdasarkan sebuah file bernama '{uploaded_file.name}', jawab pertanyaan ini dari sudut pandang keamanan siber: {prompt}"

            try:
                system_message = {"role": "system", "content": SYSTEM_PROMPT_CONTENT}
                # Kirim hanya system prompt dan user prompt terbaru
                messages_to_send = [system_message, {"role": "user", "content": final_prompt}]

                with st.spinner("AlfaThreat sedang menganalisis... 🤔"):
                    chat_completion = client.chat.completions.create(
                        messages=messages_to_send,
                        model=model_option,
                    )
                    response_text = chat_completion.choices[0].message.content

                # Tambahkan respons AI ke riwayat dan tampilkan
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    
                    # --- TOMBOL SIMPAN SEBAGAI PDF ---
                    # Muncul tepat di bawah respons AI
                    pdf_bytes = create_pdf(response_text)
                    st.download_button(
                        label="📄 Simpan Hasil sebagai PDF",
                        data=pdf_bytes,
                        file_name="hasil_analisis_alfathreat.pdf",
                        mime="application/pdf"
                    )
            
            except Exception as e:
                st.error(f"Terjadi kesalahan saat berkomunikasi dengan API Groq. Detail: {e}")
                # Hapus pesan pengguna terakhir jika terjadi error
                st.session_state.messages.pop()

# --- FUNGSI UNTUK HALAMAN LOGIN ---
def login_page():
    st.title("Login ke Alfa Threat Model")
    st.write("Silakan masukkan kredensial Anda untuk melanjutkan.")
    
    # Kredensial yang valid (contoh)
    VALID_CREDENTIALS = {
        "admin": "password123",
        "user": "U$3R",
        "jeremy": "jeremy",
        "bambang": "hermanto"
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
# Inisialisasi session state jika belum ada
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = 0

# Cek timeout sesi (misalnya 30 menit = 1800 detik)
SESSION_TIMEOUT = 1800 
if st.session_state.authenticated and (time.time() - st.session_state.last_activity > SESSION_TIMEOUT):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.warning("Sesi Anda telah berakhir karena tidak aktif. Silakan login kembali.")
    time.sleep(3)
    st.rerun()

# Tampilkan halaman yang sesuai
if st.session_state.authenticated:
    main_app()
else:
    login_page()
