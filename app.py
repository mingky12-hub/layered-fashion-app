import json
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="일교차 레이어드 코디",
    page_icon="🧥",
    layout="centered"
)

st.title("🧥 출퇴근 레이어드 코디")
st.caption("일교차와 실내외 냉난방을 고려한 오늘 맞춤 룩")

# API 키 설정
with st.sidebar:
    st.header("⚙️ 환경 설정")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    if not gemini_api_key and "GEMINI_API_KEY" in st.secrets:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]

# 입력 폼
with st.form("coordi_form"):
    city = st.text_input("지역 (시/구)", value="서울 영등포구")
    commute_type = st.selectbox("이동 수단", ["지하철/버스", "도보 위주", "자차/택시"])
    hours = st.selectbox("외출 시간대", ["출퇴근 (오전 8시 ~ 저녁 7시)", "낮 외출 (오전 11시 ~ 오후 4시)", "종일 (오전 ~ 밤)"])
    sensitivity = st.select_slider("체질", options=["추위 탐", "보통", "더위 탐"], value="보통")
    submit_btn = st.form_submit_button("오늘의 레이어드 코디 추천받기", use_container_width=True)

def get_recommendation(api_key, location, commute, time_range, user_sens):
    client = genai.Client(api_key=api_key)
    
    sys_inst = (
        "당신은 일교차와 실내외 환경(대중교통 냉난방, 실내 온도)을 고려하는 패션 스타일리스트입니다. "
        "주어진 조건에 맞춰 탈착이 용이한 최적의 3단 레이어드 코디를 반드시 유효한 JSON 형식으로만 작성하세요."
    )
    
    prompt = f"""
    [조건]
    위치: {location}
    이동수단: {commute}
    외출시간대: {time_range}
    체질: {user_sens}
    
    오늘 날씨와 일교차를 고려해 아래 JSON 형식 그대로 응답하세요:
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
        "transitTip": "지하철 내부 난방 시 아우터를 벗어 체온을 조절하세요.",
        "officeTip": "실내에서는 가디건만 걸쳐 쾌적함을 유지하세요.",
        "caution": "두꺼운 니트 단벌은 온도차 대응에 불리합니다."
      }}
    }}
    """
    
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
        st.error("좌측 사이드바 또는 Secrets에 Gemini API Key를 입력해 주세요.")
    else:
        with st.spinner("오늘 날씨 분석 및 최적 레이어드 조합 계산 중..."):
            try:
                res = get_recommendation(gemini_api_key, city, commute_type, hours, sensitivity)
                w = res.get("weatherSummary", {})
                o = res.get("outfit", {})
                t = res.get("actionableTips", {})

                # 1. 체감 기온 분석
                st.subheader("🌡️ 체감 기온 분석")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("출근 체감", f"{w.get('morningTemp', 0):+.0f}°")
                c2.metric("낮 최고", f"{w.get('dayMaxTemp', 0):+.0f}°")
                c3.metric("퇴근 체감", f"{w.get('eveningTemp', 0):+.0f}°")
                c4.metric("일교차", f"{w.get('tempDifference', 0):.0f}°")
                st.caption(f"📌 **날씨 상태**: {w.get('condition', '맑음')}")

                # 2. 3단 레이어드 코디
                st.subheader("👕 3단 레이어드 코디")
                with st.container(border=True):
                    st.write(f"🧥 **아우터:** {o.get('outer', '-')}")
                    st.write(f"🧶 **미들웨어:** {o.get('middle', '-')}")
                    st.write(f"👕 **이너:** {o.get('inner', '-')}")
                    st.divider()
                    st.write(f"👖 **하의:** {o.get('bottom', '-')}")
                    st.write(f"👟 **신발:** {o.get('shoes', '-')}")
                    acc_text = ", ".join(o.get("accessories", []))
                    st.write(f"🎒 **소품:** {acc_text if acc_text else '-'}")

                # 3. 실전 팁
                st.subheader("💡 실전 조절 가이드")
                st.info(f"🚇 **대중교통:** {t.get('transitTip', '-')}")
                st.info(f"🏢 **실내 근무:** {t.get('
