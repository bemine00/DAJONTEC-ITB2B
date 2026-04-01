import streamlit as st
import os
import zipfile
import io
import shutil
from datetime import datetime

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
        
        # [핵심] 완료 처리 버튼 - 파일을 ARCHIVE_DIR로 이동
        if st.sidebar.button("✅ 선택 날짜 작업 완료 처리"):
            for f in sel_f:
                src = os.path.join(SAVE_DIR, f)
                dst = os.path.join(ARCHIVE_DIR, f)
                # 동일 이름 파일이 보관함에 있을 경우를 대비해 shutil.move 사용
                shutil.move(src, dst)
            st.sidebar.success(f"{len(sel_f)}건 보관함 이동 완료!")
            st.rerun()

    else:
        st.sidebar.warning(f"처리할 사진 없음 ({t_str})")

# 4. 메인 입력 영역 (기사님용)
with st.container():
    c1, c2 = st.columns(2)
    with c1: driver = st.text_input("👤 기사님 성함", placeholder="성함 입력")
    with c2: car = st.text_input("🚛 차량 번호", placeholder="예: 12가 3456")
    rep_date = st.date_input("📅 작업 날짜", datetime.now().date())

st.divider()

# 섹션 설정
categories = [{"name": "①IPTV 설치사진", "icon": "📺"}, {"name": "②폐가전 입고사진", "icon": "♻️"}, 
              {"name": "③다수량 설치사진", "icon": "🏢"}, {"name": "④현장 기타", "icon": "📎"}]
data_dict = {}

for cat in categories:
    with st.expander(f"{cat['icon']} {cat['name']} 입력", expanded=False):
        d_no = st.text_input(f"🔢 납품번호", key=f"n_{cat['name']}")
        u_files = st.file_uploader(f"📷 사진 선택", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"u_{cat['name']}")
        data_dict[cat['name']] = {"no": d_no.strip(), "files": u_files}

# 5. 전송 로직
if st.button("🚀 모든 사진 데이터 일괄 전송"):
    # 업로드된 파일 총 개수 계산
    total = sum([len(v["files"]) for v in data_dict.values()])
    
    if not driver or not car:
        st.error("⚠️ 기사님 성함과 차량번호를 먼저 입력해 주세요.")
    elif total == 0:
        st.warning("⚠️ 전송할 사진이 없습니다. 사진을 먼저 선택해 주세요.")
    else:
        # 납품번호 누락 체크 (에러가 하나라도 있으면 중단)
        missing_no = False
        for cat_name, val in data_dict.items():
            if len(val["files"]) > 0 and not val["no"]:
                st.error(f"❌ '{cat_name}'의 납품번호가 누락되었습니다. 번호를 입력해 주세요.")
                missing_no = True
        
        if not missing_no:
            with st.spinner("📦 사진 데이터를 안전하게 전송 중입니다..."):
                car4 = car.replace(" ", "")[-4:]
                d_pre = rep_date.strftime("%Y%m%d")
                
                # 파일 저장 실행
                for cat_name, val in data_dict.items():
                    for i, f in enumerate(val["files"]):
                        ext = os.path.splitext(f.name)[1]
                        # 파일명 규칙 적용
                        if "①" in cat_name: fn = f"①_{val['no']}_{car4}_{i+1}{ext}"
                        elif "②" in cat_name: fn = f"②_{val['no']}_{car4}_{i+1}{ext}"
                        elif "③" in cat_name: fn = f"③_{d_pre}_{val['no']}_{car4}_{i+1}{ext}"
                        else: fn = f"④_{val['no']}_{car4}_{i+1}{ext}"
                        
                        # 서버 폴더에 저장
                        with open(os.path.join(SAVE_DIR, fn), "wb") as save_f:
                            save_f.write(f.getbuffer())

                # --- 시각화 강화 및 완료 처리 ---
                st.balloons() # 풍선 효과
                st.snow()     # 눈 내리는 효과 추가
                
                # 큰 성공 메시지 팝업
                st.success(f"✅ {driver} 기사님, 모든 데이터가 정상적으로 전송되었습니다!")
                st.info("💡 전송이 끝났습니다. 이제 창을 닫으시거나 다음 작업을 진행하세요.")
                
                # 중요: 전송 완료 후 기사님이 또 누르지 않도록 입력폼을 초기화하려는 경우 
                # st.rerun()을 바로 쓰면 메시지가 순식간에 사라지므로, 
                # 기사님이 완료 메시지를 충분히 볼 수 있게 5초 후 리프레시하거나 
                # 버튼을 다시 누르기 전까지 상태를 유지하는 것이 좋습니다.
