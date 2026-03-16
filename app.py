import streamlit as st
import re

st.set_page_config(page_title="Team Sorter", layout="centered")
st.title("Team Sorter")

DEFAULT_INPUT = (
    "*Team Ayan* - 3/5.36L*Team Prosenjit*-2/3.2L*Team Kol 3*-  1/1.2L"
    "*Team Bhasker*-  5/5L*Team Suman* -  *Team Raviteja* -  *Team Rajkumar* - "
    "*Team Rateesh* - 8/8.16*Team Harisha* - 3/4.75L*Team Prabhakar*-1/1L"
    "*Team  Muni*- 3/6L*Team Manjula*- 3/13.5L*Team Mukesh*-  3/4.16L"
    "*Team Bala* - 5/5.09L*Team Prem* -2/3.30*Team Somashekhar*- 3/9.3L"
)

text = st.text_area("Paste team data:", value=DEFAULT_INPUT, height=180)

if st.button("Sort Teams", type="primary"):
    parts = text.split('*')
    teams = []
    i = 0
    while i < len(parts):
        name = parts[i].strip()
        name = re.sub(r'\s+', ' ', name)
        if name.startswith('Team '):
            data_str = parts[i + 1] if i + 1 < len(parts) else ''
            m = re.search(r'([\d.]+)\s*/\s*([\d.]+)', data_str)
            if m:
                epi = float(m.group(2))
                teams.append({'Team': name, 'EPI': epi})
            else:
                teams.append({'Team': name, 'EPI': None})
            i += 2
        else:
            i += 1

    if not teams:
        st.warning("No teams found. Check the input format.")
    else:

        ranked = sorted(
            [t for t in teams if t['EPI'] is not None],
            key=lambda x: x['EPI'],
            reverse=True
        )
        unranked = [t for t in teams if t['EPI'] is None]

        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        for i, t in enumerate(ranked, 1):
            medal = medals.get(i, '')
            st.markdown(
                f"**{i}**&nbsp;&nbsp;{medal}&nbsp;&nbsp;{t['Team']}",
                unsafe_allow_html=True
            )
        for t in unranked:
            st.markdown(
                f"**—**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{t['Team']}",
                unsafe_allow_html=True
            )
