import json
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="일교차 레이어드 코디", page_icon="🧥")

st.title("🧥 출퇴근 레이어드 코디")
st.caption("일교차와 실내외 냉난방을 고려한 오늘 맞춤 룩")

with st.sidebar:
    st.header("설정")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    if not gemini_api_key and "GEMINI_API_KEY" in st.secrets:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]

with st.form("form"):
    city = st.text_input("지역", value="서울 영등포구")
    commute_type = st.selectbox("이동 수단", ["지하철/버스", "도보 위주", "자차/택시"])
    hours = st.selectbox("시간대", ["출퇴근 (08시~19시)", "낮 외출 (11시~16시)", "종일 (아침~밤)"])
    sensitivity = st.select_slider("체질", options=["추위 탐", "보통", "더위 탐"], value="보통")
    submit = st.form_submit_button("코디 추천받기", use_container_width=True)

def run_ai(key, loc, trans, tm, sens):
    client = genai.Client(api_key=key)
    prompt = f"""
    위치: {loc}, 이동: {trans}, 시간대: {tm}, 체질: {sens}
    오늘 일교차와 실내외 환경에 맞는 3단 레이어드 코디를 아래 JSON으로 응답해줘.
    {{
      "morningTemp": 5,
      "dayTemp": 18,
      "diff": 13,
      "cond": "일교차 큼",
      "outer": "트렌치코트",
      "mid": "가디건",
      "inner": "롱슬리브 티셔츠",
      "bottom": "슬랙스",
      "shoes": "스니커즈",
      "acc": "가벼운 머플러",
      "tip1": "지하철 탑승 시 아우터는 벗어 손에 걸쳐주세요.",
      "tip2": "사무실에서는 가디건만 입어 쾌적함을 유지하세요.",
      "warn": "두꺼운 니트 단벌은 온도 조절에 불리합니다."
    }}
    """
    res = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return json.loads(res.text)

if submit:
    if not gemini_api_key:
        st.error("Gemini API 키를 입력해주세요.")
    else:
        with st.spinner("코디 생성 중..."):
            try:
                d = run_ai(gemini_api_key, city, commute_type, hours, sensitivity)

                st.subheader("🌡️ 체감 기온")
                c1, c2, c3 = st.columns(3)
                c1.metric("출근 체감", f"{d.get('morningTemp', 0)}도")
                c2.metric("낮 최고", f"{d.get('dayTemp', 0)}도")
                c3.metric("일교차", f"{d.get('diff', 0)}도")
                st.caption(f"상태: {d.get('cond', '맑음')}")

                st.subheader("👕 레이어드 코디")
                st.write(f"• **아우터:** {d.get('outer', '-')}")
                st.write(f"• **미들웨어:** {d.get('mid', '-')}")
                st.write(f"• **이너:** {d.get('inner', '-')}")
                st.write(f"• **하의:** {d.get('bottom', '-')}")
                st.write(f"• **신발:** {d.get('shoes', '-')}")
                st.write(f"• **소품:** {d.get('acc', '-')}")

                st.subheader("💡 실전 팁")
                st.info(d.get("tip1", "-"))
                st.info(d.get("tip2", "-"))
                st.warning(d.get("warn", "-"))
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
