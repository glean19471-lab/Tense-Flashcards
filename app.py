import streamlit as st
import pandas as pd
import random

# 1. แก้ไข: เปลี่ยนไปใช้ลิงก์ Thumbnail ของ Google Drive เพื่อหลีกเลี่ยงการถูกบล็อกรูปภาพ
def get_direct_gdrive_link(url):
    try:
        if isinstance(url, str) and 'drive.google.com/file/d/' in url:
            file_id = url.split('/d/')[1].split('/')[0]
            # ใช้ thumbnail endpoint จะทำให้ Streamlit ดึงภาพมาโชว์ได้ 100%
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"
        return url
    except:
        return url

# 2. ฟังก์ชันโหลดและเตรียมข้อมูล
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
    st.error(f"ไม่พบไฟล์ข้อมูล กรุณาตรวจสอบว่าอัปโหลดไฟล์เสร็จสิ้นและชื่อไฟล์ถูกต้อง")
    st.stop()

# 3. ตั้งค่า UI ของหน้าเว็บ
st.set_page_config(page_title="Tense Flashcards", page_icon="🃏", layout="wide")

st.sidebar.title("📚 เมนูหลัก")
st.sidebar.markdown("เลือกโครงสร้าง Tense ที่กำลังสอน")
selected_tense = st.sidebar.radio("หมวดหมู่ (Tenses):", list(tenses_map.keys()))

st.title(f"🎯 ฝึกแต่งประโยค: {selected_tense}")

valid_time_words = tenses_map[selected_tense]
filtered_times = [t for t in times_list if str(t['คำบอกเวลา']).strip() in valid_time_words]

if 'current_cards' not in st.session_state:
    st.session_state.current_cards = None
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = ""
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False

if st.button("🎲 สุ่มการ์ด (Random)", use_container_width=True):
    sub = random.choice(subjects)
    vrb = random.choice(verbs)
    tm = random.choice(filtered_times)
    st.session_state.current_cards = (sub, vrb, tm)
    st.session_state.show_answer = False
    st.session_state.user_answer = ""

st.markdown("---")

# แสดงผลการ์ด
if st.session_state.current_cards:
    sub, vrb, tm = st.session_state.current_cards
    
    col1, col2, col3 = st.columns(3)
    
    # แก้ไข: เปลี่ยน use_column_width เป็น use_container_width และใช้ div แทน h3 เพื่อแก้ปัญหาตัวหนังสือกลายเป็น HTML
    with col1:
        st.info("👤 ประธาน (Subject)")
        st.image(get_direct_gdrive_link(sub['ลิงค์รูป']), use_container_width=True)
        st.markdown(f"<div style='text-align: center; font-size: 24px; font-weight: bold;'>{sub['ประธาน']}</div>", unsafe_allow_html=True)
        
    with col2:
        st.warning("🏃 กริยา (Verb)")
        st.image(get_direct_gdrive_link(vrb['ลิงค์รูป']), use_container_width=True)
        st.markdown(f"<div style='text-align: center; font-size: 24px; font-weight: bold;'>{vrb['กริยา']}</div>", unsafe_allow_html=True)
        
    with col3:
        st.success("⏱️ คำบอกเวลา (Time)")
        st.image(get_direct_gdrive_link(tm['ลิงค์รูป']), use_container_width=True)
        st.markdown(f"<div style='text-align: center; font-size: 24px; font-weight: bold;'>{tm['คำบอกเวลา']}</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.subheader("✍️ นำคำศัพท์ทั้ง 3 คำมาเรียงประโยคให้ถูกต้อง")
    user_input = st.text_input("พิมพ์ประโยค (อย่าลืมจุด full stop ด้วยนะ):", value=st.session_state.user_answer)
    st.session_state.user_answer = user_input
    
    question_key = f"{sub['ประธาน']} / {vrb['กริยา']} / {tm['คำบอกเวลา']}"
    correct_answer = qa_dict.get(question_key, "ไม่พบเฉลยในระบบ")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ ตรวจคำตอบ", use_container_width=True):
            if not user_input.strip():
                st.warning("กรุณาพิมพ์ประโยคก่อนตรวจคำตอบครับ")
            elif user_input.strip().lower() == str(correct_answer).strip().lower():
                st.success("🎉 เก่งมาก! แต่งประโยคได้ถูกต้อง")
                st.balloons()
            else:
                st.error("❌ ยังไม่ถูกต้อง ลองเช็ก Tense อีกนิดแล้วพยายามใหม่นะ!")
                
    with col_btn2:
        if st.button("💡 ดูเฉลย", use_container_width=True):
            st.session_state.show_answer = True
            
    if st.session_state.show_answer:
        st.info(f"**เฉลยที่ถูกต้องคือ:** {correct_answer}")
