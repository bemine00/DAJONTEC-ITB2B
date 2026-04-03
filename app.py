import streamlit as st
import os
import zipfile
import io
import shutil
from datetime import datetime
import smtplib  # 메일 발송용 추가
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


# 1. 페이지 설정
st.set_page_config(page_title="다존텍 ITB2B 혁신 시스템", page_icon="📦", layout="centered")

# 폴더 설정 (업로드용 / 완료 보관용)
SAVE_DIR = "uploaded_photos"
ARCHIVE_DIR = "processed_photos"
for folder in [SAVE_DIR, ARCHIVE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 2. 다존텍 전용 블루 테마 디자인 (CSS)

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

    /* 버튼 스타일 강화 */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 4.5em;
        background-color: #0056b3; color: white; font-weight: bold; font-size: 1.1em;
        border: none; box-shadow: 0 4px 10px rgba(0,86,179,0.3);
    }

    /* 관리자 완료 버튼 전용 (빨간색 계열) */
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

# 3. 사이드바 - 관리자 메뉴 (중복 방지 & 완료 처리 로직)
st.sidebar.title("🔐 관리자 모드")
admin_pw = st.sidebar.text_input("접속 암호", type="password")
if admin_pw == "1234":
    st.sidebar.success("✅ 인증 완료")
    target_date = st.sidebar.date_input("조회 날짜", datetime.now().date())
    t_str = target_date.strftime("%Y%m%d")   

    # 1단계: 업로드 폴더에서 해당 날짜 파일 필터링
    all_f = [f for f in os.listdir(SAVE_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))]
    sel_f = []
    for f in all_f:
        f_path = os.path.join(SAVE_DIR, f)
        mtime = datetime.fromtimestamp(os.path.getmtime(f_path)).strftime("%Y%m%d")
        if t_str in f or mtime == t_str:
            sel_f.append(f)    

    # 모든 파일 목록을 그냥 다 보여주기
    all_files_in_folder = os.listdir(SAVE_DIR)
    st.sidebar.write(f"현재 서버에 있는 전체 파일: {all_files_in_folder}") 
    if sel_f:
        st.sidebar.info(f"📂 미처리 데이터: {len(sel_f)}건")       
        # 압축 파일 생성
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for f in sel_f:
                if "①" in f: fol = "①IPTV"
                elif "②" in f: fol = "②폐가전"
                elif "③" in f: fol = "③다수량"
                else: fol = "④기타"
                clean_name = f.split('_', 1)[-1] if '_' in f else f
                z.write(os.path.join(SAVE_DIR, f), arcname=os.path.join(fol, clean_name))
        
        # 다운로드 버튼
        st.sidebar.download_button(
            label=f"📥 {t_str} 자료 받기", 
            data=buf.getvalue(), 
            file_name=f"DAJON_{t_str}.zip",
            key="download_btn"
        )        
        st.sidebar.markdown("---")
        st.sidebar.warning("파일 확인 후 아래 버튼을 누르면 목록에서 제외됩니다.")        

# --- [수정된 섹션 설정: 다중 납품번호 대응] ---
# 앱이 실행될 때 입력줄 상태를 기억하기 위한 설정
if "delivery_rows" not in st.session_state:
    st.session_state.delivery_rows = [{"cat": "①IPTV 설치사진", "no": "", "files": []}]

# 입력줄 추가 함수
def add_row():
    st.session_state.delivery_rows.append({"cat": "①IPTV 설치사진", "no": "", "files": []})

# 입력줄 삭제 함수
def del_row(idx):
    if len(st.session_state.delivery_rows) > 1:
        st.session_state.delivery_rows.pop(idx)

st.subheader("📸 사진 등록 (다중 건수 대응)")
st.caption("납품 건이 여러 개라면 아래 '➕ 납품건 추가' 버튼을 눌러주세요.")

# 기사님이 추가한 줄 수만큼 반복해서 입력칸 생성
for i, row in enumerate(st.session_state.delivery_rows):
    with st.expander(f"📦 납품 건 #{i+1} ({row['cat']})", expanded=True):
        col_cat, col_no = st.columns(2)
        with col_cat:
            row["cat"] = st.selectbox(f"카테고리 선택##{i}", 
                                    ["①IPTV 설치사진", "②폐가전 입고사진", "③다수량 설치사진", "④현장 기타"],
                                    key=f"cat_select_{i}")
        with col_no:
            row["no"] = st.text_input(f"납품번호 입력##{i}", value=row["no"], key=f"no_input_{i}")
        
        row["files"] = st.file_uploader(f"사진 선택##{i}", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"file_up_{i}")
        
        if len(st.session_state.delivery_rows) > 1:
            st.button(f"🗑️ 이 납품 건 삭제", key=f"del_btn_{i}", on_click=del_row, args=(i,))

# 행 추가 버튼
st.button("➕ 납품 건(번호) 추가하기", on_click=add_row)

# 전송 로직에서 사용할 데이터 딕셔너리 준비 (기존 로직과 호환을 위함)
# 이 부분은 아래 5번 전송 로직에서 'st.session_state.delivery_rows'를 직접 사용하도록 수정할 예정입니다.


# 5. 전송 로직 (다중 건수 통합 처리)
if st.button("🚀 모든 납품 데이터 일괄 전송"):
    # 유효성 검사
    all_data = st.session_state.delivery_rows
    has_error = False
    valid_count = 0
    
    for row in all_data:
        if row["files"]:
            if not row["no"]:
                st.error(f"❌ #{all_data.index(row)+1}번째 건의 납품번호가 없습니다.")
                has_error = True
            valid_count += len(row["files"])
            
    if not driver or not car:
        st.error("⚠️ 기사님 정보를 입력해 주세요.")
    elif valid_count == 0:
        st.warning("⚠️ 전송할 사진이 하나도 없습니다.")
    elif not has_error:
        with st.spinner("📧 모든 데이터를 메일로 백경 및 서버 저장 중..."):
            try:
                car4 = car.replace(" ", "")[-4:]
                d_pre = rep_date.strftime("%Y%m%d")
                saved_files_for_email = []

                # 모든 행(Row)을 돌면서 저장 및 메일 준비
                for row in all_data:
                    if not row["files"]: continue
                    
                    cat_name = row["cat"]
                    for idx, f in enumerate(row["files"]):
                        ext = os.path.splitext(f.name)[1]
                        # 파일명 규칙 (기존 로직 유지)
                        if "①" in cat_name: fn = f"①_{row['no']}_{car4}_{idx+1}{ext}"
                        elif "②" in cat_name: fn = f"②_{row['no']}_{car4}_{idx+1}{ext}"
                        elif "③" in cat_name: fn = f"③_{d_pre}_{row['no']}_{car4}_{idx+1}{ext}"
                        else: fn = f"④_{row['no']}_{car4}_{idx+1}{ext}"
                        
                        f_bytes = f.getvalue()
                        with open(os.path.join(SAVE_DIR, fn), "wb") as sf:
                            sf.write(f_bytes)
                        saved_files_for_email.append((fn, f_bytes))

                    # --- 2. 네이버 메일 발송 로직 ---
                    naver_user = "djtb2b2141" # @naver.com 제외 아이디만
                    naver_pw = "ZJH3FGZKFWL3" # 띄어쓰기 없이 입력
                    
                    msg = MIMEMultipart()
                    msg['Subject'] = f"[ITB2B] {driver}_{car}_{rep_date.strftime('%m%d')} 전송완료"
                    msg['From'] = f"{naver_user}@naver.com"
                    msg['To'] = f"{naver_user}@naver.com"
                    
                    body = f"기사님: {driver}\n차량: {car}\n날짜: {rep_date}\n개수: {len(saved_files_for_email)}건"
                    msg.attach(MIMEText(body))

                    for filename, filedata in saved_files_for_email:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(filedata)
                        encoders.encode_base64(part)
                        # 한글 깨짐 방지 처리
                        part.add_header('Content-Disposition', f"attachment; filename={filename.encode('utf-8').decode('iso-8859-1')}")
                        msg.attach(part)

                    server = smtplib.SMTP_SSL('smtp.naver.com', 465)
                    server.login(naver_user, naver_pw)
                    server.send_message(msg)
                    server.quit()

                    # --- 3. 완료 알림 ---
                st.balloons()
                st.success(f"✅ 총 {len(all_data)}건의 납품 정보가 전송되었습니다!")
                
                # 전송 후 입력값 초기화 (선택사항)
                st.session_state.delivery_rows = [{"id": 0, "cat": "①IPTV 설치사진", "no": "", "files": []}]
                st.rerun()

            except Exception as e:
                st.error(f"❌ 전송 오류: {e}")
