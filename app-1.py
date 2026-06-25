import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import plotly.express as px
import plotly.graph_objects as go
import hashlib
from datetime import datetime, timedelta
import joblib
import warnings
warnings.filterwarnings('ignore')

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RentIQ — Tenant Risk Platform",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── IMAGE REGISTRY (always online — Unsplash CDN, no local dependency) ───────
IMG = {
    "hero_bg":    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=1600&q=80",
    "city":       "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=1400&q=80",
    "dashboard":  "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&q=80",
    "apartment":  "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=700&q=80",
    "house":      "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=700&q=80",
    "commercial": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=700&q=80",
    "room":       "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=700&q=80",
    "harare1":    "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=700&q=80",
    "harare2":    "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=700&q=80",
    "harare3":    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=700&q=80",
    "avatar_base":"https://ui-avatars.com/api/?background=1e3a6e&color=c8f542&bold=true&size=64&name=",
}

def prop_img(prop_type):
    t = (prop_type or "apartment").lower()
    return IMG.get(t, IMG["apartment"])

def avatar(name):
    return f"{IMG['avatar_base']}{(name or 'U').replace(' ', '+')}"


# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

:root {
  --bg-deep:    #030e1c;
  --bg-main:    #061322;
  --bg-card:    #0b1c35;
  --bg-raised:  #102240;
  --bg-hover:   #163055;
  --border:     #183060;
  --border-lit: #234d8a;
  --text-1:     #ddeaf8;
  --text-2:     #7a9cc4;
  --text-3:     #3a5880;
  --lime:       #c8f542;
  --violet:     #5b54f0;
  --cyan:       #22d3ee;
  --low:        #34d399; --low-bg: rgba(52,211,153,0.13);
  --mid:        #fbbf24; --mid-bg: rgba(251,191,36,0.13);
  --high:       #f87171; --high-bg:rgba(248,113,113,0.13);
}

html,body,[class*="css"] { font-family:'DM Sans',sans-serif; background:var(--bg-deep)!important; color:var(--text-1); }
#MainMenu,footer { visibility:hidden; }
header { visibility:visible!important; background:transparent!important; }
.block-container { padding:0!important; max-width:100%!important; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:var(--bg-deep); }
::-webkit-scrollbar-thumb { background:var(--border-lit); border-radius:3px; }

/* SIDEBAR */
[data-testid="stSidebar"] { background:var(--bg-deep)!important; border-right:1px solid var(--border)!important; min-width:290px!important; }
[data-testid="stSidebar"][aria-expanded="false"] { min-width:0!important; }
[data-testid="stSidebarContent"] { overflow-y:auto!important; max-height:100vh!important; padding:1.1rem 1rem 2rem!important; }
[data-testid="collapsedControl"] { visibility:visible!important; color:var(--lime)!important; background:var(--bg-card)!important; border:1px solid var(--border-lit)!important; border-radius:9px!important; margin:0.6rem!important; }
[data-testid="stSidebar"] * { color:var(--text-1)!important; }
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p { font-family:'DM Sans',sans-serif; font-size:0.85rem; }

/* PAGE */
.pw { padding:1.6rem 2.4rem; background:var(--bg-main); min-height:100vh; }

/* UNIVERSITY STRIP */
.uni-strip { background:var(--bg-deep); color:var(--text-3); font-size:0.67rem; letter-spacing:0.08em; text-align:center; padding:0.42rem; text-transform:uppercase; border-bottom:1px solid var(--border); }
.uni-strip strong { color:var(--lime); }

/* HERO */
.hero { position:relative; border-radius:20px; overflow:hidden; margin-bottom:1.6rem; min-height:420px; display:flex; align-items:flex-end; }
.hero-bg { position:absolute; inset:0; background-size:cover; background-position:center; }
.hero-overlay { position:absolute; inset:0; background:linear-gradient(135deg, rgba(3,14,28,0.92) 0%, rgba(11,28,53,0.75) 60%, rgba(91,84,240,0.25) 100%); }
.hero-body { position:relative; z-index:2; padding:3rem 3.5rem; width:100%; display:flex; justify-content:space-between; align-items:flex-end; gap:2rem; }
.hero-left { flex:1; max-width:580px; }
.hero-badge { display:inline-block; margin-bottom:1.2rem; background:rgba(200,245,66,0.1); border:1px solid rgba(200,245,66,0.3); color:var(--lime); padding:4px 14px; border-radius:100px; font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase; font-weight:600; }
.hero h1 { font-family:'Syne',sans-serif; font-weight:800; font-size:clamp(2.2rem,4vw,3.8rem); line-height:1.06; margin:0 0 1rem; letter-spacing:-0.02em; color:var(--text-1); }
.hero h1 em { color:var(--lime); font-style:normal; }
.hero p { font-size:1rem; color:var(--text-2); line-height:1.7; font-weight:300; margin:0; }
.hero-stats { display:flex; gap:0; border:1px solid var(--border); border-radius:14px; overflow:hidden; background:rgba(3,14,28,0.6); backdrop-filter:blur(8px); flex-shrink:0; }
.hs { padding:1.2rem 1.8rem; border-right:1px solid var(--border); text-align:center; }
.hs:last-child { border-right:none; }
.hs-num { font-family:'Syne',sans-serif; font-size:1.9rem; font-weight:800; color:var(--lime); line-height:1; }
.hs-lbl { font-size:0.68rem; color:var(--text-3); text-transform:uppercase; letter-spacing:0.07em; margin-top:3px; }

/* IMAGE MOSAIC on landing */
.mosaic { display:grid; grid-template-columns:repeat(3,1fr); gap:0.8rem; margin-bottom:1.6rem; }
.mosaic img { width:100%; height:140px; object-fit:cover; border-radius:12px; border:1px solid var(--border); display:block; filter:saturate(0.55) brightness(0.55) hue-rotate(195deg); transition:filter 0.3s; }
.mosaic img:hover { filter:saturate(0.8) brightness(0.75) hue-rotate(185deg); }
.mosaic img:first-child { grid-column:span 2; height:180px; }

/* FEATURE GRID */
.fg { display:grid; grid-template-columns:repeat(3,1fr); gap:1.1rem; margin-bottom:1.6rem; }
.fc { background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:1.5rem; transition:transform 0.2s,border-color 0.2s; }
.fc:hover { transform:translateY(-3px); border-color:var(--border-lit); }
.fi { width:42px; height:42px; border-radius:10px; background:linear-gradient(135deg,var(--violet),var(--cyan)); display:flex; align-items:center; justify-content:center; font-size:1.2rem; margin-bottom:1rem; }
.fc h3 { font-family:'Syne',sans-serif; font-size:0.95rem; font-weight:700; margin:0 0 0.45rem; color:var(--text-1); }
.fc p { font-size:0.83rem; color:var(--text-2); line-height:1.6; margin:0; }

/* SECTION */
.sh { font-family:'Syne',sans-serif; font-size:1.35rem; font-weight:700; color:var(--text-1); margin-bottom:0.2rem; }
.ss { font-size:0.84rem; color:var(--text-3); margin-bottom:1.2rem; }

/* AUTH */
.auth-wrap { background:var(--bg-card); border:1px solid var(--border); border-radius:18px; padding:2rem; }

/* INPUTS */
.stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div, .stTextArea textarea {
  background:var(--bg-raised)!important; border:1px solid var(--border-lit)!important;
  border-radius:9px!important; font-family:'DM Sans',sans-serif!important;
  font-size:0.88rem!important; color:var(--text-1)!important;
}
.stTextInput>div>div>input:focus, .stTextArea textarea:focus {
  border-color:var(--violet)!important; box-shadow:0 0 0 3px rgba(91,84,240,0.16)!important;
}
label,.stSelectbox label,.stTextInput label,.stNumberInput label,.stCheckbox label,.stSlider label {
  color:var(--text-2)!important; font-size:0.81rem!important;
}

/* BUTTONS */
.stButton>button { background:linear-gradient(135deg,var(--violet),#3730d4)!important; color:#fff!important; border:none!important; border-radius:9px!important; font-family:'Syne',sans-serif!important; font-size:0.82rem!important; font-weight:700!important; letter-spacing:0.04em!important; padding:0.55rem 1.3rem!important; transition:opacity 0.15s,transform 0.15s!important; }
.stButton>button:hover { opacity:0.86!important; transform:translateY(-1px)!important; }
.stFormSubmitButton>button { width:100%!important; background:linear-gradient(135deg,var(--lime),#a3e635)!important; color:var(--bg-deep)!important; font-size:0.88rem!important; padding:0.7rem!important; }

/* METRICS */
[data-testid="metric-container"] { background:var(--bg-card)!important; border:1px solid var(--border)!important; border-radius:12px!important; padding:1rem 1.3rem!important; }
[data-testid="metric-container"] [data-testid="stMetricLabel"] { font-size:0.69rem!important; text-transform:uppercase; letter-spacing:0.07em; color:var(--text-3)!important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; font-size:1.75rem!important; font-weight:800!important; color:var(--lime)!important; }

/* RISK PILLS */
.rp { display:inline-flex; align-items:center; gap:5px; padding:4px 12px; border-radius:100px; font-size:0.77rem; font-weight:600; }
.rp-low  { background:var(--low-bg);  color:var(--low);  border:1px solid rgba(52,211,153,0.28); }
.rp-mid  { background:var(--mid-bg);  color:var(--mid);  border:1px solid rgba(251,191,36,0.28); }
.rp-high { background:var(--high-bg); color:var(--high); border:1px solid rgba(248,113,113,0.28); }

/* SCORE CARD */
.score-card { background:linear-gradient(145deg,#061322,#102240); border:1px solid var(--border-lit); border-radius:14px; padding:1.4rem; text-align:center; }
.sc-num { font-family:'Syne',sans-serif; font-size:3.5rem; font-weight:800; color:var(--lime); line-height:1; }
.sc-lbl { font-size:0.7rem; color:var(--text-3); text-transform:uppercase; letter-spacing:0.09em; margin-top:5px; }

/* PROPERTY CARD (standalone, not expander) */
.pcard { background:var(--bg-card); border:1px solid var(--border); border-radius:14px; overflow:hidden; transition:border-color 0.2s,transform 0.2s; margin-bottom:1rem; }
.pcard:hover { border-color:var(--border-lit); transform:translateY(-2px); }
.pcard-img { width:100%; height:170px; object-fit:cover; display:block; filter:saturate(0.65) brightness(0.72) hue-rotate(185deg); transition:filter 0.3s; }
.pcard:hover .pcard-img { filter:saturate(0.85) brightness(0.85) hue-rotate(175deg); }
.pcard-body { padding:1.1rem 1.2rem; }
.pcard-type { font-size:0.7rem; color:var(--text-3); text-transform:uppercase; letter-spacing:0.07em; margin-bottom:4px; }
.pcard-name { font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:var(--text-1); margin-bottom:2px; }
.pcard-loc  { font-size:0.78rem; color:var(--text-2); margin-bottom:0.8rem; }
.pcard-row  { display:flex; justify-content:space-between; align-items:center; }
.pcard-rent { font-family:'Syne',sans-serif; font-size:1.2rem; font-weight:800; color:var(--lime); }
.pcard-rent span { font-size:0.7rem; color:var(--text-3); font-weight:400; font-family:'DM Sans',sans-serif; }
.pcard-beds { font-size:0.78rem; color:var(--text-2); background:var(--bg-raised); padding:3px 9px; border-radius:6px; border:1px solid var(--border); }
.pcard-footer { padding:0.7rem 1.2rem; border-top:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; }
.pcard-landlord { font-size:0.75rem; color:var(--text-3); }

/* APPLICATION ROW CARD */
.app-card { background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.75rem; display:grid; grid-template-columns:64px 1fr 1fr 1fr auto; gap:1rem; align-items:center; }
.app-card:hover { border-color:var(--border-lit); }
.app-img { width:60px; height:48px; object-fit:cover; border-radius:8px; border:1px solid var(--border); filter:brightness(0.7) hue-rotate(185deg); }
.app-field-lbl { font-size:0.68rem; color:var(--text-3); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:2px; }
.app-field-val { font-size:0.86rem; color:var(--text-1); font-weight:500; }

/* EXPANDERS */
.stExpander { background:var(--bg-card)!important; border:1px solid var(--border)!important; border-radius:12px!important; margin-bottom:0.6rem!important; overflow:hidden; }
[data-testid="stExpander"] details summary p { color:var(--text-1)!important; }
[data-testid="stMarkdownContainer"] p { color:var(--text-2); font-size:0.88rem; }
[data-testid="stMarkdownContainer"] strong { color:var(--text-1); }

/* TABS */
.stTabs [data-baseweb="tab-list"] { gap:0.3rem; background:transparent; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { font-family:'Syne',sans-serif; font-size:0.82rem; font-weight:700; letter-spacing:0.04em; border-radius:8px 8px 0 0; color:var(--text-3)!important; background:transparent!important; border:none!important; padding:0.55rem 1rem!important; }
.stTabs [aria-selected="true"] { color:var(--lime)!important; border-bottom:2px solid var(--lime)!important; }

/* SIDEBAR COMPONENTS */
.sb-logo { font-family:'Syne',sans-serif; font-size:1.35rem; font-weight:800; color:var(--lime)!important; }
.sb-logo span { color:var(--text-3)!important; font-weight:300; font-size:0.7rem; display:block; margin-top:-2px; }
.sb-div { border:none; border-top:1px solid var(--border); margin:0.9rem 0; }
.sb-badge { background:rgba(91,84,240,0.1); border:1px solid rgba(91,84,240,0.22); border-radius:10px; padding:0.7rem 0.9rem; margin-bottom:0.9rem; }
.sb-name { font-family:'Syne',sans-serif; font-size:0.9rem; font-weight:700; color:var(--lime)!important; }
.sb-type { font-size:0.66rem; color:var(--text-3)!important; text-transform:uppercase; letter-spacing:0.09em; margin-top:2px; }
.sb-av { width:38px; height:38px; border-radius:50%; object-fit:cover; border:2px solid var(--border-lit); margin-bottom:7px; display:block; }

/* INFO/SUMMARY TILES (replace empty st.info) */
.info-tile { background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:1.1rem 1.3rem; margin-bottom:0.75rem; display:flex; align-items:center; gap:1rem; }
.info-tile-icon { font-size:1.5rem; flex-shrink:0; }
.info-tile-body h4 { font-family:'Syne',sans-serif; font-size:0.92rem; font-weight:700; color:var(--text-1); margin:0 0 3px; }
.info-tile-body p { font-size:0.8rem; color:var(--text-2); margin:0; }

/* FORMS */
[data-testid="stForm"] { background:var(--bg-card)!important; border:1px solid var(--border)!important; border-radius:14px!important; padding:1.4rem!important; }
.stAlert, div[data-testid="stAlert"] { background:var(--bg-raised)!important; border:1px solid var(--border-lit)!important; border-radius:10px!important; }
.stAlert p,.stAlert div { color:var(--text-1)!important; }
.js-plotly-plot { border-radius:12px; overflow:hidden; border:1px solid var(--border); }
hr { border-color:var(--border)!important; }

/* REVIEW CARD */
.rev-card { background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.75rem; display:grid; grid-template-columns:44px 1fr 72px; gap:1rem; align-items:start; }
.rev-card:hover { border-color:var(--border-lit); }

/* CHAT */
.chat-wrap { background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:1rem; max-height:430px; overflow-y:auto; }
.msg { display:flex; gap:0.7rem; align-items:flex-start; margin-bottom:0.9rem; }
.msg.mine { flex-direction:row-reverse; }
.msg-bubble { max-width:72%; padding:0.65rem 0.9rem; border-radius:14px; font-size:0.84rem; line-height:1.55; }
.msg.theirs .msg-bubble { background:var(--bg-raised); border:1px solid var(--border); color:var(--text-1); border-top-left-radius:3px; }
.msg.mine .msg-bubble { background:linear-gradient(135deg,var(--violet),#3730d4); color:#fff; border-top-right-radius:3px; }
.msg-meta { font-size:0.62rem; color:var(--text-3); margin-top:3px; }
.msg-avatar { width:32px; height:32px; border-radius:50%; overflow:hidden; flex-shrink:0; }
</style>
""", unsafe_allow_html=True)

# ─── UNIVERSITY STRIP ─────────────────────────────────────────────────────────
st.markdown("""
<div class="uni-strip">
  <strong>Bindura University of Science Education</strong> &nbsp;·&nbsp;
  Faculty of Science &amp; Engineering &nbsp;·&nbsp; Dept. of Computer Science &nbsp;·&nbsp;
  <strong>B220637B</strong> — Muriro Tinaye L
</div>
""", unsafe_allow_html=True)

# ─── DB CONFIG ────────────────────────────────────────────────────────────────
db_config = {'host':'localhost','user':'root','password':'','database':'rental_risk_assessment','unix_socket':'/opt/lampp/var/mysql/mysql.sock'}

for k,v in [('authenticated',False),('user_id',None),('user_type',None),('username',None),('chat_partner',None)]:
    if k not in st.session_state: st.session_state[k] = v

def get_server_connection():
    cfg = {k: v for k, v in db_config.items() if k != 'database'}
    try:
        return mysql.connector.connect(**cfg)
    except Error as e:
        st.error(f"MySQL server connection failed: {e}")
        return None

def get_db_connection():
    try: return mysql.connector.connect(**db_config)
    except Error as e: st.error(f"DB: {e}"); return None

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def register_user(username, password, email, full_name, phone, user_type):
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("INSERT INTO users(username,email,password_hash,full_name,phone,user_type) VALUES(%s,%s,%s,%s,%s,%s)",
                      (username,email,hash_password(password),full_name,phone,user_type))
            conn.commit(); return True,"Registration successful!"
        except Error as e: return False,f"Failed: {e}"
        finally: c.close(); conn.close()
    return False,"DB connection failed"

def login_user(username, password):
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor(dictionary=True)
            c.execute("SELECT * FROM users WHERE username=%s AND password_hash=%s",(username,hash_password(password)))
            u = c.fetchone(); return (True,u) if u else (False,"Invalid credentials")
        except Error as e: return False,f"Error: {e}"
        finally: c.close(); conn.close()
    return False,"DB connection failed"

@st.cache_resource
def load_ml_model():
    try:
        return (joblib.load('models/best_model.pkl'),
                joblib.load('models/scaler.pkl'),
                joblib.load('models/label_encoders.pkl'),
                joblib.load('models/feature_names.pkl'),
                joblib.load('models/model_info.pkl'),
                joblib.load('models/feature_config.pkl'))
    except Exception:
        return None,None,None,None,None,None

def normalize_employment_status(value):
    text = str(value or '').strip().lower().replace('-', ' ').replace('_', ' ')
    if text in {'full time', 'part time', 'employed'}:
        return 'employed'
    if text in {'self employed', 'self-employed', 'business'}:
        return 'self_employed'
    if text == 'student':
        return 'student'
    if text == 'unemployed':
        return 'unemployed'
    return text or 'unknown'

def bounded(value, low=0, high=100):
    return float(np.clip(value, low, high))

def scale_between(value, best, worst, points):
    if best == worst:
        return points
    ratio = (float(value) - worst) / (best - worst)
    return bounded(ratio, 0, 1) * points

def rule_based_score(data):
    income = float(data.get('monthly_income', 0) or 0)
    rent = float(data.get('property_monthly_rent', data.get('monthly_rent', 0)) or 0)
    current_rent = float(data.get('current_monthly_rent', 0) or 0)
    credit = float(data.get('credit_score', 300) or 300)
    debt = float(data.get('debt_to_income_ratio', 100) or 0)
    years = float(data.get('years_at_current_job', 0) or 0)
    late = float(data.get('previous_late_payments', 0) or 0)
    dependents = float(data.get('number_of_dependents', max(float(data.get('family_size', 1) or 1) - 1, 0)) or 0)
    r2i = float(data.get('rent_to_income_ratio', (rent / income * 100) if income > 0 else 100) or 0)
    remaining = float(data.get('remaining_income', income - rent) or 0)
    remaining_ratio = float(data.get('income_after_rent_ratio', (remaining / income * 100) if income > 0 else -100) or -100)
    employment = normalize_employment_status(data.get('employment_status'))

    components = {
        'affordability': scale_between(r2i, 20, 75, 24),
        'income_buffer': scale_between(remaining_ratio, 70, -20, 12),
        'credit': scale_between(credit, 800, 350, 16),
        'debt': scale_between(debt, 5, 85, 12),
        'job_stability': scale_between(years, 6, 0, 8),
        'rental_history': 7 if int(data.get('previous_rental_history', 0) or 0) else 0,
        'references': 6 if int(data.get('has_references', 0) or 0) else 0,
        'late_payments': scale_between(late, 0, 6, 7),
        'employment': {'employed': 6, 'self_employed': 4.5, 'student': 3, 'unemployed': 0}.get(employment, 2),
        'household_load': scale_between(dependents, 0, 8, 5),
        'current_rent_record': 3 if current_rent > 0 else 1.5,
    }
    score = bounded(sum(components.values()), 0, 100)
    return score, {key: round(value, 2) for key, value in components.items()}

def prediction_score(prob_by_class, rule_score):
    low = prob_by_class.get('low', 0)
    medium = prob_by_class.get('medium', 0)
    high = prob_by_class.get('high', 0)
    ml_score = float(np.clip((low * 100) + (medium * 55) + (high * 10), 0, 100))
    return bounded((rule_score * 0.85) + (ml_score * 0.15), 0, 100)

def score_category(score):
    if score >= 70:
        return 'low'
    if score >= 40:
        return 'medium'
    return 'high'

def predict_tenant_risk(data, model, scaler, les, feature_names=None, model_info=None, feature_config=None):
    try:
        feature_config = feature_config or {}
        numerical_features = feature_config.get('numerical_features') or [
            'monthly_income','years_at_current_job','previous_rental_history',
            'has_references','credit_score','debt_to_income_ratio','age',
            'family_size','number_of_dependents','previous_late_payments',
            'current_monthly_rent','property_monthly_rent','rent_to_income_ratio',
            'remaining_income','income_after_rent_ratio'
        ]
        categorical_features = feature_config.get('categorical_features') or list((les or {}).keys())

        prepared = dict(data)
        prepared.setdefault('number_of_dependents', max(float(prepared.get('family_size', 1)) - 1, 0))
        prepared.setdefault('current_monthly_rent', 0)
        prepared.setdefault('property_monthly_rent', prepared.get('monthly_rent', 0))
        prepared.setdefault('remaining_income', prepared.get('monthly_income', 0) - prepared.get('property_monthly_rent', 0))
        prepared.setdefault(
            'income_after_rent_ratio',
            (prepared['remaining_income'] / prepared['monthly_income'] * 100) if prepared.get('monthly_income', 0) else -100
        )
        prepared.setdefault('employment_position', prepared.get('employment_status', 'unknown'))
        prepared['employment_status'] = normalize_employment_status(prepared.get('employment_status'))
        prepared.setdefault('property_type', 'unknown')
        prepared.setdefault('affordability_status', 'Unknown')
        rule_score, components = rule_based_score(prepared)

        if model is None:
            score = round(rule_score, 2)
            cat = score_category(score)
            if   cat == 'low':    rec = 'Approve - low-risk applicant'
            elif cat == 'medium': rec = 'Consider with higher deposit or guarantor'
            else:                 rec = 'Reject or require significant guarantees'
            return {'risk_score':score,'risk_category':cat,'recommendation':rec,'score_components':components}

        features = pd.DataFrame(index=[0])
        for col in numerical_features:
            features[col] = float(prepared.get(col, 0) or 0)
        for col in categorical_features:
            le = (les or {}).get(col)
            value = str(prepared.get(col, 'unknown'))
            features[col + '_encoded'] = le.transform([value])[0] if le is not None and value in le.classes_ else -1

        if feature_names:
            for col in feature_names:
                if col not in features.columns:
                    features[col] = 0
            features = features[feature_names]

        probs = model.predict_proba(scaler.transform(features))[0]
        class_labels = (model_info or {}).get('class_labels')
        if not class_labels:
            class_labels = [str(c) for c in getattr(model, 'classes_', ['high','low','medium'])]
        prob_by_class = dict(zip(class_labels, probs))
        score = round(prediction_score(prob_by_class, rule_score), 2)
        cat = score_category(score)
        if   cat == 'low':    rec = 'Approve - low-risk applicant'
        elif cat == 'medium': rec = 'Consider with higher deposit or guarantor'
        else:                 rec = 'Reject or require significant guarantees'
        return {'risk_score':score,'risk_category':cat,'recommendation':rec,'probabilities':prob_by_class,'score_components':components}
    except Exception as e:
        fallback_score, components = rule_based_score(data)
        cat = score_category(fallback_score)
        return {'risk_score':round(fallback_score,2),'risk_category':cat,'recommendation':f'Rule-based fallback used: {e}','score_components':components}

def rp(cat, score=None):
    css = {'low':'rp-low','medium':'rp-mid','high':'rp-high'}
    lbl = {'low':'Low Risk','medium':'Medium Risk','high':'High Risk'}
    c   = cat.lower() if cat and cat.lower() in css else 'medium'
    s   = f" · {score}/100" if score is not None else ""
    return f'<span class="rp {css[c]}">● {lbl[c]}{s}</span>'

def dark_fig(fig):
    fig.update_layout(
        plot_bgcolor='#0b1c35', paper_bgcolor='#0b1c35',
        font=dict(family='DM Sans',color='#7a9cc4'),
        title_font=dict(family='Syne',color='#ddeaf8'),
        xaxis=dict(gridcolor='#183060',zerolinecolor='#183060'),
        yaxis=dict(gridcolor='#183060',zerolinecolor='#183060'),
        legend=dict(bgcolor='#102240',bordercolor='#183060'),
        margin=dict(l=16,r=16,t=46,b=16),
    )
    return fig

def ensure_database_exists():
    conn = get_server_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
        finally:
            try: c.close(); conn.close()
            except Exception: pass

def ensure_core_tables():
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS users(
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(160) NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                full_name VARCHAR(160) NOT NULL,
                phone VARCHAR(40) NULL,
                user_type ENUM('tenant','landlord') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS properties(
                property_id INT AUTO_INCREMENT PRIMARY KEY,
                landlord_id INT NOT NULL,
                property_name VARCHAR(160) NOT NULL,
                property_type VARCHAR(40) NOT NULL,
                address TEXT NOT NULL,
                city VARCHAR(80) NOT NULL,
                suburb VARCHAR(80) NULL,
                bedrooms INT DEFAULT 0,
                bathrooms INT DEFAULT 0,
                monthly_rent DECIMAL(12,2) NOT NULL,
                deposit_required DECIMAL(12,2) DEFAULT 0,
                image_path TEXT NULL,
                is_available TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(landlord_id) REFERENCES users(user_id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS tenant_applications(
                application_id INT AUTO_INCREMENT PRIMARY KEY,
                property_id INT NOT NULL,
                tenant_id INT NOT NULL,
                employment_status VARCHAR(50) NULL,
                employment_position VARCHAR(50) NULL,
                monthly_income DECIMAL(12,2) DEFAULT 0,
                years_at_current_job INT DEFAULT 0,
                previous_rental_history TINYINT(1) DEFAULT 0,
                has_references TINYINT(1) DEFAULT 0,
                credit_score INT DEFAULT 0,
                risk_score DECIMAL(6,2) DEFAULT 50,
                risk_category VARCHAR(20) DEFAULT 'medium',
                application_status VARCHAR(20) DEFAULT 'pending',
                number_of_dependents INT DEFAULT 0,
                current_monthly_rent DECIMAL(12,2) DEFAULT 0,
                household_notes TEXT NULL,
                affordability_status VARCHAR(40) NULL,
                affordability_comment TEXT NULL,
                application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(property_id) REFERENCES properties(property_id),
                FOREIGN KEY(tenant_id) REFERENCES users(user_id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS payments(
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                application_id INT NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                payment_date DATE NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(application_id) REFERENCES tenant_applications(application_id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS tenant_reviews(
                review_id INT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                landlord_id INT NOT NULL,
                property_id INT NOT NULL,
                rating INT NOT NULL,
                review_text TEXT NULL,
                would_recommend TINYINT(1) DEFAULT 1,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(tenant_id) REFERENCES users(user_id),
                FOREIGN KEY(landlord_id) REFERENCES users(user_id),
                FOREIGN KEY(property_id) REFERENCES properties(property_id)
            )""")
            conn.commit()
        finally:
            try: c.close(); conn.close()
            except Exception: pass

def run_schema_migrations():
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            migrations = [
                "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE properties ADD COLUMN image_path TEXT NULL",
                "ALTER TABLE properties ADD COLUMN is_available TINYINT(1) DEFAULT 1",
                "ALTER TABLE properties ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE properties ADD COLUMN deposit_required DECIMAL(12,2) DEFAULT 0",
                "ALTER TABLE tenant_applications ADD COLUMN employment_position VARCHAR(50) NULL",
                "ALTER TABLE tenant_applications ADD COLUMN number_of_dependents INT DEFAULT 0",
                "ALTER TABLE tenant_applications ADD COLUMN current_monthly_rent DECIMAL(12,2) DEFAULT 0",
                "ALTER TABLE tenant_applications ADD COLUMN household_notes TEXT NULL",
                "ALTER TABLE tenant_applications ADD COLUMN affordability_status VARCHAR(40) NULL",
                "ALTER TABLE tenant_applications ADD COLUMN affordability_comment TEXT NULL",
                "ALTER TABLE tenant_applications ADD COLUMN application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE payments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE tenant_reviews ADD COLUMN would_recommend TINYINT(1) DEFAULT 1",
                "ALTER TABLE tenant_reviews ADD COLUMN review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]
            for sql in migrations:
                try:
                    c.execute(sql); conn.commit()
                except Error:
                    pass
        finally:
            try: c.close(); conn.close()
            except Exception: pass

def ensure_tenant_application_columns():
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            migrations = [
                "ALTER TABLE tenant_applications ADD COLUMN employment_position VARCHAR(50) NULL",
                "ALTER TABLE tenant_applications ADD COLUMN number_of_dependents INT DEFAULT 0",
                "ALTER TABLE tenant_applications ADD COLUMN current_monthly_rent DECIMAL(12,2) DEFAULT 0",
                "ALTER TABLE tenant_applications ADD COLUMN household_notes TEXT NULL",
                "ALTER TABLE tenant_applications ADD COLUMN affordability_status VARCHAR(40) NULL",
                "ALTER TABLE tenant_applications ADD COLUMN affordability_comment TEXT NULL",
            ]
            for sql in migrations:
                try:
                    c.execute(sql); conn.commit()
                except Error:
                    pass
        finally:
            try: c.close(); conn.close()
            except Exception: pass

def ensure_messages_table():
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS messages(
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                message_text TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read TINYINT(1) DEFAULT 0,
                FOREIGN KEY(sender_id) REFERENCES users(user_id),
                FOREIGN KEY(receiver_id) REFERENCES users(user_id)
            )""")
            conn.commit()
        finally:
            try: c.close(); conn.close()
            except Exception: pass

ensure_database_exists()
ensure_core_tables()
run_schema_migrations()
ensure_tenant_application_columns()
ensure_messages_table()

def get_unread_count(user_id):
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=%s AND is_read=0", (user_id,))
            return c.fetchone()[0]
        except Error:
            return 0
        finally:
            c.close(); conn.close()
    return 0

def get_chat_partners(user_id):
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor(dictionary=True)
            c.execute("""SELECT DISTINCT u.user_id,u.username,u.full_name,u.user_type,
                (SELECT COUNT(*) FROM messages m2 WHERE m2.sender_id=u.user_id AND m2.receiver_id=%s AND m2.is_read=0) as unread
                FROM messages m JOIN users u ON (
                    CASE WHEN m.sender_id=%s THEN u.user_id=m.receiver_id
                    ELSE u.user_id=m.sender_id END)
                WHERE m.sender_id=%s OR m.receiver_id=%s
                ORDER BY (SELECT MAX(sent_at) FROM messages m3
                    WHERE (m3.sender_id=%s AND m3.receiver_id=u.user_id)
                       OR (m3.sender_id=u.user_id AND m3.receiver_id=%s)) DESC""",
                (user_id,user_id,user_id,user_id,user_id,user_id))
            return c.fetchall()
        except Error:
            return []
        finally:
            c.close(); conn.close()
    return []

def get_potential_chat_users(user_id, user_type):
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor(dictionary=True)
            if user_type == 'tenant':
                c.execute("""SELECT DISTINCT u.user_id,u.username,u.full_name,u.user_type
                    FROM tenant_applications a
                    JOIN properties p ON a.property_id=p.property_id
                    JOIN users u ON p.landlord_id=u.user_id
                    WHERE a.tenant_id=%s AND a.application_status='approved'""", (user_id,))
            else:
                c.execute("""SELECT DISTINCT u.user_id,u.username,u.full_name,u.user_type
                    FROM tenant_applications a
                    JOIN properties p ON a.property_id=p.property_id
                    JOIN users u ON a.tenant_id=u.user_id
                    WHERE p.landlord_id=%s AND a.application_status='approved'""", (user_id,))
            return c.fetchall()
        except Error:
            return []
        finally:
            c.close(); conn.close()
    return []

def get_messages(user_id, partner_id):
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor(dictionary=True)
            c.execute("""SELECT m.*,u.full_name FROM messages m
                JOIN users u ON m.sender_id=u.user_id
                WHERE (m.sender_id=%s AND m.receiver_id=%s)
                   OR (m.sender_id=%s AND m.receiver_id=%s)
                ORDER BY m.sent_at ASC""", (user_id,partner_id,partner_id,user_id))
            msgs = c.fetchall()
            c.execute("UPDATE messages SET is_read=1 WHERE sender_id=%s AND receiver_id=%s AND is_read=0", (partner_id,user_id))
            conn.commit()
            return msgs
        except Error:
            return []
        finally:
            c.close(); conn.close()
    return []

def send_message(sender_id, receiver_id, text):
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("INSERT INTO messages(sender_id,receiver_id,message_text) VALUES(%s,%s,%s)", (sender_id,receiver_id,text))
            conn.commit()
            return True
        except Error as e:
            st.error(f"Message failed: {e}")
            return False
        finally:
            c.close(); conn.close()
    return False

def messages_section(title="Messages"):
    st.markdown(f'<div class="sh">💬 {title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="ss">Communication opens after a tenant application has been accepted.</div>', unsafe_allow_html=True)
    uid = st.session_state.user_id
    existing = get_chat_partners(uid)
    potential = get_potential_chat_users(uid, st.session_state.user_type)
    existing_ids = {p['user_id'] for p in existing}
    contacts = existing + [{**p, 'unread': 0} for p in potential if p['user_id'] not in existing_ids]

    col_contacts, col_chat = st.columns([1, 2.4])
    with col_contacts:
        if not contacts:
            st.info("No accepted contacts yet.")
        for p in contacts:
            unread = p.get('unread', 0)
            selected = st.session_state.chat_partner == p['user_id']
            border = '#5b54f0' if selected else '#183060'
            badge = f" · {unread} unread" if unread else ""
            st.markdown(f"""<div style="background:var(--bg-card);border:1px solid {border};border-radius:10px;padding:0.7rem 0.8rem;margin-bottom:0.45rem;">
              <div style="font-family:'Syne',sans-serif;font-size:0.86rem;font-weight:700;color:#ddeaf8;">{p['full_name']}</div>
              <div style="font-size:0.68rem;color:#7a9cc4;text-transform:uppercase;">{p['user_type']}{badge}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open", key=f"chat_open_{p['user_id']}", use_container_width=True):
                st.session_state.chat_partner = p['user_id']; st.rerun()

    with col_chat:
        partner_id = st.session_state.chat_partner
        if not partner_id:
            st.markdown('<div class="chat-wrap" style="display:flex;align-items:center;justify-content:center;height:280px;color:#3a5880;">Select a contact to start chatting.</div>', unsafe_allow_html=True)
            return

        partner_name = "User"
        conn = get_db_connection()
        if conn:
            try:
                c = conn.cursor(dictionary=True)
                c.execute("SELECT full_name FROM users WHERE user_id=%s", (partner_id,))
                row = c.fetchone()
                if row: partner_name = row['full_name']
            finally:
                c.close(); conn.close()

        st.markdown(f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px 12px 0 0;padding:0.75rem 1rem;border-bottom:none;font-family:Syne,sans-serif;font-weight:700;color:#ddeaf8;">{partner_name}</div>', unsafe_allow_html=True)
        st.markdown('<div class="chat-wrap" style="border-radius:0;border-top:none;border-bottom:none;">', unsafe_allow_html=True)
        msgs = get_messages(uid, partner_id)
        if not msgs:
            st.markdown('<div style="text-align:center;color:#3a5880;padding:2rem 0;font-size:0.84rem;">No messages yet.</div>', unsafe_allow_html=True)
        for m in msgs:
            mine = m['sender_id'] == uid
            css_class = 'mine' if mine else 'theirs'
            ts = m['sent_at'].strftime('%d %b · %H:%M') if hasattr(m['sent_at'], 'strftime') else str(m['sent_at'])
            st.markdown(f"""<div class="msg {css_class}">
              <div class="msg-avatar"><img src="{avatar(m['full_name'])}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
              <div><div class="msg-bubble">{m['message_text']}</div><div class="msg-meta">{ts}</div></div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        with st.form(f"chat_form_{partner_id}", clear_on_submit=True):
            msg = st.text_input("", placeholder=f"Message {partner_name}...", label_visibility="collapsed")
            if st.form_submit_button("Send →") and msg.strip():
                send_message(uid, partner_id, msg.strip()); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════════
def landing_page():
    # HERO
    st.markdown(f"""
    <div class="hero">
      <div class="hero-bg" style="background-image:url('{IMG["hero_bg"]}');"></div>
      <div class="hero-overlay"></div>
      <div class="hero-body">
        <div class="hero-left">
          <div class="hero-badge">🇿🇼 AI-Powered · Zimbabwe Rental Market</div>
          <h1>Smarter Rentals.<br>Fairer Outcomes.<br><em>Zero Guesswork.</em></h1>
          <p>
            RentIQ uses machine learning to assess tenant risk and bridge the information
            asymmetry between landlords and tenants across Zimbabwe's rental market.
          </p>
        </div>
        <div class="hero-stats">
          <div class="hs"><div class="hs-num">94%</div><div class="hs-lbl">Accuracy</div></div>
          <div class="hs"><div class="hs-num">12s</div><div class="hs-lbl">Assessment</div></div>
          <div class="hs"><div class="hs-num">3×</div><div class="hs-lbl">Less Disputes</div></div>
          <div class="hs"><div class="hs-num">10+</div><div class="hs-lbl">Risk Signals</div></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # IMAGE MOSAIC
    st.markdown(f"""
    <div class="mosaic">
      <img src="{IMG['city']}" alt="Harare"/>
      <img src="{IMG['apartment']}" alt="Apartment"/>
      <img src="{IMG['house']}" alt="House"/>
      <img src="{IMG['commercial']}" alt="Commercial"/>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.35, 1], gap="large")

    with col_left:
        st.markdown('<div class="sh">How RentIQ Works</div>', unsafe_allow_html=True)
        st.markdown('<div class="ss">Three pillars powering transparent, data-driven rental decisions</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="fg">
          <div class="fc">
            <div class="fi">🧠</div>
            <h3>AI Risk Scoring</h3>
            <p>Gradient-boosted model analyses 10+ signals — income, credit, employment — producing an objective risk score in seconds.</p>
          </div>
          <div class="fc">
            <div class="fi">🏘️</div>
            <h3>Marketplace</h3>
            <p>Landlords list with photos. Tenants browse, filter by location and budget, then apply — all on one transparent platform.</p>
          </div>
          <div class="fc">
            <div class="fi">📊</div>
            <h3>Live Analytics</h3>
            <p>Track applications, risk distributions, and portfolio performance through real-time interactive charts.</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="position:relative;border-radius:14px;overflow:hidden;border:1px solid #183060;">
          <img src="{IMG['dashboard']}" style="width:100%;height:195px;object-fit:cover;display:block;filter:saturate(0.55) brightness(0.55) hue-rotate(190deg);"/>
          <div style="position:absolute;inset:0;display:flex;align-items:flex-end;padding:1rem 1.2rem;background:linear-gradient(transparent 40%,rgba(3,14,28,0.9));">
            <div>
              <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.9rem;color:#ddeaf8;">Live Analytics Dashboard</div>
              <div style="font-size:0.75rem;color:#7a9cc4;margin-top:2px;">Real-time risk distribution · Application trends · Portfolio metrics</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="sh">Access the Platform</div>', unsafe_allow_html=True)
        st.markdown('<div class="ss">Sign in or create a free account</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
            t1, t2 = st.tabs(["Sign In", "Create Account"])

            with t1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="your_username")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    if st.form_submit_button("Sign In →"):
                        ok, result = login_user(username, password)
                        if ok:
                            st.session_state.authenticated = True
                            st.session_state.user_id = result['user_id']
                            st.session_state.user_type = result['user_type']
                            st.session_state.username = result['username']
                            st.rerun()
                        else:
                            st.error(result)

            with t2:
                with st.form("register_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        ru = st.text_input("Username*")
                        re = st.text_input("Email*")
                        rp_in = st.text_input("Password*", type="password")
                    with c2:
                        rf = st.text_input("Full Name*")
                        rh = st.text_input("Phone")
                        rt = st.selectbox("I am a*", ["tenant", "landlord"])

                    if st.form_submit_button("Create Account →"):
                        if ru and re and rp_in and rf:
                            ok, msg = register_user(ru, rp_in, re, rf, rh, rt)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                        else:
                            st.warning("Fill all required fields.")

            st.markdown('</div>', unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sb-logo">RentIQ<span>Rental Risk Platform</span></div>', unsafe_allow_html=True)
        st.markdown('<hr class="sb-div">', unsafe_allow_html=True)
        st.markdown(f"""
        <img class="sb-av" src="{avatar(st.session_state.username)}" alt="av"/>
        <div class="sb-badge">
          <div class="sb-name">{st.session_state.username}</div>
          <div class="sb-type">{st.session_state.user_type}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.user_type == 'tenant':
            opts = ["🔍 Browse Properties","📝 Apply for Property","📋 My Applications","💳 Payment History"]
        else:
            opts = ["📊 Overview","🏘️ Manage Properties","📝 Applications","⭐ Tenant Reviews","📈 Analytics"]

        unread_count = get_unread_count(st.session_state.user_id)
        unread_dot = "  new" if unread_count else ""
        opts.append(f"Messages{unread_dot}")
        action = st.radio("Navigation", opts, label_visibility="collapsed")
        st.markdown('<hr class="sb-div">', unsafe_allow_html=True)
        if st.button("🚪 Sign Out"):
            for k in ['authenticated','user_id','user_type','username']:
                st.session_state[k] = False if k=='authenticated' else None
            st.session_state.chat_partner = None
            st.rerun()
        return action


# ══════════════════════════════════════════════════════════════════════════════
#  TENANT DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def tenant_dashboard(action):
    model, scaler, les, feature_names, model_info, feature_config = load_ml_model()
    st.markdown('<div class="pw">', unsafe_allow_html=True)

    # ── BROWSE ────────────────────────────────────────────────────────────────
    if "Browse" in action and 'selected_property' not in st.session_state:
        st.markdown('<div class="sh">🔍 Available Properties</div>', unsafe_allow_html=True)
        conn = get_db_connection()
        if conn:
            c = conn.cursor(dictionary=True)
            c.execute("SELECT p.*,u.full_name as landlord_name FROM properties p JOIN users u ON p.landlord_id=u.user_id WHERE p.is_available=TRUE")
            props = c.fetchall(); c.close(); conn.close()

            if props:
                st.markdown(f'<div class="ss">{len(props)} propert{"ies" if len(props)!=1 else "y"} available now</div>', unsafe_allow_html=True)
                cols = st.columns(3)
                for i, p in enumerate(props):
                    img = p.get('image_path') or p.get('property_image') or prop_img(p.get('property_type','apartment'))
                    with cols[i % 3]:
                        apply_key = f"ap_{p['property_id']}"
                        st.markdown(f"""
                        <div class="pcard">
                          <img class="pcard-img" src="{img}" alt="{p['property_name']}"/>
                          <div class="pcard-body">
                            <div class="pcard-type">{p['property_type'].upper()}</div>
                            <div class="pcard-name">{p['property_name']}</div>
                            <div class="pcard-loc">📍 {p.get('suburb','')}, {p['city']}</div>
                            <div class="pcard-row">
                              <div class="pcard-rent">ZWL {p['monthly_rent']:,.0f}<span>/mo</span></div>
                              <div class="pcard-beds">🛏 {p['bedrooms']} · 🚿 {p['bathrooms']}</div>
                            </div>
                          </div>
                          <div class="pcard-footer">
                            <div class="pcard-landlord">🏠 {p['landlord_name']}</div>
                            <div class="pcard-landlord">Deposit: ZWL {p['deposit_required']:,.0f}</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                        comp = {}  # Initialize empty comparison data for browse view
                        st.markdown(f"""
                        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:0.8rem;margin-top:0.6rem;">
                          <div style="font-size:0.68rem;color:#3a5880;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:5px;">Weighted Points</div>
                          <div style="font-size:0.72rem;color:#7a9cc4;line-height:1.55;">Affordability: {comp.get('affordability', 0)}/24</div>
                          <div style="font-size:0.72rem;color:#7a9cc4;line-height:1.55;">Credit: {comp.get('credit', 0)}/16</div>
                          <div style="font-size:0.72rem;color:#7a9cc4;line-height:1.55;">Debt: {comp.get('debt', 0)}/12</div>
                          <div style="font-size:0.72rem;color:#7a9cc4;line-height:1.55;">Income buffer: {comp.get('income_buffer', 0)}/12</div>
                          <div style="font-size:0.72rem;color:#7a9cc4;line-height:1.55;">Job: {comp.get('job_stability', 0)}/8</div>
                          <div style="font-size:0.72rem;color:#7a9cc4;line-height:1.55;">Late payments: {comp.get('late_payments', 0)}/7</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Apply Now →", key=apply_key, use_container_width=True):
                            st.session_state.selected_property = p; st.rerun()
            else:
                # No empty white box — show a rich placeholder
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;">
                  <img src="{IMG['city']}" style="width:100%;height:180px;object-fit:cover;filter:saturate(0.4) brightness(0.5) hue-rotate(195deg);display:block;"/>
                  <div style="padding:1.5rem;text-align:center;">
                    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ddeaf8;margin-bottom:0.4rem;">No Properties Listed Yet</div>
                    <div style="font-size:0.83rem;color:#7a9cc4;">Landlords haven't listed any available properties. Check back soon — new listings are added daily.</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── APPLY ─────────────────────────────────────────────────────────────────
    elif "Apply" in action or ("Browse" in action and 'selected_property' in st.session_state):
        if 'selected_property' not in st.session_state:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:1rem;">
              <img src="{IMG['apartment']}" style="width:100%;height:160px;object-fit:cover;filter:saturate(0.5) brightness(0.55) hue-rotate(190deg);display:block;"/>
              <div style="padding:1.2rem;">
                <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ddeaf8;margin-bottom:0.3rem;">No Property Selected</div>
                <div style="font-size:0.83rem;color:#7a9cc4;">Go to Browse Properties and click Apply on any listing to start your application.</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            prop = st.session_state.selected_property
            img  = prop.get('image_path') or prop.get('property_image') or prop_img(prop.get('property_type','apartment'))

            # Property banner with overlay text
            st.markdown(f"""
            <div style="position:relative;border-radius:16px;overflow:hidden;border:1px solid #183060;margin-bottom:1.2rem;">
              <img src="{img}" style="width:100%;height:220px;object-fit:cover;display:block;filter:brightness(0.65) saturate(0.7) hue-rotate(185deg);"/>
              <div style="position:absolute;inset:0;background:linear-gradient(transparent 20%,rgba(3,14,28,0.92));display:flex;align-items:flex-end;padding:1.4rem 1.6rem;">
                <div>
                  <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#ddeaf8;">{prop['property_name']}</div>
                  <div style="font-size:0.85rem;color:#7a9cc4;margin-top:4px;">📍 {prop.get('suburb','')}, {prop['city']} &nbsp;·&nbsp; <span style="color:#c8f542;font-weight:700;">ZWL {prop['monthly_rent']:,.0f}/mo</span></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Choose a Different Property", use_container_width=False):
                del st.session_state.selected_property
                st.rerun()

            with st.form("tenant_app"):
                c1, c2 = st.columns(2)
                with c1:
                    income = st.number_input("Monthly Salary / Income (ZWL)", min_value=0, value=50000)
                    emp_position = st.selectbox("Employment Information", ["Full time","Part time","Self employed","Unemployed","Student"])
                    emp_map = {"Full time":"employed","Part time":"employed","Self employed":"self_employed","Unemployed":"unemployed","Student":"student"}
                    emp = emp_map[emp_position]
                    yrs    = st.number_input("Years at Current Job / Business", min_value=0, value=0)
                    current_rent = st.number_input("Current Monthly Rent Paid (ZWL)", min_value=0, value=0)
                    r_hist = st.checkbox("Has Previous Rental History")
                    refs   = st.checkbox("Has References")
                with c2:
                    dependents = st.number_input("Number of Dependents", 0, 20, 0)
                    household_notes = st.text_area("Household Information", placeholder="Example: 2 children and 1 elderly parent", height=80)
                    credit = st.slider("Credit Score", 300, 850, 600)
                    debt   = st.slider("Debt-to-Income (%)", 0, 100, 30)
                    age    = st.number_input("Age", 18, 100, 30)
                    fam    = dependents + 1
                    late   = st.number_input("Prior Late Payments", 0, 50, 0)

                r2i  = (prop['monthly_rent']/income*100) if income > 0 else 100
                remaining_income = income - prop['monthly_rent']
                affordability_status = 'Sustainable' if r2i <= 33 and remaining_income > 0 else ('Manageable with caution' if r2i <= 50 and remaining_income > 0 else 'Not sustainable')
                affordability_comment = f"AI affordability check: rent consumes {r2i:.1f}% of salary; estimated balance after rent is ZWL {remaining_income:,.0f}."
                icon = '✅' if r2i < 33 else ('⚠️' if r2i < 50 else '🔴')
                st.info(f"Rent-to-Income Ratio: **{r2i:.1f}%** {icon}  ({'Healthy' if r2i<33 else 'Elevated' if r2i<50 else 'High — may affect approval'})")

                if st.form_submit_button("Submit Application →"):
                    td = {'monthly_income':income,'employment_status':emp,'years_at_current_job':yrs,
                          'employment_position':emp_position,
                          'previous_rental_history':int(r_hist),'has_references':int(refs),
                          'credit_score':credit,'debt_to_income_ratio':debt,'age':age,
                          'family_size':fam,'number_of_dependents':dependents,
                          'previous_late_payments':late,'current_monthly_rent':current_rent,
                          'property_monthly_rent':prop['monthly_rent'],'rent_to_income_ratio':r2i,
                          'remaining_income':remaining_income,
                          'income_after_rent_ratio':(remaining_income/income*100) if income > 0 else -100,
                          'property_type':prop['property_type'],
                          'affordability_status':affordability_status}
                    res = predict_tenant_risk(td, model, scaler, les, feature_names, model_info, feature_config)

                    rc1, rc2, rc3 = st.columns([1, 2, 1])
                    with rc1:
                        st.markdown(f'<div class="score-card"><div class="sc-num">{res["risk_score"]}</div><div class="sc-lbl">Risk Score / 100</div></div>', unsafe_allow_html=True)
                    with rc2:
                        st.markdown(rp(res['risk_category']), unsafe_allow_html=True)
                        st.markdown(f"<br><strong style='color:#ddeaf8;font-size:0.95rem;'>{res['recommendation']}</strong>", unsafe_allow_html=True)
                        # Score bar
                        pct = res['risk_score']
                        bar_color = '#34d399' if pct>=70 else ('#fbbf24' if pct>=40 else '#f87171')
                        st.markdown(f"""
                        <div style="margin-top:0.8rem;">
                          <div style="font-size:0.7rem;color:#3a5880;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">Score breakdown</div>
                          <div style="background:#183060;border-radius:6px;height:8px;overflow:hidden;">
                            <div style="width:{pct}%;height:100%;background:{bar_color};border-radius:6px;transition:width 0.5s;"></div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with rc3:
                        # Key signals
                        comp = res.get('score_components', {})
                        st.markdown(f"""
                        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:0.8rem;">
                          <div style="font-size:0.68rem;color:#3a5880;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:6px;">Key Signals</div>
                          <div style="font-size:0.78rem;color:#ddeaf8;margin-bottom:3px;">{'✅' if credit>600 else '⚠️'} Credit: {credit}</div>
                          <div style="font-size:0.78rem;color:#ddeaf8;margin-bottom:3px;">{'✅' if debt<40 else '⚠️'} Debt ratio: {debt}%</div>
                          <div style="font-size:0.78rem;color:#ddeaf8;margin-bottom:3px;">{'✅' if refs else '❌'} References</div>
                          <div style="font-size:0.78rem;color:#ddeaf8;">{'✅' if r_hist else '❌'} Rental history</div>
                        </div>
                        """, unsafe_allow_html=True)

                    conn = get_db_connection()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("""INSERT INTO tenant_applications
                            (property_id,tenant_id,employment_status,employment_position,monthly_income,years_at_current_job,
                             previous_rental_history,has_references,credit_score,risk_score,risk_category,application_status,
                             number_of_dependents,current_monthly_rent,household_notes,affordability_status,affordability_comment)
                            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (prop['property_id'],st.session_state.user_id,emp,emp_position,income,yrs,
                             int(r_hist),int(refs),credit,res['risk_score'],res['risk_category'],'pending',
                             dependents,current_rent,household_notes,affordability_status,affordability_comment))
                        conn.commit(); cur.close(); conn.close()
                        st.success("Application submitted successfully!")
                        del st.session_state.selected_property

    # ── MY APPLICATIONS ───────────────────────────────────────────────────────
    elif "Applications" in action:
        st.markdown('<div class="sh">📋 My Applications</div>', unsafe_allow_html=True)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT a.*,p.property_name,p.city,p.property_type,p.image_path,
                                  p.monthly_rent,u.full_name as landlord_name,u.user_id as landlord_id
                           FROM tenant_applications a
                           JOIN properties p ON a.property_id=p.property_id
                           JOIN users u ON p.landlord_id=u.user_id
                           WHERE a.tenant_id=%s ORDER BY a.application_date DESC""",
                        (st.session_state.user_id,))
            apps = cur.fetchall(); cur.close(); conn.close()

            if apps:
                # Summary row
                total   = len(apps)
                pending = sum(1 for a in apps if a['application_status']=='pending')
                approved= sum(1 for a in apps if a['application_status']=='approved')
                rejected= sum(1 for a in apps if a['application_status']=='rejected')
                mc1,mc2,mc3,mc4 = st.columns(4)
                mc1.metric("Total Applications", total)
                mc2.metric("Pending",  pending)
                mc3.metric("Approved", approved)
                mc4.metric("Rejected", rejected)
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

                for app in apps:
                    img = app.get('image_path') or prop_img(app.get('property_type','apartment'))
                    status_color = {'pending':'#fbbf24','approved':'#34d399','rejected':'#f87171'}.get(app['application_status'],'#7a9cc4')
                    st.markdown(f"""
                    <div class="app-card">
                      <img class="app-img" src="{img}" alt="prop"/>
                      <div>
                        <div class="app-field-lbl">Property</div>
                        <div class="app-field-val">{app['property_name']}</div>
                        <div style="font-size:0.75rem;color:#7a9cc4;">📍 {app['city']}</div>
                      </div>
                      <div>
                        <div class="app-field-lbl">Risk Assessment</div>
                        <div>{rp(app['risk_category'], app['risk_score'])}</div>
                        <div style="font-size:0.75rem;color:#7a9cc4;margin-top:3px;">Income: ZWL {app['monthly_income']:,.0f}</div>
                        <div style="font-size:0.75rem;color:#7a9cc4;">{app.get('employment_position') or app.get('employment_status')} · Dependents: {app.get('number_of_dependents',0)}</div>
                        <div style="font-size:0.75rem;color:#c8f542;">{app.get('affordability_status') or 'Affordability pending'}</div>
                      </div>
                      <div>
                        <div class="app-field-lbl">Landlord</div>
                        <div class="app-field-val">{app['landlord_name']}</div>
                        <div style="font-size:0.75rem;color:#7a9cc4;">{app['application_date'].strftime('%d %b %Y')}</div>
                      </div>
                      <div style="text-align:right;">
                        <div style="font-size:0.68rem;color:#3a5880;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Status</div>
                        <div style="font-family:'Syne',sans-serif;font-size:0.82rem;font-weight:700;color:{status_color};">{app['application_status'].upper()}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if app['application_status'] == 'approved':
                        if st.button("Message Landlord", key=f"msg_landlord_{app['application_id']}", use_container_width=True):
                            st.session_state.chat_partner = app['landlord_id']; st.rerun()
            else:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;">
                  <img src="{IMG['apartment']}" style="width:100%;height:160px;object-fit:cover;filter:saturate(0.4) brightness(0.5) hue-rotate(195deg);display:block;"/>
                  <div style="padding:1.4rem;text-align:center;">
                    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ddeaf8;margin-bottom:0.3rem;">No Applications Yet</div>
                    <div style="font-size:0.83rem;color:#7a9cc4;">Browse available properties and submit your first application to get started.</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── PAYMENT HISTORY ───────────────────────────────────────────────────────
    elif "Payment" in action:
        st.markdown('<div class="sh">💳 Payment History</div>', unsafe_allow_html=True)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT p.*,pr.property_name,pr.property_type,pr.image_path
                           FROM payments p
                           JOIN tenant_applications a ON p.application_id=a.application_id
                           JOIN properties pr ON a.property_id=pr.property_id
                           WHERE a.tenant_id=%s ORDER BY p.payment_date DESC""",
                        (st.session_state.user_id,))
            pays = cur.fetchall(); cur.close(); conn.close()

            if pays:
                df = pd.DataFrame(pays)
                total = df[df.payment_status=='completed']['amount'].sum()
                late  = len(df[df.payment_status=='late'])
                rate  = len(df[df.payment_status=='completed'])/len(df)*100
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Total Paid",    f"ZWL {total:,.0f}")
                c2.metric("Transactions",  len(df))
                c3.metric("Late Payments", late)
                c4.metric("On-time Rate",  f"{rate:.1f}%")
                col_chart, col_list = st.columns([2,1])
                with col_chart:
                    fig = dark_fig(px.bar(df, x='payment_date', y='amount', color='payment_status',
                        color_discrete_map={'completed':'#34d399','late':'#f87171','pending':'#fbbf24'},
                        title='Payment History by Date'))
                    st.plotly_chart(fig, use_container_width=True)
                with col_list:
                    st.markdown('<div class="ss" style="margin-top:0.3rem;">Recent Payments</div>', unsafe_allow_html=True)
                    for _, row in df.head(8).iterrows():
                        sc = {'completed':'#34d399','late':'#f87171','pending':'#fbbf24'}.get(row['payment_status'],'#7a9cc4')
                        p_img = row.get('image_path') or prop_img(row.get('property_type','apartment'))
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:0.7rem;background:var(--bg-card);border:1px solid var(--border);border-radius:9px;padding:0.65rem 0.8rem;margin-bottom:0.5rem;">
                          <img src="{p_img}" style="width:38px;height:30px;object-fit:cover;border-radius:6px;filter:brightness(0.65) hue-rotate(185deg);flex-shrink:0;"/>
                          <div style="flex:1;min-width:0;">
                            <div style="font-size:0.78rem;color:#ddeaf8;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row['property_name']}</div>
                            <div style="font-size:0.7rem;color:#7a9cc4;">{row['payment_date'].strftime('%d %b %Y') if hasattr(row['payment_date'],'strftime') else row['payment_date']}</div>
                          </div>
                          <div style="text-align:right;flex-shrink:0;">
                            <div style="font-family:'Syne',sans-serif;font-size:0.82rem;font-weight:700;color:{sc};">ZWL {row['amount']:,.0f}</div>
                            <div style="font-size:0.68rem;color:{sc};">{row['payment_status']}</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;">
                  <img src="{IMG['house']}" style="width:100%;height:160px;object-fit:cover;filter:saturate(0.4) brightness(0.5) hue-rotate(195deg);display:block;"/>
                  <div style="padding:1.4rem;text-align:center;">
                    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ddeaf8;margin-bottom:0.3rem;">No Payment Records</div>
                    <div style="font-size:0.83rem;color:#7a9cc4;">Payment history will appear here once you have an active tenancy agreement.</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    elif "Messages" in action:
        messages_section("Messages")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  LANDLORD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def landlord_dashboard(action):
    st.markdown('<div class="pw">', unsafe_allow_html=True)

    # ── OVERVIEW ──────────────────────────────────────────────────────────────
    if "Overview" in action:
        st.markdown('<div class="sh">📊 Portfolio Overview</div>', unsafe_allow_html=True)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT COUNT(*) as total,SUM(CASE WHEN is_available THEN 1 ELSE 0 END) as avail,AVG(monthly_rent) as avg_rent FROM properties WHERE landlord_id=%s",(st.session_state.user_id,))
            ps = cur.fetchone()
            cur.execute("""SELECT COUNT(*) as total,AVG(risk_score) as avg_risk,
                                  SUM(CASE WHEN application_status='pending' THEN 1 ELSE 0 END) as pending,
                                  SUM(CASE WHEN application_status='approved' THEN 1 ELSE 0 END) as approved
                           FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id
                           WHERE p.landlord_id=%s""",(st.session_state.user_id,))
            as_ = cur.fetchone()

            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Properties",        ps['total']       if ps  else 0)
            c2.metric("Available",          ps['avail']       if ps  else 0)
            c3.metric("Avg Rent (ZWL)",    f"{(ps['avg_rent'] or 0):,.0f}" if ps else "0")
            c4.metric("Pending Review",     as_['pending']    if as_ else 0)
            c5.metric("Avg Risk Score",    f"{(as_['avg_risk'] or 0):.0f}" if as_ else "—")

            # Charts row
            cur.execute("""SELECT risk_category,COUNT(*) as cnt FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY risk_category""",(st.session_state.user_id,))
            rd = cur.fetchall()
            cur.execute("""SELECT application_status,COUNT(*) as cnt FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY application_status""",(st.session_state.user_id,))
            sd = cur.fetchall()
            cur.execute("""SELECT p.property_name,p.image_path,p.property_type,p.monthly_rent,p.is_available,
                                  COUNT(a.application_id) as apps
                           FROM properties p LEFT JOIN tenant_applications a ON p.property_id=a.property_id
                           WHERE p.landlord_id=%s GROUP BY p.property_id ORDER BY apps DESC LIMIT 4""",(st.session_state.user_id,))
            top_props = cur.fetchall()
            cur.close(); conn.close()

            col_pie, col_status, col_props = st.columns([1,1,1.4])
            with col_pie:
                if rd:
                    df_r = pd.DataFrame(rd)
                    fig = dark_fig(px.pie(df_r, values='cnt', names='risk_category',
                        color='risk_category',
                        color_discrete_map={'low':'#34d399','medium':'#fbbf24','high':'#f87171'},
                        title='Risk Distribution', hole=0.5))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.markdown(f'<img src="{IMG["dashboard"]}" style="width:100%;height:250px;object-fit:cover;border-radius:12px;filter:saturate(0.4) brightness(0.5) hue-rotate(190deg);border:1px solid #183060;"/>', unsafe_allow_html=True)

            with col_status:
                if sd:
                    df_s = pd.DataFrame(sd)
                    fig2 = dark_fig(px.bar(df_s, x='application_status', y='cnt',
                        color='application_status',
                        color_discrete_map={'pending':'#fbbf24','approved':'#34d399','rejected':'#f87171'},
                        title='Applications by Status'))
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.markdown(f'<img src="{IMG["city"]}" style="width:100%;height:250px;object-fit:cover;border-radius:12px;filter:saturate(0.4) brightness(0.5) hue-rotate(190deg);border:1px solid #183060;"/>', unsafe_allow_html=True)

            with col_props:
                st.markdown('<div class="ss" style="margin-bottom:0.6rem;">Top Properties by Applications</div>', unsafe_allow_html=True)
                if top_props:
                    for p in top_props:
                        p_img = p.get('image_path') or prop_img(p.get('property_type','apartment'))
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:0.8rem;background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:0.7rem 0.9rem;margin-bottom:0.55rem;">
                          <img src="{p_img}" style="width:54px;height:42px;object-fit:cover;border-radius:7px;flex-shrink:0;filter:brightness(0.7) hue-rotate(185deg);"/>
                          <div style="flex:1;min-width:0;">
                            <div style="font-family:'Syne',sans-serif;font-size:0.85rem;font-weight:700;color:#ddeaf8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{p['property_name']}</div>
                            <div style="font-size:0.73rem;color:#7a9cc4;">ZWL {p['monthly_rent']:,.0f}/mo · {'🟢' if p['is_available'] else '🔴'} {'Available' if p['is_available'] else 'Rented'}</div>
                          </div>
                          <div style="text-align:right;flex-shrink:0;">
                            <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:#c8f542;">{p['apps']}</div>
                            <div style="font-size:0.68rem;color:#3a5880;">apps</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f'<img src="{IMG["harare1"]}" style="width:100%;height:250px;object-fit:cover;border-radius:12px;filter:saturate(0.4) brightness(0.5) hue-rotate(190deg);border:1px solid #183060;"/>', unsafe_allow_html=True)

    # ── MANAGE PROPERTIES ─────────────────────────────────────────────────────
    elif "Manage" in action or "Properties" in action:
        st.markdown('<div class="sh">🏘️ Manage Properties</div>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["➕ Add Property", "📋 My Properties"])

        with t1:
            col_form, col_prev = st.columns([1.2, 1])
            with col_form:
                with st.form("add_prop"):
                    c1,c2 = st.columns(2)
                    with c1:
                        pname  = st.text_input("Property Name*")
                        ptype  = st.selectbox("Type*", ["apartment","house","commercial","room"])
                        beds   = st.number_input("Bedrooms", 0, 20, 1)
                        baths  = st.number_input("Bathrooms", 0, 20, 1)
                    with c2:
                        rent   = st.number_input("Monthly Rent (ZWL)*", 0, value=5000)
                        dep    = st.number_input("Deposit (ZWL)", 0, value=5000)
                        city   = st.text_input("City*")
                        suburb = st.text_input("Suburb")
                    addr     = st.text_area("Full Address*", height=70)
                    img_path = st.text_input("Property Image URL",
                        placeholder="https://images.unsplash.com/... or leave blank for default",
                        help="Paste any public image URL — Unsplash, Google Photos, etc.")
                    if st.form_submit_button("Add Property →"):
                        if pname and rent and city and addr:
                            conn = get_db_connection()
                            if conn:
                                cur = conn.cursor()
                                cur.execute("""INSERT INTO properties(landlord_id,property_name,property_type,address,city,suburb,bedrooms,bathrooms,monthly_rent,deposit_required,image_path) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                    (st.session_state.user_id,pname,ptype,addr,city,suburb,beds,baths,rent,dep,img_path or None))
                                conn.commit(); cur.close(); conn.close()
                                st.success(f"'{pname}' added successfully!")
                        else:
                            st.warning("Fill all required fields.")
            with col_prev:
                # Show preview images for each type
                st.markdown('<div class="ss">Property type previews</div>', unsafe_allow_html=True)
                for ptype_k, label in [("apartment","Apartment"),("house","House"),("room","Room"),("commercial","Commercial")]:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.55rem;background:var(--bg-card);border:1px solid var(--border);border-radius:9px;padding:0.5rem 0.7rem;">
                      <img src="{IMG[ptype_k]}" style="width:64px;height:46px;object-fit:cover;border-radius:7px;filter:saturate(0.55) brightness(0.65) hue-rotate(185deg);flex-shrink:0;"/>
                      <div style="font-family:'Syne',sans-serif;font-size:0.85rem;font-weight:700;color:#ddeaf8;">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

        with t2:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT * FROM properties WHERE landlord_id=%s ORDER BY created_at DESC",(st.session_state.user_id,))
                props = cur.fetchall(); cur.close(); conn.close()
                if props:
                    cols = st.columns(3)
                    for i, p in enumerate(props):
                        img = p.get('image_path') or prop_img(p.get('property_type','apartment'))
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div class="pcard">
                              <img class="pcard-img" src="{img}" alt="{p['property_name']}"/>
                              <div class="pcard-body">
                                <div class="pcard-type">{p['property_type'].upper()} · {'🟢 AVAILABLE' if p['is_available'] else '🔴 RENTED'}</div>
                                <div class="pcard-name">{p['property_name']}</div>
                                <div class="pcard-loc">📍 {p.get('suburb','')}, {p['city']}</div>
                                <div class="pcard-row">
                                  <div class="pcard-rent">ZWL {p['monthly_rent']:,.0f}<span>/mo</span></div>
                                  <div class="pcard-beds">🛏 {p['bedrooms']} · 🚿 {p['bathrooms']}</div>
                                </div>
                              </div>
                              <div class="pcard-footer">
                                <div class="pcard-landlord">Deposit: ZWL {p['deposit_required']:,.0f}</div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("Toggle Availability", key=f"tog_{p['property_id']}", use_container_width=True):
                                conn2 = get_db_connection()
                                if conn2:
                                    c2 = conn2.cursor()
                                    c2.execute("UPDATE properties SET is_available=NOT is_available WHERE property_id=%s",(p['property_id'],))
                                    conn2.commit(); c2.close(); conn2.close(); st.rerun()
                else:
                    st.markdown(f"""
                    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;">
                      <img src="{IMG['harare1']}" style="width:100%;height:200px;object-fit:cover;filter:saturate(0.4) brightness(0.5) hue-rotate(195deg);display:block;"/>
                      <div style="padding:1.4rem;text-align:center;">
                        <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ddeaf8;margin-bottom:0.3rem;">No Properties Listed Yet</div>
                        <div style="font-size:0.83rem;color:#7a9cc4;">Use the Add Property tab to list your first property and start receiving tenant applications.</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── APPLICATIONS ──────────────────────────────────────────────────────────
    elif "Applications" in action:
        st.markdown('<div class="sh">📝 Tenant Applications</div>', unsafe_allow_html=True)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT a.*,u.full_name as tenant_name,u.email,u.phone,
                                  p.property_name,p.city,p.property_type,p.image_path
                           FROM tenant_applications a
                           JOIN properties p ON a.property_id=p.property_id
                           JOIN users u ON a.tenant_id=u.user_id
                           WHERE p.landlord_id=%s ORDER BY a.application_date DESC""",
                        (st.session_state.user_id,))
            apps = cur.fetchall(); cur.close(); conn.close()

            if apps:
                pending_apps = [a for a in apps if a['application_status']=='pending']
                other_apps   = [a for a in apps if a['application_status']!='pending']

                if pending_apps:
                    st.markdown(f'<div class="ss">{len(pending_apps)} pending · {len(other_apps)} resolved</div>', unsafe_allow_html=True)

                for app in apps:
                    img      = app.get('image_path') or prop_img(app.get('property_type','apartment'))
                    t_av     = avatar(app['tenant_name'])
                    sc       = {'pending':'#fbbf24','approved':'#34d399','rejected':'#f87171'}.get(app['application_status'],'#7a9cc4')

                    with st.expander(f"{'🕐' if app['application_status']=='pending' else '✅' if app['application_status']=='approved' else '❌'}  {app['tenant_name']}  ·  {app['property_name']}  ·  {app['application_date'].strftime('%d %b %Y')}"):
                        top_l, top_r = st.columns([3,1])
                        with top_l:
                            r1c1,r1c2,r1c3,r1c4 = st.columns(4)
                            with r1c1:
                                st.markdown(f'<img src="{t_av}" style="width:48px;height:48px;border-radius:50%;border:2px solid #234d8a;display:block;margin-bottom:4px;"/>', unsafe_allow_html=True)
                                st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:0.82rem;font-weight:700;color:#ddeaf8;">{app["tenant_name"]}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div style="font-size:0.72rem;color:#7a9cc4;">{app["email"]}</div>', unsafe_allow_html=True)
                            with r1c2:
                                st.markdown(f'<div class="app-field-lbl">Risk</div>{rp(app["risk_category"],app["risk_score"])}<br><div style="font-size:0.75rem;color:#7a9cc4;margin-top:3px;">Credit: {app["credit_score"]}</div>', unsafe_allow_html=True)
                            with r1c3:
                                st.markdown(f'<div class="app-field-lbl">Financials</div><div class="app-field-val">ZWL {app["monthly_income"]:,.0f}/mo</div><div style="font-size:0.75rem;color:#7a9cc4;">{app["employment_status"]} · {app["years_at_current_job"]}yrs</div>', unsafe_allow_html=True)
                            st.markdown(f'<div style="font-size:0.75rem;color:#7a9cc4;margin-top:0.35rem;">Dependents: {app.get("number_of_dependents",0)} · Current rent: ZWL {float(app.get("current_monthly_rent") or 0):,.0f}</div><div style="font-size:0.75rem;color:#c8f542;">{app.get("affordability_status") or "Affordability pending"}</div>', unsafe_allow_html=True)
                            with r1c4:
                                st.markdown(f'<div class="app-field-lbl">Contact</div><div class="app-field-val" style="font-size:0.8rem;">{app["phone"] or "—"}</div><div style="font-size:0.75rem;color:#7a9cc4;">{app["city"]}</div>', unsafe_allow_html=True)
                        with top_r:
                            st.markdown(f'<img src="{img}" style="width:100%;height:85px;object-fit:cover;border-radius:10px;border:1px solid #183060;filter:brightness(0.7) hue-rotate(185deg);display:block;"/>', unsafe_allow_html=True)
                            st.markdown(f'<div style="font-size:0.7rem;color:{sc};font-weight:700;text-transform:uppercase;margin-top:5px;text-align:center;">{app["application_status"]}</div>', unsafe_allow_html=True)

                        if app['application_status'] == 'pending':
                            ca,cb,_ = st.columns([1,1,2])
                            with ca:
                                if st.button("✅ Approve", key=f"apr_{app['application_id']}", use_container_width=True):
                                    conn2 = get_db_connection()
                                    if conn2:
                                        c2 = conn2.cursor()
                                        c2.execute("UPDATE tenant_applications SET application_status='approved' WHERE application_id=%s",(app['application_id'],))
                                        conn2.commit(); c2.close(); conn2.close(); st.success("Approved!"); st.rerun()
                            with cb:
                                if st.button("❌ Reject", key=f"rej_{app['application_id']}", use_container_width=True):
                                    conn2 = get_db_connection()
                                    if conn2:
                                        c2 = conn2.cursor()
                                        c2.execute("UPDATE tenant_applications SET application_status='rejected' WHERE application_id=%s",(app['application_id'],))
                                        conn2.commit(); c2.close(); conn2.close(); st.success("Rejected!"); st.rerun()
                        elif app['application_status'] == 'approved':
                            if st.button("Message Tenant", key=f"msg_tenant_{app['application_id']}", use_container_width=True):
                                st.session_state.chat_partner = app['tenant_id']; st.rerun()
            else:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;">
                  <img src="{IMG['harare2']}" style="width:100%;height:200px;object-fit:cover;filter:saturate(0.4) brightness(0.5) hue-rotate(195deg);display:block;"/>
                  <div style="padding:1.4rem;text-align:center;">
                    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ddeaf8;margin-bottom:0.3rem;">No Applications Received Yet</div>
                    <div style="font-size:0.83rem;color:#7a9cc4;">Once tenants apply to your properties, their applications will appear here with full risk assessments.</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── REVIEWS ───────────────────────────────────────────────────────────────
    elif "Reviews" in action:
        st.markdown('<div class="sh">⭐ Tenant Reviews</div>', unsafe_allow_html=True)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT r.*,u.full_name as tenant_name,p.property_name,p.image_path,p.property_type
                           FROM tenant_reviews r JOIN users u ON r.tenant_id=u.user_id
                           JOIN properties p ON r.property_id=p.property_id
                           WHERE r.landlord_id=%s ORDER BY r.review_date DESC""",(st.session_state.user_id,))
            reviews = cur.fetchall(); cur.close(); conn.close()

            if reviews:
                avg_rating = sum(r['rating'] for r in reviews)/len(reviews)
                recommends = sum(1 for r in reviews if r['would_recommend'])
                mc1,mc2,mc3 = st.columns(3)
                mc1.metric("Total Reviews",   len(reviews))
                mc2.metric("Average Rating",  f"{avg_rating:.1f} / 5")
                mc3.metric("Would Recommend", f"{recommends}/{len(reviews)}")

                for r in reviews:
                    img  = r.get('image_path') or prop_img(r.get('property_type','apartment'))
                    t_av = avatar(r['tenant_name'])
                    st.markdown(f"""
                    <div class="rev-card">
                      <img src="{t_av}" style="width:42px;height:42px;border-radius:50%;border:2px solid #183060;object-fit:cover;"/>
                      <div>
                        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:3px;">
                          <span style="font-family:'Syne',sans-serif;font-size:0.88rem;font-weight:700;color:#ddeaf8;">{r['tenant_name']}</span>
                          <span style="font-size:0.72rem;color:#3a5880;">·</span>
                          <span style="font-size:0.72rem;color:#7a9cc4;">{r['property_name']}</span>
                          <span style="font-size:0.72rem;color:#3a5880;margin-left:auto;">{'✅ Recommends' if r['would_recommend'] else '❌ No'}</span>
                        </div>
                        <div style="font-size:0.85rem;color:#fbbf24;margin-bottom:4px;">{'⭐'*int(r['rating'])}{'☆'*(5-int(r['rating']))}</div>
                        <div style="font-size:0.83rem;color:#7a9cc4;line-height:1.5;font-style:italic;">"{r['review_text']}"</div>
                      </div>
                      <img src="{img}" style="width:70px;height:54px;object-fit:cover;border-radius:8px;border:1px solid #183060;filter:brightness(0.65) hue-rotate(185deg);"/>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;">
                  <img src="{IMG['harare3']}" style="width:100%;height:180px;object-fit:cover;filter:saturate(0.4) brightness(0.5) hue-rotate(195deg);display:block;"/>
                  <div style="padding:1.4rem;text-align:center;">
                    <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#ddeaf8;margin-bottom:0.3rem;">No Reviews Yet</div>
                    <div style="font-size:0.83rem;color:#7a9cc4;">Tenant reviews will appear here after completed tenancy agreements.</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── ANALYTICS ─────────────────────────────────────────────────────────────
    elif "Analytics" in action:
        st.markdown('<div class="sh">📈 Analytics Dashboard</div>', unsafe_allow_html=True)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""SELECT DATE(application_date) as date,COUNT(*) as count FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY DATE(application_date) ORDER BY date""",(st.session_state.user_id,))
            trend = cur.fetchall()
            cur.execute("""SELECT risk_score,risk_category FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s""",(st.session_state.user_id,))
            scores = cur.fetchall()
            cur.execute("""SELECT p.property_name,COUNT(a.application_id) as apps,AVG(a.risk_score) as avg_risk FROM properties p LEFT JOIN tenant_applications a ON p.property_id=a.property_id WHERE p.landlord_id=%s GROUP BY p.property_id""",(st.session_state.user_id,))
            perf = cur.fetchall()
            cur.execute("""SELECT employment_status,COUNT(*) as cnt FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY employment_status""",(st.session_state.user_id,))
            emp_data = cur.fetchall()
            cur.close(); conn.close()

            if trend:
                df_t = pd.DataFrame(trend)
                fig  = dark_fig(px.area(df_t, x='date', y='count', title='Applications Over Time', color_discrete_sequence=['#5b54f0']))
                fig.update_traces(fillcolor='rgba(91,84,240,0.12)', line_color='#5b54f0')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(f'<img src="{IMG["dashboard"]}" style="width:100%;height:200px;object-fit:cover;border-radius:12px;filter:saturate(0.4) brightness(0.5) hue-rotate(190deg);border:1px solid #183060;margin-bottom:1rem;display:block;"/>', unsafe_allow_html=True)

            c1,c2,c3 = st.columns(3)
            with c1:
                if scores:
                    df2 = pd.DataFrame(scores)
                    fig2 = dark_fig(px.histogram(df2, x='risk_score', nbins=20, title='Risk Score Distribution', color_discrete_sequence=['#c8f542']))
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.markdown(f'<img src="{IMG["apartment"]}" style="width:100%;height:220px;object-fit:cover;border-radius:12px;filter:saturate(0.4) brightness(0.5) hue-rotate(190deg);border:1px solid #183060;"/>', unsafe_allow_html=True)
            with c2:
                if perf:
                    df3 = pd.DataFrame(perf)
                    fig3 = dark_fig(px.bar(df3, x='property_name', y='apps', title='Apps per Property', color='avg_risk', color_continuous_scale=[[0,'#34d399'],[0.5,'#fbbf24'],[1,'#f87171']]))
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.markdown(f'<img src="{IMG["house"]}" style="width:100%;height:220px;object-fit:cover;border-radius:12px;filter:saturate(0.4) brightness(0.5) hue-rotate(190deg);border:1px solid #183060;"/>', unsafe_allow_html=True)
            with c3:
                if emp_data:
                    df4 = pd.DataFrame(emp_data)
                    fig4 = dark_fig(px.pie(df4, values='cnt', names='employment_status', title='Employment Mix', hole=0.45, color_discrete_sequence=['#5b54f0','#22d3ee','#c8f542','#f87171']))
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.markdown(f'<img src="{IMG["commercial"]}" style="width:100%;height:220px;object-fit:cover;border-radius:12px;filter:saturate(0.4) brightness(0.5) hue-rotate(190deg);border:1px solid #183060;"/>', unsafe_allow_html=True)

    elif "Messages" in action:
        messages_section("Messages")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.authenticated:
        landing_page(); return
    action = render_sidebar()
    if   st.session_state.user_type == 'tenant':   tenant_dashboard(action)
    elif st.session_state.user_type == 'landlord': landlord_dashboard(action)

if __name__ == "__main__":
    main()
