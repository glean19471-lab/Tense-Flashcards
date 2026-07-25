import streamlit as st
import pandas as pd
import random
import requests

# 🔗 ลิงก์ Web App URL สำหรับส่งข้อมูลเข้า Google Sheets ของคุณครู
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzCXPY7eWWWV0VVoJ5j8ZE8QMxVAxjgKbMFIDYC4x_-b3iy3ES0EiFZu0dyhVatFSHq/exec"

def get_image_url(url):
    try:
        if isinstance(url, str) and 'drive.google.com' in url:
            file_id = url.split('/d/')[1].split('/')[0]
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"
        return url
    except:
        return ""

@st.cache_data
def load_data():
    vocab_file = 'ข้อมูลใช้ทำสื่อ.xlsx - คำศัพท์และลิงค์รูป.csv'
    qa_file = 'ข้อมูลใช้ทำสื่อ.xlsx - โจทย์และเฉลย.csv'
    
    df_vocab = pd.read_csv(vocab_file)
    df_qa = pd.read_csv(qa_file)
    
    subjects = df_vocab[['ประธาน', 'ลิงค์รูป']].dropna().to_dict('records')
    verbs = df_vocab[['กริยา', 'ลิงค์รูป.1']].dropna().rename(columns={'ลิงค์รูป.1': 'ลิงค์รูป'}).to_dict('records')
    
    times_df = df_vocab[['คำบอกเวลา/กริยาวิเศษณ์บอกความถี่', 'ลิงค์รูป.2']].dropna()
    times_df.rename(columns={'คำบอกเวลา/กริยาวิเศษณ์บอกความถี่': 'คำบอกเวลา', 'ลิงค์รูป.2': 'ลิงค์รูป'}, inplace=True)
    times_df['คำบอกเวลา'] = times_df['คำบอกเวลา'].replace({'lask week': 'last week'})
    times_list = times_df.to_dict('records')
    
    tenses_map = {
        'Present Simple Tense': ['always', 'sometimes', 'never'],
        'Present Continuous Tense': ['now', 'at the moment', 'right now'],
        'Past Simple Tense': ['yesterday', 'last week', 'an hour ago'],
        'Future Simple Tense': ['tomorrow', 'next week', 'soon']
    }
    
    qa_dict = dict(zip(df_qa['โจทย์'].str.strip(), df_qa['เฉลย'].str.strip()))
    return subjects, verbs, times_list, qa_dict, tenses_map

try:
    subjects, verbs, times_list, qa_dict, tenses_map = load_data()
except Exception as e:
    st.error("❌ ไม่พบไฟล์ข้อมูลคำศัพท์ในระบบ กรุณาตรวจสอบว่าชื่อไฟล์ CSV ใน GitHub ตรงกับในโค้ดนี้หรือไม่")
    st.stop()

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

st.sidebar.title("🎮 Tense Master v3")
st.sidebar.markdown("---")
st.sidebar.subheader("👨‍🎓 ข้อมูลผู้เล่น")
student_name = st.sidebar.text_input("ชื่อ-นามสกุล:", placeholder="ด.ช. สมชาย ตั้งใจเรียน")
student_class = st.sidebar.selectbox("ระดับชั้น:", ["กรุณาเลือกชั้นเรียน", "ป.1", "ป.4", "ป.5", "ป.6"])
student_no = st.sidebar.text_input("เลขที่:", placeholder="12")

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
selected_tense = st.sidebar.radio("เลือกบทเรียน Tense:", list(tenses_map.keys()))

st.title(f"✨ {selected_tense}")

valid_time_words = tenses_map[selected_tense]
filtered_times = [t for t in times_list if str(t['คำบอกเวลา']).strip() in valid_time_words]

if 'cards' not in st.session_state: st.session_state.cards = None
if 'ans_view' not in st.session_state: st.session_state.ans_view = False

if st.button("🎲 สุ่มคำศัพท์ (Random Cards)", type="primary", use_container_width=True):
    st.session_state.cards = (random.choice(subjects), random.choice(verbs), random.choice(filtered_times))
    st.session_state.ans_view = False

st.markdown("---")

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
    
    st.subheader("📝 เขียนประโยคของคุณที่นี่:")
    user_input = st.text_input("ตัวอย่างประโยค: I always jump.", placeholder="ระวังตัวพิมพ์ใหญ่ขึ้นต้นประโยค และจุด Full Stop ด้วยนะ!")
    
    key = f"{sub['ประธาน']} / {vrb['กริยา']} / {tm['คำบอกเวลา']}"
    answer = qa_dict.get(key, "ไม่พบข้อมูลเฉลยในระบบ")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 ตรวจคำตอบและส่งคะแนน", use_container_width=True):
            if not student_name or student_class == "กรุณาเลือกชั้นเรียน" or not student_no:
                st.warning("⚠️ แจ้งเตือน: นักเรียนต้องกรอก ชื่อ-นามสกุล ชั้น และเลขที่ ให้ครบถ้วนก่อนส่งตรวจนะครับ!")
            elif not user_input.strip():
                st.warning("กรุณาพิมพ์ประโยคในช่องว่างก่อนกดส่งคำตอบครับ")
            else:
                # ---------------------------------------------------------
                # ส่วนอัปเกรด: ระบบตรวจคำตอบแบบเข้มงวด (Strict Mode)
                # ---------------------------------------------------------
                # เคลียร์ช่องว่างส่วนเกินที่เด็กอาจเผลอเคาะสเปซบาร์เกิน
                user_clean = " ".join(user_input.strip().split()) 
                ans_clean = " ".join(str(answer).strip().split())
                
                # ตรวจเงื่อนไข 1: ถูกต้องเป๊ะ 100%
                if user_clean == ans_clean:
                    st.success("🌟 Correct! ยอดเยี่ยมมาก แต่งประโยคได้ถูกต้องตามหลักไวยากรณ์เป๊ะๆ")
                    st.balloons()
                    result_text = "ถูกต้อง"
                    st.session_state.score_correct += 1
                    
                # ตรวจเงื่อนไข 2: ถูกทุกคำ แต่ตัวพิมพ์เล็ก-ใหญ่ผิด
                elif user_clean.lower() == ans_clean.lower():
                    if user_clean[0].islower():
                        st.error("❌ เกือบถูกแล้ว! ตามหลักไวยากรณ์ประโยคต้อง **ขึ้นต้นด้วยตัวอักษรพิมพ์ใหญ่ (Capital letter)** เสมอนะครับ")
                    else:
                        st.error("❌ เกือบถูกแล้ว! ระวังเรื่องการใช้ตัวพิมพ์เล็ก/พิมพ์ใหญ่ในประโยคให้ถูกต้องด้วยนะครับ (เช่น คำว่า I ต้องเป็นพิมพ์ใหญ่เสมอ)")
                    result_text = "ผิด (ไวยากรณ์ตัวพิมพ์ใหญ่/เล็ก)"
                    st.session_state.score_incorrect += 1
                    
                # ตรวจเงื่อนไข 3: เด็กลืมใส่จุด Full stop
                elif user_clean + "." == ans_clean or user_clean.lower() + "." == ans_clean.lower():
                    st.error("❌ เกือบถูกแล้ว! จบประโยคแล้วอย่าลืมใส่ **จุด Full Stop (.)** ด้วยนะครับ")
                    result_text = "ผิด (ลืมจุด Full stop)"
                    st.session_state.score_incorrect += 1
                    
                # ตรวจเงื่อนไข 4: ผิดโครงสร้าง Tense หรือสะกดคำผิด
                else:
                    st.error("❌ Try again! ยังไม่ถูกน้า ลองเช็กโครงสร้างประโยค การเติม s/es/ing หรือกริยาช่อง 2 อีกรอบ")
                    result_text = "ผิด"
                    st.session_state.score_incorrect += 1
                
                # ฟังก์ชันทำงานหลังบ้าน: ส่งข้อมูลคะแนนเข้า Google Sheets
                if WEB_APP_URL:
                    try:
                        payload = {
                            "name": student_name,
                            "class": student_class,
                            "no": student_no,
                            "tense": selected_tense,
                            "question": key,
                            "user_answer": user_clean,
                            "result": result_text
                        }
                        requests.post(WEB_APP_URL, json=payload, timeout=3)
                        st.toast("📊 ระบบได้ทำการบันทึกคะแนนและคำตอบลง Google Sheets เรียบร้อยแล้ว!", icon="💾")
                    except:
                        pass
                        
    with col_btn2:
        if st.button("🔍 ดูเฉลย (Show Answer)", use_container_width=True):
            st.session_state.ans_view = True
            
    if st.session_state.ans_view:
        st.info(f"💡 เฉลยประโยคที่ถูกต้องตามโครงสร้างคือ: **{answer}**")