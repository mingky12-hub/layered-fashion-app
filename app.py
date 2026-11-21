import json
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="일교차 레이어드 코디",
    page_icon="🧥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 모바일 카드 스타일 CSS
st.markdown("""
<style>
    .main-title { font-size: 1.5rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-title { font-size: 0.9rem; color: #64748B; margin-bottom: 1.2rem; }
    .metric-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px; text-align: center; }
    .metric-val { font-size: 1.3rem; font-weight: 700; color: #0F172A; }
    .metric-lbl { font-size: 0.75rem; color: #64748B; }
    .outfit-box { background: white; border: 1px solid #CBD5E1; border-radius: 12px; padding: 16px; margin: 12px 0; }
    .outfit-item { margin-bottom: 8px; font-size: 0.95rem; }
    .outfit-badge { display: inline-block; background: #EEF2F6; color: #334155; font-weight: 600; font-size: 0.78rem; padding: 2px 8px; border-radius: 6px; margin-right: 6px; }
    .tip-box { background: #EFF6FF; border-left: 4px solid #3B82F6; padding: 10px 14px; border-radius: 0 8px 8px 0; margin-bottom: 10px; font-size: 0.9rem; }
    .warn-box { background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 10px 14px; border-radius: 0 8px 8px 0; margin-bottom: 10px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🧥 출퇴근 레이어드 코디네이터</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">일교차와 대중교통/실내 냉난방을 고려한 오늘 맞춤 룩</div>', unsafe_allow_html=True)

# API 키 설정
with st.sidebar:
    st.header("⚙️ 환경 설정")
    gemini_api_key = st.text_input("Gemini API Key", type="password", help="Google AI Studio 발급 키")
    if not gemini_api_key and "GEMINI_API_KEY" in st.secrets:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]

# 입력 폼
with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("지역 (시/구)", value="서울 영등포구")
        commute_type = st.selectbox("주요 이동 수단", ["지하철/버스", "도보 위주", "자차/택시"])
    with col2:
        hours = st.selectbox("외출 시간대", ["출퇴근 (오전 8시 ~ 저녁 7시)", "낮 외출 (오전 11시 ~ 오후 4시)", "종일 (오전 ~ 밤)"])
        sensitivity = st.select_slider("체질 보정", options=["추위 탐", "보통", "더위 탐"], value="보통")

    submit_btn = st.form_submit_button("오늘의 레이어드 코디 추천받기", use_container_width=True)

def generate_recommendation(api_key, location, commute, time_range, user_sens):
    client = genai.Client(api_key=api_key)
    
    sys_inst = (
        "당신은 일교차와 실내외 환경(대중교통 냉난방, 실내 온도)을 고려하는 패션 스타일리스트입니다. "
        "주어진 조건에 맞춰 탈착이 용이한 최적의 3단 레이어드 코디를 반드시 유효한 JSON 형식으로만 작성하세요."
    )
    
    prompt = f"""
    [사용자 조건]
    - 위치: {location}
    - 이동 수단: {commute}
    - 시간대: {time_range}
    - 체질: {user_sens}
    
    현재 계절과 일교차를 고려해 아래 JSON 형식 그대로 작성해주세요:
    {{
      "weatherSummary": {{
        "morningTemp": 5,
        "dayMaxTemp": 18,
        "eveningTemp": 9,
        "tempDifference": 13,
        "condition": "일교차 크고 맑음"
      }},
      "outfit": {{
        "outer": "트렌치코트 또는 바람막이",
        "middle": "가디건 또는 니트 조끼",
        "inner": "면 롱슬리브 티셔츠",
        "bottom": "슬랙스 또는 데님 팬츠",
        "shoes": "스니커즈 또는 로퍼",
        "accessories": ["가벼운 머플러", "휴대용 에코백"]
      }},
      "actionableTips": {{
        "transitTip": "지하철 내부 난방 시 아우터를 벗어 손에 걸쳐 체온을 조절하세요.",
        "officeTip": "실내 근무 시에는 가디건만 단독으로 입어 쾌적함을 유지하세요.",
        "caution": "두꺼운 헤비 니트 단벌은 실내외 급격한 온도차 대응에 불리합니다."
      }}
    }}
    """
    
    # AI Studio 표준 모델인 gemini-2.0-flash 적용
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=sys_inst,
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return json.loads(response.text)

if submit_btn:
    if not gemini_api_key:
        st.error("좌측 사이드바에 Gemini API Key를 입력해 주세요.")
    else:
        with st.spinner("오늘 날씨 분석 및 최적 레이어드 조합 계산 중..."):
            try:
                res = generate_recommendation(gemini_api_key, city, commute_type, hours, sensitivity)
                w = res.get("weatherSummary", {})
                o = res.get("outfit", {})
                t = res.get("actionableTips", {})

                # 1. 체감 기온 분석
                st.markdown("#### 🌡️ 오늘 체감 기온 분석")
                cols = st.columns(4)
                cols[0].markdown(f'<div class="metric-card"><div class="metric-val">{w.get("morningTemp", 0):+.0f}°</div><div class="metric-lbl">출근 체감</div></div>', unsafe_allow_html=True)
                cols[1].markdown(f'<div class="metric-card"><div class="metric-val">{w.get("dayMaxTemp", 0):+.0f}°</div><div class="metric-lbl">낮 최고</div></div>', unsafe_allow_html=True)
                cols[2].markdown(f'<div class="metric-card"><div class="metric-val">{w.get("eveningTemp", 0):+.0f}°</div><div class="metric-lbl">퇴근 체감</div></div>', unsafe_allow_html=True)
                cols[3].markdown(f'<div class="metric-card"><div class="metric-val" style="color:#E11D48;">{w.get("tempDifference", 0):.0f}°</div><div class="metric-lbl">일교차</div></div>', unsafe_allow_html=True)

                st.caption(f"📌 **날씨 요약**: {w.get('condition', '맑음')}")

                # 2. 3단 레이어드 코디
                st.markdown("#### 👕 3단 레이어드 코디 추천")
                accs = ", ".join(o.get("accessories", []))
                outfit_html = f"""
                <div class="outfit-box">
                    <div class="outfit-item"><span
