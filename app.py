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
    escaped = text.replace('`', r'\`').replace('$', r'\$')
    html = f"""
    <div style="margin-top:6px;margin-bottom:12px">
        <button onclick="navigator.clipboard.writeText(`{escaped}`).then(()=>{{this.innerText='✅ Copied!';setTimeout(()=>this.innerText='📋 Copy {label}',1500)}})"
        style="background:#4CAF50;color:white;padding:6px 16px;border:none;border-radius:6px;cursor:pointer;font-size:14px;">
        📋 Copy {label}
        </button>
    </div>
    """
    components.html(html, height=50)

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

        # Teams with 0 or no data (X) → Duck Tale list
        duck = [t for t in teams if t["EPI"] == 0 or t["EPI"] is None]

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        # ---------- MAIN RANKED LIST (no extra blank lines) ----------
        st.subheader("All Ranked Teams")

        rows_html = '<div style="line-height:1">'
        for idx, t in enumerate(ranked, 1):
            medal = medals.get(idx, "")
            rows_html += (
                f'<div style="margin:0;padding:2px 0;">'
                f'<b>{idx}</b>&nbsp;&nbsp;{medal}&nbsp;&nbsp;{t["Team"]}'
                f'</div>'
            )
        for t in duck:
            rows_html += (
                f'<div style="margin:0;padding:2px 0;">'
                f'<b>—</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{t["Team"]}'
                f'</div>'
            )
        rows_html += '</div>'
        st.markdown(rows_html, unsafe_allow_html=True)

        # ---------- TOP 3 ----------
        st.markdown("## Top 3 CSM Teams")

        top3_lines = []
        top3_html = '<div style="line-height:1">'

        for i, t in enumerate(ranked[:3], 1):
            medal = medals.get(i, "")
            team_name = re.sub(r'\bTeam\b\s*', '', t["Team"], flags=re.IGNORECASE).strip().upper()
            top3_html += (
                f'<div style="margin:0;padding:4px 0;font-size:1.1em;font-weight:bold;">'
                f'{medal}&nbsp;&nbsp;{team_name}'
                f'</div>'
            )
            top3_lines.append(f"{medal} {team_name}")

        top3_html += '</div>'
        st.markdown(top3_html, unsafe_allow_html=True)

        if top3_lines:
            copy_text = "Top 3 CSM Teams FTD\n\n" + "\n".join(top3_lines)
            top3_md_lines = ["**Top 3 CSM Teams FTD**", ""] + [f"**{line}**" for line in top3_lines]
            top3_md_html = "<br>".join(top3_md_lines)
            st.markdown(
                f'<div style="border:1px solid #444;border-radius:6px;padding:10px 14px;'
                f'background:#1e1e1e;color:#fff;font-size:0.95em;line-height:1.8;">'
                f'{top3_md_html}</div>',
                unsafe_allow_html=True
            )
            st.markdown("")
            copy_button(copy_text, "Top 3")

        # ---------- DUCK LIST ----------
        st.markdown("## 🦆 DUCK TALES TEAM FTD 🦆")

        duck_lines = []
        duck_html = '<div style="line-height:1">'

        for t in duck:
            team_name = re.sub(r'\bTeam\b\s*', '', t["Team"], flags=re.IGNORECASE).strip()
            duck_html += (
                f'<div style="margin:0;padding:4px 0;">'
                f'{team_name}&nbsp;&nbsp;'
                f'<span style="background:#e53935;color:white;font-weight:bold;'
                f'border-radius:4px;padding:1px 7px;font-size:1em;">0</span>'
                f'</div>'
            )
            duck_lines.append(f"{team_name} 0")

        duck_html += '</div>'
        st.markdown(duck_html, unsafe_allow_html=True)

        if duck_lines:
            duck_text = "🦆DUCK TALES TEAM FTD🦆\n\n" + "\n".join(duck_lines)
            st.code(duck_text, language=None)
            copy_button(duck_text, "Duck Tale Team")
