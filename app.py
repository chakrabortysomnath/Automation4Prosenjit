import streamlit as st
import re
import pandas as pd

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
    # Match *Team Name* optionally followed by - NOP/EPI
    pattern = r'\*([^*]+)\*\s*-?\s*([\d.]+/[\d.]+L?)?'
    matches = re.findall(pattern, text)

    if not matches:
        st.warning("No teams found. Check the input format.")
    else:
        teams = []
        for name, data in matches:
            name = name.strip()
            data = data.strip()
            if data:
                raw_epi = data.rstrip('L')
                parts = raw_epi.split('/')
                nop = parts[0].strip()
                epi = float(parts[1].strip())
                teams.append({'Team': name, 'NOP': nop, 'EPI': epi, 'Display': data})
            else:
                teams.append({'Team': name, 'NOP': None, 'EPI': None, 'Display': None})

        ranked = sorted(
            [t for t in teams if t['EPI'] is not None],
            key=lambda x: x['EPI'],
            reverse=True
        )
        unranked = [t for t in teams if t['EPI'] is None]

        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        rows = []
        for i, t in enumerate(ranked, 1):
            rows.append({
                'Rank': i,
                'Medal': medals.get(i, ''),
                'Team': t['Team'],
                'NOP / EPI': t['Display'],
            })
        for t in unranked:
            rows.append({
                'Rank': '—',
                'Medal': '',
                'Team': t['Team'],
                'NOP / EPI': '—',
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.caption(f"Total teams: {len(ranked)} ranked, {len(unranked)} unranked")
