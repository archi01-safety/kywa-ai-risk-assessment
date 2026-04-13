import streamlit as st
import os, io, json, base64, datetime, requests
import pandas as pd
import numpy as np
import cv2
import plotly.express as px
from PIL import Image
from docx import Document
import google.genai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- [0] 설정 파일 로드 ---
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

cfg = load_config()

# --- [1] 페이지 설정 ---
st.set_page_config(
    page_title=f"{cfg['institution']['abbr']} {cfg['institution']['app_title']}",
    layout="wide",
    page_icon="🚨"
)

# --- [2] 구글 서비스 연결 (기존 로직 유지) ---
@st.cache_resource
def get_gcp_services():
    if "gcp_service_account" in st.secrets:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds), build('sheets', 'v4', credentials=creds)
    return None, None

drive_service, sheets_service = get_gcp_services()

# --- [3] 헬퍼 함수: 로고 인코딩 ---
def get_base64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None

inst_logo = get_base64_img(cfg['institution']['logo_path'])
partner_logo = get_base64_img(cfg['partner']['logo_path'])

# --- [4] UI 스타일링 (Dynamic CSS) ---
st.markdown(f"""
    <style>
    header {{visibility: hidden;}}
    .block-container {{padding-top: 1rem;}}
    .stButton > button {{
        background-color: #ff4b4b !important; color: white !important;
        border-radius: 8px !important; font-weight: bold !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- [5] 동적 헤더: [협업기관 로고 x 우리기관 로고] ---
h_col1, h_col2 = st.columns([2, 3])
with h_col1:
    # 두 로고를 나란히 배치
    logo_html = ""
    if partner_logo: logo_html += f'<img src="{partner_logo}" height="40" style="margin-right:20px;">'
    if inst_logo: logo_html += f'<a href="{cfg["institution"]["website_url"]}" target="_blank"><img src="{inst_logo}" height="45"></a>'
    st.markdown(logo_html, unsafe_allow_html=True)

with h_col2:
    st.markdown(f"""
        <div style="text-align: right;">
            <h2 style='margin:0;'>🚨 {cfg['institution']['name']}</h2>
            <p style='color:gray; margin:0;'>{cfg['institution']['app_title']} - {cfg['institution']['app_subtitle']}</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# --- [6] 입력 섹션 (Config 데이터 바인딩) ---
col1, col2 = st.columns(2)
with col1:
    st.markdown("### **🏢 점검 대상 정보**")
    selected_facility = st.radio("• 시설명 선택", cfg['ui_options']['facilities'], horizontal=True)
    selected_dept = st.selectbox("• 담당 부서 선택", cfg['ui_options']['departments'])
    user_description = st.text_area("• 상황 설명 입력", height=150)

with col2:
    st.markdown("### **📸 사진 기록**")
    img_file = st.file_uploader("사진 업로드", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    if img_file:
        st.image(img_file, caption="업로드 원본", width=300)

# --- [7] AI 분석 로직 (Prompt Persona 동적 삽입) ---
if st.button(f"🚀 {cfg['institution']['abbr']} AI 분석 시작", width="stretch"):
    # (기존 apply_face_blur_ai 및 Gemini 호출 로직 유지)
    # prompt 변수 내의 페르소나 부분만 cfg['ai_settings']['persona']로 교체
    dynamic_prompt = f"""
    {cfg['ai_settings']['persona']}
    [시설 정보]
    - 시설명: {selected_facility}
    - 담당부서: {selected_dept}
    ... (중략: 기존 프롬프트 규칙) ...
    """
    # [기존 분석 코드 실행...]

# --- [8] 데이터 Governance 푸터 (동적 삽입) ---
st.write("---")
f_col1, f_col2 = st.columns([3, 1])
with f_col1:
    st.markdown(f"### 🔒 Data Governance & Privacy")
    st.caption(f"""
    **© 2026 {cfg['institution']['name']} {cfg['footer']['department']}.** 본 시스템은 공공기관 AI 활용 가이드라인을 준수합니다.
    * **보안:** API Opt-out 설정으로 입력 데이터는 학습에 사용되지 않습니다.
    * **운영:** 전송된 데이터는 {cfg['institution']['abbr']} 안전센터 담당자의 검토를 거칩니다.
    """)

with f_col2:
    st.markdown("### 📞 Contact")
    st.markdown(f"""
    <div style="font-size: 0.85rem; color: #444;">
        <b>{cfg['footer']['department']}</b><br>
        📧 {cfg['footer']['email']}<br>
        📞 {cfg['footer']['phone']}
    </div>
    """, unsafe_allow_html=True)
