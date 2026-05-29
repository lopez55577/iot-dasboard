import streamlit as st
import pandas as pd
import numpy as np
import json, os, csv, time, math
from io import StringIO
from datetime import datetime
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SISMIK — Sistem Pemantauan Bencana",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
#  HELPER — hex → rgba  (fixes Plotly 8-digit hex error)
# ══════════════════════════════════════════════════════════════════
def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ══════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Force dark base - override Streamlit light mode completely ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section[data-testid="stSidebar"],
.main, .block-container { background: #060810 !important; color: #d0d8f0 !important; }

* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

/* ── All native Streamlit text → light ── */
p, span, div, label, li, td, th, h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdown"] p,
[data-testid="stText"],
.stTextInput label, .stSelectbox label, .stSlider label,
.stNumberInput label, .stTextArea label, .stToggle label,
.stRadio label, .stCheckbox label,
[data-baseweb="select"] span,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea { color: #c8d4ea !important; }

/* ── Input / select / textarea backgrounds ── */
[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
[data-baseweb="textarea"] > div,
input, textarea, select {
    background: #0c0e1c !important;
    border-color: #2a2f4a !important;
    color: #c8d4ea !important;
}
[data-baseweb="input"]:focus-within > div,
[data-baseweb="select"]:focus-within > div {
    border-color: #cc3333 !important;
    box-shadow: 0 0 0 2px rgba(204,51,51,.2) !important;
}
input::placeholder, textarea::placeholder { color: #3a4060 !important; }

/* ── Dropdown list ── */
[data-baseweb="popover"] [role="option"],
[data-baseweb="menu"] { background: #0c0e1c !important; color: #c8d4ea !important; }
[data-baseweb="popover"] [role="option"]:hover { background: #1a1f35 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #08091a !important;
    border-right: 1px solid #1a1f35;
}
[data-testid="stSidebar"] * { color: #a0b0cc !important; }
[data-testid="stSidebar"] h2 { color: #e03030 !important; font-size: 1rem !important; }
[data-testid="stSidebar"] .stButton button {
    background: #1a0808 !important; border: 1px solid #3a1010 !important;
    color: #cc3333 !important; font-weight: 700 !important; font-size: .73rem !important;
}
[data-testid="stSidebar"] hr { border-color: #1a1f35 !important; }

/* ── Block container ── */
[data-testid="block-container"] { padding: 1.2rem 2rem 3rem 2rem; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #08091a;
    border-radius: 10px 10px 0 0;
    border: 1px solid #1a1f35;
    border-bottom: none;
    padding: 0 8px; gap: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: #6070a0 !important;
    font-size: 0.7rem !important; font-weight: 700 !important;
    letter-spacing: .1em !important; text-transform: uppercase !important;
    padding: 12px 20px !important; border-radius: 8px 8px 0 0 !important;
    border: none !important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background: #0c0e1c !important;
    color: #e74c3c !important;
    border-bottom: 2px solid #e74c3c !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    background: #060810; border: 1px solid #1a1f35;
    border-top: none; border-radius: 0 0 12px 12px; padding: 24px;
}

/* ── Topbar ── */
.topbar {
    background: linear-gradient(90deg,#0d0f1e 0%,#110a0a 100%);
    border: 1px solid #2a1010; border-radius: 12px;
    padding: 16px 28px; display: flex;
    justify-content: space-between; align-items: center; margin-bottom: 20px;
}
.topbar-title { font-size: 1rem; font-weight: 800; letter-spacing: .1em; color: #f0f0f0; }
.topbar-sub   { font-size: 0.63rem; color: #6070a0; letter-spacing: .05em; margin-top: 3px; }
.live-pill {
    display: inline-flex; align-items: center; gap: 7px;
    background: #0a1a0a; border: 1px solid #1a4a1a;
    border-radius: 20px; padding: 6px 14px;
    font-size: .7rem; font-weight: 700; color: #2ecc71; letter-spacing: .05em;
}
.live-dot { width:8px;height:8px;border-radius:50%;background:#2ecc71; animation:blink 1.4s ease infinite; }
@keyframes blink { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.35;transform:scale(1.35)} }

/* ── Section header ── */
.sec-hdr {
    display: flex; align-items: center; gap: 10px;
    margin: 28px 0 14px 0; padding-bottom: 8px; border-bottom: 1px solid #1a1f35;
}
.sec-hdr-icon { font-size: .95rem; }
.sec-hdr-text { font-size: .67rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #cc3333; }
.sec-hdr-line { flex:1; height:1px; background: linear-gradient(90deg,#1a1f35,transparent); }

/* ── KPI cards ── */
.kpi-card {
    background: #0c0e1c; border: 1px solid #1a1f35;
    border-radius: 10px; padding: 15px 17px; position: relative; overflow: hidden;
}
.kpi-card::before { content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--accent); }
.kpi-label { font-size: .61rem; text-transform: uppercase; letter-spacing: .1em; color: #6070a0; margin-bottom: 7px; }
.kpi-value { font-size: 1.65rem; font-weight: 800; color: var(--accent); font-family: 'JetBrains Mono', monospace; line-height: 1; }
.kpi-sub   { font-size: .59rem; color: #4a5578; margin-top: 5px; text-transform: uppercase; letter-spacing: .05em; }

/* ── Panels ── */
.panel { background: #0c0e1c; border-radius: 12px; border: 1px solid #1a1f35; overflow: hidden; height: 100%; }
.panel-header {
    padding: 10px 18px; background: #0a0c18; border-bottom: 1px solid #1a1f35;
    font-size: .61rem; text-transform: uppercase; letter-spacing: .12em; color: #6070a0;
}
.panel-body { padding: 16px 18px; }

/* ── Alert block ── */
.alert-block { border-radius: 8px; padding: 14px 16px; text-align: center; margin-bottom: 12px; border: 2px solid var(--a-border); background: var(--a-bg); }
.alert-code { font-size: .6rem; font-weight: 700; letter-spacing: .2em; color: var(--a-color); opacity: .8; }
.alert-name { font-size: 1.4rem; font-weight: 800; color: var(--a-color); letter-spacing: .06em; margin: 4px 0; }
.alert-desc { font-size: .67rem; color: var(--a-color); opacity: .75; line-height: 1.5; }

/* ── Assess rows ── */
.assess-row { background: #080a18; border: 1px solid #151a2e; border-radius: 7px; padding: 9px 13px; margin-bottom: 7px; }
.assess-key { font-size: .57rem; text-transform: uppercase; letter-spacing: .1em; color: #5060a0; margin-bottom: 3px; }
.assess-val { font-size: .78rem; font-weight: 600; color: #d0d8f0; }

/* ── Sensor grid ── */
.sensor-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; }
.sensor-cell { background: #080a18; border: 1px solid #151a2e; border-radius: 7px; padding: 9px 13px; }
.sensor-key  { font-size: .57rem; text-transform: uppercase; letter-spacing: .1em; color: #5060a0; margin-bottom: 3px; }
.sensor-val  { font-size: .98rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #70b5fa; }
.sensor-unit { font-size: .57rem; color: #4a5578; margin-left: 3px; }

/* ── MMI bar ── */
.mmi-track { display: flex; gap: 2px; margin: 6px 0; }
.mmi-seg { flex:1;height:15px;border-radius:3px;display:flex;align-items:center;justify-content:center;font-size:.5rem;font-weight:700;color:rgba(255,255,255,.55); }

/* ── Prob bars ── */
.prob-row  { margin-bottom: 12px; }
.prob-hdr  { display: flex; justify-content: space-between; margin-bottom: 5px; }
.prob-lbl  { font-size: .7rem; font-weight: 600; color: #d0d8f0; }
.prob-pct  { font-size: .7rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.prob-track{ height: 9px; background: #080a18; border-radius: 5px; overflow: hidden; border: 1px solid #1a1f35; }
.prob-fill { height: 100%; border-radius: 5px; }

/* ── Image cards ── */
.img-card { background: #0c0e1c; border-radius: 10px; border: 1px solid #1a1f35; overflow: hidden; }
.img-card:hover { border-color: #6b1010; }
.img-footer { padding: 8px 10px; background: #080a18; border-top: 1px solid #1a1f35; }
.img-lbl { font-size: .62rem; font-weight: 700; letter-spacing: .07em; }
.img-vis { font-size: .57rem; color: #6070a0; margin-top: 2px; }
.img-ts  { font-size: .54rem; color: #4a5578; font-family: 'JetBrains Mono', monospace; margin-top: 1px; }
.img-placeholder { background:#080a18;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:120px; }

/* ── CRUD / Manajemen table ── */
.crud-row {
    display: flex; align-items: center; gap: 10px;
    background: #0c0e1c; border: 1px solid #1a1f35;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;
}
.crud-row:hover { border-color: #2a2f4a; }
.crud-id   { font-size: .62rem; font-family: 'JetBrains Mono',monospace; color: #6070a0; flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.crud-lbl  { font-size: .62rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
.crud-ts   { font-size: .58rem; color: #5060a0; font-family: 'JetBrains Mono',monospace; }
.crud-vis  { font-size: .6rem; color: #8090b0; }

/* ── Location cards ── */
.loc-card {
    background: #0c0e1c; border: 1px solid #1a2a4a;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
    position: relative;
}
.loc-card-name { font-size: .88rem; font-weight: 700; color: #d0d8f0; margin-bottom: 4px; }
.loc-card-addr { font-size: .7rem; color: #8090b0; margin-bottom: 6px; }
.loc-card-coord { font-size: .62rem; font-family: 'JetBrains Mono',monospace; color: #5070a0; }
.loc-badge {
    display: inline-block; font-size: .58rem; font-weight: 700;
    background: #0a1a3a; border: 1px solid #1a3a6a;
    color: #60a0e0; padding: 2px 8px; border-radius: 4px; margin-top: 6px;
}

/* ── Form card ── */
.form-card {
    background: #0c0e1c; border: 1px solid #1a1f35;
    border-radius: 10px; padding: 20px 22px; margin-bottom: 16px;
}

/* ── Buttons override ── */
.stButton button {
    background: #0c0e1c !important;
    border: 1px solid #2a2f4a !important;
    color: #c8d4ea !important;
    font-weight: 600 !important; border-radius: 7px !important;
}
.stButton button:hover {
    border-color: #cc3333 !important; color: #ff6060 !important;
}

/* ── Delete button red ── */
.btn-danger button {
    background: #1a0808 !important; border: 1px solid #4a1010 !important;
    color: #ff5050 !important;
}
.btn-danger button:hover { background: #2a0808 !important; border-color: #cc2020 !important; }

/* ── Success button ── */
.btn-success button {
    background: #071a0e !important; border: 1px solid #0d3b1a !important;
    color: #2ecc71 !important;
}
.btn-success button:hover { background: #0a2418 !important; }

/* ── Alert / info boxes ── */
[data-testid="stAlert"] { background: #0c0e1c !important; border-color: #1a1f35 !important; color: #c8d4ea !important; }
.stSuccess { background: #071a0e !important; border-color: #0d3b1a !important; color: #2ecc71 !important; }
.stError   { background: #1a0700 !important; border-color: #3b0d0d !important; color: #ff6060 !important; }
.stWarning { background: #1a1000 !important; border-color: #3b2400 !important; color: #f39c12 !important; }

/* ── Checkbox ── */
[data-baseweb="checkbox"] { color: #c8d4ea !important; }

/* ── Table / DataFrame ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #1a1f35; }
[data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { color: #c8d4ea !important; background: #0c0e1c !important; }
[data-testid="stDataFrame"] th { color: #6070a0 !important; }

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0a0c18; }
::-webkit-scrollbar-thumb { background: #2a2f4a; border-radius: 4px; }

/* ── Number input ── */
[data-testid="stNumberInput"] input { background: #0c0e1c !important; color: #c8d4ea !important; }
[data-testid="stNumberInput"] button { background: #1a1f35 !important; color: #8090b0 !important; }

/* ── Multiselect ── */
[data-baseweb="tag"] { background: #1a1f35 !important; color: #c8d4ea !important; }

/* ── Divider ── */
hr { border-color: #1a1f35 !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════
LABEL_COLOR  = {"aman": "#2ecc71", "waspada": "#f39c12", "bahaya": "#e74c3c"}
VISUAL_COLOR = {"Tidak Retak": "#3b82f6", "Retak Ringan": "#f59e0b", "Retak Berat": "#ef4444"}
RISK_COLOR   = {
    "RENDAH" : "#2ecc71", "NORMAL": "#3b82f6",
    "WASPADA": "#f39c12", "SEDANG": "#e67e22", "TINGGI": "#e74c3c",
}
ALERT_CFG = {
    "aman"   : dict(code="SIAGA IV", name="AMAN",    color="#2ecc71",
                    bg="#071a0e", border="#0d3b1a",
                    desc="Kondisi normal. Tidak terdeteksi ancaman seismik signifikan."),
    "waspada": dict(code="SIAGA II", name="WASPADA", color="#f39c12",
                    bg="#1a1000", border="#3b2400",
                    desc="Terdeteksi getaran abnormal. Lakukan pemantauan intensif."),
    "bahaya" : dict(code="SIAGA I",  name="BAHAYA",  color="#e74c3c",
                    bg="#1a0700", border="#3b0d0d",
                    desc="⚠️ PERINGATAN AKTIF. Segera aktifkan prosedur evakuasi."),
}
MMI_COLORS = [
    "#2ecc71","#27ae60","#f1c40f","#e67e22","#e74c3c","#c0392b",
    "#8e1a1a","#6b0000","#4a0000","#2d0000","#1a0000","#0d0000",
]

PLOT_BG = PAPER_BG = "#060810"
FONT_CLR = "#4a5578"; GRID_CLR = "#0e1020"
CHART_BASE = dict(
    paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
    font=dict(color=FONT_CLR, size=11, family="Inter"),
    margin=dict(l=42, r=20, t=42, b=42),
    # 'legend' dihapus dari sini — tiap fungsi chart mengatur legend-nya sendiri
    # agar tidak terjadi "multiple values for keyword argument 'legend'"
)


# ══════════════════════════════════════════════════════════════════
#  CSV PARSER  (anchor-based — handles evolving schema)
# ══════════════════════════════════════════════════════════════════
def parse_inference_csv(path: str) -> pd.DataFrame:
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except FileNotFoundError:
        return pd.DataFrame()

    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            parts = next(csv.reader(StringIO(raw)))
        except StopIteration:
            continue

        # Locate JSON probs field
        json_idx, probs = None, {}
        for i, p in enumerate(parts):
            if '"aman"' in p:
                try:
                    probs = json.loads(p); json_idx = i; break
                except Exception:
                    pass
        if json_idx is None:
            continue

        def col(off):
            idx = json_idx + off
            return parts[idx].strip() if 0 <= idx < len(parts) else ""

        description = col(-1)
        pred_raw    = col(-2)
        risk_level  = col(-4)

        jpg_paths  = [p.strip() for p in parts if p.strip().endswith(".jpg")]
        image_path = jpg_paths[0] if len(jpg_paths) >= 1 else ""
        ann_path   = jpg_paths[1] if len(jpg_paths) >= 2 else ""

        KNOWN_VIS = {"Retak Berat", "Retak Ringan", "Tidak Retak"}
        visual_label = intensity_label = ""
        pga = rms = crest = np.nan
        intensity_num = 0

        for i, p in enumerate(parts):
            if p.strip() in KNOWN_VIS:
                visual_label = p.strip()
                try:
                    pga           = float(parts[i + 1])
                    rms           = float(parts[i + 2])
                    crest         = float(parts[i + 3])
                    intensity_label = parts[i + 5].strip()
                    try: intensity_num = int(parts[i + 4])
                    except: pass
                except Exception:
                    pass
                break

        if not visual_label and "|" in description:
            visual_label = description.split("|")[0].strip()

        pl = pred_raw.lower()
        if pl not in {"aman", "waspada", "bahaya"}:
            if "|" in description:
                pl = description.split("|")[-1].strip().lower()
            if pl not in {"aman", "waspada", "bahaya"}:
                pl = ""

        rows.append({
            "timestamp"    : parts[0].strip(),
            "sample_id"    : parts[1].strip(),
            "image_path"   : image_path,
            "ann_path"     : ann_path,
            "visual_label" : visual_label,
            "pga"          : pga,
            "rms"          : rms,
            "crest"        : crest,
            "intensity_num": intensity_num,
            "intensity_lbl": intensity_label,
            "risk_level"   : risk_level,
            "pred_label"   : pl,
            "description"  : description,
            "p_aman"       : probs.get("aman",    0.0),
            "p_waspada"    : probs.get("waspada", 0.0),
            "p_bahaya"     : probs.get("bahaya",  0.0),
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for c in ["pga", "rms", "crest", "p_aman", "p_waspada", "p_bahaya"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["intensity_num"] = pd.to_numeric(
        df["intensity_num"], errors="coerce"
    ).fillna(0).astype(int)
    return df.sort_values("timestamp", ascending=True).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════
#  CRUD HELPERS — Delete log rows & image files
# ══════════════════════════════════════════════════════════════════
def delete_rows_from_csv(csv_path: str, sample_ids: set) -> tuple[int, str]:
    """
    Rewrite CSV, skipping rows whose sample_id is in sample_ids.
    Returns (n_deleted, error_msg).
    """
    if not os.path.exists(csv_path):
        return 0, "File CSV tidak ditemukan."
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        kept, removed = [], 0
        for raw in raw_lines:
            stripped = raw.strip()
            if not stripped:
                kept.append(raw); continue
            try:
                parts = next(csv.reader(StringIO(stripped)))
            except StopIteration:
                kept.append(raw); continue
            sid = parts[1].strip() if len(parts) > 1 else ""
            if sid in sample_ids:
                removed += 1
            else:
                kept.append(raw)

        with open(csv_path, "w", encoding="utf-8") as f:
            f.writelines(kept)

        return removed, ""
    except Exception as e:
        return 0, str(e)


def delete_image_files(row: pd.Series) -> list[str]:
    """Delete image and annotated image files. Returns list of deleted paths."""
    deleted = []
    for col in ["image_path", "ann_path"]:
        p = str(row.get(col, ""))
        if p and os.path.exists(p):
            try:
                os.remove(p)
                deleted.append(p)
            except Exception:
                pass
    return deleted


# ══════════════════════════════════════════════════════════════════
#  LOCATION MANAGEMENT — JSON-backed CRUD
# ══════════════════════════════════════════════════════════════════
import uuid as _uuid

def _loc_path(csv_path: str) -> str:
    """Simpan lokasi.json di direktori yang sama dengan CSV."""
    return os.path.join(os.path.dirname(csv_path), "lokasi.json")


def load_locations(csv_path: str) -> list[dict]:
    p = _loc_path(csv_path)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_locations(csv_path: str, locs: list[dict]) -> bool:
    try:
        with open(_loc_path(csv_path), "w", encoding="utf-8") as f:
            json.dump(locs, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def add_location(csv_path: str, nama: str, alamat: str,
                 lat: float, lon: float, deskripsi: str, tipe: str) -> bool:
    locs = load_locations(csv_path)
    locs.append({
        "id"         : str(_uuid.uuid4())[:8],
        "nama"       : nama.strip(),
        "alamat"     : alamat.strip(),
        "lat"        : lat,
        "lon"        : lon,
        "deskripsi"  : deskripsi.strip(),
        "tipe"       : tipe,
        "ditambahkan": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return save_locations(csv_path, locs)


def delete_location(csv_path: str, loc_id: str) -> bool:
    locs = load_locations(csv_path)
    locs = [l for l in locs if l.get("id") != loc_id]
    return save_locations(csv_path, locs)


def update_location(csv_path: str, loc_id: str, **kwargs) -> bool:
    locs = load_locations(csv_path)
    for l in locs:
        if l.get("id") == loc_id:
            l.update(kwargs)
            break
    return save_locations(csv_path, locs)


# ══════════════════════════════════════════════════════════════════
#  LOCATION ↔ RECORD ASSIGNMENT  (lokasi_assign.json)
# ══════════════════════════════════════════════════════════════════
def _assign_path(csv_path: str) -> str:
    return os.path.join(os.path.dirname(csv_path), "lokasi_assign.json")


def load_loc_assignments(csv_path: str) -> dict:
    """Returns {lokasi_id: [sample_id, ...]}"""
    p = _assign_path(csv_path)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_loc_assignments(csv_path: str, assignments: dict) -> bool:
    try:
        with open(_assign_path(csv_path), "w", encoding="utf-8") as f:
            json.dump(assignments, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def assign_records_to_loc(csv_path: str, lokasi_id: str,
                           sample_ids: list[str], mode: str = "add") -> bool:
    """
    mode='add'     → append to existing list (no duplicates)
    mode='replace' → replace entirely
    mode='remove'  → remove from list
    """
    asgn = load_loc_assignments(csv_path)
    existing = set(asgn.get(lokasi_id, []))
    if mode == "add":
        existing.update(sample_ids)
    elif mode == "replace":
        existing = set(sample_ids)
    elif mode == "remove":
        existing -= set(sample_ids)
    asgn[lokasi_id] = sorted(existing)
    return save_loc_assignments(csv_path, asgn)


def filter_df_by_location(df: pd.DataFrame, csv_path: str,
                           lokasi_id: str | None) -> pd.DataFrame:
    """Return df filtered to records assigned to lokasi_id, or full df if None."""
    if not lokasi_id:
        return df
    asgn = load_loc_assignments(csv_path)
    ids  = set(asgn.get(lokasi_id, []))
    if not ids:
        return df.iloc[0:0]   # empty but same schema
    return df[df["sample_id"].isin(ids)].copy()


# ══════════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════════
def sec_header(icon: str, text: str):
    st.markdown(f"""
<div class="sec-hdr">
  <span class="sec-hdr-icon">{icon}</span>
  <span class="sec-hdr-text">{text}</span>
  <div class="sec-hdr-line"></div>
</div>""", unsafe_allow_html=True)


def _fmt(v, d=4):
    return f"{v:.{d}f}" if pd.notna(v) and not (isinstance(v, float) and math.isnan(v)) else "—"


def render_alert_panel(row: pd.Series):
    lbl = row["pred_label"] or "aman"
    cfg = ALERT_CFG.get(lbl, ALERT_CFG["aman"])
    c, bg, bd = cfg["color"], cfg["bg"], cfg["border"]

    parts_desc = [d.strip() for d in str(row["description"]).split("|")]
    vis_txt = parts_desc[0] if parts_desc else "—"
    int_txt = parts_desc[1] if len(parts_desc) > 1 else "—"
    pre_txt = parts_desc[2].upper() if len(parts_desc) > 2 else "—"
    ts  = str(row["timestamp"])[:19] if pd.notna(row["timestamp"]) else "—"
    sid = str(row["sample_id"])

    st.markdown(f"""
<div class="panel">
  <div class="panel-header">🚨 &nbsp;STATUS PERINGATAN DINI TERKINI</div>
  <div class="panel-body">
    <div class="alert-block" style="--a-color:{c};--a-bg:{bg};--a-border:{bd}">
      <div class="alert-code">{cfg['code']}</div>
      <div class="alert-name">{cfg['name']}</div>
      <div class="alert-desc">{cfg['desc']}</div>
    </div>
    <div class="assess-row">
      <div class="assess-key">Kondisi Bangunan</div>
      <div class="assess-val">{vis_txt}</div>
    </div>
    <div class="assess-row">
      <div class="assess-key">Skala Intensitas</div>
      <div class="assess-val">{int_txt}</div>
    </div>
    <div class="assess-row">
      <div class="assess-key">Status Prediksi AI</div>
      <div class="assess-val" style="color:{c}">{pre_txt}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
      <div class="assess-row" style="margin:0">
        <div class="assess-key">ID Kejadian</div>
        <div style="font-size:.63rem;font-family:'JetBrains Mono',monospace;
                    color:#4a6090;word-break:break-all">{sid}</div>
      </div>
      <div class="assess-row" style="margin:0">
        <div class="assess-key">Timestamp</div>
        <div style="font-size:.63rem;font-family:'JetBrains Mono',monospace;color:#4a6090">{ts}</div>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


def render_seismic_panel(row: pd.Series):
    pga_s   = _fmt(row["pga"])
    rms_s   = _fmt(row["rms"])
    crest_s = _fmt(row["crest"], 3)
    int_n   = int(row["intensity_num"]) if pd.notna(row["intensity_num"]) else 0
    int_l   = row["intensity_lbl"] or "—"
    risk    = row["risk_level"] or "—"
    risk_c  = RISK_COLOR.get(risk, "#4a5578")

    mmi_capped = min(max(int_n, 0), 12)
    mmi_segs = "".join(
        '<div class="mmi-seg" style="background:{bg};opacity:{op}">{n}</div>'.format(
            bg=MMI_COLORS[i - 1] if i <= mmi_capped else "#0d0f1e",
            op="1" if i <= mmi_capped else ".3",
            n=i,
        )
        for i in range(1, 13)
    )

    st.markdown(f"""
<div class="panel">
  <div class="panel-header">📡 &nbsp;DATA SENSOR SEISMIK REAL-TIME</div>
  <div class="panel-body">
    <div class="sensor-grid">
      <div class="sensor-cell">
        <div class="sensor-key">PGA Peak</div>
        <div class="sensor-val">{pga_s}<span class="sensor-unit">g</span></div>
      </div>
      <div class="sensor-cell">
        <div class="sensor-key">RMS Acceleration</div>
        <div class="sensor-val">{rms_s}<span class="sensor-unit">g</span></div>
      </div>
      <div class="sensor-cell">
        <div class="sensor-key">Crest Factor</div>
        <div class="sensor-val">{crest_s}</div>
      </div>
      <div class="sensor-cell">
        <div class="sensor-key">Tingkat Risiko</div>
        <div class="sensor-val" style="color:{risk_c};font-size:.85rem">{risk}</div>
      </div>
    </div>
    <div class="assess-row">
      <div class="assess-key" style="margin-bottom:8px">Skala Intensitas MMI — Level {int_l}</div>
      <div class="mmi-track">{mmi_segs}</div>
      <div style="display:flex;justify-content:space-between;
                  font-size:.49rem;color:#2a3050;margin-top:4px;
                  font-family:'JetBrains Mono',monospace">
        <span>I · Tidak Terasa</span>
        <span>VI · Kuat</span>
        <span>XII · Dahsyat</span>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


def render_prob_panel(row: pd.Series):
    p_a = float(row.get("p_aman",    0) or 0)
    p_w = float(row.get("p_waspada", 0) or 0)
    p_b = float(row.get("p_bahaya",  0) or 0)

    values = {"aman": p_a, "waspada": p_w, "bahaya": p_b}
    dom   = max(values, key=values.get)
    dom_c = LABEL_COLOR.get(dom, "#fff")

    ps = [max(v, 1e-9) for v in [p_a, p_w, p_b]]
    confidence = 1 - (-sum(p * math.log(p) for p in ps)) / math.log(3)

    def bar(label, pct, color, icon):
        w = int(pct * 100)
        return f"""
<div class="prob-row">
  <div class="prob-hdr">
    <span class="prob-lbl">{icon}&nbsp;{label.upper()}</span>
    <span class="prob-pct" style="color:{color}">{pct:.1%}</span>
  </div>
  <div class="prob-track">
    <div class="prob-fill"
         style="width:{w}%;background:linear-gradient(90deg,{rgba(color,.35)},{color})">
    </div>
  </div>
</div>"""

    bars = (bar("Aman",    p_a, "#2ecc71", "🟢") +
            bar("Waspada", p_w, "#f39c12", "🟡") +
            bar("Bahaya",  p_b, "#e74c3c", "🔴"))

    st.markdown(f"""
<div class="panel">
  <div class="panel-header">📊 &nbsp;PROBABILITAS KLASIFIKASI AI</div>
  <div class="panel-body">
    {bars}
    <div style="background:#080a18;border:1px solid #151a2e;border-radius:8px;
                padding:12px 14px;margin-top:10px;
                display:flex;justify-content:space-between;align-items:center">
      <div>
        <div class="assess-key">Kelas Dominan</div>
        <div style="font-size:1.05rem;font-weight:800;color:{dom_c};
                    letter-spacing:.06em">{dom.upper()}</div>
      </div>
      <div style="text-align:right">
        <div class="assess-key">Confidence Model</div>
        <div style="font-size:1.05rem;font-weight:800;color:#a5b4fc;
                    font-family:'JetBrains Mono',monospace">{confidence:.1%}</div>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


def render_img_card(row: pd.Series, cols_n: int = 4):
    """Render satu kartu gambar + metadata di footer."""
    lbl   = row["pred_label"] or "aman"
    lbl_c = LABEL_COLOR.get(lbl, "#4a5578")
    vis   = row["visual_label"] or "—"
    vis_c = VISUAL_COLOR.get(vis, "#4a5578")
    ts    = str(row["timestamp"])[:16] if pd.notna(row["timestamp"]) else "—"
    risk  = row["risk_level"] or ""
    risk_c= RISK_COLOR.get(risk, "#4a5578")
    pga_s = f"{row['pga']:.4f}g" if pd.notna(row["pga"]) else "—"
    sid   = str(row["sample_id"])

    # Prefer annotated if exists, otherwise raw capture
    ann = str(row["ann_path"])
    raw = str(row["image_path"])
    disp = ann if ann and os.path.exists(ann) else raw
    has  = bool(disp and os.path.exists(disp))

    st.markdown('<div class="img-card">', unsafe_allow_html=True)

    if has:
        st.image(disp, use_container_width=True)
    else:
        st.markdown(f"""
<div class="img-placeholder">
  <div style="font-size:1.6rem">📷</div>
  <div style="font-size:.6rem;color:{vis_c};font-weight:700;margin-top:4px">{vis}</div>
  <div style="font-size:.54rem;color:#1a2030;margin-top:2px">Gambar tidak tersedia di server</div>
</div>""", unsafe_allow_html=True)

    # Footer strip
    sid_short = (sid[-20:] if len(sid) > 20 else sid)
    st.markdown(f"""
<div class="img-footer">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">
    <span class="img-lbl" style="color:{lbl_c}">{lbl.upper()}</span>
    <span style="font-size:.57rem;color:{risk_c};font-weight:700">{risk}</span>
  </div>
  <div class="img-vis" style="color:{vis_c}">{vis} · PGA {pga_s}</div>
  <div class="img-ts">{ts} · {sid_short}</div>
</div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  CHART BUILDERS
# ══════════════════════════════════════════════════════════════════
def chart_donut(counts: pd.Series, colors: dict, title: str) -> go.Figure:
    labels = counts.index.tolist(); vals = counts.values.tolist()
    clrs   = [colors.get(l, "#4a5578") for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=vals, hole=.55,
        marker=dict(colors=clrs, line=dict(color=PLOT_BG, width=3)),
        textinfo="label+value+percent",
        textfont=dict(color="#e8edf8", size=12, family="Inter"),
        insidetextfont=dict(color="#ffffff", size=11),
        outsidetextfont=dict(color="#c0cce0", size=12),
        hovertemplate="<b>%{label}</b><br>Jumlah: <b>%{value}</b> kejadian<br>Proporsi: <b>%{percent}</b><extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#e05050", size=13, family="Inter")),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#b0bcd8", size=12, family="Inter"),
            itemsizing="constant",
        ),
        **CHART_BASE,
    )
    return fig


def chart_bar(counts: pd.Series, colors: dict, title: str) -> go.Figure:
    labels = counts.index.tolist(); vals = counts.values.tolist()
    clrs   = [colors.get(l, "#4a5578") for l in labels]
    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(color=clrs, line=dict(color=PLOT_BG, width=1)),
        text=[f"<b>{v}</b>" for v in vals],
        textposition="outside",
        textfont=dict(color="#c8d4ea", size=13, family="Inter"),
        hovertemplate="<b>%{x}</b><br>Jumlah: <b>%{y}</b> kejadian<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#e05050", size=13, family="Inter")),
        xaxis=dict(
            gridcolor=GRID_CLR,
            tickfont=dict(color="#b0bcd8", size=12, family="Inter"),
            title=dict(text="Tingkat Risiko", font=dict(color="#8090b0", size=11)),
        ),
        yaxis=dict(
            gridcolor=GRID_CLR,
            tickfont=dict(color="#b0bcd8", size=12, family="Inter"),
            title=dict(text="Jumlah Kejadian", font=dict(color="#8090b0", size=11)),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#b0bcd8", size=12, family="Inter")),
        **CHART_BASE,
    )
    return fig


def chart_pga(df: pd.DataFrame) -> go.Figure:
    """PGA timeline — dirancang agar mudah dipahami masyarakat umum."""
    cmap  = df["pred_label"].map(LABEL_COLOR).fillna("#4a5578")
    y_max = max(df["pga"].max() * 1.2, 0.2)
    fig   = go.Figure()

    # ── Colored zone bands ────────────────────────────────────────
    fig.add_hrect(y0=0,    y1=0.02,  fillcolor=rgba("#2ecc71", .07), line_width=0)
    fig.add_hrect(y0=0.02, y1=0.1,   fillcolor=rgba("#f39c12", .07), line_width=0)
    fig.add_hrect(y0=0.1,  y1=y_max, fillcolor=rgba("#e74c3c", .07), line_width=0)

    # Zone border lines
    fig.add_hline(y=0.02, line=dict(color="#f39c12", width=1.5, dash="dash"),
                  annotation_text="⚠️  Mulai Waspada",
                  annotation_font=dict(color="#f39c12", size=10, family="Inter"),
                  annotation_position="top left")
    fig.add_hline(y=0.1,  line=dict(color="#e74c3c", width=1.5, dash="dash"),
                  annotation_text="🔴  Zona Berbahaya",
                  annotation_font=dict(color="#e74c3c", size=10, family="Inter"),
                  annotation_position="top left")

    # Main data line
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["pga"],
        mode="lines+markers", name="Kekuatan Getaran",
        line=dict(color="#5b7ee5", width=2),
        marker=dict(
            size=7,
            color=cmap.tolist(),
            line=dict(color=PLOT_BG, width=1.5),
            symbol="circle",
        ),
        hovertemplate=(
            "<b>%{x|%d %b %Y  %H:%M}</b><br>"
            "Kekuatan: <b>%{y:.5f} g</b><br>"
            "<extra></extra>"
        ),
    ))

    # Custom y-axis tick labels so non-experts understand scale
    tick_vals = [0, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7]
    tick_vals = [v for v in tick_vals if v <= y_max]

    fig.update_layout(
        title=dict(
            text="📈  Grafik Kekuatan Gempa dari Waktu ke Waktu",
            font=dict(color="#e05050", size=13, family="Inter"),
        ),
        xaxis=dict(
            gridcolor=GRID_CLR,
            tickfont=dict(color="#b0bcd8", size=11, family="Inter"),
            title=dict(text="Waktu Kejadian", font=dict(color="#8090b0", size=11)),
        ),
        yaxis=dict(
            gridcolor=GRID_CLR,
            tickfont=dict(color="#b0bcd8", size=11, family="Inter"),
            title=dict(text="Kekuatan Getaran (g)", font=dict(color="#8090b0", size=11)),
            tickvals=tick_vals,
            ticktext=[f"{v:.2f}g" for v in tick_vals],
            range=[0, y_max],
        ),
        # Zone legend as invisible scatter (for context)
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#b0bcd8", size=11, family="Inter"),
            x=0.01, y=0.99, xanchor="left", yanchor="top",
        ),
        **CHART_BASE,
    )

    # Add invisible legend entries for zones
    for lbl, clr in [("🟢 Aman", "#2ecc71"), ("🟡 Waspada", "#f39c12"), ("🔴 Bahaya", "#e74c3c")]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=clr, symbol="square"),
            name=lbl, showlegend=True,
        ))

    return fig


def chart_status_history(df: pd.DataFrame, n: int = 60) -> go.Figure:
    """
    Riwayat status deteksi per kejadian — mudah dipahami masyarakat umum.
    Tiap titik = satu kejadian, posisi & warna menunjukkan tingkat bahaya.
    Ukuran titik = kekuatan getaran (PGA).
    """
    sub = df.tail(n).copy()
    sub = sub[sub["pred_label"].isin(["aman", "waspada", "bahaya"])]
    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(text="Belum ada data status tersedia",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color="#4a5578", size=13))
        fig.update_layout(title=dict(text="Riwayat Status Deteksi",
                                     font=dict(color="#e05050", size=13)),
                          **CHART_BASE)
        return fig

    LABEL_Y    = {"aman": 1, "waspada": 2, "bahaya": 3}
    LABEL_NAME = {"aman": "✅  Aman", "waspada": "⚠️  Waspada", "bahaya": "🔴  Bahaya"}

    fig = go.Figure()

    # ── Horizontal band background per level ─────────────────────
    fig.add_hrect(y0=0.55, y1=1.45, fillcolor=rgba("#2ecc71", .06), line_width=0)
    fig.add_hrect(y0=1.55, y1=2.45, fillcolor=rgba("#f39c12", .06), line_width=0)
    fig.add_hrect(y0=2.55, y1=3.45, fillcolor=rgba("#e74c3c", .06), line_width=0)

    # ── Separator lines ───────────────────────────────────────────
    for y, clr in [(1.5, "#2a3050"), (2.5, "#2a3050")]:
        fig.add_hline(y=y, line=dict(color=clr, width=1, dash="dot"))

    # ── Data points per status level ─────────────────────────────
    for lbl, clr in [("aman","#2ecc71"), ("waspada","#f39c12"), ("bahaya","#e74c3c")]:
        mask = sub["pred_label"] == lbl
        if not mask.any():
            continue
        grp      = sub[mask]
        pga_raw  = grp["pga"].fillna(0.01)
        vis_vals = grp["visual_label"].fillna("—")
        ts_vals  = grp["timestamp"].dt.strftime("%d %b %Y  %H:%M").fillna("—")
        risk_vals= grp["risk_level"].fillna("—")

        # Marker size scaled to PGA (bigger = stronger quake), min 9 max 22
        sizes = (9 + (pga_raw.clip(0, 0.5) / 0.5) * 13).tolist()

        fig.add_trace(go.Scatter(
            x=grp["timestamp"],
            y=[LABEL_Y[lbl]] * len(grp),
            mode="markers",
            name=LABEL_NAME[lbl],
            marker=dict(
                size=sizes,
                color=clr,
                opacity=0.88,
                line=dict(color=PLOT_BG, width=1.5),
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Status: <b style='color:" + clr + "'>" + lbl.upper() + "</b><br>"
                "Kondisi Bangunan: <b>%{customdata[1]}</b><br>"
                "Tingkat Risiko: <b>%{customdata[2]}</b><br>"
                "Kekuatan Getaran: <b>%{customdata[3]:.4f} g</b><br>"
                "<extra></extra>"
            ),
            customdata=list(zip(ts_vals, vis_vals, risk_vals, pga_raw)),
        ))

    fig.update_layout(
        title=dict(
            text="🕐  Riwayat Status Deteksi Kejadian",
            font=dict(color="#e05050", size=13, family="Inter"),
        ),
        xaxis=dict(
            gridcolor=GRID_CLR,
            tickfont=dict(color="#b0bcd8", size=11, family="Inter"),
            title=dict(text="Waktu Kejadian", font=dict(color="#8090b0", size=11)),
        ),
        yaxis=dict(
            tickvals=[1, 2, 3],
            ticktext=["✅  AMAN", "⚠️  WASPADA", "🔴  BAHAYA"],
            tickfont=dict(color="#c8d0e8", size=12, family="Inter"),
            gridcolor="rgba(0,0,0,0)",
            range=[0.3, 3.7],
            fixedrange=True,
            side="left",
        ),
        legend=dict(
            bgcolor=rgba("#060810", 0.8),
            bordercolor="#1a1f35",
            borderwidth=1,
            font=dict(color="#b0bcd8", size=11, family="Inter"),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
        ),
        showlegend=True,
        **CHART_BASE,
    )
    return fig


def chart_cross(df: pd.DataFrame):
    df_c = df[(df["visual_label"] != "") & (df["pred_label"] != "")]
    if df_c.empty:
        return None
    pivot = df_c.groupby(["visual_label", "pred_label"]).size().unstack(fill_value=0)
    fig   = go.Figure()
    label_names = {"aman": "🟢 Aman", "waspada": "🟡 Waspada", "bahaya": "🔴 Bahaya"}
    for lbl in ["aman", "waspada", "bahaya"]:
        if lbl in pivot.columns:
            fig.add_trace(go.Bar(
                name=label_names.get(lbl, lbl.capitalize()),
                x=pivot.index.tolist(),
                y=pivot[lbl].tolist(),
                marker_color=LABEL_COLOR[lbl],
                text=[f"<b>{v}</b>" if v > 0 else "" for v in pivot[lbl].tolist()],
                textposition="inside",
                textfont=dict(color="#ffffff", size=12),
                hovertemplate=f"<b>%{{x}}</b><br>{label_names.get(lbl,lbl)}: <b>%{{y}} kejadian</b><extra></extra>",
            ))
    fig.update_layout(
        barmode="stack",
        title=dict(
            text="🏗️  Kondisi Bangunan berdasarkan Status Bahaya",
            font=dict(color="#e05050", size=13, family="Inter"),
        ),
        xaxis=dict(
            gridcolor=GRID_CLR,
            tickfont=dict(color="#b0bcd8", size=12, family="Inter"),
            title=dict(text="Kondisi Visual Bangunan", font=dict(color="#8090b0", size=11)),
        ),
        yaxis=dict(
            gridcolor=GRID_CLR,
            tickfont=dict(color="#b0bcd8", size=12, family="Inter"),
            title=dict(text="Jumlah Kejadian", font=dict(color="#8090b0", size=11)),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#b0bcd8", size=12, family="Inter"),
        ),
        **CHART_BASE,
    )
    return fig


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚨 SISMIK")
    st.markdown(
        "<p style='font-size:.6rem;color:#6080a0;letter-spacing:.08em;"
        "text-transform:uppercase'>Sistem Pemantauan Bencana Seismik</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    csv_path = st.text_input(
        "📂 Path File CSV",
        value="/home/raspi/pi/pa2_multimodal/outputs/realtime_inference_log.csv",
    )
    refresh_interval = st.slider("🔄 Refresh (detik)", 3, 60, 3)
    n_recent         = st.slider("🖼️ Capture terbaru (dashboard)", 3, 12, 6)
    n_table          = st.slider("📋 Baris log", 10, 100, 20, 5)
    gallery_cols_n   = st.radio("Kolom gallery", [3, 4, 5, 6], index=2, horizontal=True)

    st.divider()

    # ── Lokasi Assessment selector ─────────────────────────────────
    st.markdown("""
<p style='font-size:.65rem;font-weight:700;text-transform:uppercase;
   letter-spacing:.12em;color:#cc3333;margin-bottom:6px'>
  📍 LOKASI ASSESSMENT
</p>""", unsafe_allow_html=True)

    _locs_sidebar = load_locations(csv_path)
    _loc_options  = ["— Semua Lokasi —"] + [l["nama"] for l in _locs_sidebar]
    _loc_sel_name = st.selectbox("Lokasi", _loc_options, key="sb_loc_sel",
                                  label_visibility="collapsed")

    # Resolve selected lokasi_id
    _sel_loc_obj = None
    selected_loc_id = None
    if _loc_sel_name != "— Semua Lokasi —":
        _sel_loc_obj = next((l for l in _locs_sidebar if l["nama"] == _loc_sel_name), None)
        if _sel_loc_obj:
            selected_loc_id = _sel_loc_obj["id"]

    # Show mini-info for selected location
    if _sel_loc_obj:
        _maps_url = (f"https://www.google.com/maps?q="
                     f"{_sel_loc_obj.get('lat',0)},{_sel_loc_obj.get('lon',0)}")
        st.markdown(f"""
<div style="background:#080a18;border:1px solid #1a2a4a;border-radius:7px;
            padding:8px 12px;margin-top:4px;font-size:.6rem;line-height:1.8">
  <div style="color:#8090b0">{_sel_loc_obj.get('tipe','—')}</div>
  <div style="color:#a0b0cc">{_sel_loc_obj.get('alamat','—') or '—'}</div>
  <div style="color:#5070a0;font-family:'JetBrains Mono',monospace">
    {_sel_loc_obj.get('lat',0):.5f}, {_sel_loc_obj.get('lon',0):.5f}
  </div>
  <a href="{_maps_url}" target="_blank"
     style="color:#4090cc;text-decoration:none">🗺️ Lihat Peta ↗</a>
</div>""", unsafe_allow_html=True)

    st.divider()
    auto_refresh = st.toggle("▶ Auto Refresh", value=True)
    if st.button("🔃 Refresh Manual", use_container_width=True):
        st.cache_data.clear()

    st.divider()
    st.markdown("""
<div style='font-size:.6rem;line-height:2.2;color:#4a6080'>
DEVICE &nbsp;· ESP32-MPU01 + Raspberry Pi<br>
MODEL &nbsp;&nbsp;· Random Forest Multimodal<br>
LABELS · Aman / Waspada / Bahaya<br>
VISUAL · Tidak Retak / Ringan / Berat
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  LOAD DATA
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=5)
def load_data(p: str) -> pd.DataFrame:
    return parse_inference_csv(p)

df = load_data(csv_path)

# ── Location-filtered view ──────────────────────────────────────
# df_view = data sesuai lokasi yang dipilih di sidebar
df_view = filter_df_by_location(df, csv_path, selected_loc_id)
# fallback ke full df jika filtered kosong karena belum ada assignment
if df_view.empty and selected_loc_id:
    df_view_empty = True
else:
    df_view_empty = False

# Use df_view for all display; df for global stats only where noted
_df_display = df_view if (not df_view.empty) else df

# ══════════════════════════════════════════════════════════════════
#  TOPBAR  (above tabs, always visible)
# ══════════════════════════════════════════════════════════════════
ts_now   = datetime.now().strftime("%d %b %Y  %H:%M:%S")
total    = len(df)
# Status terakhir dari df_display (bisa filtered per lokasi)
last_lbl = _df_display.iloc[-1]["pred_label"] if not _df_display.empty else "aman"
last_c   = LABEL_COLOR.get(last_lbl, "#2ecc71")

_loc_label = f"📍 {_sel_loc_obj['nama']}" if _sel_loc_obj else "🌐 Semua Lokasi"
_loc_color = "#60a0e0" if _sel_loc_obj else "#6070a0"

st.markdown(f"""
<div class="topbar">
  <div>
    <div class="topbar-title">🚨 &nbsp;SISMIK — SISTEM PEMANTAUAN BENCANA SEISMIK</div>
    <div class="topbar-sub">
      AI Multimodal Classifier · Raspberry Pi + ESP32 MPU-01 · Random Forest &nbsp;|&nbsp;
      <span style="color:{_loc_color}">{_loc_label}</span>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:16px">
    <div style="text-align:right">
      <div style="font-size:.57rem;color:#5060a0;text-transform:uppercase;letter-spacing:.1em">
        Status Terakhir
      </div>
      <div style="font-size:.9rem;font-weight:800;color:{last_c}">{last_lbl.upper()}</div>
    </div>
    <div class="live-pill">
      <div class="live-dot"></div>LIVE &nbsp;·&nbsp; {ts_now}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

if df.empty:
    st.error(f"⚠️ File CSV tidak ditemukan atau kosong: `{csv_path}`")
    st.stop()

last_row = _df_display.iloc[-1] if not _df_display.empty else df.iloc[-1]


# ══════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════
tab_dashboard, tab_gallery, tab_crud, tab_lokasi = st.tabs([
    "📡  DASHBOARD PEMANTAUAN",
    "🗂️  ARSIP GAMBAR CAPTURE",
    "🗑️  KELOLA DATA",
    "📍  MANAJEMEN LOKASI",
])


# ╔══════════════════════════════════════════════════════════════════
# ║  TAB 1 — DASHBOARD
# ╚══════════════════════════════════════════════════════════════════
with tab_dashboard:

    # ── Location context banner ───────────────────────────────────
    if _sel_loc_obj:
        TIPE_ICON_MAP = {
            "Gedung Pemerintahan":"🏛️","Gedung Pendidikan":"🏫","Gedung Kesehatan":"🏥",
            "Gedung Komersial":"🏢","Infrastruktur Kritis":"⚡","Pemukiman":"🏘️","Lainnya":"📍",
        }
        _t_icon = TIPE_ICON_MAP.get(_sel_loc_obj.get("tipe",""), "📍")
        _maps_u = f"https://www.google.com/maps?q={_sel_loc_obj.get('lat',0)},{_sel_loc_obj.get('lon',0)}"
        _n_asgn = len(load_loc_assignments(csv_path).get(selected_loc_id, []))
        _warn   = ""
        if df_view_empty:
            _warn = """<div style="font-size:.65rem;color:#f39c12;margin-top:6px">
⚠️ Belum ada data yang ditetapkan ke lokasi ini. Gunakan tab <b>Kelola Data → Tetapkan ke Lokasi</b>.</div>"""
        st.markdown(f"""
<div style="background:#08091f;border:1px solid #1a2a5a;border-radius:10px;
            padding:12px 18px;margin-bottom:16px;display:flex;
            align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
  <div style="display:flex;align-items:center;gap:14px">
    <div style="font-size:2rem;line-height:1">{_t_icon}</div>
    <div>
      <div style="font-size:.95rem;font-weight:800;color:#d0d8f0">{_sel_loc_obj['nama']}</div>
      <div style="font-size:.65rem;color:#7080a0;margin-top:2px">
        {_sel_loc_obj.get('tipe','—')} &nbsp;·&nbsp; {_sel_loc_obj.get('alamat','—') or '—'}
      </div>
      {_warn}
    </div>
  </div>
  <div style="display:flex;gap:14px;align-items:center">
    <div style="text-align:center">
      <div style="font-size:.55rem;color:#4a5578;text-transform:uppercase;letter-spacing:.08em">Rekaman</div>
      <div style="font-size:1.1rem;font-weight:800;color:#60a0e0">{len(_df_display)}</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:.55rem;color:#4a5578;text-transform:uppercase;letter-spacing:.08em">Koordinat</div>
      <div style="font-size:.65rem;font-family:'JetBrains Mono',monospace;color:#5070a0">
        {_sel_loc_obj.get('lat',0):.5f}, {_sel_loc_obj.get('lon',0):.5f}
      </div>
    </div>
    <a href="{_maps_u}" target="_blank"
       style="background:#0a1830;border:1px solid #1a3060;border-radius:6px;
              padding:6px 12px;font-size:.65rem;color:#60a0e0;text-decoration:none;
              font-weight:600">🗺️ Lihat Peta</a>
  </div>
</div>""", unsafe_allow_html=True)

    # ── KPI ───────────────────────────────────────────────────────
    _loc_suffix = f" — {_sel_loc_obj['nama']}" if _sel_loc_obj else ""
    sec_header("📊", f"RINGKASAN STATISTIK KEJADIAN{_loc_suffix}")

    # Use _df_display for all stats (respects location filter)
    lc        = _df_display["pred_label"].value_counts()
    n_aman    = int(lc.get("aman",    0))
    n_waspada = int(lc.get("waspada", 0))
    n_bahaya  = int(lc.get("bahaya",  0))
    pga_max   = _df_display["pga"].max() if not _df_display.empty else float("nan")
    n_events  = len(_df_display[_df_display["sample_id"].str.startswith("EVT", na=False)])
    total_view= len(_df_display)

    # ── FIX: Latest crack — scan from newest to oldest, skip missing images ──
    df_crack_src = _df_display if not _df_display.empty else df
    df_crack = df_crack_src[
        df_crack_src["visual_label"].isin(["Retak Ringan", "Retak Berat"])
    ].sort_values("timestamp", ascending=False)

    crack_row  = None
    disp_crack = None
    for _, _cr in df_crack.iterrows():
        _ann = str(_cr.get("ann_path", ""))
        _raw = str(_cr.get("image_path", ""))
        # Try annotated first, then raw
        _candidate = _ann if (_ann and os.path.exists(_ann)) else (
                     _raw if (_raw and os.path.exists(_raw)) else None)
        if _candidate:
            crack_row  = _cr
            disp_crack = _candidate
            break
    has_crack = crack_row is not None

    def kpi(col, accent, label, value, sub):
        with col:
            st.markdown(f"""
<div class="kpi-card" style="--accent:{accent}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-sub">{sub}</div>
</div>""", unsafe_allow_html=True)

    # Layout: 5 KPI cards (left) + crack capture card (right)
    stats_block, crack_block = st.columns([3.8, 1.5])

    with stats_block:
        k1, k2, k3, k4, k5 = st.columns(5)
        kpi(k1, "#2ecc71", "Kejadian Aman",    str(n_aman),    "status aman terdeteksi")
        kpi(k2, "#f39c12", "Kejadian Waspada", str(n_waspada), "status waspada terdeteksi")
        kpi(k3, "#e74c3c", "Kejadian Bahaya",  str(n_bahaya),  "status bahaya terdeteksi")
        kpi(k4, "#3b82f6", "PGA Maks",
            f"{pga_max:.4f}g" if pd.notna(pga_max) else "—",
            "peak ground acceleration")
        kpi(k5, "#a78bfa", "Total Rekaman",    str(total_view),f"{n_events} event seismik")

    with crack_block:
        if has_crack:
            vis   = crack_row["visual_label"]
            lbl   = crack_row["pred_label"] or "aman"
            lbl_c = LABEL_COLOR.get(lbl, "#4a5578")
            vis_c = VISUAL_COLOR.get(vis, "#4a5578")
            ts_c  = str(crack_row["timestamp"])[:16] if pd.notna(crack_row["timestamp"]) else "—"
            pga_c = f"{crack_row['pga']:.4f}g" if pd.notna(crack_row["pga"]) else "—"
            risk  = crack_row["risk_level"] or "—"
            risk_c= RISK_COLOR.get(risk, "#4a5578")
            lbl_bg= ALERT_CFG.get(lbl, ALERT_CFG["aman"])["bg"]
            lbl_bd= ALERT_CFG.get(lbl, ALERT_CFG["aman"])["border"]

            st.markdown(f"""
<div style="background:#0c0e1c;border:1px solid {lbl_c}55;border-radius:10px;overflow:hidden">
  <div style="background:#0a0c18;border-bottom:1px solid #1a1f35;
              padding:7px 12px;display:flex;align-items:center;justify-content:space-between">
    <span style="font-size:.58rem;text-transform:uppercase;letter-spacing:.1em;
                 color:#cc3333;font-weight:700">📸 Assessment Terbaru</span>
    <span style="font-size:.6rem;color:{lbl_c};font-weight:800;background:{lbl_bg};
                 padding:2px 9px;border-radius:4px;border:1px solid {lbl_bd}">{lbl.upper()}</span>
  </div>""", unsafe_allow_html=True)
            st.image(disp_crack, use_container_width=True)
            st.markdown(f"""
<div style="padding:8px 12px;background:#080a18;border-top:1px solid #151a2e">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
    <span style="font-size:.65rem;font-weight:700;color:{vis_c}">{vis}</span>
    <span style="font-size:.6rem;font-weight:700;color:{risk_c};background:#080a18;
                 padding:1px 7px;border-radius:3px;border:1px solid {risk_c}44">{risk}</span>
  </div>
  <div style="font-size:.58rem;color:#4a5578">Getaran: <b style="color:#7090c0">{pga_c}</b></div>
  <div style="font-size:.54rem;color:#4a5578;font-family:'JetBrains Mono',monospace;
              margin-top:2px">{ts_c}</div>
</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
<div style="background:#0c0e1c;border:1px solid #1a1f35;border-radius:10px;
            display:flex;flex-direction:column;align-items:center;
            justify-content:center;padding:24px 16px;text-align:center;min-height:140px">
  <div style="font-size:2rem;margin-bottom:8px">🏗️</div>
  <div style="font-size:.65rem;color:#4a5578;font-weight:600;line-height:1.6">
    Belum ada<br>data retakan<br>terdeteksi
  </div>
</div>""", unsafe_allow_html=True)

    # ── Assessment panels ─────────────────────────────────────────
    sec_header("🔍", "ASSESSMENT KEJADIAN TERKINI")
    p1, p2, p3 = st.columns([1.1, 1.2, 1.1])
    with p1: render_alert_panel(last_row)
    with p2: render_seismic_panel(last_row)
    with p3: render_prob_panel(last_row)

    # ── Recent captures — from _df_display ───────────────────────
    sec_header("📷", "CAPTURE TERBARU — REAL-TIME")
    recent = _df_display[_df_display["image_path"].str.len() > 0].tail(n_recent).iloc[::-1]
    if recent.empty:
        st.info("Tidak ada capture untuk lokasi/filter yang dipilih.")
    else:
        g_cols = st.columns(min(n_recent, 6))
        for idx, (_, row) in enumerate(recent.iterrows()):
            if idx >= len(g_cols): break
            with g_cols[idx]: render_img_card(row)

    # ── Charts row 1 — all use _df_display ───────────────────────
    sec_header("📊", "DISTRIBUSI & ANALISIS RISIKO")
    c1, c2, c3 = st.columns(3)
    with c1:
        lc2 = _df_display["pred_label"][_df_display["pred_label"] != ""].value_counts()
        if not lc2.empty:
            st.plotly_chart(chart_donut(lc2, LABEL_COLOR, "Status Keselamatan"),
                            use_container_width=True, config={"displayModeBar": False})
    with c2:
        vc = _df_display["visual_label"][_df_display["visual_label"] != ""].value_counts()
        if not vc.empty:
            st.plotly_chart(chart_donut(vc, VISUAL_COLOR, "Kondisi Struktural Bangunan"),
                            use_container_width=True, config={"displayModeBar": False})
    with c3:
        rc = _df_display["risk_level"][_df_display["risk_level"] != ""].value_counts()
        if not rc.empty:
            order = [k for k in ["RENDAH","NORMAL","WASPADA","SEDANG","TINGGI"] if k in rc.index]
            rc    = rc.reindex(order).dropna()
            st.plotly_chart(chart_bar(rc, RISK_COLOR, "Distribusi Tingkat Risiko"),
                            use_container_width=True, config={"displayModeBar": False})
    fig_cross = chart_cross(_df_display)
    if fig_cross:
        st.plotly_chart(fig_cross, use_container_width=True, config={"displayModeBar": False})

    # ── Charts row 2 ─────────────────────────────────────────────
    sec_header("📈", "TIMELINE SENSOR SEISMIK & RIWAYAT STATUS")
    t1, t2 = st.columns(2)
    with t1:
        df_pga = _df_display[_df_display["pga"].notna()]
        if not df_pga.empty:
            st.plotly_chart(chart_pga(df_pga),
                            use_container_width=True, config={"displayModeBar": False})
    with t2:
        st.plotly_chart(chart_status_history(_df_display),
                        use_container_width=True, config={"displayModeBar": False})

    # ── Log table — uses _df_display ─────────────────────────────
    sec_header("📋", "LOG INFERENSI AI — RIWAYAT KEJADIAN")
    disp_cols = ["timestamp","sample_id","visual_label","pred_label","risk_level",
                 "pga","rms","crest","intensity_lbl","p_aman","p_waspada","p_bahaya","description"]
    disp_cols = [c for c in disp_cols if c in _df_display.columns]
    df_tbl = _df_display[disp_cols].tail(n_table).iloc[::-1].copy()
    for c in ["pga","rms","crest"]:
        if c in df_tbl: df_tbl[c] = df_tbl[c].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
    for c in ["p_aman","p_waspada","p_bahaya"]:
        if c in df_tbl: df_tbl[c] = df_tbl[c].map(lambda x: f"{x:.1%}" if pd.notna(x) else "—")
    st.dataframe(
        df_tbl, use_container_width=True,
        height=min(500, n_table * 36 + 50), hide_index=True,
        column_config={
            "timestamp"    : st.column_config.TextColumn("⏱ Waktu",     width="medium"),
            "sample_id"    : st.column_config.TextColumn("🆔 ID",        width="large"),
            "visual_label" : st.column_config.TextColumn("🏗️ Kondisi",  width="medium"),
            "pred_label"   : st.column_config.TextColumn("🎯 Status",   width="small"),
            "risk_level"   : st.column_config.TextColumn("⚠️ Risiko",   width="small"),
            "pga"          : st.column_config.TextColumn("PGA (g)",     width="small"),
            "rms"          : st.column_config.TextColumn("RMS (g)",     width="small"),
            "crest"        : st.column_config.TextColumn("Crest Factor",width="small"),
            "intensity_lbl": st.column_config.TextColumn("MMI",         width="small"),
            "p_aman"       : st.column_config.TextColumn("P(Aman)",     width="small"),
            "p_waspada"    : st.column_config.TextColumn("P(Waspada)",  width="small"),
            "p_bahaya"     : st.column_config.TextColumn("P(Bahaya)",   width="small"),
            "description"  : st.column_config.TextColumn("📝 Deskripsi",width="large"),
        },
    )


# ╔══════════════════════════════════════════════════════════════════
# ║  TAB 2 — ARSIP GAMBAR CAPTURE (semua capture + filter + paginasi)
# ╚══════════════════════════════════════════════════════════════════
with tab_gallery:

    _gal_loc_label = f" — {_sel_loc_obj['nama']}" if _sel_loc_obj else " — Semua Lokasi"
    sec_header("🗂️", f"ARSIP GAMBAR CAPTURE{_gal_loc_label}")

    if _sel_loc_obj and df_view_empty:
        st.warning("⚠️ Belum ada data yang ditetapkan ke lokasi ini. Gunakan tab **Kelola Data** untuk menetapkan rekaman.")

    # Filter controls
    fc1, fc2, fc3, fc4 = st.columns([1.2, 1.5, 1.5, 1.5])
    with fc1:
        f_label  = st.selectbox("Filter Status",
                                ["Semua", "aman", "waspada", "bahaya"], key="gal_fl")
    with fc2:
        f_visual = st.selectbox("Filter Kondisi Bangunan",
                                ["Semua", "Tidak Retak", "Retak Ringan", "Retak Berat"], key="gal_fv")
    with fc3:
        f_sort   = st.selectbox("Urutan", [
                                "Terbaru → Lama", "Lama → Terbaru",
                                "PGA Tertinggi",  "PGA Terendah"], key="gal_fs")
    with fc4:
        page_size = st.select_slider(
            "Gambar per halaman", [12, 24, 36, 48, 72], value=24, key="gal_fps"
        )

    # Apply filters on _df_display (already location-filtered)
    df_gal = _df_display[_df_display["image_path"].str.len() > 0].copy()
    if f_label  != "Semua": df_gal = df_gal[df_gal["pred_label"]   == f_label]
    if f_visual != "Semua": df_gal = df_gal[df_gal["visual_label"] == f_visual]

    sort_map = {
        "Terbaru → Lama":  ("timestamp", False),
        "Lama → Terbaru":  ("timestamp", True),
        "PGA Tertinggi":   ("pga",       False),
        "PGA Terendah":    ("pga",       True),
    }
    scol, sasc = sort_map[f_sort]
    df_gal = df_gal.sort_values(scol, ascending=sasc).reset_index(drop=True)

    tot_gal   = len(df_gal)
    n_pages   = max(1, math.ceil(tot_gal / page_size))
    g_aman    = int((df_gal["pred_label"] == "aman").sum())
    g_waspada = int((df_gal["pred_label"] == "waspada").sum())
    g_bahaya  = int((df_gal["pred_label"] == "bahaya").sum())

    st.markdown(f"""
<div style="background:#0c0e1c;border:1px solid #1a1f35;border-radius:8px;
            padding:10px 18px;display:flex;align-items:center;
            gap:18px;flex-wrap:wrap;margin-bottom:14px">
  <div style="font-size:.61rem;color:#5060a0;text-transform:uppercase;
              letter-spacing:.08em;flex:1">
    Menampilkan {tot_gal} dari {len(_df_display)} rekaman
  </div>
  <div style="display:flex;gap:8px">
    <span style="background:#0a1e0a;border:1px solid #0d3b1a;border-radius:4px;
                 padding:3px 12px;font-size:.6rem;font-weight:700;color:#2ecc71">
      ✅ AMAN · {g_aman}
    </span>
    <span style="background:#1e1400;border:1px solid #3b2400;border-radius:4px;
                 padding:3px 12px;font-size:.6rem;font-weight:700;color:#f39c12">
      ⚠️ WASPADA · {g_waspada}
    </span>
    <span style="background:#1e0700;border:1px solid #3b0d0d;border-radius:4px;
                 padding:3px 12px;font-size:.6rem;font-weight:700;color:#e74c3c">
      🔴 BAHAYA · {g_bahaya}
    </span>
  </div>
</div>""", unsafe_allow_html=True)

    if tot_gal == 0:
        st.markdown("""
<div style='text-align:center;padding:60px;color:#2a3050'>
  <div style='font-size:2.5rem;margin-bottom:12px'>📭</div>
  <div style='font-size:.85rem;font-weight:600;color:#3a4060'>Tidak ada data sesuai filter</div>
</div>""", unsafe_allow_html=True)
    else:
        if n_pages > 1:
            pc1, pc2, pc3 = st.columns([2, 1, 2])
            with pc2:
                page_num = st.number_input(
                    f"Hal.", min_value=1, max_value=n_pages, value=1,
                    key="gal_page", label_visibility="collapsed",
                )
            st.markdown(
                f"<p style='text-align:center;font-size:.6rem;color:#4a5578;"
                f"margin-top:-8px;margin-bottom:12px'>"
                f"Halaman {page_num} dari {n_pages} · {tot_gal} gambar</p>",
                unsafe_allow_html=True,
            )
        else:
            page_num = 1

        start   = (page_num - 1) * page_size
        end     = min(start + page_size, tot_gal)
        df_page = df_gal.iloc[start:end]

        for row_start in range(0, len(df_page), gallery_cols_n):
            batch = df_page.iloc[row_start : row_start + gallery_cols_n]
            cols  = st.columns(gallery_cols_n)
            for ci, (_, row) in enumerate(batch.iterrows()):
                with cols[ci]: render_img_card(row, gallery_cols_n)
            st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

        st.markdown(
            f"<p style='text-align:center;font-size:.6rem;color:#4a5578;"
            f"margin-top:10px;letter-spacing:.06em'>"
            f"REKAMAN {start+1}–{end} DARI {tot_gal}</p>",
            unsafe_allow_html=True,
        )



# ╔══════════════════════════════════════════════════════════════════
# ║  TAB 3 — KELOLA DATA (CRUD)
# ╚══════════════════════════════════════════════════════════════════
with tab_crud:
    sec_header("🗑️", "KELOLA DATA — HAPUS LOG & GAMBAR INFERENSI")

    st.markdown("""
<div style="background:#1a0800;border:1px solid #3b1a00;border-radius:8px;
            padding:12px 16px;margin-bottom:20px;font-size:.78rem;color:#f5a623">
  ⚠️ <b>Peringatan:</b> Penghapusan data bersifat <b>permanen</b> dan tidak dapat dibatalkan.
  Pastikan Anda telah melakukan backup sebelum menghapus data.
</div>""", unsafe_allow_html=True)

    # ── Sub-tabs inside CRUD ───────────────────────────────────────
    crud_log, crud_img, crud_assign = st.tabs([
        "📋  Hapus Log Inferensi",
        "🖼️  Hapus Gambar Capture",
        "📍  Tetapkan ke Lokasi",
    ])

    # ── Sub-tab A: Delete log rows ─────────────────────────────────
    with crud_log:
        sec_header("📋", "HAPUS BARIS LOG INFERENSI")

        if df.empty:
            st.warning("Tidak ada data log untuk dikelola.")
        else:
            # Filter controls
            fc1, fc2, fc3 = st.columns([1.5, 1.5, 2])
            with fc1:
                cl_filter_lbl = st.selectbox("Filter Status",
                    ["Semua","aman","waspada","bahaya"], key="cl_fl")
            with fc2:
                cl_filter_vis = st.selectbox("Filter Kondisi",
                    ["Semua","Tidak Retak","Retak Ringan","Retak Berat"], key="cl_fv")
            with fc3:
                cl_search = st.text_input("🔍 Cari Sample ID / Deskripsi",
                    placeholder="Ketik untuk mencari...", key="cl_search")

            df_crud = df.copy()
            if cl_filter_lbl != "Semua":
                df_crud = df_crud[df_crud["pred_label"] == cl_filter_lbl]
            if cl_filter_vis != "Semua":
                df_crud = df_crud[df_crud["visual_label"] == cl_filter_vis]
            if cl_search.strip():
                q = cl_search.strip().lower()
                df_crud = df_crud[
                    df_crud["sample_id"].str.lower().str.contains(q, na=False) |
                    df_crud["description"].str.lower().str.contains(q, na=False)
                ]
            df_crud = df_crud.sort_values("timestamp", ascending=False).reset_index(drop=True)

            st.markdown(f"""
<div style="font-size:.65rem;color:#6070a0;margin-bottom:10px">
  Ditemukan <b style="color:#d0d8f0">{len(df_crud)}</b> dari {len(df)} rekaman
</div>""", unsafe_allow_html=True)

            if df_crud.empty:
                st.info("Tidak ada data yang sesuai filter.")
            else:
                # Multiselect by sample_id
                all_ids = df_crud["sample_id"].tolist()
                id_labels = {
                    row["sample_id"]: (
                        f"{str(row['timestamp'])[:16]}  |  "
                        f"{row['pred_label'].upper():8s}  |  "
                        f"{row['visual_label'] or '—':15s}  |  "
                        f"{row['sample_id'][-20:]}"
                    )
                    for _, row in df_crud.iterrows()
                }

                st.markdown("""
<div style="font-size:.68rem;color:#8090b0;margin-bottom:6px">
  Pilih rekaman yang akan dihapus:
</div>""", unsafe_allow_html=True)

                # Select All toggle
                sel_col1, sel_col2 = st.columns([1, 4])
                with sel_col1:
                    select_all = st.checkbox("Pilih semua", key="cl_all")

                selected_ids = all_ids if select_all else []

                # Show table of records
                disp_df = df_crud[["timestamp","sample_id","pred_label","visual_label",
                                   "risk_level","pga","description"]].copy()
                disp_df["timestamp"]  = disp_df["timestamp"].astype(str).str[:16]
                disp_df["pga"]        = disp_df["pga"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
                disp_df["sample_id"]  = disp_df["sample_id"].str[-24:]

                selected_from_table = st.multiselect(
                    "Atau pilih per baris (Sample ID):",
                    options=all_ids,
                    default=selected_ids,
                    format_func=lambda x: id_labels.get(x, x),
                    key="cl_multisel",
                    label_visibility="collapsed",
                )

                # Show preview table
                with st.expander(f"📋 Preview data terpilih ({len(selected_from_table)} rekaman)", expanded=False):
                    if selected_from_table:
                        prev = df_crud[df_crud["sample_id"].isin(selected_from_table)][
                            ["timestamp","sample_id","pred_label","visual_label","risk_level","pga"]
                        ].copy()
                        prev["pga"] = prev["pga"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
                        st.dataframe(prev, use_container_width=True, hide_index=True)
                    else:
                        st.info("Belum ada rekaman dipilih.")

                # Delete confirmation + button
                if selected_from_table:
                    st.markdown(f"""
<div style="background:#1a0700;border:1px solid #3b0d0d;border-radius:8px;
            padding:12px 16px;margin:12px 0;font-size:.78rem;color:#f87171">
  🗑️ Akan menghapus <b>{len(selected_from_table)}</b> baris dari log CSV.
  Gambar terkait <b>tidak</b> ikut dihapus di sini (gunakan tab Hapus Gambar).
</div>""", unsafe_allow_html=True)

                    col_del, col_cancel = st.columns([1, 3])
                    with col_del:
                        confirm_del = st.checkbox("Saya yakin ingin menghapus", key="cl_confirm")
                    if confirm_del:
                        with st.container():
                            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                            if st.button(f"🗑️ HAPUS {len(selected_from_table)} REKAMAN LOG",
                                         use_container_width=True, key="cl_delete_btn"):
                                n_del, err = delete_rows_from_csv(csv_path, set(selected_from_table))
                                if err:
                                    st.error(f"Gagal: {err}")
                                else:
                                    st.success(f"✅ Berhasil menghapus {n_del} baris log inferensi.")
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

    # ── Sub-tab B: Delete images ───────────────────────────────────
    with crud_img:
        sec_header("🖼️", "HAPUS GAMBAR CAPTURE")

        df_imgs = df[df["image_path"].str.len() > 0].copy()
        df_imgs = df_imgs.sort_values("timestamp", ascending=False).reset_index(drop=True)

        if df_imgs.empty:
            st.warning("Tidak ada gambar capture dalam log.")
        else:
            # Filter
            img_f1, img_f2 = st.columns(2)
            with img_f1:
                img_fl = st.selectbox("Filter Status",
                    ["Semua","aman","waspada","bahaya"], key="img_fl")
            with img_f2:
                img_fv = st.selectbox("Filter Kondisi",
                    ["Semua","Tidak Retak","Retak Ringan","Retak Berat"], key="img_fv")

            if img_fl != "Semua": df_imgs = df_imgs[df_imgs["pred_label"] == img_fl]
            if img_fv != "Semua": df_imgs = df_imgs[df_imgs["visual_label"] == img_fv]
            df_imgs = df_imgs.reset_index(drop=True)

            st.markdown(f"""
<div style="font-size:.65rem;color:#6070a0;margin-bottom:12px">
  {len(df_imgs)} gambar ditemukan
</div>""", unsafe_allow_html=True)

            # Show image grid with checkboxes
            img_selected = []
            n_img_cols = 4
            for row_start in range(0, len(df_imgs), n_img_cols):
                batch = df_imgs.iloc[row_start:row_start + n_img_cols]
                cols  = st.columns(n_img_cols)
                for ci, (_, row) in enumerate(batch.iterrows()):
                    with cols[ci]:
                        lbl   = row["pred_label"] or "aman"
                        lbl_c = LABEL_COLOR.get(lbl, "#4a5578")
                        vis   = row["visual_label"] or "—"
                        ts    = str(row["timestamp"])[:16]
                        ann   = str(row["ann_path"])
                        raw   = str(row["image_path"])
                        disp  = ann if ann and os.path.exists(ann) else raw
                        has   = bool(disp and os.path.exists(disp))

                        st.markdown('<div class="img-card">', unsafe_allow_html=True)
                        if has:
                            st.image(disp, use_container_width=True)
                        else:
                            st.markdown(f"""
<div class="img-placeholder" style="min-height:90px">
  <div style="font-size:1.4rem">📷</div>
  <div style="font-size:.55rem;color:{lbl_c};margin-top:3px">{vis}</div>
</div>""", unsafe_allow_html=True)
                        st.markdown(f"""
<div class="img-footer">
  <div class="img-lbl" style="color:{lbl_c}">{lbl.upper()}</div>
  <div class="img-vis">{vis}</div>
  <div class="img-ts">{ts}</div>
</div></div>""", unsafe_allow_html=True)

                        # Checkbox per image
                        if st.checkbox("Pilih untuk hapus", key=f"imgck_{row['sample_id']}",
                                       label_visibility="collapsed"):
                            img_selected.append(row)

            if img_selected:
                also_del_log = st.checkbox(
                    f"Juga hapus {len(img_selected)} baris log CSV terkait", key="img_also_log"
                )
                st.markdown(f"""
<div style="background:#1a0700;border:1px solid #3b0d0d;border-radius:8px;
            padding:12px 16px;margin:12px 0;font-size:.78rem;color:#f87171">
  🗑️ Akan menghapus file gambar dari <b>{len(img_selected)}</b> rekaman.
  {'+ menghapus baris log CSV terkait.' if also_del_log else ''}
</div>""", unsafe_allow_html=True)

                confirm_img = st.checkbox("Saya yakin ingin menghapus file gambar", key="img_confirm")
                if confirm_img:
                    st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                    if st.button(f"🗑️ HAPUS {len(img_selected)} GAMBAR",
                                 use_container_width=True, key="img_delete_btn"):
                        total_files = 0
                        for row in img_selected:
                            deleted = delete_image_files(row)
                            total_files += len(deleted)

                        if also_del_log:
                            ids = {r["sample_id"] for r in img_selected}
                            n_del, err = delete_rows_from_csv(csv_path, ids)
                            if err:
                                st.error(f"Hapus gambar OK, tapi gagal hapus log: {err}")
                            else:
                                st.success(f"✅ {total_files} file gambar + {n_del} baris log dihapus.")
                        else:
                            st.success(f"✅ {total_files} file gambar berhasil dihapus.")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sub-tab C: Assign records to location ─────────────────────
    with crud_assign:
        sec_header("📍", "TETAPKAN REKAMAN KE LOKASI ASSESSMENT")
        _locs_asgn = load_locations(csv_path)

        if not _locs_asgn:
            st.warning("Belum ada lokasi terdaftar. Tambahkan lokasi di tab **Manajemen Lokasi** terlebih dahulu.")
        elif df.empty:
            st.warning("Tidak ada data log.")
        else:
            asgn_col1, asgn_col2 = st.columns([1.5, 2])
            with asgn_col1:
                # Target location
                _asgn_loc_names = [l["nama"] for l in _locs_asgn]
                _asgn_sel_name  = st.selectbox("📍 Pilih Lokasi Tujuan",
                    _asgn_loc_names, key="asgn_loc")
                _asgn_loc_obj   = next((l for l in _locs_asgn if l["nama"] == _asgn_sel_name), None)
                _asgn_loc_id    = _asgn_loc_obj["id"] if _asgn_loc_obj else None

                # Current assignment count
                if _asgn_loc_id:
                    _cur_asgn = load_loc_assignments(csv_path)
                    _cur_ids  = _cur_asgn.get(_asgn_loc_id, [])
                    st.markdown(f"""
<div style="background:#080a18;border:1px solid #1a2a4a;border-radius:7px;
            padding:8px 12px;margin:8px 0;font-size:.65rem">
  <div style="color:#6080a0">Rekaman sudah ditetapkan:</div>
  <div style="font-size:1rem;font-weight:800;color:#60a0e0">{len(_cur_ids)} rekaman</div>
</div>""", unsafe_allow_html=True)

                # Time range quick-assign
                st.markdown("""
<div style="font-size:.65rem;font-weight:700;color:#8090b0;
            text-transform:uppercase;letter-spacing:.1em;margin:12px 0 6px 0">
  Assign berdasarkan Rentang Waktu
</div>""", unsafe_allow_html=True)
                ts_min = df["timestamp"].min()
                ts_max = df["timestamp"].max()
                if pd.notna(ts_min):
                    _d1 = st.date_input("Dari tanggal", value=ts_min.date(), key="asgn_d1")
                    _d2 = st.date_input("Sampai tanggal", value=ts_max.date(), key="asgn_d2")

                    _mask_time = (
                        (df["timestamp"].dt.date >= _d1) &
                        (df["timestamp"].dt.date <= _d2)
                    )
                    _df_range = df[_mask_time]
                    st.markdown(f"""
<div style="font-size:.65rem;color:#5060a0;margin-top:4px">
  {len(_df_range)} rekaman dalam rentang waktu ini
</div>""", unsafe_allow_html=True)

                    # Mode
                    _asgn_mode = st.radio("Mode penetapan",
                        ["Tambahkan ke lokasi (tidak hapus yang lama)",
                         "Ganti seluruh penetapan lokasi ini"],
                        key="asgn_mode", horizontal=False)
                    _mode_key = "add" if "Tambahkan" in _asgn_mode else "replace"

                    if _asgn_loc_id and st.button("📍 Tetapkan Rekaman ke Lokasi",
                                                   use_container_width=True, key="asgn_btn"):
                        _ids_to_assign = _df_range["sample_id"].tolist()
                        ok = assign_records_to_loc(csv_path, _asgn_loc_id,
                                                    _ids_to_assign, mode=_mode_key)
                        if ok:
                            st.success(f"✅ {len(_ids_to_assign)} rekaman ditetapkan ke '{_asgn_sel_name}'.")
                            time.sleep(0.5); st.rerun()
                        else:
                            st.error("Gagal menyimpan. Periksa izin tulis.")

                # Remove all assignments for this location
                if _asgn_loc_id and _cur_ids:
                    st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                    if st.button("🗑️ Hapus Semua Penetapan Lokasi Ini",
                                 use_container_width=True, key="asgn_clear"):
                        assign_records_to_loc(csv_path, _asgn_loc_id, [], mode="replace")
                        st.success("✅ Semua penetapan dihapus.")
                        time.sleep(0.5); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            with asgn_col2:
                sec_header("📋", "REKAMAN SAAT INI")
                if _asgn_loc_id:
                    _cur_asgn2 = load_loc_assignments(csv_path)
                    _cur_ids2  = set(_cur_asgn2.get(_asgn_loc_id, []))
                    _df_asgn_view = df[df["sample_id"].isin(_cur_ids2)].sort_values(
                        "timestamp", ascending=False).head(30)
                    if _df_asgn_view.empty:
                        st.info("Belum ada rekaman ditetapkan ke lokasi ini.")
                    else:
                        _tbl = _df_asgn_view[["timestamp","sample_id","pred_label",
                                               "visual_label","risk_level","pga"]].copy()
                        _tbl["timestamp"] = _tbl["timestamp"].astype(str).str[:16]
                        _tbl["pga"]       = _tbl["pga"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
                        st.dataframe(_tbl, use_container_width=True,
                                     height=350, hide_index=True)


# ╔══════════════════════════════════════════════════════════════════
# ║  TAB 4 — MANAJEMEN LOKASI (with Google Maps picker)
# ╚══════════════════════════════════════════════════════════════════
with tab_lokasi:
    sec_header("📍", "MANAJEMEN LOKASI — GEDUNG & TITIK PANTAU")

    locs = load_locations(csv_path)

    # ── Layout: Form (left) + Daftar Lokasi (right) ───────────────
    form_col, list_col = st.columns([1.3, 2])

    # ── FORM TAMBAH / EDIT ────────────────────────────────────────
    with form_col:
        # Check if editing
        edit_id  = st.session_state.get("loc_edit_id", None)
        edit_loc = next((l for l in locs if l.get("id") == edit_id), None) if edit_id else None

        mode_label = "✏️ Edit Lokasi" if edit_loc else "➕ Tambah Lokasi Baru"
        sec_header("📝", mode_label)

        st.markdown('<div class="form-card">', unsafe_allow_html=True)

        lok_nama = st.text_input("🏢 Nama Gedung / Lokasi *",
            value=edit_loc["nama"]      if edit_loc else "",
            placeholder="contoh: Gedung Rektorat UNAIR", key="lok_nama")
        lok_tipe = st.selectbox("🏷️ Tipe Lokasi",
            ["Gedung Pemerintahan","Gedung Pendidikan","Gedung Kesehatan",
             "Gedung Komersial","Infrastruktur Kritis","Pemukiman","Lainnya"],
            index=["Gedung Pemerintahan","Gedung Pendidikan","Gedung Kesehatan",
                   "Gedung Komersial","Infrastruktur Kritis","Pemukiman","Lainnya"].index(
                       edit_loc["tipe"]) if edit_loc and edit_loc.get("tipe") in
                   ["Gedung Pemerintahan","Gedung Pendidikan","Gedung Kesehatan",
                    "Gedung Komersial","Infrastruktur Kritis","Pemukiman","Lainnya"] else 6,
            key="lok_tipe")
        lok_alamat = st.text_area("📫 Alamat Lengkap",
            value=edit_loc["alamat"]    if edit_loc else "",
            placeholder="Jl. Dharmawangsa Dalam, Surabaya 60286",
            height=70, key="lok_alamat")

        coord_c1, coord_c2 = st.columns(2)
        with coord_c1:
            lok_lat = st.number_input("🌐 Latitude",
                value=float(edit_loc["lat"]) if edit_loc else -7.2575,
                format="%.6f", step=0.0001, key="lok_lat",
                help="Contoh: -7.257500 (Surabaya)")
        with coord_c2:
            lok_lon = st.number_input("🌐 Longitude",
                value=float(edit_loc["lon"]) if edit_loc else 112.7521,
                format="%.6f", step=0.0001, key="lok_lon",
                help="Contoh: 112.752100 (Surabaya)")

        # ── Interactive Leaflet map picker ────────────────────────
        st.markdown("""
<div style="font-size:.65rem;color:#8090b0;margin:6px 0 4px 0">
  🗺️ <b>Klik pada peta</b> untuk memilih koordinat, lalu salin ke field Latitude/Longitude di atas.
</div>""", unsafe_allow_html=True)

        _init_lat = float(edit_loc["lat"]) if edit_loc else lok_lat
        _init_lon = float(edit_loc["lon"]) if edit_loc else lok_lon

        import streamlit.components.v1 as _components
        _map_html = f"""
<!DOCTYPE html><html><head>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  body{{margin:0;background:#060810;font-family:Inter,sans-serif}}
  #map{{height:280px;border-radius:8px;border:1px solid #1a2a4a}}
  #coord-display{{
    background:#0c0e1c;border:1px solid #1a2a4a;border-radius:6px;
    padding:8px 14px;margin-top:8px;font-size:12px;
    display:flex;align-items:center;justify-content:space-between;gap:10px;
  }}
  #coord-text{{color:#60a0e0;font-family:monospace;font-weight:700;flex:1}}
  #copy-btn{{
    background:#0a1830;border:1px solid #1a3060;color:#60a0e0;
    padding:4px 12px;border-radius:4px;cursor:pointer;font-size:11px;font-weight:700;
  }}
  #copy-btn:hover{{background:#0f2040}}
  #hint{{color:#4a5578;font-size:11px;margin-top:4px}}
</style>
</head><body>
<div id="map"></div>
<div id="coord-display">
  <span id="coord-text">Klik peta untuk memilih koordinat...</span>
  <button id="copy-btn" onclick="copyCoord()">📋 Salin</button>
</div>
<div id="hint">Klik peta → salin koordinat → tempel ke field Latitude & Longitude</div>
<script>
  var map = L.map('map').setView([{_init_lat}, {_init_lon}], 14);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{
    attribution:'© OpenStreetMap', maxZoom:19
  }}).addTo(map);

  var marker = L.marker([{_init_lat}, {_init_lon}], {{draggable:true}}).addTo(map);
  var selectedLat = {_init_lat}, selectedLon = {_init_lon};

  function updateCoord(lat, lon) {{
    selectedLat = lat.toFixed(6); selectedLon = lon.toFixed(6);
    document.getElementById('coord-text').textContent =
      'Lat: ' + selectedLat + '  |  Lon: ' + selectedLon;
  }}

  map.on('click', function(e) {{
    marker.setLatLng(e.latlng);
    updateCoord(e.latlng.lat, e.latlng.lng);
  }});

  marker.on('dragend', function(e) {{
    var ll = e.target.getLatLng();
    updateCoord(ll.lat, ll.lng);
  }});

  function copyCoord() {{
    var txt = selectedLat + ', ' + selectedLon;
    navigator.clipboard.writeText(txt).then(function(){{
      var btn = document.getElementById('copy-btn');
      btn.textContent = '✅ Disalin!';
      setTimeout(function(){{btn.textContent='📋 Salin'}}, 2000);
    }});
  }}

  updateCoord({_init_lat}, {_init_lon});
</script>
</body></html>"""
        _components.html(_map_html, height=340, scrolling=False)

        lok_desc = st.text_area("📝 Deskripsi / Catatan",
            value=edit_loc["deskripsi"] if edit_loc else "",
            placeholder="Keterangan tambahan, jumlah lantai, kondisi bangunan, dll.",
            height=70, key="lok_desc")

        st.markdown('</div>', unsafe_allow_html=True)

        # Maps preview link
        if lok_lat and lok_lon:
            maps_url = f"https://www.google.com/maps?q={lok_lat},{lok_lon}"
            st.markdown(f"""
<a href="{maps_url}" target="_blank"
   style="font-size:.68rem;color:#60a0e0;text-decoration:none">
  🗺️ Lihat di Google Maps ↗
</a>""", unsafe_allow_html=True)

        # Buttons
        b1, b2 = st.columns(2)
        with b1:
            st.markdown('<div class="btn-success">', unsafe_allow_html=True)
            save_clicked = st.button(
                "✏️ Simpan Perubahan" if edit_loc else "➕ Tambah Lokasi",
                use_container_width=True, key="lok_save"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        with b2:
            if edit_loc:
                if st.button("✖ Batal Edit", use_container_width=True, key="lok_cancel"):
                    st.session_state.pop("loc_edit_id", None)
                    st.rerun()

        if save_clicked:
            if not lok_nama.strip():
                st.error("Nama lokasi tidak boleh kosong.")
            else:
                if edit_loc:
                    ok = update_location(csv_path, edit_id,
                                         nama=lok_nama, tipe=lok_tipe, alamat=lok_alamat,
                                         lat=lok_lat, lon=lok_lon, deskripsi=lok_desc)
                    if ok:
                        st.success(f"✅ Lokasi '{lok_nama}' berhasil diperbarui.")
                        st.session_state.pop("loc_edit_id", None)
                        time.sleep(0.8); st.rerun()
                    else:
                        st.error("Gagal menyimpan. Periksa path CSV.")
                else:
                    ok = add_location(csv_path, lok_nama, lok_alamat,
                                      lok_lat, lok_lon, lok_desc, lok_tipe)
                    if ok:
                        st.success(f"✅ Lokasi '{lok_nama}' berhasil ditambahkan.")
                        time.sleep(0.8); st.rerun()
                    else:
                        st.error("Gagal menyimpan. Periksa izin tulis di direktori CSV.")

    # ── DAFTAR LOKASI ─────────────────────────────────────────────
    with list_col:
        sec_header("🗺️", f"DAFTAR LOKASI TERDAFTAR ({len(locs)} lokasi)")

        if not locs:
            st.markdown("""
<div style="background:#0c0e1c;border:1px solid #1a1f35;border-radius:10px;
            padding:40px;text-align:center">
  <div style="font-size:2.5rem;margin-bottom:12px">📍</div>
  <div style="font-size:.82rem;color:#6070a0;font-weight:600">Belum ada lokasi terdaftar</div>
  <div style="font-size:.68rem;color:#4a5578;margin-top:6px">
    Gunakan form di kiri untuk menambahkan lokasi pertama
  </div>
</div>""", unsafe_allow_html=True)
        else:
            # Search
            loc_search = st.text_input("🔍 Cari lokasi...",
                placeholder="Nama atau alamat", key="loc_srch",
                label_visibility="collapsed")
            locs_disp = locs
            if loc_search.strip():
                q = loc_search.strip().lower()
                locs_disp = [l for l in locs if
                             q in l.get("nama","").lower() or
                             q in l.get("alamat","").lower() or
                             q in l.get("tipe","").lower()]

            TIPE_ICON = {
                "Gedung Pemerintahan": "🏛️",  "Gedung Pendidikan": "🏫",
                "Gedung Kesehatan": "🏥",      "Gedung Komersial": "🏢",
                "Infrastruktur Kritis": "⚡",  "Pemukiman": "🏘️",
                "Lainnya": "📍",
            }

            for loc in locs_disp:
                icon = TIPE_ICON.get(loc.get("tipe",""), "📍")
                maps_url = f"https://www.google.com/maps?q={loc.get('lat',0)},{loc.get('lon',0)}"

                st.markdown(f"""
<div class="loc-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
    <div>
      <div class="loc-card-name">{icon} {loc.get('nama','—')}</div>
      <div class="loc-card-addr">📫 {loc.get('alamat','—') or '—'}</div>
    </div>
    <span class="loc-badge">{loc.get('tipe','—')}</span>
  </div>
  <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px">
    <div class="loc-card-coord">🌐 {loc.get('lat',0):.6f}, {loc.get('lon',0):.6f}</div>
    <a href="{maps_url}" target="_blank"
       style="font-size:.62rem;color:#60a0e0;text-decoration:none">🗺️ Maps ↗</a>
  </div>
  {f'<div style="font-size:.68rem;color:#8090b0;margin-bottom:8px;line-height:1.5">{loc.get("deskripsi","")}</div>' if loc.get("deskripsi") else ""}
  <div style="font-size:.56rem;color:#3a4060">ID: {loc.get('id','—')} &nbsp;·&nbsp; Ditambahkan: {loc.get('ditambahkan','—')}</div>
</div>""", unsafe_allow_html=True)

                # Action buttons
                ba1, ba2, ba3 = st.columns([1, 1, 3])
                with ba1:
                    if st.button("✏️ Edit", key=f"loc_edit_{loc['id']}", use_container_width=True):
                        st.session_state["loc_edit_id"] = loc["id"]
                        st.rerun()
                with ba2:
                    st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                    if st.button("🗑️ Hapus", key=f"loc_del_{loc['id']}", use_container_width=True):
                        st.session_state[f"loc_del_confirm_{loc['id']}"] = True
                    st.markdown('</div>', unsafe_allow_html=True)

                # Confirm delete inline
                if st.session_state.get(f"loc_del_confirm_{loc['id']}", False):
                    st.warning(f"Konfirmasi: Hapus lokasi **{loc.get('nama','')}**?")
                    yc, nc = st.columns(2)
                    with yc:
                        if st.button("✅ Ya, Hapus", key=f"loc_yes_{loc['id']}", use_container_width=True):
                            delete_location(csv_path, loc["id"])
                            st.session_state.pop(f"loc_del_confirm_{loc['id']}", None)
                            st.rerun()
                    with nc:
                        if st.button("✖ Batal", key=f"loc_no_{loc['id']}", use_container_width=True):
                            st.session_state.pop(f"loc_del_confirm_{loc['id']}", None)
                            st.rerun()


# ══════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='margin-top:40px;padding:12px 0;border-top:1px solid #0e1020;
            text-align:center;font-size:.59rem;color:#1a2030;
            letter-spacing:.08em;text-transform:uppercase'>
  SISMIK DASHBOARD &nbsp;·&nbsp; SISTEM PEMANTAUAN BENCANA SEISMIK BERBASIS AI &nbsp;·&nbsp;
  {total} REKAMAN &nbsp;·&nbsp; REFRESH {refresh_interval}S &nbsp;·&nbsp;
  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>""", unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
