import streamlit as st
import json
from google import genai
from google.genai import types

st.set_page_config(
    page_title="일교차 & 실내 적응형 레이어드 코디",
    page_icon="🧥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for polished mobile card layout
st.markdown("""
<style>
    .main-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #1E293B;
    }
    .sub-title {
        font-size: 0.9rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-val {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #64748B;
    }
    .outfit-box {
        background: white;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .outfit-item {
        margin-bottom: 8px;
        font-size: 0.95rem;
    }
    .outfit-badge {
        display: inline-block;
        background: #EEF2F6;
        color: #334155;
        font-weight: 600;
        font-size: 0.78rem;
        padding: 2px 8px;
        border-radius: 6px;
        margin-right: 6px;
    }
    .tip-box {
        background: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }
    .warn-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🧥 출퇴근 레이어드 코디네이터</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">일교차와 대중교통/실내 냉난방을 고려한 오늘 맞춤 룩</div>', unsafe_allow_html=True)

# Sidebar: API Keys & Settings
with st.sidebar:
    st.header("⚙️ 환경 설정")
    gemini_api_key = st.text_input("Gemini API Key", type="password", help="Google AI Studio에서 발급받은 API 키")
    st.caption("Streamlit Secrets에 `GEMINI_API_KEY`를 설정하면 자동 인식됩니다.")
    
    # Try reading from secrets if available
    if not gemini_api_key and "GEMINI_API_KEY" in st.secrets:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]

# User Input Form
with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("지역 (시/구)", value="서울 영등포구")
        commute_type = st.selectbox("주요 이동 수단", ["지하철/버스", "도보 위주", "자차/택시"])
    with col2:
        hours = st.selectbox("외출 시간대", ["출퇴근 (오전 8시 ~ 저녁 7시)", "낮 시간 외출 (오전 11시 ~ 오후 4시)", "종일 (오전 ~ 늦은 밤)"])
        sensitivity = st.select_slider("체질 보정", options=["추위 많이 탐", "보통", "더위 많이 탐"], value="보통")

    submit_btn = st.form_submit_button("오늘의 레이어드 코디 추천받기", use_container_width=True)

def generate_recommendation(api_key, location, commute, time_range, user_sens):
    client = genai.Client(api_key=api_key)
    
    system_instruction = """당신은 일교차와 실내외 환경(대중교통 난방/냉방 과열, 사무실 환경)을 고려한 맞춤형 패션 스타일리스트입니다.
주어진 날씨 조건과 사용자의 출퇴근 동선을 분석하여, 탈착이 용이한 최적의 3단 '레이어드 코디'를 제안해야 합니다.

[작성 원칙]
1. 단순 최고기온이 아니라 '출퇴근 시간대 체감온도'와 '낮 최고기온'의 일교차를 핵심 기준으로 삼습니다.
2. 대중교통 및 실내 난방/냉방 과열을 고려해, 두꺼운 단벌보다는 벗고 입기 편한 3단 레이어(이너-미들-아우터) 조합을 우선합니다.
3. 비/바람 예보가 있을 경우 하의 기장(밑단 오염 방지) 및 신발/소재 주의사항을 반드시 명시합니다.
4. 개인 체질(더위/추위 타는 정도)을 반영해 적정 두께를 가감합니다.
5. 반드시 지정된 JSON 구조로만 응답합니다."""

    prompt = f"""
    [사용자 조건]
    - 위치: {location}
    - 이동 수단: {commute}
    - 외출 시간대: {time_range}
    - 체질 특성: {user_sens}
    
    현재 계절과 해당 지역의 전형적인 일교차 및 대중교통 환승 환경을 종합 고려하여 오늘자 최적의 레이어드 코디와 주의사항을 도출해줘.
    """

    schema = {
        "type": "OBJECT",
        "properties": {
            "weatherSummary": {
                "type": "OBJECT",
                "properties": {
                    "morningTemp": {"type": "NUMBER", "description": "출근 시간대 체감온도 (°C)"},
                    "dayMaxTemp": {"type": "NUMBER", "description": "낮 최고기온 (°C)"},
                    "eveningTemp": {"type": "NUMBER", "description": "퇴근/저녁 시간대 기온 (°C)"},
                    "tempDifference": {"type": "NUMBER", "description": "일교차 (°C)"},
                    "condition": {"type": "STRING", "description": "날씨 상태 요약 (예: 맑음, 강풍, 일교차 12도)"}
                },
                "required": ["morningTemp", "dayMaxTemp", "eveningTemp", "tempDifference", "condition"]
            },
            "outfit": {
                "type": "OBJECT",
                "properties": {
                    "outer": {"type": "STRING", "description": "외투 (탈착 편의성 고려)"},
                    "middle": {"type": "STRING", "description": "중간 레이어 (가디건, 조끼, 자켓 등)"},
                    "inner": {"type": "STRING", "description": "기본 이너 (티셔츠, 셔츠 등)"},
                    "bottom": {"type": "STRING", "description": "하의 (소재, 기장 등)"},
                    "shoes": {"type": "STRING", "description": "신발 (노면/온도 고려)"},
                    "accessories": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "머플러, 접이식 우산, 가방 등 소품"
                    }
                },
                "required": ["outer", "middle", "inner", "bottom", "shoes", "accessories"]
            },
            "actionableTips": {
                "type": "OBJECT",
                "properties": {
                    "transitTip": {"type": "STRING", "description": "대중교통 이동 및 환승 시 체온 조절 팁"},
                    "officeTip": {"type": "STRING", "description": "실내 근무 시 적정 룩 유지 요령"},
                    "caution": {"type": "STRING", "description": "오늘 피해야 할 아이템 또는 코디 금기사항"}
                },
                "required": ["transitTip", "officeTip", "caution"]
            }
        },
        "required": ["weatherSummary", "outfit", "actionableTips"]
    }

    # models/gemini-2.5-flash deprecated 에러를 방지하기 위해 최신 모델(gemini-3.8-flash)로 호출
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            ),
        )
    except Exception:
        # gemini-3.8-flash 호출 불가 시 gemini-1.5-flash로 자동 대체
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            ),
        )
    return json.loads(response.text)

if submit_btn:
    if not gemini_api_key:
        st.error("좌측 사이드바에 Gemini API Key를 입력해 주세요.")
    else:
        with st.spinner("오늘 날씨 분석 및 최적 레이어드 조합 계산 중..."):
            try:
                res = generate_recommendation(gemini_api_key, city, commute_type, hours, sensitivity)
                w = res["weatherSummary"]
                o = res["outfit"]
                t = res["actionableTips"]

                # 1. Weather Summary Card
                st.markdown("#### 🌡️ 오늘 체감 기온 분석")
                cols = st.columns(4)
                cols[0].markdown(f'<div class="metric-card"><div class="metric-val">{w["morningTemp"]:+.0f}°</div><div class="metric-lbl">출근 체감</div></div>', unsafe_allow_html=True)
                cols[1].markdown(f'<div class="metric-card"><div class="metric-val">{w["dayMaxTemp"]:+.0f}°</div><div class="metric-lbl">낮 최고</div></div>', unsafe_allow_html=True)
                cols[2].markdown(f'<div class="metric-card"><div class="metric-val">{w["eveningTemp"]:+.0f}°</div><div class="metric-lbl">퇴근 체감</div></div>', unsafe_allow_html=True)
                cols[3].markdown(f'<div class="metric-card"><div class="metric-val" style="color:#E11D48;">{w["tempDifference"]:.0f}°</div><div class="metric-lbl">일교차</div></div>', unsafe_allow_html=True)

                st.caption(f"📌 **날씨 요약**: {w['condition']}")

                # 2. Layered Outfit Card
                st.markdown("#### 👕 3단 레이어드 코디 추천")
                outfit_html = f"""
                <div class="outfit-box">
                    <div class="outfit-item"><span class="outfit-badge">아우터</span> <b>{o['outer']}</b></div>
                    <div class="outfit-item"><span class="outfit-badge">미들웨어</span> <b>{o['middle']}</b></div>
                    <div class="outfit-item"><span class="outfit-badge">이너</span> <b>{o['inner']}</b></div>
                    <hr style="margin: 10px 0; border: none; border-top: 1px dashed #E2E8F0;">
                    <div class="outfit-item"><span class="outfit-badge">하의</span> {o['bottom']}</div>
                    <div class="outfit-item"><span class="outfit-badge">신발</span> {o['shoes']}</div>
                    <div class="outfit-item"><span class="outfit-badge">소품</span> {', '.join(o['accessories'])}</div>
                </div>
                """
                st.markdown(outfit_html, unsafe_allow_html=True)

                # 3. Actionable Tips
                st.markdown("#### 💡 실전 조절 가이드")
                st.markdown(f'<div class="tip-box"><b>🚇 대중교통 팁:</b> {t["transitTip"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tip-box"><b>🏢 실내 근무 팁:</b> {t["officeTip"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="warn-box"><b>⚠️ 오늘 피해야 할 아이템:</b> {t["caution"]}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
