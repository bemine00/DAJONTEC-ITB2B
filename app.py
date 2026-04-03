import streamlit as st
import os
import zipfile
import io
import shutil
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# 1. 페이지 설정
st.set_page_config(page_title="다존텍 ITB2B 혁신 시스템", page_icon="📦", layout="centered")

# 폴더 설정
SAVE_DIR = "uploaded_photos"
ARCHIVE_DIR = "processed_photos"
for folder in [SAVE_DIR, ARCHIVE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 2. 디자인 (CSS) - 시인성 강화 및 버튼 최적화
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; font-family: 'Pretendard', sans-serif; }
    .header-container {
        background: linear-gradient(135deg, #003399 0%, #0056b3 100%);
        padding: 30px 20px;
        border-radius: 0px 0px 20px 20px;
        margin: -60px -20px 20px -20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        text-align: center;
        color: white;
    }
    .header-title { font-size: 22px; font-weight: 800; margin: 0; }
    
    /* 카테고리별 헤더 색상 설정 */
    .cat-header-1 { background-color: #e7f0ff; color: #004085; border-left: 6px solid #007bff; padding: 8px 12px; border-radius: 4px; font-weight: bold; margin-top: 15px; }
    .cat-header-2 { background-color: #fff3e0; color: #856404; border-left: 6px solid #ff9800; padding: 8px 12px; border-radius: 4px; font-weight: bold; margin-top: 15px; }
    .cat-header-3 { background-color: #e8f5e9; color: #1b5e20; border-left: 6px solid #4caf50; padding: 8px 12px; border-radius: 4px; font-weight: bold; margin-top: 15px; }
    .cat-header-4 { background-color: #f5f5f5; color: #424242; border-left: 6px solid #9e9e9e; padding: 8px 12px; border-radius: 4px; font-weight: bold; margin-top: 15px; }

    /* 전송 버튼 스타일 */
    .stButton>button[kind="primary"] {
        background-color: #0056b3; color: white; font-weight: bold; height: 3.5em; border-radius: 10px;
    }
    
    /* 추가 등록 버튼 스타일 (슬림화) */
    div.stButton > button:not([kind="primary"]) {
        height: 2.2em;
        font-size: 0.85em;
        border-radius: 8px;
        margin-top: -10px;
    }
    </style> 
    <div class="header-container">
        <p class="header-title">DAJONTEC ITB2B 물류 혁신</p>
    </div>
    """, unsafe_allow_html=True)

# 3. 사이드바 - 관리자 메뉴 (기존과 동일)
st.sidebar.title("🔐 관리자 모드")
admin_pw = st.sidebar.text_input("접속 암호", type="password")
if admin_pw == "1234":
    st.sidebar.success("✅ 인증")
    target_date = st.sidebar.date_input("조회 날짜", datetime.now().date())
    t_str = target_date.strftime("%Y%m%d")
    all_f = [f for f in os.listdir(SAVE_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))]
    sel_f = [f for f in all_f if t_str in f]

    if sel_f:
        st.sidebar.info(f"📂 미처리: {len(sel_f)}건")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for f in sel_f:
                fol = "①IPTV" if "①" in f else "②폐가전" if "②" in f else "③다수량" if "③" in f else "④기타"
                z.write(os.path.join(SAVE_DIR, f), arcname=os.path.join(fol, f.split('_', 1)[-1]))
        st.sidebar.download_button(label="📥 압축파일 다운로드", data=buf.getvalue(), file_name=f"DAJON_{t_str}.zip")
        if st.sidebar.button("✅ 완료 처리 (보관함 이동)"):
            for f in sel_f: shutil.move(os.path.join(SAVE_DIR, f), os.path.join(ARCHIVE_DIR, f))
            st.rerun()

# 4. 기사 정보 입력 (자동 완성 기능 포함)
q_params = st.query_params
saved_d, saved_c = q_params.get("d", ""), q_params.get("c", "")

with st.container():
    c1, c2 = st.columns(2)
    with c1: driver = st.text_input("👤 기사님 성함", value=saved_d)
    with c2: car = st.text_input("🚛 차량 번호", value=saved_c)
    rep_date = st.date_input("📅 작업 날짜", datetime.now().date())

# 5. 사진 등록 (카테고리별 색상 구분 및 입력창 최적화)
cat_info = [
    {"name": "①IPTV 설치사진", "class": "cat-header-1"},
    {"name": "②폐가전 입고사진", "class": "cat-header-2"},
    {"name": "③다수량 설치사진", "class": "cat-header-3"},
    {"name": "④현장 기타", "class": "cat-header-4"}
]

if "multi_rows" not in st.session_state:
    st.session_state.multi_rows = {c["name"]: [{"no": "", "files": []}] for c in cat_info}

def add_entry(cat): st.session_state.multi_rows[cat].append({"no": "", "files": []})
def del_entry(cat, idx): 
    if len(st.session_state.multi_rows[cat]) > 1: st.session_state.multi_rows[cat].pop(idx)

st.divider()

for cat in cat_info:
    c_name = cat["name"]
    st.markdown(f'<div class="{cat["class"]}">{c_name}</div>', unsafe_allow_html=True)
    
    for i, entry in enumerate(st.session_state.multi_rows[c_name]):
        col_no, col_file, col_del = st.columns([1.5, 3, 0.5])
        with col_no:
            entry["no"] = st.text_input(f"번호##{c_name}_{i}", value=entry["no"], key=f"no_{c_name}_{i}", placeholder="납품번호", label_visibility="collapsed")
        with col_file:
            entry["files"] = st.file_uploader(f"파일##{c_name}_{i}", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"f_{c_name}_{i}", label_visibility="collapsed")
        with col_del:
            if len(st.session_state.multi_rows[c_name]) > 1:
                if st.button("❌", key=f"del_{c_name}_{i}"):
                    del_entry(c_name, i)
                    st.rerun()
    
    # 추가 버튼 슬림화 (use_container_width=False로 크기 조절)
    st.button(f"➕ {c_name.split(' ')[0]} 추가", key=f"add_{c_name}", on_click=add_entry, args=(c_name,), use_container_width=False)

st.divider()

# 6. 일괄 전송 로직
if st.button("🚀 사진 데이터 일괄 전송", type="primary"):
    rows_to_send = []
    for c_name, entries in st.session_state.multi_rows.items():
        for entry in entries:
            if entry["files"]:
                if not entry["no"]:
                    st.error(f"❌ {c_name}의 납품번호를 입력해주세요.")
                    st.stop()
                rows_to_send.append({"cat": c_name, "no": entry["no"], "files": entry["files"]})

    if not driver or not car:
        st.error("⚠️ 기사님 정보를 확인해주세요.")
    elif not rows_to_send:
        st.warning("⚠️ 전송할 사진이 없습니다.")
    else:
        with st.spinner("📧 데이터 전송 중..."):
            try:
                car4 = car.replace(" ", "")[-4:]
                d_pre = rep_date.strftime("%Y%m%d")
                saved_files = []

                for row in rows_to_send:
                    for idx, f in enumerate(row["files"]):
                        ext = os.path.splitext(f.name)[1]
                        if "①" in row["cat"]: fn = f"①_{row['no']}_{car4}_{idx+1}{ext}"
                        elif "②" in row["cat"]: fn = f"②_{row['no']}_{car4}_{idx+1}{ext}"
                        elif "③" in row["cat"]: fn = f"③_{d_pre}_{row['no']}_{car4}_{idx+1}{ext}"
                        else: fn = f"④_{row['no']}_{car4}_{idx+1}{ext}"
                        
                        f_bytes = f.getvalue()
                        with open(os.path.join(SAVE_DIR, fn), "wb") as sf: sf.write(f_bytes)
                        saved_files.append((fn, f_bytes))

                # 메일 발송 (네이버 SMTP)
                naver_user, naver_pw = "djtb2b2141", "ZJH3FGZKFWL3"
                msg = MIMEMultipart()
                msg['Subject'] = f"[ITB2B] {driver}_{car}_{rep_date.strftime('%m%d')}"
                msg['From'] = f"{naver_user}@naver.com"
                msg['To'] = f"{naver_user}@naver.com"
                
                body = f"기사: {driver}\n차량: {car}\n건수: {len(rows_to_send)}건"
                msg.attach(MIMEText(body))

                for fname, fdata in saved_files:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(fdata)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={fname.encode('utf-8').decode('iso-8859-1')}")
                    msg.attach(part)

                server = smtplib.SMTP_SSL('smtp.naver.com', 465)
                server.login(naver_user, naver_pw)
                server.send_message(msg)
                server.quit()

                st.balloons()
                st.success("✅ 전송이 완료되었습니다!")
                st.session_state.multi_rows = {c["name"]: [{"no": "", "files": []}] for c in cat_info}
                st.rerun()
            except Exception as e:
                st.error(f"❌ 오류: {e}")
