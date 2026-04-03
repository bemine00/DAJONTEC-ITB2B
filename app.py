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
    div[data-testid="stSidebar"] .stButton>button {
        background-color: #d9534f; height: 3em; font-size: 0.9em;
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

# 4. 메인 입력 영역 (자동 저장 링크 기능 포함)
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

# --- 다중 납품 건 입력 섹션 ---
if "delivery_rows" not in st.session_state:
    st.session_state.delivery_rows = [{"cat": "①IPTV 설치사진", "no": "", "files": []}]

def add_row():
    st.session_state.delivery_rows.append({"cat": "①IPTV 설치사진", "no": "", "files": []})

def del_row(idx):
    if len(st.session_state.delivery_rows) > 1:
        st.session_state.delivery_rows.pop(idx)

st.subheader("📸 사진 등록")
cat_options = ["①IPTV 설치사진", "②폐가전 입고사진", "③다수량 설치사진", "④현장 기타"]

for i, row in enumerate(st.session_state.delivery_rows):
    with st.expander(f"📦 납품 건 #{i+1} - {row['cat']}", expanded=True):
        col_cat, col_no = st.columns(2)
        with col_cat:
            row["cat"] = st.selectbox(f"카테고리 선택##{i}", cat_options, 
                                    index=cat_options.index(row["cat"]) if row["cat"] in cat_options else 0,
                                    key=f"cat_sel_{i}")
        with col_no:
            row["no"] = st.text_input(f"납품번호 입력##{i}", value=row["no"], key=f"no_in_{i}")
        
        row["files"] = st.file_uploader(f"사진 선택##{i}", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"file_up_{i}")
        
        if len(st.session_state.delivery_rows) > 1:
            st.button(f"🗑️ #{i+1} 건 삭제", key=f"del_btn_{i}", on_click=del_row, args=(i,))

st.button("➕ 납품 건 추가하기", on_click=add_row)

# 5. 전송 로직
if st.button("🚀 모든 납품 데이터 일괄 전송"):
    all_data = st.session_state.delivery_rows
    valid_count = sum(len(r["files"]) for r in all_data)
    has_no_error = True

    for r in all_data:
        if r["files"] and not r["no"]:
            st.error(f"❌ #{all_data.index(r)+1}번째 건의 납품번호가 없습니다.")
            has_no_error = False

    if not driver or not car:
        st.error("⚠️ 기사님 정보를 입력해 주세요.")
    elif valid_count == 0:
        st.warning("⚠️ 사진을 선택해 주세요.")
    elif has_no_error:
        with st.spinner("📧 서버 저장 및 메일 백업 중..."):
            try:
                car4 = car.replace(" ", "")[-4:]
                d_pre = rep_date.strftime("%Y%m%d")
                saved_files = []

                for row in all_data:
                    if not row["files"]: continue
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
                msg.attach(MIMEText(f"기사: {driver}\n차량: {car}\n건수: {len(all_data)}건"))

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
                st.success(f"✅ {len(all_data)}건 전송 완료!")
                st.session_state.delivery_rows = [{"cat": "①IPTV 설치사진", "no": "", "files": []}]
                st.rerun()
            except Exception as e:
                st.error(f"❌ 오류: {e}")
