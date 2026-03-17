import streamlit as st
import re
import io
import os
import json
from PIL import Image, ImageDraw, ImageFont

with open(os.path.join(os.path.dirname(__file__), 'config.json')) as _f:
    _CFG = json.load(_f)

st.set_page_config(page_title="Team Sorter", layout="centered")
st.title("Team Sorter")

# ---------- FONT RESOLUTION (works locally and on Streamlit Cloud) ----------
def _find_font(bold=True):
    """Return a path to a TTF font, falling back to matplotlib's bundled DejaVu."""
    key = 'bold_candidates' if bold else 'regular_candidates'
    for p in _CFG['fonts'][key]:
        if os.path.exists(p):
            return p
    # Always-available fallback via matplotlib
    import matplotlib.font_manager as fm
    weight = 'bold' if bold else 'regular'
    family = _CFG['fonts']['matplotlib_fallback_family']
    prop = fm.FontProperties(weight=weight, family=family)
    return fm.findfont(prop)


BOLD_FONT = _find_font(bold=True)
REG_FONT  = _find_font(bold=False)

# Bundled Twemoji PNGs (committed to repo — no CDN or system font needed)
_ASSETS = os.path.join(os.path.dirname(__file__), 'assets', 'emoji')
_EMOJI_FILES = {
    '🥇': os.path.join(_ASSETS, '1f947.png'),
    '🥈': os.path.join(_ASSETS, '1f948.png'),
    '🥉': os.path.join(_ASSETS, '1f949.png'),
    '🦆': os.path.join(_ASSETS, '1f986.png'),
}

# Medal colours for fallback circle badges (if PNG files somehow missing)
MEDAL_COLORS = {
    1: (255, 215,   0),   # gold
    2: (192, 192, 192),   # silver
    3: (205, 127,  50),   # bronze
}

# ---------- IMAGE HELPERS ----------
def _emoji_img(char, target_h):
    """Load bundled Twemoji PNG and scale to target_h pixels tall."""
    path = _EMOJI_FILES.get(char)
    if path and os.path.exists(path):
        em = Image.open(path).convert('RGBA')
        w, h = em.size
        scale = target_h / h
        return em.resize((max(1, int(w * scale)), target_h), Image.LANCZOS)
    return None   # triggers coloured-circle / duck-badge fallback


def _medal_circle(rank, size):
    """Draw a coloured circle with rank number — fallback when emoji unavailable."""
    color = MEDAL_COLORS.get(rank, (150, 150, 150))
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=color)
    font = ImageFont.truetype(BOLD_FONT, int(size * 0.55))
    txt  = str(rank)
    bb   = font.getbbox(txt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((size - tw) // 2 - bb[0], (size - th) // 2 - bb[1]), txt,
           font=font, fill=(30, 30, 30))
    return img


def _duck_badge(size):
    """Simple teal duck-shaped rectangle when emoji unavailable."""
    img = Image.new('RGBA', (size * 2, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size * 2 - 1, size - 1], radius=size // 4,
                         fill=(0, 150, 136))
    font = ImageFont.truetype(BOLD_FONT, int(size * 0.5))
    bb   = font.getbbox("DK")
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((size * 2 - tw) // 2 - bb[0], (size - th) // 2 - bb[1]), "DK",
           font=font, fill=(255, 255, 255))
    return img


# ---------- WATERMARK HELPER ----------
def _apply_watermark(img):
    """Paste a faded logo centred on img (in-place)."""
    logo_path = os.path.join(os.path.dirname(__file__),
                             _CFG['theme']['watermark_logo'])
    if not os.path.exists(logo_path):
        return
    opacity = _CFG['theme']['watermark_opacity']   # 0-255
    logo = Image.open(logo_path).convert('RGBA')
    # Scale logo to fit 70% of the smaller canvas dimension
    scale = (min(img.width, img.height) * 0.70) / max(logo.width, logo.height)
    new_w = max(1, int(logo.width  * scale))
    new_h = max(1, int(logo.height * scale))
    logo = logo.resize((new_w, new_h), Image.LANCZOS)
    # Apply opacity to alpha channel
    r, g, b, a = logo.split()
    a = a.point(lambda p: int(p * opacity / 255))
    logo = Image.merge('RGBA', (r, g, b, a))
    # Centre on canvas
    x = (img.width  - new_w) // 2
    y = (img.height - new_h) // 2
    img.paste(logo, (x, y), logo)


# ---------- IMAGE GENERATORS ----------
def make_top3_image(top3_entries):
    """top3_entries: list of (rank_int, team_name_str)"""
    ICON_H     = _CFG['top3']['ICON_H']
    TEXT_SIZE  = _CFG['top3']['TEXT_SIZE']
    PAD        = _CFG['top3']['PAD']
    ROW_GAP    = _CFG['top3']['ROW_GAP']
    TITLE_SIZE = _CFG['top3']['TITLE_SIZE']

    _f = {'bold': BOLD_FONT, 'regular': REG_FONT}
    font_title = ImageFont.truetype(_f[_CFG['top3']['title_font']], TITLE_SIZE)
    font_name  = ImageFont.truetype(_f[_CFG['top3']['name_font']],  TEXT_SIZE)

    title    = _CFG['top3']['header']
    title_bb = font_title.getbbox(title)
    title_h  = title_bb[3] - title_bb[1]
    row_h    = max(ICON_H, TEXT_SIZE + 6)
    n        = len(top3_entries)
    total_h  = PAD + title_h + PAD + n * row_h + (n - 1) * ROW_GAP + PAD

    max_text_w = max(font_name.getbbox(name)[2] for _, name in top3_entries)
    total_w    = max(PAD + ICON_H + 16 + max_text_w + PAD,
                     title_bb[2] - title_bb[0] + PAD * 2)

    BG     = tuple(_CFG['theme']['bg_color']) + (255,)
    BORDER = tuple(_CFG['theme']['border_color'])
    BW     = _CFG['theme']['border_width']
    M      = _CFG['theme']['margin']

    canvas_w = total_w + M * 2
    canvas_h = total_h + M * 2
    img = Image.new('RGBA', (canvas_w, canvas_h), BG)
    _apply_watermark(img)
    d   = ImageDraw.Draw(img)
    d.rectangle([0, 0, canvas_w - 1, canvas_h - 1], outline=BORDER, width=BW)

    # Title row
    y = M + PAD
    d.text((M + PAD, y), title, font=font_title, fill=(255, 255, 255))
    y += title_h + PAD

    # Medal rows
    medal_chars = {1: '🥇', 2: '🥈', 3: '🥉'}
    for rank, name in top3_entries:
        em = _emoji_img(medal_chars.get(rank, ''), ICON_H)
        if em is None:
            em = _medal_circle(rank, ICON_H)
        img.paste(em, (M + PAD, y + (row_h - ICON_H) // 2), em)
        text_y = y + (row_h - TEXT_SIZE) // 2
        d.text((M + PAD + ICON_H + 16, text_y), name, font=font_name, fill=(255, 255, 255))
        y += row_h + ROW_GAP

    return img


def make_duck_image(duck_names):
    """duck_names: list of team name strings (no 'Team' prefix)"""
    ICON_H     = _CFG['duck']['ICON_H']
    TEXT_SIZE  = _CFG['duck']['TEXT_SIZE']
    BADGE_SIZE = _CFG['duck']['BADGE_SIZE']
    PAD        = _CFG['duck']['PAD']
    ROW_GAP    = _CFG['duck']['ROW_GAP']
    TITLE_SIZE = _CFG['duck']['TITLE_SIZE']

    _f = {'bold': BOLD_FONT, 'regular': REG_FONT}
    font_title = ImageFont.truetype(_f[_CFG['duck']['title_font']], TITLE_SIZE)
    font_name  = ImageFont.truetype(_f[_CFG['duck']['name_font']],  TEXT_SIZE)
    font_badge = ImageFont.truetype(_f[_CFG['duck']['badge_font']], BADGE_SIZE)

    title    = _CFG['duck']['header']
    title_bb = font_title.getbbox(title)
    title_h  = title_bb[3] - title_bb[1]

    duck_em = _emoji_img('🦆', ICON_H)
    if duck_em is None:
        duck_em = _duck_badge(ICON_H)

    row_h   = max(ICON_H, TEXT_SIZE + 6)
    n       = len(duck_names)
    total_h = PAD + ICON_H + PAD + n * row_h + (n - 1) * ROW_GAP + PAD

    max_name_w = max((font_name.getbbox(nm)[2] for nm in duck_names), default=200)
    badge_w    = 36
    hdr_w      = PAD + duck_em.width + 10 + (title_bb[2] - title_bb[0]) + 10 + duck_em.width + PAD
    total_w    = max(PAD + max_name_w + 14 + badge_w + PAD, hdr_w)

    BG     = tuple(_CFG['theme']['bg_color']) + (255,)
    BORDER = tuple(_CFG['theme']['border_color'])
    BW     = _CFG['theme']['border_width']
    M      = _CFG['theme']['margin']

    canvas_w = total_w + M * 2
    canvas_h = total_h + M * 2
    img = Image.new('RGBA', (canvas_w, canvas_h), BG)
    _apply_watermark(img)
    d   = ImageDraw.Draw(img)
    d.rectangle([0, 0, canvas_w - 1, canvas_h - 1], outline=BORDER, width=BW)

    # Header: 🦆 DUCK TALES TEAM FTD 🦆
    y = M + PAD
    x = M + PAD
    img.paste(duck_em, (x, y), duck_em)
    x += duck_em.width + 10
    d.text((x, y + (ICON_H - title_h) // 2), title, font=font_title, fill=(255, 220, 50))
    x += title_bb[2] - title_bb[0] + 10
    img.paste(duck_em, (x, y), duck_em)
    y += ICON_H + PAD

    # Team rows: name + red 0 badge
    for name in duck_names:
        name_bb = font_name.getbbox(name)
        d.text((M + PAD, y + (row_h - (name_bb[3] - name_bb[1])) // 2),
               name, font=font_name, fill=(255, 255, 255))

        bx = M + PAD + max_name_w + 14
        by = y + (row_h - BADGE_SIZE - 4) // 2
        bw, bh = badge_w, BADGE_SIZE + 4
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=5, fill=(229, 57, 53))
        zbb = font_badge.getbbox("0")
        zw, zh = zbb[2] - zbb[0], zbb[3] - zbb[1]
        d.text((bx + (bw - zw) // 2 - zbb[0], by + (bh - zh) // 2 - zbb[1]),
               "0", font=font_badge, fill=(255, 255, 255))
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
            team_name = re.sub(r'\bTeam\b\s*', '', t["Team"], flags=re.IGNORECASE).strip().upper()
            top3_display_html += (
                f'<div style="margin:0;padding:4px 0;font-size:1.1em;font-weight:bold;">'
                f'{medals[i]}&nbsp;&nbsp;{team_name}'
                f'</div>'
            )
            top3_entries.append((i, team_name))
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
