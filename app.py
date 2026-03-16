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
    pattern = r'\*([^*]+)\*\s*[-\u2013\u2014]?\s*([\d.]+\s*/\s*[\d.]+L?)?'
    matches = re.findall(pattern, text)

    if not matches:
        st.warning("No teams found. Check the input format.")
    else:
        teams = []
        for name, data in matches:
            name = name.strip()
            if not name.startswith("Team"):
                continue
            data = data.strip()
            if data:
                raw_epi = data.rstrip('L')
                parts = raw_epi.split('/')
                epi = float(parts[1].strip())
                teams.append({'Team': name, 'EPI': epi})
            else:
                teams.append({'Team': name, 'EPI': None})

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
