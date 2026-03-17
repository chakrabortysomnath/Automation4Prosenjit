import streamlit as st
import re
import io
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Team Sorter", layout="centered")
st.title("Team Sorter")

# ---------- FONT PATHS ----------
BOLD_FONT  = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
REG_FONT   = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

# ---------- IMAGE HELPERS ----------
def _emoji_img(char, target_h):
    """Render a single emoji to an RGBA image scaled to target_h pixels tall."""
    ef = ImageFont.truetype(EMOJI_FONT, 109)
    bb = ef.getbbox(char)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    if h == 0:
        return Image.new('RGBA', (target_h, target_h), (0, 0, 0, 0))
    tmp = Image.new('RGBA', (w + 4, h + 4), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((-bb[0] + 2, -bb[1] + 2), char, font=ef, embedded_color=True)
    scale = target_h / h
    return tmp.resize((max(1, int(w * scale)), target_h), Image.LANCZOS)


def make_top3_image(top3_entries):
    """
    top3_entries: list of (medal_emoji, team_name_str)
    Returns a PIL Image.
    """
    EMOJI_H   = 38
    TEXT_SIZE = 36
    PAD       = 24
    ROW_GAP   = 14
    TITLE_SIZE = 28

    font_title = ImageFont.truetype(BOLD_FONT, TITLE_SIZE)
    font_name  = ImageFont.truetype(BOLD_FONT, TEXT_SIZE)

    title = "Top 3 CSM Teams FTD"
    title_bb = font_title.getbbox(title)
    title_h  = title_bb[3] - title_bb[1]

    row_h = max(EMOJI_H, TEXT_SIZE + 6)
    n     = len(top3_entries)
    total_h = PAD + title_h + PAD + n * row_h + (n - 1) * ROW_GAP + PAD

    # Estimate width
    max_text_w = max(font_name.getbbox(name)[2] for _, name in top3_entries)
    total_w = PAD + EMOJI_H + 14 + max_text_w + PAD
    total_w = max(total_w, font_title.getbbox(title)[2] + PAD * 2)

    img = Image.new('RGBA', (total_w, total_h), (28, 28, 28, 255))
    d   = ImageDraw.Draw(img)

    # Title
    y = PAD
    d.text((PAD, y), title, font=font_title, fill=(220, 220, 220))
    y += title_h + PAD

    # Rows
    for medal_char, name in top3_entries:
        em_img = _emoji_img(medal_char, EMOJI_H)
        img.paste(em_img, (PAD, y), em_img)
        text_y = y + (EMOJI_H - TEXT_SIZE) // 2
        d.text((PAD + em_img.width + 14, text_y), name, font=font_name, fill=(255, 255, 255))
        y += row_h + ROW_GAP

    return img


def make_duck_image(duck_names):
    """
    duck_names: list of team name strings (no 'Team' prefix)
    Returns a PIL Image.
    """
    EMOJI_H    = 36
    TEXT_SIZE  = 30
    BADGE_SIZE = 26
    PAD        = 24
    ROW_GAP    = 12
    TITLE_SIZE = 28

    font_title = ImageFont.truetype(BOLD_FONT, TITLE_SIZE)
    font_name  = ImageFont.truetype(REG_FONT,  TEXT_SIZE)
    font_badge = ImageFont.truetype(BOLD_FONT, BADGE_SIZE)

    title = "DUCK TALES TEAM FTD"
    title_bb = font_title.getbbox(title)
    title_h  = title_bb[3] - title_bb[1]

    duck_em = _emoji_img('🦆', EMOJI_H)

    row_h = max(EMOJI_H, TEXT_SIZE + 6)
    n     = len(duck_names)
    total_h = PAD + EMOJI_H + 10 + title_h + PAD + n * row_h + (n - 1) * ROW_GAP + PAD

    # Estimate width: name + badge
    max_name_w = max((font_name.getbbox(nm)[2] for nm in duck_names), default=200)
    badge_w = 34
    total_w = PAD + max_name_w + 14 + badge_w + PAD
    header_w = PAD + duck_em.width + 10 + font_title.getbbox(title)[2] + 10 + duck_em.width + PAD
    total_w = max(total_w, header_w)

    img = Image.new('RGBA', (total_w, total_h), (28, 28, 28, 255))
    d   = ImageDraw.Draw(img)

    # Header: 🦆 DUCK TALES TEAM FTD 🦆
    y = PAD
    x = PAD
    img.paste(duck_em, (x, y), duck_em)
    x += duck_em.width + 10
    title_y = y + (EMOJI_H - title_h) // 2
    d.text((x, title_y), title, font=font_title, fill=(255, 220, 50))
    x += font_title.getbbox(title)[2] + 10
    img.paste(duck_em, (x, y), duck_em)
    y += EMOJI_H + PAD

    # Rows: name  [0]
    for name in duck_names:
        name_bb = font_name.getbbox(name)
        text_y  = y + (row_h - (name_bb[3] - name_bb[1])) // 2
        d.text((PAD, text_y), name, font=font_name, fill=(255, 255, 255))

        # Red badge
        bx = PAD + max_name_w + 14
        by = y + (row_h - BADGE_SIZE - 4) // 2
        bw, bh = badge_w, BADGE_SIZE + 4
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=5, fill=(229, 57, 53))
        zero_bb = font_badge.getbbox("0")
        zw = zero_bb[2] - zero_bb[0]
        zh = zero_bb[3] - zero_bb[1]
        d.text((bx + (bw - zw) // 2, by + (bh - zh) // 2 - zero_bb[1]), "0",
               font=font_badge, fill=(255, 255, 255))

        y += row_h + ROW_GAP

    return img


def img_to_bytes(pil_img):
    buf = io.BytesIO()
    pil_img.convert('RGB').save(buf, format='PNG')
    return buf.getvalue()


# ---------- SESSION STATE ----------
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# ---------- INPUT ----------
col1, col2 = st.columns(2)
with col1:
    sort_btn = st.button("Sort Teams", type="primary")
with col2:
    if st.button("Clear"):
        st.session_state.input_text = ""
        st.rerun()

text = st.text_area(
    "Paste team data:",
    key="input_text",
    height=180,
    placeholder="Paste new team dataset here..."
)

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
        duck = [t for t in teams if t["EPI"] == 0 or t["EPI"] is None]

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        # ── List 1: Full sorted ranking ──────────────────────────────────────
        st.markdown("---")
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

        # ── List 2: Top 3 CSM Teams ───────────────────────────────────────────
        st.markdown("---")
        st.markdown("## Top 3 CSM Teams")

        top3_display_html = '<div style="line-height:1">'
        top3_entries = []
        for i, t in enumerate(ranked[:3], 1):
            medal = medals[i]
            team_name = re.sub(r'\bTeam\b\s*', '', t["Team"], flags=re.IGNORECASE).strip().upper()
            top3_display_html += (
                f'<div style="margin:0;padding:4px 0;font-size:1.1em;font-weight:bold;">'
                f'{medal}&nbsp;&nbsp;{team_name}'
                f'</div>'
            )
            top3_entries.append((medal, team_name))
        top3_display_html += '</div>'
        st.markdown(top3_display_html, unsafe_allow_html=True)

        if top3_entries:
            st.markdown("---")
            top3_img = make_top3_image(top3_entries)
            st.image(top3_img, caption="Right-click → Copy image  /  Long-press to share")
            st.download_button(
                "⬇️ Download Top 3 image",
                data=img_to_bytes(top3_img),
                file_name="top3_csm_teams.png",
                mime="image/png"
            )

        # ── List 3: Duck Tales Team FTD ───────────────────────────────────────
        st.markdown("---")
        st.markdown("## 🦆 DUCK TALES TEAM FTD 🦆")

        duck_display_html = '<div style="line-height:1">'
        duck_names = []
        for t in duck:
            team_name = re.sub(r'\bTeam\b\s*', '', t["Team"], flags=re.IGNORECASE).strip()
            duck_display_html += (
                f'<div style="margin:0;padding:4px 0;">'
                f'{team_name}&nbsp;&nbsp;'
                f'<span style="background:#e53935;color:white;font-weight:bold;'
                f'border-radius:4px;padding:1px 7px;font-size:1em;">0</span>'
                f'</div>'
            )
            duck_names.append(team_name)
        duck_display_html += '</div>'
        st.markdown(duck_display_html, unsafe_allow_html=True)

        if duck_names:
            st.markdown("---")
            duck_img = make_duck_image(duck_names)
            st.image(duck_img, caption="Right-click → Copy image  /  Long-press to share")
            st.download_button(
                "⬇️ Download Duck Tales image",
                data=img_to_bytes(duck_img),
                file_name="duck_tales_team_ftd.png",
                mime="image/png"
            )
