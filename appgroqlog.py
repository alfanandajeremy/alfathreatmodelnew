# --- FUNGSI UTAMA APLIKASI (SUDAH DIMODIFIKASI) ---
# --- Pastikan Anda sudah menambahkan impor di bagian atas file ---
# from fpdf import FPDF

# --- Fungsi untuk membuat PDF (letakkan di luar main_app) ---
def create_pdf(text):
    """
    Membuat file PDF dari string teks.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, txt=text)
    return pdf.output(dest='S').encode('latin-1')


def main_app():
    """Fungsi ini berisi seluruh aplikasi utama Anda setelah login berhasil."""
    
    # Perbarui waktu aktivitas setiap kali halaman utama dimuat ulang (ada interaksi)
    st.session_state.last_activity = time.time()
    
    st.title("⚡️ Alfa Threat Model Expert Analysis")
    st.write("Deskripsikan Flow aplikasi maka alfathreat akan menganalisa nya dengan mudah dan akurat ")
    st.markdown("---")

    # --- PERBARUI SYSTEM PROMPT DI SINI ---
    SYSTEM_PROMPT_CONTENT = """
    Anda adalah pakar keamanan siber dengan pengalaman 30 tahun, yang mahir dalam mengidentifikasi dan menganalisis potensi ancaman keamanan siber lebih dari 30 tahun. jika ada pertanyaan diluar cyber security jangan berikan jawaban.
    Peran Anda adalah membuat kajian/report dalam tabel yang rapih serta up to date dengan perkembangan cyber security atas poin berikut :
    1. gambarkan threat modelling diagram dfd menggunakan arrow
    
    2. berikan dalam tabel T01, C01, A01 nya dan code threat pada asvs attack code nya nomor berapa.

    3. berikan list kerentanan dalam satu tabel pada Confidentiallity,Integrity, Authentication, Availability, Non repudiation atas threat tersebut termasuk dalam threat apa (misalkan contoh serangan sql,xss, idor, ddos) lalu pada kolom sampingnya berikan Scenario serangan(Source : NIST 800-30), lalu pada kolom sampingnya serta rekomendasi keamananya pada tabel minimal 5 rekomendasi.
      contoh format output tabel harus seperti dibawah:
      | FLOW PROSES | THREAT                       | C | I | A | A | N | SCENARIO                                                      | REKOMENDASI PENGAMANAN                |
      ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
      | user login  | contoh threat :injection A06:01    | v |   | v |   | v | fraudster menyerang dengan cara masuk ke sistem dan injeksi form login    | implementasikan parameterize queries  |      
      |             |                                    |   |   |   |   |   |                                                                       |                                       |
      |             |                                    |   |   |   |   |   |                                                                       |                                       |   

    4. memberikan penilaian DREAD dalam penilaian ancaman dimana kategorinya (INFORMATIONAL=1, LOW RISK=2, MEDIUM=3, HIGH RISK=4, CRITICAL =5.) berikan nilai pada masing masing komponen dalam satu kolom. misalkan : Discoverability = 3 , reproducibility = 2, nanti dari nilai semuanya dibagi 5 itu merupakan score nya.
    
    5. Menggunakan standar industri dan praktik terbaik dari OWASP, ASVS, Gartner, NIST, serta standar keamanan siber internasional lainnya untuk memberikan analisis teknis.
    
    6. Selalu batasi jawaban Anda hanya dalam lingkup keamanan siber. Jangan menjawab pertanyaan di luar topik ini.
    
    7. semua outputnya bahasa indonesia dan jangan buang makna serapan bahasa inggrisnya.
    """

    # --- Sidebar untuk Unggah File dan Kontrol ---
    with st.sidebar:
        st.subheader(f"Selamat datang, {st.session_state['username']}!")
        
        if 'GROQ_API_KEY' not in st.session_state:
            st.session_state.GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
        
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

    # Inisialisasi session messages sebagai daftar kosong
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Tampilkan riwayat chat LAMA. Perubahan ada di bagian bawah ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Jika pesan dari asisten, tampilkan juga tombol download untuk riwayat chat
            if message["role"] == "assistant":
                pdf_bytes = create_pdf(message["content"])
                st.download_button(
                    label="📄 Simpan Hasil sebagai PDF",
                    data=pdf_bytes,
                    file_name=f"hasil_analisis_{message['content'][:20].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"download_{message['content'][:20]}" # key unik untuk setiap tombol
                )


    # --- Terima Input Pengguna dan Proses ---
    if prompt := st.chat_input("Deskripsikan skenario atau ajukan pertanyaan keamanan..."):
        if not client:
            st.error("Tidak dapat melanjutkan. Klien Groq belum terinisialisasi.")
        else:
            # Hapus riwayat chat lama agar hanya menampilkan hasil terbaru
            st.session_state.messages = [] 
            
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

            # Tambahkan prompt pengguna ke riwayat
            st.session_state.messages.append({"role": "user", "content": final_prompt})

            try:
                # Sisipkan system prompt sebelum mengirim ke API
                system_message = {"role": "system", "content": SYSTEM_PROMPT_CONTENT}
                messages_to_send = [system_message] + [{"role": "user", "content": final_prompt}] # Kirim hanya prompt terbaru

                with st.spinner(f"Alfa Threat sedang menganalisis tunggu ya!!! ... 🤔"):
                    chat_completion = client.chat.completions.create(
                        messages=messages_to_send,
                        model=model_option,
                    )
                
                response_text = chat_completion.choices[0].message.content
                # Tambahkan respons AI ke riwayat
                st.session_state.messages.append({"role": "assistant", "content": response_text})

                # Tampilkan respons AI yang baru
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                    
                    # --- INI BAGIAN UTAMA PENAMBAHAN FITUR ---
                    pdf_bytes = create_pdf(response_text)
                    st.download_button(
                        label="📄 Simpan Hasil sebagai PDF",
                        data=pdf_bytes,
                        file_name="hasil_analisis_alfathreat.pdf",
                        mime="application/pdf"
                    )
                # st.rerun() # Opsional: jika ingin membersihkan input box dan merender ulang dari message log

            except Exception as e:
                st.error(f"Terjadi kesalahan saat berkomunikasi dengan API Groq. Detail: {e}")
