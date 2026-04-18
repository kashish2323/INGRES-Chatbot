import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator

st.set_page_config(layout="wide")

# ------------------------
# 🎨 UI Styling
# ------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}
h1 {
    color: #38bdf8;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ✅ UPDATED TITLE
#st.title("💧 INDIA-Groundwater Resource Estimation System (IN-GRES)")
st.markdown("""
<div style='text-align: center; margin-top: 30px;'>
    <h1 style='color:#38bdf8; font-size: 50px; font-weight: 700; margin-bottom: 5px;'>
        💧 IN-GRES Chatbot
    </h1>
    <p style='color: #94a3b8; font-size: 18px;'>
        INDIA-Groundwater Resource Estimation System
    </p>
</div>
""", unsafe_allow_html=True)

# ------------------------
# Sidebar
# ------------------------
with st.sidebar:

    st.header("💡 Example Queries")
    st.markdown("""
- Groundwater Rajasthan 2021  
- Show trend Punjab  
- Compare Rajasthan Haryana 2021  
- राजस्थान 2021 का भूजल स्तर क्या है  
""")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_state = None
        st.session_state.last_year = None
        st.session_state.chart_visibility = {}
        st.rerun()

# ------------------------
# Load Data
# ------------------------
data = pd.read_csv("groundwater_data.csv")
states = data["state"].unique().tolist()

# ------------------------
# Hindi Detection
# ------------------------
def is_hindi(text):
    return any('\u0900' <= ch <= '\u097F' for ch in text)

# ------------------------
# Memory
# ------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_state" not in st.session_state:
    st.session_state.last_state = None

if "last_year" not in st.session_state:
    st.session_state.last_year = None

# ⭐ Track chart visibility per message
if "chart_visibility" not in st.session_state:
    st.session_state.chart_visibility = {}

# ------------------------
# Display Chat
# ------------------------
for i, msg in enumerate(st.session_state.messages):

    with st.chat_message(msg["role"]):
        st.write(msg["text"])

        # ⭐ Toggle Button
        if "chart" in msg and msg["chart"] is not None:

            if i not in st.session_state.chart_visibility:
                st.session_state.chart_visibility[i] = False

            toggle = st.button(
                "📊 View Chart" if not st.session_state.chart_visibility[i] else "❌ Close Chart",
                key=f"toggle_{i}"
            )

            if toggle:
                st.session_state.chart_visibility[i] = not st.session_state.chart_visibility[i]

            if st.session_state.chart_visibility[i]:
                st.pyplot(msg["chart"])

# ------------------------
# Input
# ------------------------
user_input = st.chat_input("💬 Ask something...")

if user_input:

    st.session_state.messages.append({"role": "user", "text": user_input})

    hindi_flag = is_hindi(user_input)

    if hindi_flag:
        text = GoogleTranslator(source='auto', target='en').translate(user_input).lower()
    else:
        text = user_input.lower()

    detected_states = [s for s in states if s in text]

    detected_year = None
    for w in text.split():
        if w.isdigit() and len(w) == 4:
            detected_year = w

    if detected_states:
        st.session_state.last_state = detected_states[0]

    if detected_year:
        st.session_state.last_year = detected_year

    # Intent
    if "compare" in text:
        intent = "comparison"
    elif "trend" in text:
        intent = "trend"
    elif detected_states:
        intent = "groundwater"
    else:
        intent = None

    def translate(msg):
        return GoogleTranslator(source='auto', target='hi').translate(msg) if hindi_flag else msg

    with st.spinner("🤖 Thinking..."):

        response = ""
        chart = None

        # ------------------------
        # COMPARISON
        # ------------------------
        if intent == "comparison":

            if len(detected_states) < 2 or not detected_year:
                response = translate("Please provide two states and a year.")

            else:
                s1, s2 = detected_states[0], detected_states[1]
                year = int(detected_year)

                r1 = data[(data["state"] == s1) & (data["year"] == year)]
                r2 = data[(data["state"] == s2) & (data["year"] == year)]

                if not r1.empty and not r2.empty:
                    v1 = r1.iloc[0]["groundwater_level"]
                    v2 = r2.iloc[0]["groundwater_level"]

                    fig = plt.figure()
                    plt.bar([s1, s2], [v1, v2])

                    chart = fig

                    response = translate(f"{s1} = {v1}, {s2} = {v2}")
                else:
                    response = translate("Data not found.")

        # ------------------------
        # TREND
        # ------------------------
        elif intent == "trend":

            state = detected_states[0] if detected_states else st.session_state.last_state

            if not state:
                response = translate("Please specify a state.")
            else:
                df = data[data["state"] == state]

                fig = plt.figure()
                plt.plot(df["year"], df["groundwater_level"], marker="o")

                chart = fig

                response = translate(f"Trend shown for {state}")

        # ------------------------
        # GROUNDWATER
        # ------------------------
        elif intent == "groundwater":

            state = detected_states[0] if detected_states else st.session_state.last_state
            year = detected_year if detected_year else st.session_state.last_year

            if not state or not year:
                response = translate("Please specify state and year.")
            else:
                year = int(year)
                result = data[(data["state"] == state) & (data["year"] == year)]

                if not result.empty:
                    value = result.iloc[0]["groundwater_level"]
                    response = translate(f"{state} {year} groundwater level is {value}")
                else:
                    response = translate("No data found.")

        else:
            response = translate("Sorry, I didn't understand.")

    st.session_state.messages.append({
        "role": "assistant",
        "text": response,
        "chart": chart
    })

    with st.chat_message("assistant"):
        st.write(response)

        if chart is not None:
            if "latest" not in st.session_state.chart_visibility:
                st.session_state.chart_visibility["latest"] = True

            toggle = st.button("❌ Close Chart", key="latest_toggle")

            if toggle:
                st.session_state.chart_visibility["latest"] = not st.session_state.chart_visibility["latest"]

            if st.session_state.chart_visibility["latest"]:
                st.pyplot(chart)