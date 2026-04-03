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

# 2. 디자인 (CSS)
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; font-family: 'Malgun Gothic', sans-serif; }
    .header-container {
        background: linear-gradient(135deg, #003399 0%, #0056b3 100%);
        padding: 35px 20px;
        border-radius: 0px 0px 25px 25px;
        margin: -60px -20px 30px -20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        text-align: center;
        color: white;
    }
    .header-title { font-size: 24px; font-weight: 800; margin: 0; letter-spacing: 1px; }
    .header-subtitle { color: #d1e3ff; font-size: 14px; margin-top: 8px; font-weight: 300; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 4.5em;
        background-color: #0056b3; color: white; font-weight: bold; font-size: 1.1em;
        border: none; box-shadow: 0 4px 10px rgba(0,86,179,0.3);
    }
    /* 카테고리 헤더 스타일 */
    .cat-header {
        background-color: #e9ecef;
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        margin-top: 20px;
        border-left: 5px solid #003399;
    }
    </style> 
    <div class="header-container">
        <p class="header-title">DAJONTEC ITB2B</p>
        <p class="header-title" style="font-size: 21px;">물류 혁신 시스템</p>
        <p class="header-subtitle">Smart Logistics & Installation Proof Service</p>
    </div>
    """, unsafe_allow_html=True)

# 3. 사이드바 - 관리자 메뉴
st.sidebar.title("🔐 관리자 모드")
admin_pw = st.sidebar.text_input("접속 암호", type="password")
if admin_pw == "1234":
    st.sidebar.success("✅ 인증 완료")
    target_date = st.sidebar.date_input("조회 날짜", datetime.now().date())
    t_str = target_date.strftime("%Y%m%d")

    all_f = [f for f in os.listdir(SAVE_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))]
    sel_f = []
    for f in all_f:
        f_path = os.path.join(SAVE_DIR, f)
        mtime = datetime.fromtimestamp(os.path.getmtime(f_path)).strftime("%Y%m%d")
        if t_str in f or mtime == t_str:
            sel_f.append(f)

    if sel_f:
        st.sidebar.info(f"📂 미처리 데이터: {len(sel_f)}건")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for f in sel_f:
                if "①" in f: fol = "①IPTV"
                elif "②" in f: fol = "②폐가전"
                elif "③" in f: fol = "③다수량"
                else: fol = "④기타"
                clean_name = f.split('_', 1)[-1] if '_' in f else f
                z.write(os.path.join(SAVE_DIR, f), arcname=os.path.join(fol, clean_name))
        
        st.sidebar.download_button(label=f"📥 {t_str} 자료 받기", data=buf.getvalue(), file_name=f"DAJON_{t_str}.zip")
        
        if st.sidebar.button("✅ 선택 날짜 작업 완료 처리"):
            for f in sel_f:
                shutil.move(os.path.join(SAVE_DIR, f), os.path.join(ARCHIVE_DIR, f))
            st.sidebar.success(f"보관함 이동 완료!")
            st.rerun()
    else:
        st.sidebar.warning(f"처리할 사진 없음 ({t_str})")

# 4. 메인 입력 영역
query_params = st.query_params
saved_driver = query_params.get("d", "")
saved_car = query_params.get("c", "")

with st.container():
    c1, c2 = st.columns(2)
    with c1: driver = st.text_input("👤 기사님 성함", value=saved_driver, placeholder="성함 입력")
    with c2: car = st.text_input("🚛 차량 번호", value=saved_car, placeholder="예: 12가 3456")
    rep_date = st.date_input("📅 작업 날짜", datetime.now().date())

    with st.expander("🔗 나만의 자동 입력 링크 만들기"):
        if st.button("자동 입력 링크 생성"):
            if driver and car:
                clean_d, clean_c = driver.strip(), car.replace(" ", "")
                personal_url = f"https://dajontec-itb2b.streamlit.app/?d={clean_d}&c={clean_c}"
                st.success("링크가 생성되었습니다! 북마크해서 사용하세요.")
                st.code(personal_url)
            else:
                st.warning("성함과 차량번호를 먼저 입력하세요.")

st.divider()

# --- [개선] 카테고리 전체 펼침형 입력 로직 ---
cat_list = ["①IPTV 설치사진", "②폐가전 입고사진", "③다수량 설치사진", "④현장 기타"]

# 상태 관리 초기화
if "multi_rows" not in st.session_state:
    # 각 카테고리별로 기본 1개씩 입력칸 생성
    st.session_state.multi_rows = {cat: [{"no": "", "files": []}] for cat in cat_list}

def add_entry(cat):
    st.session_state.multi_rows[cat].append({"no": "", "files": []})

def del_entry(cat, idx):
    if len(st.session_state.multi_rows[cat]) > 1:
        st.session_state.multi_rows[cat].pop(idx)

st.subheader("📸 사진 등록")

# 카테고리별로 화면에 모두 표시 (Expander가 아닌 일반 영역에 나열)
for cat in cat_list:
    st.markdown(f'<div class="cat-header">{cat}</div>', unsafe_allow_html=True)
    
    for i, entry in enumerate(st.session_state.multi_rows[cat]):
        col_no, col_file, col_del = st.columns([2, 3, 0.5])
        
        with col_no:
            entry["no"] = st.text_input(f"납품번호##{cat}_{i}", value=entry["no"], key=f"no_{cat}_{i}", placeholder="번호 입력")
        with col_file:
            entry["files"] = st.file_uploader(f"사진 선택##{cat}_{i}", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"file_{cat}_{i}")
        with col_del:
            if len(st.session_state.multi_rows[cat]) > 1:
                if st.button("❌", key=f"del_{cat}_{i}"):
                    del_entry(cat, i)
                    st.rerun()
    
    # 각 카테고리 하단에 추가 버튼
    st.button(f"➕ {cat} 추가 등록", key=f"add_{cat}", on_click=add_entry, args=(cat,))

st.divider()

# 5. 전송 로직
if st.button("🚀 모든 사진 데이터 일괄 전송"):
    rows_to_send = []
    for cat, entries in st.session_state.multi_rows.items():
        for entry in entries:
            if entry["files"]:
                if not entry["no"]:
                    st.error(f"❌ {cat}의 납품번호가 입력되지 않았습니다.")
                    st.stop()
                rows_to_send.append({"cat": cat, "no": entry["no"], "files": entry["files"]})

    if not driver or not car:
        st.error("⚠️ 기사님 정보를 입력해 주세요.")
    elif not rows_to_send:
        st.warning("⚠️ 전송할 사진이 없습니다.")
    else:
        with st.spinner("📧 서버 저장 및 메일 백업 중..."):
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
                        with open(os.path.join(SAVE_DIR, fn), "wb") as sf:
                            sf.write(f_bytes)
                        saved_files.append((fn, f_bytes))

                # 네이버 메일 발송
                naver_user, naver_pw = "djtb2b2141", "ZJH3FGZKFWL3"
                msg = MIMEMultipart()
                msg['Subject'] = f"[ITB2B] {driver}_{car}_{rep_date.strftime('%m%d')} 전송완료"
                msg['From'] = f"{naver_user}@naver.com"
                msg['To'] = f"{naver_user}@naver.com"
                
                body_text = f"기사님: {driver}\n차량: {car}\n날짜: {rep_date}\n\n[상세 내역]\n"
                for r in rows_to_send:
                    body_text += f"- {r['cat']}: {r['no']} ({len(r['files'])}장)\n"
                msg.attach(MIMEText(body_text))

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
                st.success(f"✅ {len(saved_files)}장의 사진이 성공적으로 전송되었습니다!")
                # 전송 후 초기화
                st.session_state.multi_rows = {cat: [{"no": "", "files": []}] for cat in cat_list}
                st.rerun()
            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
