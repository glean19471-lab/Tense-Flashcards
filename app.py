import streamlit as st
import pandas as pd
import random
import requests

# 🔗 ลิงก์ Web App URL สำหรับส่งข้อมูลเข้า Google Sheets
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzCXPY7eWWWV0VVoJ5j8ZE8QMxVAxjgKbMFIDYC4x_-b3iy3ES0EiFZu0dyhVatFSHq/exec"

# 1. ฟังก์ชันแปลงลิงก์ Google Drive ให้แสดงผลเป็นรูปภาพขนาดกำลังดี โหลดไว ไม่หน่วงหน้าเว็บ
def get_image_url(url):
    try:
        if isinstance(url, str) and 'drive.google.com' in url:
            file_id = url.split('/d/')[1].split('/')[0]
            # ใช้ระบบ Thumbnail เพื่อข้ามระบบล็อกความปลอดภัย และจำกัดขนาดภาพที่ 400px เพื่อให้โหลดเร็ว
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"
        return url
    except:
        return ""

# 2. ฟังก์ชันโหลดและเตรียมข้อมูลจากไฟล์ CSV
@st.cache_data
def load_data():
    vocab_file = 'ข้อมูลใช้ทำสื่อ.xlsx - คำศัพท์และลิงค์รูป.csv'
    qa_file = 'ข้อมูลใช้ทำสื่อ.xlsx - โจทย์และเฉลย.csv'
    
    df_vocab = pd.read_csv(vocab_file)
    df_qa = pd.read_csv(qa_file)
    
    # แยกกลุ่มคำศัพท์ ประธาน กริยา คำบอกเวลา
    subjects = df_vocab[['ประธาน', 'ลิงค์รูป']].dropna().to_dict('records')
    verbs = df_vocab[['กริยา', 'ลิงค์รูป.1']].dropna().rename(columns={'ลิงค์รูป.1': 'ลิงค์รูป'}).to_dict('records')
    
    times_df = df_vocab[['คำบอกเวลา/กริยาวิเศษณ์บอกความถี่', 'ลิงค์รูป.2']].dropna()
    times_df.rename(columns={'คำบอกเวลา/กริยาวิเศษณ์บอกความถี่': 'คำบอกเวลา', 'ลิงค์รูป.2': 'ลิงค์รูป'}, inplace=True)
    
    # แก้คำพิมพ์ผิดในไฟล์คำศัพท์ให้ตรงกับคีย์เวิร์ดในไฟล์เฉลย
    times_df['คำบอกเวลา'] = times_df['คำบอกเวลา'].replace({'lask week': 'last week'})
    times_list = times_df.to_dict('records')
    
    # จับคู่กลุ่มคำบอกเวลากับโครงสร้างแต่ละ Tense ตามแผนการสอน 4 หน้าย่อย
    tenses_map = {
        'Present Simple Tense': ['always', 'sometimes', 'never'],
        'Present Continuous Tense': ['now', 'at the moment', 'right now'],
        'Past Simple Tense': ['yesterday', 'last week', 'an hour ago'],
        'Future Simple Tense': ['tomorrow', 'next week', 'soon']
    }
    
    # ดึงโจทย์และเฉลยมาทำเป็น Dictionary เพื่อจับคู่คำตอบอย่างแม่นยำ
    qa_dict = dict(zip(df_qa['โจทย์'].str.strip(), df_qa['เฉลย'].str.strip()))
    
    return subjects, verbs, times_list, qa_dict, tenses_map

# เรียกโหลดข้อมูลเข้าสู่ระบบแอป
try:
    subjects, verbs, times_list, qa_dict, tenses_map = load_data()
except Exception as e:
    st.error("❌ ไม่พบไฟล์ข้อมูลคำศัพท์ในระบบ กรุณาตรวจสอบว่าชื่อไฟล์ CSV ใน GitHub ตรงกับในโค้ดนี้หรือไม่")
    st.stop()

# 3. ตกแต่งดีไซน์หน้าตาของแฟลชการ์ด (Digital Card CSS Style)
st.set_page_config(page_title="Tense Master Pro", layout="wide")
st.markdown("""
    <style>
    .card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        border: 2px solid #f0f2f6;
    }
    .card-title {
        color: #555;
        font-size: 16px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .vocab-text {
        font-size: 32px;
        font-weight: 800;
        color: #1E3A8A;
        margin-top: 12px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. เมนูด้านข้าง (Sidebar): ฟอร์มเก็บข้อมูลนักเรียน และ กระดานคะแนนสะสมสด
st.sidebar.title("🎮 Tense Master v3")
st.sidebar.markdown("---")
st.sidebar.subheader("👨‍🎓 ข้อมูลผู้เล่น")
student_name = st.sidebar.text_input("ชื่อ-นามสกุล:", placeholder="ด.ช. สมชาย ตั้งใจเรียน")
student_class = st.sidebar.selectbox("ระดับชั้น:", ["กรุณาเลือกชั้นเรียน", "ป.1", "ป.4", "ป.5", "ป.6"])
student_no = st.sidebar.text_input("เลขที่:", placeholder="12")

# สร้างตัวจำสถานะคะแนนสะสมชั่วคราวในหน้าจอเบราว์เซอร์ของนักเรียน
if 'score_correct' not in st.session_state: st.session_state.score_correct = 0
if 'score_incorrect' not in st.session_state: st.session_state.score_incorrect = 0

st.sidebar.markdown("---")
st.sidebar.subheader("📊 คะแนนสะสมรอบนี้")
st.sidebar.success(f"✅ ตอบถูกต้อง: {st.session_state.score_correct} ข้อ")
st.sidebar.error(f"❌ ตอบผิดพลาด: {st.session_state.score_incorrect} ข้อ")

if st.sidebar.button("🔄 รีเซ็ตคะแนนสะสมใหม่"):
    st.session_state.score_correct = 0
    st.session_state.score_incorrect = 0
    st.rerun()

st.sidebar.markdown("---")
# เมนูเปลี่ยนหน้าหมวดหมู่แบ่งตามโครงสร้าง Tense ทั้ง 4 หน้า
selected_tense = st.sidebar.radio("เลือกบทเรียน Tense:", list(tenses_map.keys()))

# 5. หน้าจอหลักของสื่อการสอนแฟลชการ์ด
st.title(f"✨ {selected_tense}")

# กรองคำบอกเวลาให้เหลือเฉพาะของ Tense ที่เลือกในปัจจุบัน
valid_time_words = tenses_map[selected_tense]
filtered_times = [t for t in times_list if str(t['คำบอกเวลา']).strip() in valid_time_words]

# ตัวจำสถานะของการ์ดที่สุ่มได้ในรอบนั้นๆ
if 'cards' not in st.session_state: st.session_state.cards = None
if 'ans_view' not in st.session_state: st.session_state.ans_view = False

# ปุ่มสำหรับกดสุ่มคำศัพท์ทั้ง 3 ใบพร้อมกัน
if st.button("🎲 สุ่มคำศัพท์ (Random Cards)", type="primary", use_container_width=True):
    st.session_state.cards = (random.choice(subjects), random.choice(verbs), random.choice(filtered_times))
    st.session_state.ans_view = False

st.markdown("---")

# แสดงผลการ์ดภาพและศัพท์ดิจิทัลทั้ง 3 ใบ
if st.session_state.cards:
    sub, vrb, tm = st.session_state.cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="card"><div class="card-title">👤 Subject</div></div>', unsafe_allow_html=True)
        st.image(get_image_url(sub['ลิงค์รูป']), use_container_width=True)
        st.markdown(f'<div class="vocab-text">{sub["ประธาน"]}</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="card"><div class="card-title">🏃 Verb</div></div>', unsafe_allow_html=True)
        st.image(get_image_url(vrb['ลิงค์รูป']), use_container_width=True)
        st.markdown(f'<div class="vocab-text">{vrb["กริยา"]}</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="card"><div class="card-title">⏱️ Time Adverb</div></div>', unsafe_allow_html=True)
        st.image(get_image_url(tm['ลิงค์รูป']), use_container_width=True)
        st.markdown(f'<div class="vocab-text">{tm["คำบอกเวลา"]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # ส่วนพื้นที่พิมพ์คำตอบแต่งประโยคของนักเรียน
    st.subheader("📝 เขียนประโยคของคุณที่นี่:")
    user_input = st.text_input("ตัวอย่างประโยค: I always jump.", placeholder="พิมพ์ประโยคตามโครงสร้าง Tense ให้ถูกต้องและครบถ้วน...")
    
    # สร้างคีย์เวิร์ดคำค้นหาเพื่อใช้ดึงข้อมูลเฉลย
    key = f"{sub['ประธาน']} / {vrb['กริยา']} / {tm['คำบอกเวลา']}"
    answer = qa_dict.get(key, "ไม่พบข้อมูลเฉลยในระบบ")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 ตรวจคำตอบและส่งคะแนน", use_container_width=True):
            # ล็อกเงื่อนไข: นักเรียนต้องพิมพ์ ชื่อ-ชั้น-เลขที่ ก่อน ถึงจะกดยอมรับคะแนนได้
            if not student_name or student_class == "กรุณาเลือกชั้นเรียน" or not student_no:
                st.warning("⚠️ แจ้งเตือน: นักเรียนต้องกรอก ชื่อ-นามสกุล ชั้น และเลขที่ ในแถบเมนูด้านซ้ายมือให้ครบถ้วนก่อนส่งตรวจนะครับ!")
            elif not user_input.strip():
                st.warning("กรุณาพิมพ์ประโยคในช่องว่างก่อนกดส่งคำตอบครับ")
            else:
                # ตรวจคำตอบโดยตัดช่องว่างซ้ายขวา และปรับเป็นตัวพิมพ์เล็กทั้งหมดเพื่อไม่ให้ระบบตรวจผิดพลาดเนื่องจาก CapsLock
                is_correct = user_input.strip().lower() == str(answer).strip().lower()
                if is_correct:
                    st.success("🌟 Correct! ยอดเยี่ยมมาก แต่งประโยคได้ถูกต้องตามโครงสร้าง")
                    st.balloons()
                    result_text = "ถูกต้อง"
                    st.session_state.score_correct += 1
                else:
                    st.error("❌ Try again! ยังไม่ถูกน้า ลองเช็กตัวสะกด การเติม s/es/ing, การใช้กริยาช่อง 2 หรือจุด Full Stop อีกรอบ")
                    result_text = "ผิด"
                    st.session_state.score_incorrect += 1
                
                # 📡 ฟังก์ชันทำงานหลังบ้าน: ส่งข้อมูลคะแนนยิงเข้าสู่ Google Sheets
                if WEB_APP_URL:
                    try:
                        payload = {
                            "name": student_name,
                            "class": student_class,
                            "no": student_no,
                            "tense": selected_tense,
                            "question": key,
                            "user_answer": user_input,
                            "result": result_text
                        }
                        # ส่งข้อมูลพร้อมตั้ง Timeout 3 วินาที เพื่อป้องกันหน้าเว็บชะงักหากเซิร์ฟเวอร์ตอบรับช้า
                        requests.post(WEB_APP_URL, json=payload, timeout=3)
                        st.toast("📊 ระบบได้ทำการบันทึกคะแนนและคำตอบลง Google Sheets เรียบร้อยแล้ว!", icon="💾")
                    except:
                        pass
                        
    with col_btn2:
        if st.button("🔍 ดูเฉลย (Show Answer)", use_container_width=True):
            st.session_state.ans_view = True
            
    if st.session_state.ans_view:
        st.info(f"💡 เฉลยประโยคที่ถูกต้องตามโครงสร้างคือ: **{answer}**")