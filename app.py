import streamlit as st
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="Team Sorter", layout="centered")
st.title("Team Sorter")

# ---------- SESSION STATE ----------
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# ---------- COPY BUTTON FUNCTION ----------
def copy_button(text, label):
    html = f"""
    <div style="margin-top:8px;margin-bottom:15px">
        <button onclick="navigator.clipboard.writeText(`{text}`)"
        style="
        background-color:#4CAF50;
        color:white;
        padding:6px 14px;
        border:none;
        border-radius:6px;
        cursor:pointer;
        font-size:14px;">
        📋 Copy {label}
        </button>
    </div>
    """
    components.html(html, height=45)

# ---------- INPUT ----------
text = st.text_area(
    "Paste team data:",
    key="input_text",
    height=180,
    placeholder="Paste new team dataset here..."
)

col1, col2 = st.columns(2)

with col1:
    sort_btn = st.button("Sort Teams", type="primary")

with col2:
    if st.button("Clear"):
        st.session_state.input_text = ""
        st.rerun()

# ---------- PROCESS ----------
if sort_btn and text.strip():

    parts = text.split('*')
    teams = []

    i = 0
    while i < len(parts):

        name = parts[i].strip()
        name = re.sub(r'\s+', ' ', name)

        if name.startswith('Team '):

            data_str = parts[i + 1] if i + 1 < len(parts) else ""

            m = re.search(r'([\d.]+)\s*/\s*([\d.]+)', data_str)

            if m:
                epi = float(m.group(2))
                teams.append({"Team": name, "EPI": epi})

            else:
                if re.search(r'\b0\b|\bX\b', data_str, re.IGNORECASE):
                    teams.append({"Team": name, "EPI": 0})
                else:
                    teams.append({"Team": name, "EPI": None})

            i += 2
        else:
            i += 1

    if not teams:
        st.warning("No teams found. Check the input format.")

    else:

        ranked = sorted(
            [t for t in teams if t["EPI"] not in (None, 0)],
            key=lambda x: x["EPI"],
            reverse=True
        )

        duck = [t for t in teams if t["EPI"] == 0]
        unranked = [t for t in teams if t["EPI"] is None]

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        # ---------- MAIN RANKED LIST ----------
        st.subheader("All Ranked Teams")

        for i, t in enumerate(ranked, 1):
            medal = medals.get(i, "")
            st.markdown(f"**{i}. {medal} {t['Team']}**")

        for t in unranked:
            st.markdown(f"**— {t['Team']}**")

        # ---------- TOP 3 ----------
        st.markdown("## Top 3 CSM Team")

        top3_lines = []

        for i, t in enumerate(ranked[:3], 1):

            medal = medals.get(i, "")

            team_name = re.sub(r'^Team\s+', '', t["Team"]).strip().upper()

            st.markdown(f"{medal} **{team_name}**")

            top3_lines.append(f"{medal} {team_name}")

        if top3_lines:

            copy_text = "\n".join(top3_lines)

            st.code(copy_text)

            copy_button(copy_text, "Top 3")

        # ---------- DUCK LIST ----------
        st.markdown("## 🦆 DUCK TALE TEAM FTD 🦆")

        duck_lines = []

        for t in duck:

            team_name = re.sub(r'^Team\s+', '', t["Team"]).strip().upper()

            st.markdown(f"🦆 **{team_name}**")

            duck_lines.append(team_name)

        if duck_lines:

            duck_text = "\n".join(duck_lines)

            st.code(duck_text)

            copy_button(duck_text, "Duck Teams")
