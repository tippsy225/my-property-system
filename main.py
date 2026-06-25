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

st.set_page_config(page_title="RentIQ — Tenant Risk Platform", page_icon="🏙️", layout="wide", initial_sidebar_state="expanded")

IMG = {
    "city":       "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=1400&q=80",
    "dashboard":  "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&q=80",
    "apartment":  "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=700&q=80",
    "house":      "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=700&q=80",
    "commercial": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=700&q=80",
    "room":       "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=700&q=80",
    "harare1":    "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=700&q=80",
    "harare2":    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=700&q=80",
    "avatar_base":"https://ui-avatars.com/api/?background=1e3a6e&color=c8f542&bold=true&size=64&name=",
}
def prop_img(t): return IMG.get((t or "apartment").lower(), IMG["apartment"])
def av(name): return f"{IMG['avatar_base']}{(name or 'U').replace(' ','+')}"

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root{
  --d0:#030e1c;--d1:#061322;--d2:#0b1c35;--d3:#102240;--d4:#163055;
  --b0:#183060;--b1:#234d8a;
  --t1:#ddeaf8;--t2:#7a9cc4;--t3:#3a5880;
  --lime:#c8f542;--violet:#5b54f0;--cyan:#22d3ee;
  --low:#34d399;--low-bg:rgba(52,211,153,.13);
  --mid:#fbbf24;--mid-bg:rgba(251,191,36,.13);
  --high:#f87171;--high-bg:rgba(248,113,113,.13);
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:var(--d0)!important;color:var(--t1);}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:0!important;padding-bottom:2rem!important;padding-left:2.5rem!important;padding-right:2.5rem!important;max-width:100%!important;}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:var(--d0)}::-webkit-scrollbar-thumb{background:var(--b1);border-radius:3px}

[data-testid="stSidebar"]{background:var(--d0)!important;border-right:1px solid var(--b0)!important;}
[data-testid="stSidebar"] *{color:var(--t1)!important;}
[data-testid="stSidebarNav"]{display:none;}

.uni{background:var(--d0);color:var(--t3);font-size:.66rem;letter-spacing:.08em;text-align:center;padding:.4rem;text-transform:uppercase;border-bottom:1px solid var(--b0);margin-bottom:1.4rem;}
.uni strong{color:var(--lime);}

/* HERO */
.hero{background:linear-gradient(135deg,#030e1c 0%,#0b1c35 40%,#0d1f45 70%,#111b40 100%);border-radius:20px;border:1px solid var(--b0);padding:2.8rem 3.2rem 2.4rem;position:relative;overflow:hidden;margin-bottom:1.4rem;}
.hero::before{content:'';position:absolute;top:-20%;right:-5%;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(91,84,240,.28) 0%,transparent 65%);pointer-events:none;}
.hero::after{content:'';position:absolute;bottom:-30%;left:15%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(34,211,238,.1) 0%,transparent 65%);pointer-events:none;}
.hero-in{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:flex-start;gap:2rem;}
.badge{display:inline-block;background:rgba(200,245,66,.1);border:1px solid rgba(200,245,66,.3);color:var(--lime);padding:4px 14px;border-radius:100px;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;font-weight:600;margin-bottom:1.1rem;}
.hero h1{font-family:'Syne',sans-serif;font-weight:800;font-size:clamp(1.8rem,3.5vw,3.2rem);line-height:1.06;margin:0 0 .8rem;letter-spacing:-.02em;color:var(--t1);}
.hero h1 em{color:var(--lime);font-style:normal;}
.hero p{font-size:.95rem;color:var(--t2);line-height:1.7;font-weight:300;max-width:500px;margin:0;}
.stats-box{display:flex;border:1px solid var(--b0);border-radius:12px;overflow:hidden;background:rgba(3,14,28,.5);flex-shrink:0;}
.stat{padding:1rem 1.4rem;border-right:1px solid var(--b0);text-align:center;}
.stat:last-child{border-right:none;}
.stat-n{font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:var(--lime);line-height:1;}
.stat-l{font-size:.63rem;color:var(--t3);text-transform:uppercase;letter-spacing:.07em;margin-top:3px;}

/* TYPOGRAPHY */
.sh{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:var(--t1);margin-bottom:.2rem;}
.ss{font-size:.82rem;color:var(--t3);margin-bottom:.9rem;}
.page-title{font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;color:var(--t1);margin-bottom:.2rem;}
.page-sub{font-size:.85rem;color:var(--t3);margin-bottom:1.2rem;}

/* FEATURE GRID */
.fg{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.2rem;}
.fc{background:var(--d2);border:1px solid var(--b0);border-radius:13px;padding:1.3rem;transition:transform .2s,border-color .2s;}
.fc:hover{transform:translateY(-3px);border-color:var(--b1);}
.fi{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,var(--violet),var(--cyan));display:flex;align-items:center;justify-content:center;font-size:1.1rem;margin-bottom:.8rem;}
.fc h3{font-family:'Syne',sans-serif;font-size:.9rem;font-weight:700;margin:0 0 .35rem;color:var(--t1);}
.fc p{font-size:.8rem;color:var(--t2);line-height:1.6;margin:0;}

/* AUTH */
.auth-wrap{background:var(--d2);border:1px solid var(--b0);border-radius:16px;padding:1.6rem;}

/* INPUTS */
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stSelectbox>div>div,.stTextArea textarea{background:var(--d3)!important;border:1px solid var(--b1)!important;border-radius:9px!important;font-family:'DM Sans',sans-serif!important;font-size:.88rem!important;color:var(--t1)!important;}
.stTextInput>div>div>input:focus,.stTextArea textarea:focus{border-color:var(--violet)!important;box-shadow:0 0 0 3px rgba(91,84,240,.16)!important;}
label,.stSelectbox label,.stTextInput label,.stNumberInput label,.stCheckbox label,.stSlider label{color:var(--t2)!important;font-size:.8rem!important;}

/* BUTTONS */
.stButton>button{background:linear-gradient(135deg,var(--violet),#3730d4)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-family:'Syne',sans-serif!important;font-size:.82rem!important;font-weight:700!important;padding:.5rem 1.2rem!important;transition:opacity .15s,transform .15s!important;}
.stButton>button:hover{opacity:.86!important;transform:translateY(-1px)!important;}
.stFormSubmitButton>button{width:100%!important;background:linear-gradient(135deg,var(--lime),#a3e635)!important;color:var(--d0)!important;font-size:.88rem!important;padding:.65rem!important;}

/* METRICS */
[data-testid="metric-container"]{background:var(--d2)!important;border:1px solid var(--b0)!important;border-radius:12px!important;padding:.9rem 1.2rem!important;}
[data-testid="metric-container"] [data-testid="stMetricLabel"]{font-size:.67rem!important;text-transform:uppercase;letter-spacing:.07em;color:var(--t3)!important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Syne',sans-serif!important;font-size:1.65rem!important;font-weight:800!important;color:var(--lime)!important;}

/* RISK PILLS */
.rp{display:inline-flex;align-items:center;gap:5px;padding:3px 11px;border-radius:100px;font-size:.75rem;font-weight:600;}
.rp-low{background:var(--low-bg);color:var(--low);border:1px solid rgba(52,211,153,.28);}
.rp-mid{background:var(--mid-bg);color:var(--mid);border:1px solid rgba(251,191,36,.28);}
.rp-high{background:var(--high-bg);color:var(--high);border:1px solid rgba(248,113,113,.28);}

/* SCORE CARD */
.score-card{background:linear-gradient(145deg,#061322,#102240);border:1px solid var(--b1);border-radius:14px;padding:1.3rem;text-align:center;}
.sc-num{font-family:'Syne',sans-serif;font-size:3.2rem;font-weight:800;color:var(--lime);line-height:1;}
.sc-lbl{font-size:.68rem;color:var(--t3);text-transform:uppercase;letter-spacing:.09em;margin-top:4px;}

/* PROPERTY CARDS */
.pcard{background:var(--d2);border:1px solid var(--b0);border-radius:13px;overflow:hidden;margin-bottom:.9rem;transition:border-color .2s,box-shadow .2s;}
.pcard:hover{border-color:var(--b1);box-shadow:0 8px 32px rgba(0,0,0,.3);}
.pcard-body{padding:.85rem .95rem;}
.pcard-type{font-size:.66rem;color:var(--t3);text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px;}
.pcard-name{font-family:'Syne',sans-serif;font-size:.93rem;font-weight:700;color:var(--t1);margin-bottom:2px;}
.pcard-loc{font-size:.73rem;color:var(--t2);margin-bottom:.55rem;}
.pcard-row{display:flex;justify-content:space-between;align-items:center;}
.pcard-rent{font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:var(--lime);}
.pcard-rent span{font-size:.65rem;color:var(--t3);font-weight:400;}
.pcard-beds{font-size:.73rem;color:var(--t2);background:var(--d3);padding:2px 7px;border-radius:5px;border:1px solid var(--b0);}
.pcard-foot{padding:.5rem .95rem;border-top:1px solid var(--b0);display:flex;justify-content:space-between;}
.pcard-meta{font-size:.7rem;color:var(--t3);}

/* IMAGE BOX */
.ibox{border-radius:11px;overflow:hidden;border:1px solid var(--b0);margin-bottom:.1rem;}
.ibox-cap{background:var(--d2);padding:.3rem .65rem;border-top:1px solid var(--b0);font-family:'Syne',sans-serif;font-size:.7rem;font-weight:700;color:var(--lime);}

/* APP ROW */
.app-row{background:var(--d2);border:1px solid var(--b0);border-radius:11px;padding:.75rem .95rem;margin-bottom:.5rem;}
.app-row:hover{border-color:var(--b1);}
.afl{font-size:.65rem;color:var(--t3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px;}
.afv{font-size:.83rem;color:var(--t1);font-weight:500;}

/* EXPANDERS */
.stExpander{background:var(--d2)!important;border:1px solid var(--b0)!important;border-radius:12px!important;margin-bottom:.5rem!important;overflow:hidden;}
[data-testid="stExpander"] details summary p{color:var(--t1)!important;}
[data-testid="stMarkdownContainer"] p{color:var(--t2);font-size:.86rem;}
[data-testid="stMarkdownContainer"] strong{color:var(--t1);}

/* TABS */
.stTabs [data-baseweb="tab-list"]{gap:.25rem;background:transparent;border-bottom:1px solid var(--b0);}
.stTabs [data-baseweb="tab"]{font-family:'Syne',sans-serif;font-size:.8rem;font-weight:700;color:var(--t3)!important;background:transparent!important;border:none!important;padding:.5rem .95rem!important;}
.stTabs [aria-selected="true"]{color:var(--lime)!important;border-bottom:2px solid var(--lime)!important;}

/* SIDEBAR */
.sb-logo{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:var(--lime)!important;}
.sb-logo span{color:var(--t3)!important;font-weight:300;font-size:.68rem;display:block;margin-top:-2px;}
.sb-div{border:none;border-top:1px solid var(--b0);margin:.8rem 0;}
.sb-badge{background:rgba(91,84,240,.1);border:1px solid rgba(91,84,240,.22);border-radius:10px;padding:.65rem .85rem;margin-bottom:.8rem;}
.sb-name{font-family:'Syne',sans-serif;font-size:.88rem;font-weight:700;color:var(--lime)!important;}
.sb-type{font-size:.64rem;color:var(--t3)!important;text-transform:uppercase;letter-spacing:.09em;margin-top:2px;}
.sb-nav-hd{font-size:.6rem;color:var(--t3);text-transform:uppercase;letter-spacing:.1em;padding:.3rem .2rem 0;font-weight:600;}

/* FORMS / ALERTS */
[data-testid="stForm"]{background:var(--d2)!important;border:1px solid var(--b0)!important;border-radius:14px!important;padding:1.2rem!important;}
.stAlert,div[data-testid="stAlert"]{background:var(--d3)!important;border:1px solid var(--b1)!important;border-radius:10px!important;}
.stAlert p,.stAlert div{color:var(--t1)!important;}
.js-plotly-plot{border-radius:12px;overflow:hidden;border:1px solid var(--b0);}
hr{border-color:var(--b0)!important;}
[data-testid="stImage"] img{border-radius:10px;display:block;width:100%;}

/* CHAT BUBBLES */
.chat-wrap{background:var(--d2);border:1px solid var(--b0);border-radius:14px;padding:1rem;margin-bottom:.7rem;max-height:420px;overflow-y:auto;}
.msg{display:flex;gap:.7rem;margin-bottom:.9rem;align-items:flex-start;}
.msg.mine{flex-direction:row-reverse;}
.msg-bubble{max-width:72%;padding:.65rem .9rem;border-radius:14px;font-size:.84rem;line-height:1.55;}
.msg.theirs .msg-bubble{background:var(--d3);border:1px solid var(--b0);color:var(--t1);border-top-left-radius:3px;}
.msg.mine .msg-bubble{background:linear-gradient(135deg,var(--violet),#3730d4);color:#fff;border-top-right-radius:3px;}
.msg-meta{font-size:.62rem;color:var(--t3);margin-top:3px;}
.msg-avatar{width:32px;height:32px;border-radius:50%;overflow:hidden;flex-shrink:0;}
.chat-input-row{display:flex;gap:.5rem;margin-top:.7rem;}

/* ADMIN TABLE */
.adm-tbl{width:100%;border-collapse:collapse;font-size:.83rem;}
.adm-tbl th{background:var(--d3);color:var(--t3);font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;padding:.55rem .75rem;text-align:left;border-bottom:1px solid var(--b0);}
.adm-tbl td{padding:.55rem .75rem;border-bottom:1px solid var(--b0);color:var(--t1);vertical-align:middle;}
.adm-tbl tr:hover td{background:var(--d3);}

/* STATUS TAGS */
.tag{display:inline-block;padding:2px 9px;border-radius:100px;font-size:.7rem;font-weight:600;}
.tag-green{background:var(--low-bg);color:var(--low);border:1px solid rgba(52,211,153,.28);}
.tag-yellow{background:var(--mid-bg);color:var(--mid);border:1px solid rgba(251,191,36,.28);}
.tag-red{background:var(--high-bg);color:var(--high);border:1px solid rgba(248,113,113,.28);}
.tag-blue{background:rgba(91,84,240,.12);color:#a5b4fc;border:1px solid rgba(91,84,240,.28);}
</style>
""", unsafe_allow_html=True)

# ── UNIVERSITY STRIP ──────────────────────────────────────────────────────────
st.markdown('<div class="uni"><strong>Bindura University of Science Education</strong> &nbsp;·&nbsp; Faculty of Science &amp; Engineering &nbsp;·&nbsp; Dept. of Computer Science &nbsp;·&nbsp; <strong>B220637B</strong> — Muriro Tinaye L</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DB & SESSION HELPERS
# ══════════════════════════════════════════════════════════════════════════════
db_config={'host':'localhost','user':'root','password':'','database':'rental_risk_assessment', 'unix_socket':'/opt/lampp/var/mysql/mysql.sock'}
for k,v in [('authenticated',False),('user_id',None),('user_type',None),('username',None),('chat_partner',None)]:
    if k not in st.session_state: st.session_state[k]=v

def get_db():
    try: return mysql.connector.connect(**db_config)
    except Error as e: st.error(f"DB Error: {e}"); return None

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def register_user(u,pw,e,fn,ph,ut):
    conn=get_db()
    if conn:
        try:
            c=conn.cursor(); c.execute("INSERT INTO users(username,email,password_hash,full_name,phone,user_type) VALUES(%s,%s,%s,%s,%s,%s)",(u,e,hp(pw),fn,ph,ut))
            conn.commit(); return True,"Registration successful!"
        except Error as ex: return False,f"Failed: {ex}"
        finally: c.close(); conn.close()
    return False,"DB connection failed"

def login_user(u,pw):
    conn=get_db()
    if conn:
        try:
            c=conn.cursor(dictionary=True); c.execute("SELECT * FROM users WHERE username=%s AND password_hash=%s",(u,hp(pw)))
            r=c.fetchone(); return (True,r) if r else (False,"Invalid credentials")
        except Error as ex: return False,f"Error: {ex}"
        finally: c.close(); conn.close()
    return False,"DB connection failed"

@st.cache_resource
def load_model():
    try: return joblib.load('models/best_model.pkl'),joblib.load('models/scaler.pkl'),joblib.load('models/label_encoders.pkl')
    except: return None,None,None

def predict(data,model,scaler,les):
    if model is None: return {'risk_score':50,'risk_category':'medium','recommendation':'Model unavailable'}
    try:
        f=pd.DataFrame([data])
        for col,le in les.items():
            if col in f.columns:
                try: f[col]=le.transform(f[col])
                except: f[col]=-1
        req=['monthly_income','years_at_current_job','previous_rental_history','has_references','credit_score','debt_to_income_ratio','age','family_size','previous_late_payments','rent_to_income_ratio']
        for x in req:
            if x not in f.columns: f[x]=0
        prob=model.predict_proba(scaler.transform(f[req]))[0][1]; s=round(100-prob*100,2)
        if s>=70: cat,rec='low','✅ Approve — low-risk applicant'
        elif s>=40: cat,rec='medium','⚠️ Consider with higher deposit or guarantor'
        else: cat,rec='high','❌ Reject or require significant guarantees'
        return {'risk_score':s,'risk_category':cat,'recommendation':rec}
    except Exception as ex: return {'risk_score':50,'risk_category':'medium','recommendation':f'Error: {ex}'}

# ── RENDER HELPERS ─────────────────────────────────────────────────────────────
def rp(cat,score=None):
    css={'low':'rp-low','medium':'rp-mid','high':'rp-high'}
    lbl={'low':'Low Risk','medium':'Medium Risk','high':'High Risk'}
    c=cat.lower() if cat and cat.lower() in css else 'medium'
    s=f" · {score}/100" if score is not None else ""
    return f'<span class="rp {css[c]}">● {lbl[c]}{s}</span>'

def tag(txt,kind='blue'):
    return f'<span class="tag tag-{kind}">{txt}</span>'

def dfig(fig):
    fig.update_layout(plot_bgcolor='#0b1c35',paper_bgcolor='#0b1c35',font=dict(family='DM Sans',color='#7a9cc4'),
        title_font=dict(family='Syne',color='#ddeaf8'),xaxis=dict(gridcolor='#183060',zerolinecolor='#183060'),
        yaxis=dict(gridcolor='#183060',zerolinecolor='#183060'),legend=dict(bgcolor='#102240',bordercolor='#183060'),
        margin=dict(l=14,r=14,t=42,b=14))
    return fig

def simg(url,w=None):
    try:
        if w is None: st.image(url,width='stretch')
        else: st.image(url,width=w)
    except: pass

def ibox(url,caption=None):
    st.markdown('<div class="ibox">',unsafe_allow_html=True)
    simg(url)
    if caption: st.markdown(f'<div class="ibox-cap">{caption}</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

def empty_state(img_url,title,desc):
    c1,c2=st.columns([1,2])
    with c1: simg(img_url)
    with c2: st.markdown(f'<div style="padding:.8rem 0;"><div style="font-family:Syne,sans-serif;font-size:1.05rem;font-weight:700;color:#ddeaf8;margin-bottom:.4rem;">{title}</div><div style="font-size:.83rem;color:#7a9cc4;line-height:1.6;">{desc}</div></div>',unsafe_allow_html=True)

def pcard(p,key=None,show_apply=False):
    img_url=p.get('image_path') or prop_img(p.get('property_type','apartment'))
    st.markdown('<div class="pcard">',unsafe_allow_html=True)
    simg(img_url)
    st.markdown(f"""<div class="pcard-body">
      <div class="pcard-type">{(p.get('property_type') or 'property').upper()}</div>
      <div class="pcard-name">{p.get('property_name','—')}</div>
      <div class="pcard-loc">📍 {p.get('suburb','')}, {p.get('city','')}</div>
      <div class="pcard-row">
        <div class="pcard-rent">ZWL {p.get('monthly_rent',0):,.0f}<span>/mo</span></div>
        <div class="pcard-beds">🛏 {p.get('bedrooms',0)} · 🚿 {p.get('bathrooms',0)}</div>
      </div></div>
    <div class="pcard-foot">
      <div class="pcard-meta">🏠 {p.get('landlord_name','')}</div>
      <div class="pcard-meta">Dep: ZWL {p.get('deposit_required',0):,.0f}</div>
    </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
    if show_apply and key:
        if st.button("Apply Now →",key=key,width='stretch'):
            st.session_state.selected_property=p; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# CHAT MODULE (shared by tenant + landlord)
# ══════════════════════════════════════════════════════════════════════════════
def ensure_chat_table():
    conn=get_db()
    if conn:
        try:
            c=conn.cursor()
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
        except: pass
        finally: c.close(); conn.close()

def ensure_payment_table():
    conn=get_db()
    if conn:
        try:
            c=conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS payments(
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                application_id INT NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                payment_type ENUM('rent','deposit','other') DEFAULT 'rent',
                payment_method ENUM('cash','ecocash','bank_transfer','other') DEFAULT 'cash',
                payment_status ENUM('pending','completed','late','failed') DEFAULT 'pending',
                due_date DATE,
                payment_date DATE,
                notes TEXT,
                recorded_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(application_id) REFERENCES tenant_applications(application_id)
            )""")
            conn.commit()
            # Migrate: add missing columns to existing payments table
            migrations = [
                "ALTER TABLE payments ADD COLUMN IF NOT EXISTS due_date DATE",
                "ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_date DATE",
                "ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_type ENUM('rent','deposit','other') DEFAULT 'rent'",
                "ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_method ENUM('cash','ecocash','bank_transfer','other') DEFAULT 'cash'",
                "ALTER TABLE payments ADD COLUMN IF NOT EXISTS notes TEXT",
                "ALTER TABLE payments ADD COLUMN IF NOT EXISTS recorded_by INT",
            ]
            for sql in migrations:
                try: c.execute(sql); conn.commit()
                except: pass
        except: pass
        finally: c.close(); conn.close()

def ensure_review_table():
    conn=get_db()
    if conn:
        try:
            c=conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS tenant_reviews(
                review_id INT AUTO_INCREMENT PRIMARY KEY,
                tenant_id INT NOT NULL,
                landlord_id INT NOT NULL,
                property_id INT NOT NULL,
                rating INT NOT NULL,
                review_text TEXT,
                would_recommend TINYINT(1) DEFAULT 1,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(tenant_id) REFERENCES users(user_id),
                FOREIGN KEY(landlord_id) REFERENCES users(user_id),
                FOREIGN KEY(property_id) REFERENCES properties(property_id)
            )""")
            conn.commit()
        except: pass
        finally: c.close(); conn.close()

def ensure_tenant_application_columns():
    """Adds the extended affordability fields without breaking older databases."""
    conn=get_db()
    if conn:
        try:
            c=conn.cursor()
            migrations=[
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
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            try: c.close(); conn.close()
            except Exception: pass

ensure_chat_table()
ensure_payment_table()
ensure_review_table()
ensure_tenant_application_columns()

def get_chat_partners(user_id):
    conn=get_db()
    if conn:
        try:
            c=conn.cursor(dictionary=True)
            c.execute("""SELECT DISTINCT u.user_id,u.username,u.full_name,u.user_type,
                (SELECT COUNT(*) FROM messages m2 WHERE m2.sender_id=u.user_id AND m2.receiver_id=%s AND m2.is_read=0) as unread
                FROM messages m JOIN users u ON (
                    CASE WHEN m.sender_id=%s THEN u.user_id=m.receiver_id
                    ELSE u.user_id=m.sender_id END)
                WHERE m.sender_id=%s OR m.receiver_id=%s
                ORDER BY (SELECT MAX(sent_at) FROM messages m3 WHERE (m3.sender_id=%s AND m3.receiver_id=u.user_id) OR (m3.sender_id=u.user_id AND m3.receiver_id=%s)) DESC""",
                (user_id,user_id,user_id,user_id,user_id,user_id))
            return c.fetchall()
        except: return []
        finally: c.close(); conn.close()
    return []

def get_messages(user_id,partner_id):
    conn=get_db()
    if conn:
        try:
            c=conn.cursor(dictionary=True)
            c.execute("""SELECT m.*,u.username,u.full_name FROM messages m JOIN users u ON m.sender_id=u.user_id
                WHERE (m.sender_id=%s AND m.receiver_id=%s) OR (m.sender_id=%s AND m.receiver_id=%s)
                ORDER BY m.sent_at ASC""",(user_id,partner_id,partner_id,user_id))
            msgs=c.fetchall()
            c.execute("UPDATE messages SET is_read=1 WHERE sender_id=%s AND receiver_id=%s AND is_read=0",(partner_id,user_id))
            conn.commit(); return msgs
        except: return []
        finally: c.close(); conn.close()
    return []

def send_message(sender_id,receiver_id,text):
    conn=get_db()
    if conn:
        try:
            c=conn.cursor(); c.execute("INSERT INTO messages(sender_id,receiver_id,message_text) VALUES(%s,%s,%s)",(sender_id,receiver_id,text))
            conn.commit(); return True
        except: return False
        finally: c.close(); conn.close()
    return False

def get_potential_chat_users(user_id, user_type):
    """Get users this person can chat with based on relationships"""
    conn=get_db()
    if conn:
        try:
            c=conn.cursor(dictionary=True)
            if user_type=='tenant':
                # Landlords whose properties tenant has approved/accepted applications only
                c.execute("""SELECT DISTINCT u.user_id,u.username,u.full_name,u.user_type
                    FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id
                    JOIN users u ON p.landlord_id=u.user_id
                    WHERE a.tenant_id=%s AND a.application_status='approved'""",(user_id,))
            elif user_type=='landlord':
                # Tenants whose applications were accepted by the landlord
                c.execute("""SELECT DISTINCT u.user_id,u.username,u.full_name,u.user_type
                    FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id
                    JOIN users u ON a.tenant_id=u.user_id
                    WHERE p.landlord_id=%s AND a.application_status='approved'""",(user_id,))
            else:
                c.execute("SELECT user_id,username,full_name,user_type FROM users WHERE user_id!=%s",(user_id,))
            return c.fetchall()
        except: return []
        finally: c.close(); conn.close()
    return []

def chat_section(title="💬 Messages"):
    st.markdown(f'<div class="page-title">{title}</div><div class="page-sub">Real-time messaging between tenants and landlords</div>',unsafe_allow_html=True)
    uid=st.session_state.user_id; utype=st.session_state.user_type

    # Get all partners (existing + potential)
    existing=get_chat_partners(uid)
    potential=get_potential_chat_users(uid,utype)
    existing_ids={p['user_id'] for p in existing}
    new_contacts=[p for p in potential if p['user_id'] not in existing_ids]
    all_contacts=existing+[{**p,'unread':0} for p in new_contacts]

    col_contacts,col_chat=st.columns([1,2.5])

    with col_contacts:
        st.markdown('<div class="ss">Contacts</div>',unsafe_allow_html=True)
        if not all_contacts:
            st.markdown('<div style="font-size:.82rem;color:#3a5880;padding:.5rem 0;">No contacts yet. Apply to a property or receive an application to start chatting.</div>',unsafe_allow_html=True)
        for p in all_contacts:
            unread=p.get('unread',0)
            selected=st.session_state.chat_partner==p['user_id']
            bg='#163055' if selected else '#0b1c35'
            border='#5b54f0' if selected else '#183060'
            badge=f'<span style="background:#c8f542;color:#030e1c;border-radius:100px;padding:1px 7px;font-size:.65rem;font-weight:800;margin-left:4px;">{unread}</span>' if unread else ''
            st.markdown(f"""<div style="background:{bg};border:1px solid {border};border-radius:10px;padding:.6rem .8rem;margin-bottom:.4rem;cursor:pointer;">
              <div style="font-family:Syne,sans-serif;font-size:.83rem;font-weight:700;color:#ddeaf8;">{p['full_name']}{badge}</div>
              <div style="font-size:.66rem;color:#3a5880;text-transform:uppercase;letter-spacing:.06em;">{p['user_type']}</div>
            </div>""",unsafe_allow_html=True)
            if st.button("Open",key=f"chat_open_{p['user_id']}",width='stretch'):
                st.session_state.chat_partner=p['user_id']; st.rerun()

    with col_chat:
        partner_id=st.session_state.chat_partner
        if not partner_id:
            st.markdown('<div class="chat-wrap" style="display:flex;align-items:center;justify-content:center;height:280px;">',unsafe_allow_html=True)
            st.markdown('<div style="text-align:center;color:#3a5880;"><div style="font-size:2rem;margin-bottom:.5rem;">💬</div><div style="font-family:Syne,sans-serif;font-size:.9rem;font-weight:700;">Select a contact to start chatting</div></div>',unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)
        else:
            # Get partner info
            conn=get_db()
            partner_name="User"
            if conn:
                try:
                    c=conn.cursor(dictionary=True); c.execute("SELECT full_name,user_type FROM users WHERE user_id=%s",(partner_id,))
                    pinfo=c.fetchone(); partner_name=pinfo['full_name'] if pinfo else "User"
                except: pass
                finally: c.close(); conn.close()

            st.markdown(f'<div style="background:var(--d2);border:1px solid var(--b0);border-radius:12px 12px 0 0;padding:.7rem 1rem;border-bottom:none;"><div style="font-family:Syne,sans-serif;font-size:.9rem;font-weight:700;color:#ddeaf8;">{partner_name}</div></div>',unsafe_allow_html=True)
            msgs=get_messages(uid,partner_id)
            st.markdown('<div class="chat-wrap" style="border-radius:0 0 0 0;border-top:none;border-bottom:none;">',unsafe_allow_html=True)
            if not msgs:
                st.markdown('<div style="text-align:center;color:#3a5880;padding:2rem 0;font-size:.84rem;">No messages yet. Say hello! 👋</div>',unsafe_allow_html=True)
            for m in msgs:
                is_mine=m['sender_id']==uid
                css_class='mine' if is_mine else 'theirs'
                ts=m['sent_at'].strftime('%d %b · %H:%M') if hasattr(m['sent_at'],'strftime') else str(m['sent_at'])
                av_url=av(m['full_name'])
                st.markdown(f"""<div class="msg {css_class}">
                  <div class="msg-avatar"><img src="{av_url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
                  <div>
                    <div class="msg-bubble">{m['message_text']}</div>
                    <div class="msg-meta">{ts}</div>
                  </div>
                </div>""",unsafe_allow_html=True)
            st.markdown('</div>',unsafe_allow_html=True)
            # Input row
            with st.form(f"chat_form_{partner_id}",clear_on_submit=True):
                msg_in=st.text_input("",placeholder=f"Message {partner_name}…",label_visibility="collapsed")
                if st.form_submit_button("Send →") and msg_in.strip():
                    send_message(uid,partner_id,msg_in.strip()); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════════
def landing_page():
    st.markdown("""
    <div class="hero"><div class="hero-in">
      <div>
        <div class="badge">🇿🇼 AI-Powered · Zimbabwe Rental Market</div>
        <h1>Smarter Rentals.<br>Fairer Outcomes.<br><em>Zero Guesswork.</em></h1>
        <p>RentIQ uses machine learning to assess tenant risk and bridge the information asymmetry between landlords and tenants across Zimbabwe's rental market.</p>
      </div>
      <div class="stats-box">
        <div class="stat"><div class="stat-n">94%</div><div class="stat-l">Accuracy</div></div>
        <div class="stat"><div class="stat-n">12s</div><div class="stat-l">Assessment</div></div>
        <div class="stat"><div class="stat-n">3×</div><div class="stat-l">Less Disputes</div></div>
        <div class="stat"><div class="stat-n">10+</div><div class="stat-l">Risk Signals</div></div>
      </div>
    </div></div>""",unsafe_allow_html=True)

    mc1,mc2,mc3=st.columns([2,1,1])
    with mc1: ibox(IMG["city"],"📍 Harare, Zimbabwe")
    with mc2: ibox(IMG["apartment"],"🏢 Apartments")
    with mc3: ibox(IMG["house"],"🏠 Houses")
    st.markdown("<div style='height:.5rem'></div>",unsafe_allow_html=True)

    col_l,col_r=st.columns([1.4,1])
    with col_l:
        st.markdown('<div class="sh">How RentIQ Works</div>',unsafe_allow_html=True)
        st.markdown('<div class="ss">Three pillars powering transparent, data-driven rental decisions</div>',unsafe_allow_html=True)
        st.markdown("""<div class="fg">
          <div class="fc"><div class="fi">🧠</div><h3>AI Risk Scoring</h3><p>Gradient-boosted model analyses 10+ signals — income, credit, employment — producing an objective score in 12 seconds.</p></div>
          <div class="fc"><div class="fi">🏘️</div><h3>Marketplace</h3><p>Landlords list with photos. Tenants browse and apply — all in one transparent platform serving Zimbabwe.</p></div>
          <div class="fc"><div class="fi">💬</div><h3>In-App Chat</h3><p>Tenants and landlords communicate directly — no phone calls needed, full message history retained.</p></div>
        </div>""",unsafe_allow_html=True)
        di1,di2,di3=st.columns([2,1,1])
        with di1: ibox(IMG["dashboard"],"📊 Analytics Dashboard")
        with di2: ibox(IMG["commercial"],"🏢 Commercial")
        with di3: ibox(IMG["room"],"🛏 Rooms")

    with col_r:
        st.markdown('<div class="sh">Access the Platform</div>',unsafe_allow_html=True)
        st.markdown('<div class="ss">Sign in or create a free account to get started</div>',unsafe_allow_html=True)
        st.markdown('<div class="auth-wrap">',unsafe_allow_html=True)
        t1,t2=st.tabs(["Sign In","Create Account"])
        with t1:
            with st.form("lf"):
                un=st.text_input("Username",placeholder="your_username")
                pw=st.text_input("Password",type="password",placeholder="••••••••")
                if st.form_submit_button("Sign In →"):
                    ok,res=login_user(un,pw)
                    if ok:
                        st.session_state.authenticated=True; st.session_state.user_id=res['user_id']
                        st.session_state.user_type=res['user_type']; st.session_state.username=res['username']
                        st.success("Welcome back!"); st.rerun()
                    else: st.error(res)
        with t2:
            with st.form("rf"):
                c1,c2=st.columns(2)
                with c1: ru=st.text_input("Username*"); re=st.text_input("Email*"); rp_=st.text_input("Password*",type="password")
                with c2: rfn=st.text_input("Full Name*"); rph=st.text_input("Phone"); rt=st.selectbox("I am a*",["tenant","landlord","admin"])
                if st.form_submit_button("Create Account →"):
                    if ru and re and rp_ and rfn:
                        ok,msg=register_user(ru,rp_,re,rfn,rph,rt); st.success(msg) if ok else st.error(msg)
                    else: st.warning("Fill all required fields.")
        st.markdown('</div>',unsafe_allow_html=True)
        st.markdown("<div style='height:.5rem'></div>",unsafe_allow_html=True)
        ga,gb=st.columns(2)
        with ga: ibox(IMG["apartment"],"🏢 Apartments")
        with gb: ibox(IMG["house"],"🏠 Houses")


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sb-logo">RentIQ<span>Rental Risk Platform</span></div>',unsafe_allow_html=True)
        st.markdown('<hr class="sb-div">',unsafe_allow_html=True)
        try: st.image(av(st.session_state.username),width=36)
        except: pass
        st.markdown(f'<div class="sb-badge"><div class="sb-name">{st.session_state.username}</div><div class="sb-type">{st.session_state.user_type}</div></div>',unsafe_allow_html=True)

        # Get unread count
        uid=st.session_state.user_id
        unread_count=0
        conn=get_db()
        if conn:
            try:
                c=conn.cursor(); c.execute("SELECT COUNT(*) FROM messages WHERE receiver_id=%s AND is_read=0",(uid,))
                unread_count=c.fetchone()[0]
            except: pass
            finally: c.close(); conn.close()

        if st.session_state.user_type=='tenant':
            opts=["🔍 Browse Properties","📝 Apply for Property","📋 My Applications",
                  "💳 My Payments","⭐ Write a Review",f"💬 Messages{'  🔴' if unread_count else ''}"]
        elif st.session_state.user_type=='landlord':
            opts=["📊 Overview","🏘️ Manage Properties","📝 Applications",
                  "💳 Manage Payments","⭐ Tenant Reviews","📈 Analytics",f"💬 Messages{'  🔴' if unread_count else ''}"]
        else:  # admin
            opts=["🛡️ Dashboard","👥 Users","🏘️ Properties","📝 Applications","💳 Payments","📈 Analytics",f"💬 Messages{'  🔴' if unread_count else ''}"]

        action=st.radio("Nav",opts,label_visibility="collapsed")
        st.markdown('<hr class="sb-div">',unsafe_allow_html=True)
        if st.button("🚪 Sign Out"):
            for k in ['authenticated','user_id','user_type','username','chat_partner','selected_property']:
                st.session_state[k]=False if k=='authenticated' else None
            st.rerun()
        return action


# ══════════════════════════════════════════════════════════════════════════════
# TENANT DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def tenant_dashboard(action):
    model,scaler,les=load_model()
    uid=st.session_state.user_id

    # ── BROWSE ────────────────────────────────────────────────────────────────
    if "Browse" in action:
        st.markdown('<div class="page-title">🔍 Available Properties</div>',unsafe_allow_html=True)
        conn=get_db()
        if conn:
            c=conn.cursor(dictionary=True)
            c.execute("SELECT p.*,u.full_name as landlord_name FROM properties p JOIN users u ON p.landlord_id=u.user_id WHERE p.is_available=TRUE")
            props=c.fetchall(); c.close(); conn.close()
            if props:
                st.markdown(f'<div class="ss">{len(props)} propert{"ies" if len(props)!=1 else "y"} listed across Zimbabwe</div>',unsafe_allow_html=True)
                cols=st.columns(3)
                for i,p in enumerate(props):
                    with cols[i%3]: pcard(p,key=f"ap_{p['property_id']}",show_apply=True)
            else:
                empty_state(IMG["city"],"No Properties Listed Yet","Landlords haven't listed any available properties yet. Check back soon.")

    # ── APPLY ─────────────────────────────────────────────────────────────────
    elif "Apply" in action or 'selected_property' in st.session_state and st.session_state.selected_property:
        if not st.session_state.get('selected_property'):
            empty_state(IMG["apartment"],"No Property Selected","Go to Browse Properties and click Apply on any listing.")
        else:
            prop=st.session_state.selected_property
            img_url=prop.get('image_path') or prop_img(prop.get('property_type','apartment'))
            b1,b2=st.columns([1,1.6])
            with b1: simg(img_url)
            with b2:
                st.markdown(f"""<div style="padding:.3rem 0 .8rem;">
                  <div style="font-family:'Syne',sans-serif;font-size:1.45rem;font-weight:800;color:#ddeaf8;margin-bottom:.35rem;">{prop['property_name']}</div>
                  <div style="font-size:.83rem;color:#7a9cc4;margin-bottom:.45rem;">📍 {prop.get('suburb','')}, {prop['city']}</div>
                  <div style="font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:800;color:#c8f542;">ZWL {prop['monthly_rent']:,.0f}<span style="font-size:.7rem;color:#3a5880;font-weight:400;">/month</span></div>
                  <div style="font-size:.77rem;color:#7a9cc4;margin-top:.3rem;">Deposit: ZWL {prop['deposit_required']:,.0f} &nbsp;·&nbsp; {prop.get('bedrooms',0)} bed · {prop.get('bathrooms',0)} bath</div>
                </div>""",unsafe_allow_html=True)
            with st.form("taf"):
                c1,c2=st.columns(2)
                with c1:
                    income=st.number_input("Monthly Salary / Income (ZWL)",min_value=0,value=50000,help="Used by AI to predict rental sustainability.")
                    emp_label=st.selectbox("Employment Information",["Full time","Part time","Self employed","Unemployed","Student"])
                    emp_map={"Full time":"employed","Part time":"employed","Self employed":"self_employed","Unemployed":"unemployed","Student":"student"}
                    emp=emp_map[emp_label]
                    yrs=st.number_input("Years at Current Job / Business",min_value=0,value=0)
                    current_rent=st.number_input("Current Monthly Rent Paid (ZWL)",min_value=0,value=0,help="Enter 0 if not currently renting.")
                    r_hist=st.checkbox("Has Previous Rental History"); refs=st.checkbox("Has References")
                with c2:
                    dependents=st.number_input("Number of Dependents",0,20,0,help="Children, elderly parents, or any others living with the tenant.")
                    fam=dependents+1
                    household_notes=st.text_area("Household Information",placeholder="Example: 2 children and 1 elderly parent",height=80)
                    credit=st.slider("Credit Score",300,850,600); debt=st.slider("Debt-to-Income (%)",0,100,30)
                    age=st.number_input("Age",18,100,30); late=st.number_input("Prior Late Payments",0,50,0)
                r2i=(prop['monthly_rent']/income*100) if income>0 else 100
                remaining_income=income-prop['monthly_rent']
                affordability_status='Sustainable' if r2i<=33 and remaining_income>0 else ('Manageable with caution' if r2i<=50 and remaining_income>0 else 'Not sustainable')
                affordability_comment=f"AI affordability check: rent consumes {r2i:.1f}% of salary; estimated balance after rent is ZWL {remaining_income:,.0f}."
                st.info(f"Rent-to-Income: **{r2i:.1f}%** {'✅' if r2i<33 else '⚠️' if r2i<50 else '🔴'} — **{affordability_status}**. {affordability_comment}")
                if st.form_submit_button("Submit Application →"):
                    res=predict({'monthly_income':income,'employment_status':emp,'years_at_current_job':yrs,'previous_rental_history':int(r_hist),'has_references':int(refs),'credit_score':credit,'debt_to_income_ratio':debt,'age':age,'family_size':fam,'previous_late_payments':late,'rent_to_income_ratio':r2i,'property_type':prop['property_type']},model,scaler,les)
                    rc1,rc2,rc3=st.columns([1,2,1])
                    with rc1: st.markdown(f'<div class="score-card"><div class="sc-num">{res["risk_score"]}</div><div class="sc-lbl">Risk Score / 100</div></div>',unsafe_allow_html=True)
                    with rc2:
                        st.markdown(rp(res['risk_category']),unsafe_allow_html=True)
                        st.markdown(f"<br><strong style='color:#ddeaf8'>{res['recommendation']}</strong>",unsafe_allow_html=True)
                        pct=res['risk_score']; bc='#34d399' if pct>=70 else('#fbbf24' if pct>=40 else '#f87171')
                        st.markdown(f'<div style="margin-top:.8rem;background:#183060;border-radius:6px;height:7px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:{bc};border-radius:6px;"></div></div>',unsafe_allow_html=True)
                    with rc3:
                        st.markdown(f'<div style="background:#0b1c35;border:1px solid #183060;border-radius:10px;padding:.8rem;"><div style="font-size:.65rem;color:#3a5880;text-transform:uppercase;letter-spacing:.07em;margin-bottom:5px;">Key Signals</div>{"".join([f"<div style=\'font-size:.76rem;color:#ddeaf8;margin-bottom:3px;\'>{"✅" if credit>600 else "⚠️"} Credit: {credit}</div><div style=\'font-size:.76rem;color:#ddeaf8;margin-bottom:3px;\'>{"✅" if debt<40 else "⚠️"} Debt: {debt}%</div><div style=\'font-size:.76rem;color:#ddeaf8;margin-bottom:3px;\'>{"✅" if refs else "❌"} References</div><div style=\'font-size:.76rem;color:#ddeaf8;\'>{"✅" if r_hist else "❌"} Rental history</div>"])}</div>',unsafe_allow_html=True)
                    conn=get_db()
                    if conn:
                        cur=conn.cursor()
                        cur.execute("""INSERT INTO tenant_applications
                            (property_id,tenant_id,employment_status,employment_position,monthly_income,years_at_current_job,
                             previous_rental_history,has_references,credit_score,risk_score,risk_category,application_status,
                             number_of_dependents,current_monthly_rent,household_notes,affordability_status,affordability_comment)
                             VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (prop['property_id'],uid,emp,emp_label,income,yrs,int(r_hist),int(refs),credit,res['risk_score'],
                             res['risk_category'],'pending',dependents,current_rent,household_notes,affordability_status,affordability_comment))
                        conn.commit(); cur.close(); conn.close()
                        st.success("Application submitted!"); st.session_state.selected_property=None; st.rerun()

    # ── MY APPLICATIONS ───────────────────────────────────────────────────────
    elif "Applications" in action:
        st.markdown('<div class="page-title">📋 My Applications</div>',unsafe_allow_html=True)
        conn=get_db()
        if conn:
            cur=conn.cursor(dictionary=True)
            cur.execute("SELECT a.*,p.property_name,p.city,p.property_type,p.image_path,p.monthly_rent,u.full_name as landlord_name,u.user_id as landlord_id FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id JOIN users u ON p.landlord_id=u.user_id WHERE a.tenant_id=%s ORDER BY a.application_date DESC",(uid,))
            apps=cur.fetchall(); cur.close(); conn.close()
            if apps:
                total=len(apps); pending=sum(1 for a in apps if a['application_status']=='pending')
                approved=sum(1 for a in apps if a['application_status']=='approved'); rejected=total-pending-approved
                m1,m2,m3,m4=st.columns(4)
                m1.metric("Total",total); m2.metric("Pending",pending); m3.metric("Approved",approved); m4.metric("Rejected",rejected)
                st.markdown("<div style='height:.3rem'></div>",unsafe_allow_html=True)
                for app in apps:
                    img_url=app.get('image_path') or prop_img(app.get('property_type','apartment'))
                    sc={'pending':'#fbbf24','approved':'#34d399','rejected':'#f87171'}.get(app['application_status'],'#7a9cc4')
                    st.markdown('<div class="app-row">',unsafe_allow_html=True)
                    a1,a2,a3,a4,a5,a6=st.columns([0.4,2,1.8,1.8,1,0.9])
                    with a1:
                        try: st.image(img_url,width=48)
                        except: pass
                    with a2: st.markdown(f'<div class="afl">Property</div><div class="afv">{app["property_name"]}</div><div style="font-size:.72rem;color:#7a9cc4;">📍 {app["city"]}</div>',unsafe_allow_html=True)
                    with a3: st.markdown(f'<div class="afl">Risk</div>{rp(app["risk_category"],app["risk_score"])}',unsafe_allow_html=True)
                    with a4: st.markdown(f'<div class="afl">Landlord</div><div class="afv">{app["landlord_name"]}</div><div style="font-size:.72rem;color:#7a9cc4;">{app["application_date"].strftime("%d %b %Y")}</div>',unsafe_allow_html=True)
                    with a5: st.markdown(f'<div class="afl">Status</div><div style="font-family:Syne,sans-serif;font-size:.8rem;font-weight:700;color:{sc};">{app["application_status"].upper()}</div>',unsafe_allow_html=True)
                    with a6:
                        if app['application_status']=='approved':
                            if st.button("💬",key=f"msg_{app['application_id']}",help="Message landlord after acceptance"):
                                st.session_state.chat_partner=app['landlord_id']; st.rerun()
                        else:
                            st.caption("Chat opens after acceptance")
                    st.markdown('</div>',unsafe_allow_html=True)
            else:
                empty_state(IMG["apartment"],"No Applications Yet","Browse available properties and submit your first application.")

    # ── MY PAYMENTS ───────────────────────────────────────────────────────────
    elif "Payment" in action:
        st.markdown('<div class="page-title">💳 My Payments</div>',unsafe_allow_html=True)
        conn=get_db()
        if conn:
            cur=conn.cursor(dictionary=True)
            cur.execute("""SELECT py.*,pr.property_name,pr.property_type,pr.image_path,pr.monthly_rent,
                u.full_name as landlord_name
                FROM payments py JOIN tenant_applications a ON py.application_id=a.application_id
                JOIN properties pr ON a.property_id=pr.property_id
                JOIN users u ON pr.landlord_id=u.user_id
                WHERE a.tenant_id=%s ORDER BY py.due_date DESC""",(uid,))
            pays=cur.fetchall(); cur.close(); conn.close()
            if pays:
                df=pd.DataFrame(pays)
                total_paid=float(df[df.payment_status=='completed']['amount'].sum()) if 'amount' in df else 0
                late_count=len(df[df.payment_status=='late'])
                pending_count=len(df[df.payment_status=='pending'])
                on_time=len(df[df.payment_status=='completed'])
                rate=(on_time/(on_time+late_count)*100) if (on_time+late_count)>0 else 100

                m1,m2,m3,m4,m5=st.columns(5)
                m1.metric("Total Paid",f"ZWL {total_paid:,.0f}")
                m2.metric("Transactions",len(df))
                m3.metric("Pending",pending_count)
                m4.metric("Late",late_count)
                m5.metric("On-time Rate",f"{rate:.0f}%")

                cc,cl=st.columns([2,1])
                with cc:
                    fig=dfig(px.bar(df,x='due_date',y='amount',color='payment_status',
                        color_discrete_map={'completed':'#34d399','late':'#f87171','pending':'#fbbf24','failed':'#9ca3af'},
                        title='Payment History by Due Date'))
                    st.plotly_chart(fig,use_container_width=True)
                with cl:
                    # Monthly summary
                    st.markdown('<div class="ss">Recent Payments</div>',unsafe_allow_html=True)
                    for _,row in df.head(8).iterrows():
                        sc={'completed':'#34d399','late':'#f87171','pending':'#fbbf24','failed':'#9ca3af'}.get(row['payment_status'],'#7a9cc4')
                        icon={'completed':'✅','late':'⚠️','pending':'🕐','failed':'❌'}.get(row['payment_status'],'•')
                        p1,p2=st.columns([0.4,1])
                        with p1:
                            try: st.image(row.get('image_path') or prop_img(row.get('property_type','apartment')),width=42)
                            except: pass
                        with p2:
                            due=row['due_date'].strftime('%d %b %Y') if hasattr(row['due_date'],'strftime') else str(row.get('due_date',''))
                            st.markdown(f'<div style="font-size:.76rem;color:#ddeaf8;font-weight:500;">{row["property_name"]}</div><div style="font-size:.78rem;color:{sc};font-weight:700;">{icon} ZWL {float(row["amount"]):,.0f}</div><div style="font-size:.65rem;color:#3a5880;">Due: {due}</div>',unsafe_allow_html=True)

                # Payment table
                st.markdown('<div class="ss" style="margin-top:.8rem;">All Records</div>',unsafe_allow_html=True)
                st.markdown('<table class="adm-tbl"><thead><tr><th>Property</th><th>Type</th><th>Amount</th><th>Method</th><th>Due Date</th><th>Paid Date</th><th>Status</th><th>Notes</th></tr></thead><tbody>',unsafe_allow_html=True)
                for _,row in df.iterrows():
                    sc={'completed':'green','late':'red','pending':'yellow','failed':'red'}.get(row['payment_status'],'blue')
                    due=row['due_date'].strftime('%d %b %Y') if hasattr(row.get('due_date'),'strftime') else '—'
                    paid=row['payment_date'].strftime('%d %b %Y') if row.get('payment_date') and hasattr(row['payment_date'],'strftime') else '—'
                    st.markdown(f'<tr><td>{row["property_name"]}</td><td>{row.get("payment_type","rent")}</td><td style="font-family:Syne,sans-serif;font-weight:700;color:#c8f542;">ZWL {float(row["amount"]):,.0f}</td><td>{row.get("payment_method","—")}</td><td>{due}</td><td>{paid}</td><td>{tag(row["payment_status"],sc)}</td><td style="color:#3a5880;font-size:.75rem;">{row.get("notes","") or "—"}</td></tr>',unsafe_allow_html=True)
                st.markdown('</tbody></table>',unsafe_allow_html=True)
            else:
                empty_state(IMG["house"],"No Payment Records","Payment history will appear once you have an active tenancy and your landlord records payments.")

    # ── WRITE A REVIEW ────────────────────────────────────────────────────────
    elif "Review" in action:
        st.markdown('<div class="page-title">⭐ Write a Review</div>',unsafe_allow_html=True)
        st.markdown('<div class="page-sub">Share your experience with a landlord or property</div>',unsafe_allow_html=True)

        conn=get_db()
        if conn:
            cur=conn.cursor(dictionary=True)
            # Get approved applications this tenant has had
            cur.execute("""SELECT a.application_id,a.property_id,p.property_name,p.city,p.landlord_id,
                u.full_name as landlord_name,
                (SELECT COUNT(*) FROM tenant_reviews r WHERE r.tenant_id=%s AND r.property_id=p.property_id) as already_reviewed
                FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id
                JOIN users u ON p.landlord_id=u.user_id
                WHERE a.tenant_id=%s AND a.application_status='approved'""",(uid,uid))
            tenancies=cur.fetchall()

            # Show existing reviews
            cur.execute("""SELECT r.*,p.property_name,u.full_name as landlord_name FROM tenant_reviews r
                JOIN properties p ON r.property_id=p.property_id
                JOIN users u ON r.landlord_id=u.user_id
                WHERE r.tenant_id=%s ORDER BY r.review_date DESC""",(uid,))
            my_reviews=cur.fetchall(); cur.close(); conn.close()

            col_form,col_reviews=st.columns([1,1])
            with col_form:
                st.markdown('<div class="sh">Submit a Review</div>',unsafe_allow_html=True)
                if not tenancies:
                    empty_state(IMG["harare1"],"No Approved Tenancies","You can only review properties where your application was approved.")
                else:
                    reviewable=[t for t in tenancies if not t['already_reviewed']]
                    if not reviewable:
                        st.info("You've already reviewed all your tenancies. Thank you!")
                    else:
                        with st.form("review_form"):
                            prop_options={f"{t['property_name']} — {t['landlord_name']}":t for t in reviewable}
                            sel=st.selectbox("Select Property",list(prop_options.keys()))
                            rating=st.slider("Rating (1–5 stars) ⭐",1,5,4)
                            recommend=st.checkbox("I would recommend this landlord",value=True)
                            review_text=st.text_area("Your Review",placeholder="Describe your experience — communication, maintenance, fairness...",height=110)
                            if st.form_submit_button("Submit Review →"):
                                if review_text.strip():
                                    t=prop_options[sel]
                                    conn2=get_db()
                                    if conn2:
                                        cur2=conn2.cursor()
                                        cur2.execute("INSERT INTO tenant_reviews(tenant_id,landlord_id,property_id,rating,review_text,would_recommend) VALUES(%s,%s,%s,%s,%s,%s)",
                                            (uid,t['landlord_id'],t['property_id'],rating,review_text.strip(),int(recommend)))
                                        conn2.commit(); cur2.close(); conn2.close()
                                        st.success("Review submitted! Thank you."); st.rerun()
                                else: st.warning("Please write a review before submitting.")

            with col_reviews:
                st.markdown('<div class="sh">My Past Reviews</div>',unsafe_allow_html=True)
                if not my_reviews:
                    st.markdown('<div style="font-size:.83rem;color:#3a5880;padding:.5rem 0;">No reviews submitted yet.</div>',unsafe_allow_html=True)
                else:
                    for r in my_reviews:
                        st.markdown(f"""<div class="app-row">
                          <div style="font-family:Syne,sans-serif;font-size:.85rem;font-weight:700;color:#ddeaf8;">{r['property_name']}</div>
                          <div style="font-size:.72rem;color:#7a9cc4;margin-bottom:.3rem;">Landlord: {r['landlord_name']}</div>
                          <div style="color:#fbbf24;font-size:.83rem;">{"⭐"*r['rating']}{"☆"*(5-r['rating'])}</div>
                          <div style="font-size:.8rem;color:#7a9cc4;font-style:italic;margin-top:.25rem;">"{r['review_text']}"</div>
                          <div style="font-size:.7rem;color:#3a5880;margin-top:.3rem;">{"✅ Recommended" if r['would_recommend'] else "❌ Not recommended"}</div>
                        </div>""",unsafe_allow_html=True)

    # ── CHAT ─────────────────────────────────────────────────────────────────
    elif "Message" in action or "💬" in action:
        chat_section()


# ══════════════════════════════════════════════════════════════════════════════
# LANDLORD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def landlord_dashboard(action):
    uid=st.session_state.user_id

    # ── OVERVIEW ──────────────────────────────────────────────────────────────
    if "Overview" in action:
        st.markdown('<div class="page-title">📊 Portfolio Overview</div>',unsafe_allow_html=True)
        conn=get_db()
        if conn:
            cur=conn.cursor(dictionary=True)
            cur.execute("SELECT COUNT(*) as total,SUM(CASE WHEN is_available THEN 1 ELSE 0 END) as avail,AVG(monthly_rent) as avg_rent FROM properties WHERE landlord_id=%s",(uid,))
            ps=cur.fetchone()
            cur.execute("SELECT COUNT(*) as total,AVG(risk_score) as avg_risk,SUM(CASE WHEN application_status='pending' THEN 1 ELSE 0 END) as pending FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s",(uid,))
            as_=cur.fetchone()
            cur.execute("SELECT COALESCE(SUM(amount),0) as collected FROM payments py JOIN tenant_applications a ON py.application_id=a.application_id JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s AND py.payment_status='completed'",(uid,))
            rev=cur.fetchone()
            m1,m2,m3,m4,m5,m6=st.columns(6)
            m1.metric("Properties",ps['total'] if ps else 0); m2.metric("Available",ps['avail'] if ps else 0)
            m3.metric("Avg Rent",f"ZWL {(ps['avg_rent'] or 0):,.0f}" if ps else "0")
            m4.metric("Pending Apps",as_['pending'] if as_ else 0)
            m5.metric("Avg Risk Score",f"{(as_['avg_risk'] or 0):.0f}" if as_ else "—")
            m6.metric("Revenue Collected",f"ZWL {float(rev['collected'] or 0):,.0f}" if rev else "0")

            cur.execute("SELECT risk_category,COUNT(*) as cnt FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY risk_category",(uid,))
            rd=cur.fetchall()
            cur.execute("SELECT application_status,COUNT(*) as cnt FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY application_status",(uid,))
            sd=cur.fetchall()
            cur.execute("SELECT p.property_name,p.image_path,p.property_type,p.monthly_rent,p.is_available,COUNT(a.application_id) as apps FROM properties p LEFT JOIN tenant_applications a ON p.property_id=a.property_id WHERE p.landlord_id=%s GROUP BY p.property_id ORDER BY apps DESC LIMIT 4",(uid,))
            top=cur.fetchall(); cur.close(); conn.close()
            cp,cs,cl=st.columns([1,1,1.2])
            with cp:
                if rd: st.plotly_chart(dfig(px.pie(pd.DataFrame(rd),values='cnt',names='risk_category',color='risk_category',color_discrete_map={'low':'#34d399','medium':'#fbbf24','high':'#f87171'},title='Risk Distribution',hole=0.5)),use_container_width=True)
                else: simg(IMG["dashboard"])
            with cs:
                if sd: st.plotly_chart(dfig(px.bar(pd.DataFrame(sd),x='application_status',y='cnt',color='application_status',color_discrete_map={'pending':'#fbbf24','approved':'#34d399','rejected':'#f87171'},title='By Status')),use_container_width=True)
                else: simg(IMG["city"])
            with cl:
                st.markdown('<div class="ss">Top Properties</div>',unsafe_allow_html=True)
                if top:
                    for p in top:
                        p_img=p.get('image_path') or prop_img(p.get('property_type','apartment'))
                        t1c,t2c=st.columns([0.45,1])
                        with t1c:
                            try: st.image(p_img,width=52)
                            except: pass
                        with t2c: st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:.82rem;font-weight:700;color:#ddeaf8;">{p["property_name"]}</div><div style="font-size:.7rem;color:#7a9cc4;">ZWL {p["monthly_rent"]:,.0f}/mo · {"🟢" if p["is_available"] else "🔴"}</div><div style="font-family:Syne,sans-serif;font-size:.92rem;font-weight:800;color:#c8f542;">{p["apps"]} apps</div>',unsafe_allow_html=True)
                        st.markdown("<div style='height:.15rem'></div>",unsafe_allow_html=True)
                else: simg(IMG["harare1"])

    # ── MANAGE PROPERTIES ─────────────────────────────────────────────────────
    elif "Manage" in action or "Properties" in action:
        st.markdown('<div class="page-title">🏘️ Manage Properties</div>',unsafe_allow_html=True)
        tab1,tab2=st.tabs(["➕ Add Property","📋 My Properties"])
        with tab1:
            cf,cprev=st.columns([1.2,1])
            with cf:
                with st.form("apf"):
                    ca,cb=st.columns(2)
                    with ca: pname=st.text_input("Property Name*"); ptype=st.selectbox("Type*",["apartment","house","commercial","room"]); beds=st.number_input("Bedrooms",0,20,1); baths=st.number_input("Bathrooms",0,20,1)
                    with cb: rent=st.number_input("Monthly Rent (ZWL)*",0,value=5000); dep=st.number_input("Deposit",0,value=5000); city=st.text_input("City*"); suburb=st.text_input("Suburb")
                    addr=st.text_area("Full Address*",height=65)
                    img_path=st.text_input("Property Image URL",placeholder="https://... or leave blank for default")
                    if st.form_submit_button("Add Property →"):
                        if pname and rent and city and addr:
                            conn=get_db()
                            if conn:
                                cur=conn.cursor(); cur.execute("INSERT INTO properties(landlord_id,property_name,property_type,address,city,suburb,bedrooms,bathrooms,monthly_rent,deposit_required,image_path) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(uid,pname,ptype,addr,city,suburb,beds,baths,rent,dep,img_path or None))
                                conn.commit(); cur.close(); conn.close(); st.success(f"'{pname}' added!")
                        else: st.warning("Fill all required fields.")
            with cprev:
                st.markdown('<div class="ss">Property type previews</div>',unsafe_allow_html=True)
                for pt,lbl in [("apartment","Apartment"),("house","House"),("room","Room"),("commercial","Commercial")]:
                    p1,p2=st.columns([0.4,1])
                    with p1:
                        try: st.image(IMG[pt],width=60)
                        except: pass
                    with p2: st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:.85rem;font-weight:700;color:#ddeaf8;padding:.4rem 0;">{lbl}</div>',unsafe_allow_html=True)
        with tab2:
            conn=get_db()
            if conn:
                cur=conn.cursor(dictionary=True); cur.execute("SELECT * FROM properties WHERE landlord_id=%s ORDER BY created_at DESC",(uid,)); props=cur.fetchall(); cur.close(); conn.close()
                if props:
                    cols=st.columns(3)
                    for i,p in enumerate(props):
                        img_url=p.get('image_path') or prop_img(p.get('property_type','apartment'))
                        with cols[i%3]:
                            st.markdown('<div class="pcard">',unsafe_allow_html=True)
                            simg(img_url)
                            st.markdown(f'<div class="pcard-body"><div class="pcard-type">{(p.get("property_type") or "").upper()} · {"🟢" if p["is_available"] else "🔴"}</div><div class="pcard-name">{p["property_name"]}</div><div class="pcard-loc">📍 {p.get("suburb","")}, {p["city"]}</div><div class="pcard-row"><div class="pcard-rent">ZWL {p["monthly_rent"]:,.0f}<span>/mo</span></div><div class="pcard-beds">🛏 {p["bedrooms"]} · 🚿 {p["bathrooms"]}</div></div></div><div class="pcard-foot"><div class="pcard-meta">Dep: ZWL {p["deposit_required"]:,.0f}</div></div>',unsafe_allow_html=True)
                            st.markdown('</div>',unsafe_allow_html=True)
                            if st.button("Toggle Availability",key=f"tog_{p['property_id']}",width='stretch'):
                                conn2=get_db()
                                if conn2:
                                    c2=conn2.cursor(); c2.execute("UPDATE properties SET is_available=NOT is_available WHERE property_id=%s",(p['property_id'],)); conn2.commit(); c2.close(); conn2.close(); st.rerun()
                else: empty_state(IMG["harare1"],"No Properties","Use Add Property to list your first property.")

    # ── APPLICATIONS ──────────────────────────────────────────────────────────
    elif "Applications" in action:
        st.markdown('<div class="page-title">📝 Tenant Applications</div>',unsafe_allow_html=True)
        conn=get_db()
        if conn:
            cur=conn.cursor(dictionary=True); cur.execute("SELECT a.*,u.full_name as tenant_name,u.email,u.phone,u.user_id as tenant_uid,p.property_name,p.city,p.property_type,p.image_path FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id JOIN users u ON a.tenant_id=u.user_id WHERE p.landlord_id=%s ORDER BY a.application_date DESC",(uid,)); apps=cur.fetchall(); cur.close(); conn.close()
            if apps:
                pending=[a for a in apps if a['application_status']=='pending']
                st.markdown(f'<div class="ss">{len(pending)} pending · {len(apps)-len(pending)} resolved · {len(apps)} total</div>',unsafe_allow_html=True)
                for app in apps:
                    img_url=app.get('image_path') or prop_img(app.get('property_type','apartment')); t_av=av(app['tenant_name'])
                    sc={'pending':'#fbbf24','approved':'#34d399','rejected':'#f87171'}.get(app['application_status'],'#7a9cc4')
                    with st.expander(f"{'🕐' if app['application_status']=='pending' else '✅' if app['application_status']=='approved' else '❌'}  {app['tenant_name']}  ·  {app['property_name']}  ·  {app['application_date'].strftime('%d %b %Y')}"):
                        tl,tr=st.columns([3,1])
                        with tl:
                            r1,r2,r3,r4=st.columns(4)
                            with r1:
                                try: st.image(t_av,width=44)
                                except: pass
                                st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:.8rem;font-weight:700;color:#ddeaf8;">{app["tenant_name"]}</div><div style="font-size:.7rem;color:#7a9cc4;">{app["email"]}</div>',unsafe_allow_html=True)
                            with r2: st.markdown(f'<div class="afl">Risk</div>{rp(app["risk_category"],app["risk_score"])}<div style="font-size:.72rem;color:#7a9cc4;margin-top:3px;">Credit: {app["credit_score"]}</div>',unsafe_allow_html=True)
                            with r3: st.markdown(f'<div class="afl">Financials</div><div class="afv">ZWL {app["monthly_income"]:,.0f}/mo</div><div style="font-size:.72rem;color:#7a9cc4;">{app.get("employment_position") or app["employment_status"]} · {app["years_at_current_job"]}yrs</div><div style="font-size:.72rem;color:#7a9cc4;">Dependents: {app.get("number_of_dependents",0)} · Current rent: ZWL {float(app.get("current_monthly_rent") or 0):,.0f}</div><div style="font-size:.72rem;color:#c8f542;">{app.get("affordability_status") or "Affordability pending"}</div>',unsafe_allow_html=True)
                            with r4: st.markdown(f'<div class="afl">Contact</div><div class="afv" style="font-size:.78rem;">{app["phone"] or "—"}</div>',unsafe_allow_html=True)
                        with tr:
                            try: st.image(img_url,width='stretch')
                            except: pass
                            st.markdown(f'<div style="font-size:.68rem;color:{sc};font-weight:700;text-align:center;margin-top:3px;">{app["application_status"].upper()}</div>',unsafe_allow_html=True)
                        btn_cols=st.columns([1,1,1,2])
                        if app['application_status']=='pending':
                            with btn_cols[0]:
                                if st.button("✅ Approve",key=f"apr_{app['application_id']}",width='stretch'):
                                    conn2=get_db()
                                    if conn2:
                                        c2=conn2.cursor(); c2.execute("UPDATE tenant_applications SET application_status='approved' WHERE application_id=%s",(app['application_id'],)); c2.execute("INSERT INTO messages(sender_id,receiver_id,message_text) VALUES(%s,%s,%s)",(uid,app['tenant_uid'],f"Your application for {app['property_name']} has been accepted. You can now chat with the landlord here.")); conn2.commit(); c2.close(); conn2.close(); st.success("Approved! Chat has been opened with the tenant."); st.rerun()
                            with btn_cols[1]:
                                if st.button("❌ Reject",key=f"rej_{app['application_id']}",width='stretch'):
                                    conn2=get_db()
                                    if conn2:
                                        c2=conn2.cursor(); c2.execute("UPDATE tenant_applications SET application_status='rejected' WHERE application_id=%s",(app['application_id'],)); conn2.commit(); c2.close(); conn2.close(); st.success("Rejected!"); st.rerun()
                        with btn_cols[2]:
                            if app['application_status']=='approved':
                                if st.button("💬 Chat",key=f"chat_{app['application_id']}",width='stretch'):
                                    st.session_state.chat_partner=app['tenant_uid']; st.rerun()
                            else:
                                st.caption("Chat after acceptance")
            else: empty_state(IMG["harare2"],"No Applications Yet","Once tenants apply, their AI risk assessments appear here.")

    # ── MANAGE PAYMENTS ───────────────────────────────────────────────────────
    elif "Payment" in action:
        st.markdown('<div class="page-title">💳 Manage Payments</div>',unsafe_allow_html=True)
        tab_rec,tab_hist=st.tabs(["💰 Record Payment","📊 Payment History"])

        with tab_rec:
            # Get approved applications
            conn=get_db()
            app_opts={}
            if conn:
                cur=conn.cursor(dictionary=True)
                cur.execute("""SELECT a.application_id,u.full_name as tenant,p.property_name,p.monthly_rent
                    FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id
                    JOIN users u ON a.tenant_id=u.user_id
                    WHERE p.landlord_id=%s AND a.application_status='approved'""",(uid,))
                approved=cur.fetchall(); cur.close(); conn.close()
                app_opts={f"{a['tenant']} — {a['property_name']} (ZWL {a['monthly_rent']:,.0f}/mo)":a for a in approved}

            if not app_opts:
                empty_state(IMG["house"],"No Approved Tenancies","Approve tenant applications first to record payments against them.")
            else:
                with st.form("pay_form"):
                    sel_app=st.selectbox("Tenancy *",list(app_opts.keys()))
                    c1,c2,c3=st.columns(3)
                    with c1:
                        pay_type=st.selectbox("Payment Type",["rent","deposit","other"])
                        pay_method=st.selectbox("Method",["cash","ecocash","bank_transfer","other"])
                    with c2:
                        amount=st.number_input("Amount (ZWL) *",min_value=0,value=int(app_opts[sel_app]['monthly_rent']))
                        pay_status=st.selectbox("Status",["completed","pending","late","failed"])
                    with c3:
                        due_date=st.date_input("Due Date",value=datetime.today())
                        pay_date=st.date_input("Payment Date",value=datetime.today())
                    notes=st.text_input("Notes / Reference",placeholder="EcoCash ref, bank slip no., etc.")
                    if st.form_submit_button("Record Payment →"):
                        app_id=app_opts[sel_app]['application_id']
                        conn2=get_db()
                        if conn2:
                            cur2=conn2.cursor()
                            cur2.execute("INSERT INTO payments(application_id,amount,payment_type,payment_method,payment_status,due_date,payment_date,notes,recorded_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                (app_id,amount,pay_type,pay_method,pay_status,due_date,pay_date if pay_status=='completed' else None,notes or None,uid))
                            conn2.commit(); cur2.close(); conn2.close()
                            st.success(f"Payment of ZWL {amount:,.0f} recorded as {pay_status}.")

        with tab_hist:
            conn=get_db()
            if conn:
                cur=conn.cursor(dictionary=True)
                cur.execute("""SELECT py.*,u.full_name as tenant_name,p.property_name,p.property_type,p.image_path
                    FROM payments py JOIN tenant_applications a ON py.application_id=a.application_id
                    JOIN properties p ON a.property_id=p.property_id
                    JOIN users u ON a.tenant_id=u.user_id
                    WHERE p.landlord_id=%s ORDER BY py.due_date DESC""",(uid,))
                pays=cur.fetchall(); cur.close(); conn.close()
                if pays:
                    df=pd.DataFrame(pays)
                    total=float(df[df.payment_status=='completed']['amount'].sum())
                    outstanding=float(df[df.payment_status=='pending']['amount'].sum())
                    late_amt=float(df[df.payment_status=='late']['amount'].sum())
                    m1,m2,m3,m4=st.columns(4)
                    m1.metric("Total Collected",f"ZWL {total:,.0f}"); m2.metric("Outstanding",f"ZWL {outstanding:,.0f}")
                    m3.metric("Late",f"ZWL {late_amt:,.0f}"); m4.metric("Transactions",len(df))

                    ch1,ch2=st.columns(2)
                    with ch1:
                        monthly=df.copy(); monthly['month']=pd.to_datetime(monthly['due_date']).dt.to_period('M').astype(str)
                        fig=dfig(px.bar(monthly.groupby('month')['amount'].sum().reset_index(),x='month',y='amount',title='Monthly Collections',color_discrete_sequence=['#c8f542']))
                        st.plotly_chart(fig,use_container_width=True)
                    with ch2:
                        fig2=dfig(px.pie(df.groupby('payment_status')['amount'].sum().reset_index(),values='amount',names='payment_status',
                            color='payment_status',color_discrete_map={'completed':'#34d399','pending':'#fbbf24','late':'#f87171','failed':'#6b7280'},
                            title='By Status',hole=0.4))
                        st.plotly_chart(fig2,use_container_width=True)

                    st.markdown('<div class="ss">All Payment Records</div>',unsafe_allow_html=True)
                    st.markdown('<table class="adm-tbl"><thead><tr><th>Tenant</th><th>Property</th><th>Type</th><th>Amount</th><th>Method</th><th>Due</th><th>Paid</th><th>Status</th><th>Notes</th></tr></thead><tbody>',unsafe_allow_html=True)
                    for _,row in df.iterrows():
                        sc={'completed':'green','late':'red','pending':'yellow','failed':'red'}.get(row['payment_status'],'blue')
                        due=row['due_date'].strftime('%d %b %Y') if hasattr(row.get('due_date'),'strftime') else '—'
                        paid=row['payment_date'].strftime('%d %b %Y') if row.get('payment_date') and hasattr(row['payment_date'],'strftime') else '—'
                        st.markdown(f'<tr><td>{row["tenant_name"]}</td><td>{row["property_name"]}</td><td>{row.get("payment_type","rent")}</td><td style="font-family:Syne,sans-serif;font-weight:700;color:#c8f542;">ZWL {float(row["amount"]):,.0f}</td><td>{row.get("payment_method","—")}</td><td>{due}</td><td>{paid}</td><td>{tag(row["payment_status"],sc)}</td><td style="color:#3a5880;font-size:.74rem;">{row.get("notes","") or "—"}</td></tr>',unsafe_allow_html=True)
                    st.markdown('</tbody></table>',unsafe_allow_html=True)
                else:
                    empty_state(IMG["harare1"],"No Payments Recorded","Record payments in the Record Payment tab.")

    # ── TENANT REVIEWS ────────────────────────────────────────────────────────
    elif "Reviews" in action:
        st.markdown('<div class="page-title">⭐ Tenant Reviews</div>',unsafe_allow_html=True)
        conn=get_db()
        if conn:
            cur=conn.cursor(dictionary=True); cur.execute("SELECT r.*,u.full_name as tenant_name,p.property_name,p.image_path,p.property_type FROM tenant_reviews r JOIN users u ON r.tenant_id=u.user_id JOIN properties p ON r.property_id=p.property_id WHERE r.landlord_id=%s ORDER BY r.review_date DESC",(uid,)); reviews=cur.fetchall(); cur.close(); conn.close()
            if reviews:
                avg=sum(r['rating'] for r in reviews)/len(reviews); rec=sum(1 for r in reviews if r['would_recommend'])
                m1,m2,m3,m4=st.columns(4)
                m1.metric("Total Reviews",len(reviews)); m2.metric("Avg Rating",f"{avg:.1f} / 5")
                m3.metric("Recommend %",f"{rec/len(reviews)*100:.0f}%"); m4.metric("5-Star Reviews",sum(1 for r in reviews if r['rating']==5))
                st.markdown("<div style='height:.3rem'></div>",unsafe_allow_html=True)
                for r in reviews:
                    img_url=r.get('image_path') or prop_img(r.get('property_type','apartment'))
                    rv1,rv2,rv3=st.columns([0.32,2.6,0.52])
                    with rv1:
                        try: st.image(av(r['tenant_name']),width=40)
                        except: pass
                    with rv2:
                        st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:.86rem;font-weight:700;color:#ddeaf8;">{r["tenant_name"]} <span style="font-size:.7rem;color:#7a9cc4;font-weight:400;">· {r["property_name"]}</span></div>',unsafe_allow_html=True)
                        st.markdown(f'<div style="color:#fbbf24;font-size:.83rem;margin:2px 0;">{"⭐"*int(r["rating"])}{"☆"*(5-int(r["rating"]))}</div>',unsafe_allow_html=True)
                        st.markdown(f'<div style="font-size:.81rem;color:#7a9cc4;font-style:italic;">"{r["review_text"]}"</div><div style="font-size:.73rem;margin-top:.25rem;">{"✅ Recommends" if r["would_recommend"] else "❌ Does not recommend"} &nbsp;·&nbsp; <span style="color:#3a5880;">{r["review_date"].strftime("%d %b %Y")}</span></div>',unsafe_allow_html=True)
                    with rv3:
                        try: st.image(img_url,width='stretch')
                        except: pass
                    st.markdown('<hr>',unsafe_allow_html=True)
            else: empty_state(IMG["harare2"],"No Reviews Yet","Reviews from tenants will appear here.")

    # ── ANALYTICS ─────────────────────────────────────────────────────────────
    elif "Analytics" in action:
        st.markdown('<div class="page-title">📈 Analytics Dashboard</div>',unsafe_allow_html=True)
        conn=get_db()
        if conn:
            cur=conn.cursor(dictionary=True)
            cur.execute("SELECT DATE(application_date) as date,COUNT(*) as count FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY DATE(application_date) ORDER BY date",(uid,)); trend=cur.fetchall()
            cur.execute("SELECT risk_score,risk_category FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s",(uid,)); scores=cur.fetchall()
            cur.execute("SELECT p.property_name,COUNT(a.application_id) as apps,AVG(a.risk_score) as avg_risk FROM properties p LEFT JOIN tenant_applications a ON p.property_id=a.property_id WHERE p.landlord_id=%s GROUP BY p.property_id",(uid,)); perf=cur.fetchall()
            cur.execute("SELECT employment_status,COUNT(*) as cnt FROM tenant_applications a JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY employment_status",(uid,)); emp=cur.fetchall()
            cur.execute("SELECT DATE_FORMAT(due_date,'%%Y-%%m') as month,SUM(amount) as total,payment_status FROM payments py JOIN tenant_applications a ON py.application_id=a.application_id JOIN properties p ON a.property_id=p.property_id WHERE p.landlord_id=%s GROUP BY month,payment_status ORDER BY month",(uid,)); pay_trend=cur.fetchall()
            cur.close(); conn.close()

            if trend:
                fig=dfig(px.area(pd.DataFrame(trend),x='date',y='count',title='Applications Over Time',color_discrete_sequence=['#5b54f0'])); fig.update_traces(fillcolor='rgba(91,84,240,.12)',line_color='#5b54f0'); st.plotly_chart(fig,use_container_width=True)
            else: simg(IMG["dashboard"])

            r1c1,r1c2,r1c3=st.columns(3)
            with r1c1:
                if scores: st.plotly_chart(dfig(px.histogram(pd.DataFrame(scores),x='risk_score',nbins=20,title='Risk Distribution',color_discrete_sequence=['#c8f542'])),use_container_width=True)
                else: simg(IMG["apartment"])
            with r1c2:
                if perf: st.plotly_chart(dfig(px.bar(pd.DataFrame(perf),x='property_name',y='apps',title='Apps per Property',color='avg_risk',color_continuous_scale=[[0,'#34d399'],[.5,'#fbbf24'],[1,'#f87171']])),use_container_width=True)
                else: simg(IMG["house"])
            with r1c3:
                if emp: st.plotly_chart(dfig(px.pie(pd.DataFrame(emp),values='cnt',names='employment_status',title='Employment Mix',hole=.45,color_discrete_sequence=['#5b54f0','#22d3ee','#c8f542','#f87171'])),use_container_width=True)
                else: simg(IMG["commercial"])

            if pay_trend:
                st.plotly_chart(dfig(px.bar(pd.DataFrame(pay_trend),x='month',y='total',color='payment_status',
                    barmode='group',title='Monthly Payment Collections',
                    color_discrete_map={'completed':'#34d399','pending':'#fbbf24','late':'#f87171','failed':'#6b7280'})),width='stretch')

    # ── CHAT ─────────────────────────────────────────────────────────────────
    elif "Message" in action or "💬" in action:
        chat_section()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def admin_dashboard(action):

    def fetch(sql,params=()):
        conn=get_db()
        if conn:
            try:
                c=conn.cursor(dictionary=True); c.execute(sql,params); return c.fetchall()
            except: return []
            finally: c.close(); conn.close()
        return []

    def execute(sql,params=()):
        conn=get_db()
        if conn:
            try:
                c=conn.cursor(); c.execute(sql,params); conn.commit(); return True
            except: return False
            finally: c.close(); conn.close()
        return False

    # ── ADMIN OVERVIEW ────────────────────────────────────────────────────────
    if "Dashboard" in action:
        st.markdown('<div class="page-title">🛡️ Admin Dashboard</div><div class="page-sub">Platform-wide overview and system health</div>',unsafe_allow_html=True)

        users=fetch("SELECT COUNT(*) as n FROM users")[0]['n'] if fetch("SELECT COUNT(*) as n FROM users") else 0
        tenants=fetch("SELECT COUNT(*) as n FROM users WHERE user_type='tenant'")[0]['n'] if fetch("SELECT COUNT(*) as n FROM users WHERE user_type='tenant'") else 0
        landlords=fetch("SELECT COUNT(*) as n FROM users WHERE user_type='landlord'")[0]['n'] if fetch("SELECT COUNT(*) as n FROM users WHERE user_type='landlord'") else 0
        properties=fetch("SELECT COUNT(*) as n FROM properties")[0]['n'] if fetch("SELECT COUNT(*) as n FROM properties") else 0
        apps=fetch("SELECT COUNT(*) as n FROM tenant_applications")[0]['n'] if fetch("SELECT COUNT(*) as n FROM tenant_applications") else 0
        pays_r=fetch("SELECT COALESCE(SUM(amount),0) as n FROM payments WHERE payment_status='completed'")
        revenue=float(pays_r[0]['n']) if pays_r else 0
        msgs=fetch("SELECT COUNT(*) as n FROM messages")[0]['n'] if fetch("SELECT COUNT(*) as n FROM messages") else 0
        reviews=fetch("SELECT COUNT(*) as n FROM tenant_reviews")[0]['n'] if fetch("SELECT COUNT(*) as n FROM tenant_reviews") else 0

        m1,m2,m3,m4=st.columns(4)
        m1.metric("Total Users",users); m2.metric("Properties",properties)
        m3.metric("Applications",apps); m4.metric("Revenue Tracked",f"ZWL {revenue:,.0f}")
        m5,m6,m7,m8=st.columns(4)
        m5.metric("Tenants",tenants); m6.metric("Landlords",landlords)
        m7.metric("Messages",msgs); m8.metric("Reviews",reviews)

        ch1,ch2,ch3=st.columns(3)
        with ch1:
            ut=fetch("SELECT user_type,COUNT(*) as cnt FROM users GROUP BY user_type")
            if ut: st.plotly_chart(dfig(px.pie(pd.DataFrame(ut),values='cnt',names='user_type',title='User Types',hole=.45,color_discrete_sequence=['#5b54f0','#c8f542','#22d3ee'])),use_container_width=True)
        with ch2:
            rs=fetch("SELECT risk_category,COUNT(*) as cnt FROM tenant_applications GROUP BY risk_category")
            if rs: st.plotly_chart(dfig(px.bar(pd.DataFrame(rs),x='risk_category',y='cnt',color='risk_category',color_discrete_map={'low':'#34d399','medium':'#fbbf24','high':'#f87171'},title='Risk Distribution')),use_container_width=True)
        with ch3:
            ps_data=fetch("SELECT payment_status,COUNT(*) as cnt FROM payments GROUP BY payment_status")
            if ps_data: st.plotly_chart(dfig(px.pie(pd.DataFrame(ps_data),values='cnt',names='payment_status',title='Payment Status',hole=.4,color_discrete_map={'completed':'#34d399','pending':'#fbbf24','late':'#f87171','failed':'#6b7280'})),use_container_width=True)

        # Recent activity
        st.markdown('<div class="sh" style="margin-top:.5rem;">Recent Applications</div>',unsafe_allow_html=True)
        recent=fetch("""SELECT a.application_id,u.full_name as tenant,p.property_name,u2.full_name as landlord,
            a.risk_score,a.risk_category,a.application_status,a.application_date
            FROM tenant_applications a JOIN users u ON a.tenant_id=u.user_id
            JOIN properties p ON a.property_id=p.property_id JOIN users u2 ON p.landlord_id=u2.user_id
            ORDER BY a.application_date DESC LIMIT 10""")
        if recent:
            st.markdown('<table class="adm-tbl"><thead><tr><th>#</th><th>Tenant</th><th>Property</th><th>Landlord</th><th>Risk Score</th><th>Category</th><th>Status</th><th>Date</th></tr></thead><tbody>',unsafe_allow_html=True)
            for r in recent:
                sc={'pending':'yellow','approved':'green','rejected':'red'}.get(r['application_status'],'blue')
                rc={'low':'green','medium':'yellow','high':'red'}.get(r['risk_category'],'blue')
                st.markdown(f'<tr><td style="color:#3a5880;">{r["application_id"]}</td><td>{r["tenant"]}</td><td>{r["property_name"]}</td><td>{r["landlord"]}</td><td style="font-family:Syne,sans-serif;font-weight:700;color:#c8f542;">{r["risk_score"]}</td><td>{tag(r["risk_category"],rc)}</td><td>{tag(r["application_status"],sc)}</td><td style="color:#3a5880;font-size:.78rem;">{r["application_date"].strftime("%d %b %Y")}</td></tr>',unsafe_allow_html=True)
            st.markdown('</tbody></table>',unsafe_allow_html=True)

    # ── ADMIN USERS ───────────────────────────────────────────────────────────
    elif "Users" in action:
        st.markdown('<div class="page-title">👥 User Management</div>',unsafe_allow_html=True)
        search=st.text_input("🔍 Search users",placeholder="Username, email, or name…")
        sql="SELECT user_id,username,full_name,email,phone,user_type,created_at FROM users"
        params=()
        if search:
            sql+=" WHERE username LIKE %s OR email LIKE %s OR full_name LIKE %s"
            params=(f'%{search}%',f'%{search}%',f'%{search}%')
        sql+=" ORDER BY created_at DESC"
        users=fetch(sql,params)
        if users:
            st.markdown(f'<div class="ss">{len(users)} user{"s" if len(users)!=1 else ""}</div>',unsafe_allow_html=True)
            st.markdown('<table class="adm-tbl"><thead><tr><th>ID</th><th>Username</th><th>Full Name</th><th>Email</th><th>Phone</th><th>Type</th><th>Joined</th><th>Actions</th></tr></thead><tbody>',unsafe_allow_html=True)
            for u in users:
                tc={'tenant':'blue','landlord':'green','admin':'red'}.get(u['user_type'],'blue')
                joined=u['created_at'].strftime('%d %b %Y') if u.get('created_at') and hasattr(u['created_at'],'strftime') else '—'
                st.markdown(f'<tr><td style="color:#3a5880;">{u["user_id"]}</td><td style="font-weight:600;color:#ddeaf8;">{u["username"]}</td><td>{u["full_name"]}</td><td style="color:#7a9cc4;">{u["email"]}</td><td style="color:#7a9cc4;">{u["phone"] or "—"}</td><td>{tag(u["user_type"],tc)}</td><td style="color:#3a5880;font-size:.78rem;">{joined}</td><td>',unsafe_allow_html=True)
                col_a,col_b=st.columns([1,1])
                with col_a:
                    if st.button("🗑️",key=f"del_u_{u['user_id']}",help=f"Delete {u['username']}"):
                        if execute("DELETE FROM users WHERE user_id=%s",(u['user_id'],)): st.success("Deleted"); st.rerun()
                st.markdown('</td></tr>',unsafe_allow_html=True)
            st.markdown('</tbody></table>',unsafe_allow_html=True)
        else:
            empty_state(IMG["city"],"No Users Found","No users match your search.")

    # ── ADMIN PROPERTIES ──────────────────────────────────────────────────────
    elif "Properties" in action:
        st.markdown('<div class="page-title">🏘️ All Properties</div>',unsafe_allow_html=True)
        props=fetch("""SELECT p.*,u.full_name as landlord_name FROM properties p JOIN users u ON p.landlord_id=u.user_id ORDER BY p.created_at DESC""")
        if props:
            st.markdown(f'<div class="ss">{len(props)} properties across the platform</div>',unsafe_allow_html=True)
            f1,f2=st.columns([1,1])
            with f1:
                city_filter=st.selectbox("Filter by city",["All"]+list({p['city'] for p in props}))
            with f2:
                type_filter=st.selectbox("Filter by type",["All"]+list({p['property_type'] for p in props}))
            filtered=[p for p in props if (city_filter=="All" or p['city']==city_filter) and (type_filter=="All" or p['property_type']==type_filter)]
            st.markdown('<table class="adm-tbl"><thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Landlord</th><th>City</th><th>Rent</th><th>Deposit</th><th>Beds</th><th>Status</th><th>Action</th></tr></thead><tbody>',unsafe_allow_html=True)
            for p in filtered:
                avail_tag=tag("Available","green") if p['is_available'] else tag("Rented","red")
                st.markdown(f'<tr><td style="color:#3a5880;">{p["property_id"]}</td><td style="font-weight:600;color:#ddeaf8;">{p["property_name"]}</td><td>{p["property_type"]}</td><td>{p["landlord_name"]}</td><td>{p["city"]}</td><td style="font-family:Syne,sans-serif;font-weight:700;color:#c8f542;">ZWL {p["monthly_rent"]:,.0f}</td><td style="color:#7a9cc4;">ZWL {p["deposit_required"]:,.0f}</td><td>{p["bedrooms"]}</td><td>{avail_tag}</td><td>',unsafe_allow_html=True)
                if st.button("🗑️",key=f"del_p_{p['property_id']}"):
                    if execute("DELETE FROM properties WHERE property_id=%s",(p['property_id'],)): st.success("Deleted"); st.rerun()
                st.markdown('</td></tr>',unsafe_allow_html=True)
            st.markdown('</tbody></table>',unsafe_allow_html=True)
        else:
            empty_state(IMG["harare1"],"No Properties","No properties have been listed yet.")

    # ── ADMIN APPLICATIONS ────────────────────────────────────────────────────
    elif "Applications" in action:
        st.markdown('<div class="page-title">📝 All Applications</div>',unsafe_allow_html=True)
        status_filter=st.selectbox("Filter by status",["all","pending","approved","rejected"])
        sql="""SELECT a.*,u.full_name as tenant_name,p.property_name,u2.full_name as landlord_name
            FROM tenant_applications a JOIN users u ON a.tenant_id=u.user_id
            JOIN properties p ON a.property_id=p.property_id JOIN users u2 ON p.landlord_id=u2.user_id"""
        if status_filter!="all": sql+=f" WHERE a.application_status='{status_filter}'"
        sql+=" ORDER BY a.application_date DESC"
        apps=fetch(sql)
        if apps:
            st.markdown(f'<div class="ss">{len(apps)} application{"s" if len(apps)!=1 else ""}</div>',unsafe_allow_html=True)
            st.markdown('<table class="adm-tbl"><thead><tr><th>#</th><th>Tenant</th><th>Property</th><th>Landlord</th><th>Income</th><th>Credit</th><th>Risk</th><th>Score</th><th>Status</th><th>Date</th></tr></thead><tbody>',unsafe_allow_html=True)
            for a in apps:
                sc={'pending':'yellow','approved':'green','rejected':'red'}.get(a['application_status'],'blue')
                rc={'low':'green','medium':'yellow','high':'red'}.get(a['risk_category'],'blue')
                st.markdown(f'<tr><td style="color:#3a5880;">{a["application_id"]}</td><td>{a["tenant_name"]}</td><td>{a["property_name"]}</td><td>{a["landlord_name"]}</td><td style="color:#7a9cc4;">ZWL {a["monthly_income"]:,.0f}</td><td>{a["credit_score"]}</td><td>{tag(a["risk_category"],rc)}</td><td style="font-family:Syne,sans-serif;font-weight:700;color:#c8f542;">{a["risk_score"]}</td><td>{tag(a["application_status"],sc)}</td><td style="color:#3a5880;font-size:.78rem;">{a["application_date"].strftime("%d %b %Y")}</td></tr>',unsafe_allow_html=True)
            st.markdown('</tbody></table>',unsafe_allow_html=True)
        else: empty_state(IMG["city"],"No Applications","No applications found.")

    # ── ADMIN PAYMENTS ────────────────────────────────────────────────────────
    elif "Payments" in action:
        st.markdown('<div class="page-title">💳 All Payments</div>',unsafe_allow_html=True)
        pays=fetch("""SELECT py.*,u.full_name as tenant_name,p.property_name,u2.full_name as landlord_name
            FROM payments py JOIN tenant_applications a ON py.application_id=a.application_id
            JOIN properties p ON a.property_id=p.property_id
            JOIN users u ON a.tenant_id=u.user_id JOIN users u2 ON p.landlord_id=u2.user_id
            ORDER BY py.due_date DESC""")
        if pays:
            df=pd.DataFrame(pays)
            total=float(df[df.payment_status=='completed']['amount'].sum())
            outstanding=float(df[df.payment_status.isin(['pending','late'])]['amount'].sum())
            m1,m2,m3,m4=st.columns(4)
            m1.metric("Total Volume",f"ZWL {float(df['amount'].sum()):,.0f}")
            m2.metric("Collected",f"ZWL {total:,.0f}")
            m3.metric("Outstanding",f"ZWL {outstanding:,.0f}")
            m4.metric("Transactions",len(df))

            st.plotly_chart(dfig(px.bar(df.groupby('payment_status')['amount'].sum().reset_index(),x='payment_status',y='amount',color='payment_status',
                color_discrete_map={'completed':'#34d399','pending':'#fbbf24','late':'#f87171','failed':'#6b7280'},
                title='Payment Volume by Status')),width='stretch')

            st.markdown('<table class="adm-tbl"><thead><tr><th>Tenant</th><th>Property</th><th>Landlord</th><th>Type</th><th>Amount</th><th>Method</th><th>Due</th><th>Paid</th><th>Status</th></tr></thead><tbody>',unsafe_allow_html=True)
            for _,row in df.iterrows():
                sc={'completed':'green','late':'red','pending':'yellow','failed':'red'}.get(row['payment_status'],'blue')
                due=row['due_date'].strftime('%d %b %Y') if hasattr(row.get('due_date'),'strftime') else '—'
                paid=row['payment_date'].strftime('%d %b %Y') if row.get('payment_date') and hasattr(row['payment_date'],'strftime') else '—'
                st.markdown(f'<tr><td>{row["tenant_name"]}</td><td>{row["property_name"]}</td><td>{row["landlord_name"]}</td><td>{row.get("payment_type","rent")}</td><td style="font-family:Syne,sans-serif;font-weight:700;color:#c8f542;">ZWL {float(row["amount"]):,.0f}</td><td>{row.get("payment_method","—")}</td><td>{due}</td><td>{paid}</td><td>{tag(row["payment_status"],sc)}</td></tr>',unsafe_allow_html=True)
            st.markdown('</tbody></table>',unsafe_allow_html=True)
        else:
            empty_state(IMG["dashboard"],"No Payment Records","Payments recorded by landlords will appear here.")

    # ── ADMIN ANALYTICS ────────────────────────────────────────────────────────
    elif "Analytics" in action:
        st.markdown('<div class="page-title">📈 Platform Analytics</div>',unsafe_allow_html=True)
        reg_trend=fetch("SELECT DATE(created_at) as date,user_type,COUNT(*) as cnt FROM users GROUP BY DATE(created_at),user_type ORDER BY date")
        app_trend=fetch("SELECT DATE(application_date) as date,COUNT(*) as cnt,AVG(risk_score) as avg_risk FROM tenant_applications GROUP BY DATE(application_date) ORDER BY date")
        city_data=fetch("SELECT city,COUNT(*) as cnt FROM properties GROUP BY city ORDER BY cnt DESC LIMIT 10")
        pay_monthly=fetch("SELECT DATE_FORMAT(due_date,'%%Y-%%m') as month,SUM(CASE WHEN payment_status='completed' THEN amount ELSE 0 END) as collected, SUM(CASE WHEN payment_status='pending' THEN amount ELSE 0 END) as pending FROM payments GROUP BY month ORDER BY month")
        top_land=fetch("SELECT u.full_name,COUNT(p.property_id) as props,AVG(a.risk_score) as avg_risk,COUNT(a.application_id) as apps FROM users u LEFT JOIN properties p ON u.user_id=p.landlord_id LEFT JOIN tenant_applications a ON p.property_id=a.property_id WHERE u.user_type='landlord' GROUP BY u.user_id ORDER BY props DESC LIMIT 8")

        if reg_trend: st.plotly_chart(dfig(px.bar(pd.DataFrame(reg_trend),x='date',y='cnt',color='user_type',title='User Registrations Over Time',color_discrete_sequence=['#5b54f0','#c8f542','#22d3ee'])),use_container_width=True)
        c1,c2=st.columns(2)
        with c1:
            if app_trend: st.plotly_chart(dfig(px.line(pd.DataFrame(app_trend),x='date',y='cnt',title='Daily Applications',color_discrete_sequence=['#22d3ee'])),use_container_width=True)
        with c2:
            if city_data: st.plotly_chart(dfig(px.bar(pd.DataFrame(city_data),x='city',y='cnt',title='Properties by City',color_discrete_sequence=['#c8f542'])),use_container_width=True)
        if pay_monthly:
            fig=dfig(px.bar(pd.DataFrame(pay_monthly),x='month',y=['collected','pending'],barmode='group',title='Monthly Revenue',color_discrete_map={'collected':'#34d399','pending':'#fbbf24'})); st.plotly_chart(fig,use_container_width=True)
        if top_land:
            st.markdown('<div class="sh">Top Landlords</div>',unsafe_allow_html=True)
            st.markdown('<table class="adm-tbl"><thead><tr><th>Landlord</th><th>Properties</th><th>Applications</th><th>Avg Risk Score</th></tr></thead><tbody>',unsafe_allow_html=True)
            for l in top_land:
                st.markdown(f'<tr><td style="font-weight:600;color:#ddeaf8;">{l["full_name"]}</td><td style="font-family:Syne,sans-serif;font-weight:700;color:#c8f542;">{l["props"]}</td><td>{l["apps"]}</td><td>{f"{float(l["avg_risk"]):.1f}" if l["avg_risk"] else "—"}</td></tr>',unsafe_allow_html=True)
            st.markdown('</tbody></table>',unsafe_allow_html=True)

    # ── ADMIN CHAT ─────────────────────────────────────────────────────────────
    elif "Message" in action or "💬" in action:
        chat_section("💬 Platform Messages")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.authenticated:
        landing_page(); return
    action=render_sidebar()
    if   st.session_state.user_type=='tenant':   tenant_dashboard(action)
    elif st.session_state.user_type=='landlord': landlord_dashboard(action)
    elif st.session_state.user_type=='admin':    admin_dashboard(action)

if __name__=="__main__":
    main()
