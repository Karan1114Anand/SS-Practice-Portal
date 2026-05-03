import streamlit as st
import json
import random
import time
import html as html_lib
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BSTS102P — Practice Portal",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE = Path(__file__).parent
IMG_DIR = BASE / "images"


# ── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open(BASE / "qdata.json", encoding="utf-8") as f:
        return json.load(f)


QDATA  = load_data()
TOPICS = list(QDATA["topics"].keys())
ALL_Q  = QDATA["all"]


# ── SESSION STATE ─────────────────────────────────────────────────────────────
_defaults = {
    "qbank_topic": TOPICS[0],
    "revealed":    set(),
    "tt":          None,   # topic-test state dict
    "ft":          None,   # full-test state dict
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── STYLES ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #0c0c0c !important; }

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    background: #161616;
    border-bottom: 1px solid #2a2a2a;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #888880 !important;
    font-size: 13.5px;
    padding: 12px 20px;
    background: transparent !important;
}
.stTabs [aria-selected="true"] { color: #f0efe8 !important; }
.stTabs [data-baseweb="tab-highlight"] { background: #f0efe8 !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 4px; }

/* ---- Buttons ---- */
.stButton > button {
    background: #161616 !important;
    border: 1px solid #2a2a2a !important;
    color: #888880 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    transition: border-color .15s, color .15s !important;
}
.stButton > button:hover {
    border-color: #383838 !important;
    color: #f0efe8 !important;
}
.stButton > button[kind="primary"] {
    background: #f0efe8 !important;
    color: #0c0c0c !important;
    border-color: #f0efe8 !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover { opacity: .88 !important; }

/* ---- Radio ---- */
div[data-baseweb="radio"] > label {
    background: #1f1f1f !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
    margin-bottom: 6px !important;
    color: #f0efe8 !important;
    font-size: 14px !important;
    width: 100%;
    cursor: pointer;
}
div[data-baseweb="radio"] > label:hover { border-color: #383838 !important; }
div[data-baseweb="radio"] [data-checked="true"] > label {
    border-color: #888880 !important;
    background: #0c0c0c !important;
}
/* hide actual radio circle dot */
div[data-baseweb="radio"] [type="radio"] { display: none !important; }

/* ---- Progress ---- */
.stProgress > div > div > div > div { background: #888880 !important; }
.stProgress > div > div { background: #2a2a2a !important; border-radius: 2px; }

/* ---- Metrics ---- */
[data-testid="stMetricLabel"] { color: #888880 !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #f0efe8 !important; font-size: 24px !important; }

/* ---- Divider ---- */
hr { border-color: #1f1f1f !important; margin: 16px 0 !important; }

/* ---- General text ---- */
h1, h2, h3, h4 { color: #f0efe8 !important; }
p, li, label { color: #888880; }
.stCaption { color: #505050 !important; }

/* ---- Sidebar ---- */
[data-testid="stSidebar"] { background: #161616 !important; border-right: 1px solid #2a2a2a; }

/* ---- Input / Select ---- */
[data-baseweb="select"] > div {
    background: #161616 !important;
    border-color: #2a2a2a !important;
    color: #f0efe8 !important;
}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def e(s):
    """HTML-escape a value."""
    return html_lib.escape(str(s)) if s is not None else ""


def show_images(q):
    imgs = [IMG_DIR / f for f in (q.get("images") or []) if (IMG_DIR / f).exists()]
    if imgs:
        cols = st.columns(min(len(imgs), 2))
        for i, p in enumerate(imgs):
            cols[i % len(cols)].image(str(p))


def opts_html(q, reveal=False):
    """Render options as HTML divs. Highlight correct if reveal=True."""
    rows = []
    for k, v in (q.get("options") or {}).items():
        is_correct = reveal and k == q["answer"]
        bg     = "#1a3a1a" if is_correct else "#1f1f1f"
        border = "#3a7a3a" if is_correct else "#2a2a2a"
        color  = "#7acc7a" if is_correct else "#f0efe8"
        lc     = "#7acc7a" if is_correct else "#505050"
        rows.append(
            f'<div style="display:flex;gap:12px;align-items:flex-start;background:{bg};'
            f'border:1px solid {border};border-radius:6px;padding:10px 14px;'
            f'margin-bottom:7px;font-size:14px;color:{color}">'
            f'<span style="font-weight:700;color:{lc};flex-shrink:0;min-width:18px">{e(k)}</span>'
            f'<span>{e(v)}</span></div>'
        )
    return "".join(rows)


def solution_html(expl, answer):
    text = expl or f"Answer: {answer}"
    return (
        f'<div style="background:#1f1f1f;border:1px solid #2a2a2a;border-radius:6px;'
        f'padding:14px 16px;margin-top:4px">'
        f'<div style="font-size:10px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;'
        f'color:#7acc7a;margin-bottom:8px">Solution</div>'
        f'<div style="font-size:13.5px;color:#888880;white-space:pre-wrap;line-height:1.7">{e(text)}</div>'
        f'</div>'
    )


def fmt_time(secs):
    secs = max(0, int(secs))
    return f"{secs // 60:02d}:{secs % 60:02d}"


def js_countdown(seconds):
    """Render a live JS countdown timer that ticks in the browser."""
    st.components.v1.html(
        f"""<div id="t" style="font-size:22px;font-weight:700;letter-spacing:2px;
            font-family:monospace;color:#f0efe8;background:#161616;
            border:1px solid #2a2a2a;border-radius:6px;
            padding:6px 16px;display:inline-block"></div>
        <script>
        var s={int(seconds)};
        (function tick(){{
          var el=document.getElementById('t');
          if(!el)return;
          el.textContent=(Math.floor(s/60)+'').padStart(2,'0')+':'+(s%60+'').padStart(2,'0');
          el.style.color=s<300?'#cc7a7a':s<600?'#ccaa55':'#f0efe8';
          el.style.borderColor=s<300?'#7a3a3a':s<600?'#806030':'#2a2a2a';
          if(s>0){{s--;setTimeout(tick,1000);}}
        }})();
        </script>""",
        height=52,
    )


# ── QUESTION BANK ─────────────────────────────────────────────────────────────
def page_qbank():
    left, right = st.columns([1, 3], gap="large")

    # ---- Sidebar: topic list ----
    with left:
        st.markdown(
            '<p style="font-size:10px;font-weight:600;letter-spacing:1.5px;'
            'color:#505050;text-transform:uppercase;margin-bottom:10px">TOPICS</p>',
            unsafe_allow_html=True,
        )
        for t in TOPICS:
            cnt    = len(QDATA["topics"][t])
            active = st.session_state.qbank_topic == t
            if st.button(
                f"{t}  ({cnt})",
                key=f"qb_t_{t}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                if st.session_state.qbank_topic != t:
                    st.session_state.qbank_topic = t
                    st.session_state.revealed    = set()
                    st.rerun()

    # ---- Main: questions ----
    with right:
        topic = st.session_state.qbank_topic
        qs    = QDATA["topics"][topic]

        st.markdown(
            f'<h2 style="font-size:20px;font-weight:600;color:#f0efe8;margin-bottom:2px">{e(topic)}</h2>'
            f'<p style="color:#505050;font-size:13px;margin-bottom:16px">{len(qs)} questions</p>',
            unsafe_allow_html=True,
        )

        for i, q in enumerate(qs):
            qid      = q["id"]
            revealed = qid in st.session_state.revealed

            # Question header + text
            st.markdown(
                f'<div style="font-size:10px;font-weight:600;letter-spacing:.8px;'
                f'color:#505050;text-transform:uppercase;margin-bottom:6px">Q{i+1}</div>'
                f'<div style="font-size:15px;color:#f0efe8;line-height:1.65;margin-bottom:12px">'
                f'{e(q["question"])}</div>',
                unsafe_allow_html=True,
            )

            # Images
            show_images(q)

            # Options
            st.markdown(opts_html(q, reveal=revealed), unsafe_allow_html=True)

            # Reveal / Solution
            if not revealed:
                if st.button("Reveal Answer", key=f"rev_{qid}"):
                    st.session_state.revealed.add(qid)
                    st.rerun()
            else:
                st.markdown(solution_html(q.get("explanation"), q["answer"]), unsafe_allow_html=True)

            st.markdown('<div style="height:1px;background:#1f1f1f;margin:20px 0"></div>', unsafe_allow_html=True)


# ── SHARED TEST UI ─────────────────────────────────────────────────────────────
def test_ui(state_key):
    s     = st.session_state[state_key]
    idx   = s["current"]
    n     = len(s["questions"])
    q     = s["questions"][idx]
    done  = sum(1 for a in s["answers"] if a is not None)

    # ---- Top bar ----
    c_hdr, c_timer = st.columns([4, 1])
    with c_hdr:
        title = s.get("topic", "Full Length Test")
        st.markdown(
            f'<h3 style="font-size:17px;font-weight:600;color:#f0efe8;margin-bottom:2px">{e(title)}</h3>'
            f'<p style="color:#505050;font-size:13px;margin:0">{done} of {n} answered</p>',
            unsafe_allow_html=True,
        )
    with c_timer:
        if state_key == "ft":
            remaining = max(0.0, s["deadline"] - time.time())
            if remaining <= 0:
                s["submitted"]  = True
                s["time_taken"] = 3600
                st.rerun()
            js_countdown(remaining)

    st.progress(done / n if n else 0)

    # ---- Question navigation (groups of 10) ----
    grp_size  = 10
    grp_start = (idx // grp_size) * grp_size
    grp_end   = min(grp_start + grp_size, n)

    nav_cols_list = []
    if n > grp_size:
        arrow_l, nav_zone, arrow_r = st.columns([1, 10, 1])
        with arrow_l:
            if grp_start > 0:
                if st.button("‹", key=f"{state_key}_gleft", use_container_width=True):
                    s["current"] = grp_start - 1
                    st.rerun()
        with arrow_r:
            if grp_end < n:
                if st.button("›", key=f"{state_key}_gright", use_container_width=True):
                    s["current"] = grp_end
                    st.rerun()
        nav_container = nav_zone
    else:
        nav_container = st

    with nav_container:
        cols = st.columns(grp_end - grp_start)
        for j, i in enumerate(range(grp_start, grp_end)):
            with cols[j]:
                is_cur  = i == idx
                is_done = s["answers"][i] is not None
                label   = f"**{i+1}**" if is_cur else ("✓" if is_done else str(i + 1))
                if st.button(label, key=f"{state_key}_nav_{i}", use_container_width=True):
                    s["current"] = i
                    st.rerun()

    st.markdown("---")

    # ---- Question ----
    topic_hint = (
        f' &nbsp;·&nbsp; <span style="font-size:11px;color:#505050;'
        f'font-weight:400;text-transform:none">{e(q.get("topic",""))}</span>'
        if state_key == "ft" else ""
    )
    st.markdown(
        f'<div style="font-size:10px;font-weight:600;letter-spacing:1px;color:#505050;'
        f'text-transform:uppercase;margin-bottom:10px">QUESTION {idx+1} OF {n}{topic_hint}</div>'
        f'<div style="font-size:15px;line-height:1.7;color:#f0efe8;margin-bottom:16px">'
        f'{e(q["question"])}</div>',
        unsafe_allow_html=True,
    )
    show_images(q)

    # ---- Options as radio ----
    opts     = q.get("options") or {}
    opt_keys = list(opts.keys())
    opt_lbls = [f"{k})  {v}" for k, v in opts.items()]
    cur_ans  = s["answers"][idx]
    cur_idx  = opt_keys.index(cur_ans) if cur_ans in opt_keys else None

    sel = st.radio(
        "answer",
        opt_lbls,
        index=cur_idx,
        key=f"{state_key}_r_{idx}",
        label_visibility="collapsed",
    )
    if sel is not None:
        sel_key = sel.split(")")[0].strip()
        s["answers"][idx] = sel_key

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Bottom navigation ----
    c1, c2, _, c3 = st.columns([1, 1, 3, 1])
    with c1:
        if idx > 0 and st.button("← Prev", key=f"{state_key}_prev"):
            s["current"] -= 1
            st.rerun()
    with c2:
        if idx < n - 1 and st.button("Next →", key=f"{state_key}_next"):
            s["current"] += 1
            st.rerun()
    with c3:
        if st.button("Submit Test", key=f"{state_key}_sub", type="primary"):
            unanswered = n - done
            if unanswered > 0 and not s.get("_confirm_sub"):
                s["_confirm_sub"] = True
                st.warning(f"{unanswered} question(s) unanswered. Click **Submit Test** again to confirm.")
            else:
                s["submitted"] = True
                if state_key == "ft":
                    s["time_taken"] = 3600 - max(0, s["deadline"] - time.time())
                s.pop("_confirm_sub", None)
                st.rerun()


# ── SHARED RESULTS ────────────────────────────────────────────────────────────
def test_results(state_key):
    s         = st.session_state[state_key]
    questions = s["questions"]
    answers   = s["answers"]
    title     = s.get("topic", "Full Length Test")

    correct = sum(1 for q, a in zip(questions, answers) if a == q["answer"])
    wrong   = sum(1 for q, a in zip(questions, answers) if a is not None and a != q["answer"])
    skipped = sum(1 for a in answers if a is None)
    total   = len(questions)
    acc     = round(correct / total * 100) if total else 0

    # ---- Score header ----
    st.markdown(
        f'<div style="text-align:center;padding:28px 0 12px">'
        f'<h2 style="font-size:28px;font-weight:700;color:#f0efe8;margin-bottom:6px">Test Complete</h2>'
        f'<p style="color:#888880;font-size:14px">{e(title)}</p></div>',
        unsafe_allow_html=True,
    )

    # Score circle approximation
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        st.markdown(
            f'<div style="background:#161616;border:2px solid #2a2a2a;border-radius:50%;'
            f'width:140px;height:140px;margin:0 auto 20px;'
            f'display:flex;flex-direction:column;align-items:center;justify-content:center">'
            f'<span style="font-size:36px;font-weight:800;color:#f0efe8;line-height:1">{acc}%</span>'
            f'<span style="font-size:11px;color:#888880;letter-spacing:1px;text-transform:uppercase;'
            f'margin-top:4px">Accuracy</span></div>',
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3)
    c1.metric("✓ Correct",  correct)
    c2.metric("✗ Wrong",    wrong)
    c3.metric("— Skipped",  skipped)

    tt = s.get("time_taken")
    if tt:
        st.markdown(
            f'<p style="text-align:center;color:#505050;font-size:13px;margin:8px 0 0">Time taken: {fmt_time(tt)}</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        if st.button("Take Another Test", key=f"{state_key}_reset", use_container_width=True):
            st.session_state[state_key] = None
            st.rerun()

    st.markdown("---")
    st.markdown(
        '<p style="font-size:10px;font-weight:600;letter-spacing:1.2px;'
        'text-transform:uppercase;color:#505050;margin-bottom:14px">Answer Review</p>',
        unsafe_allow_html=True,
    )

    for q, a in zip(questions, answers):
        is_correct = a == q["answer"]
        is_skipped = a is None
        opts       = q.get("options") or {}
        color  = "#ccaa55" if is_skipped else ("#7acc7a" if is_correct else "#cc7a7a")
        status = "Skipped"  if is_skipped else ("Correct"  if is_correct else "Wrong")
        correct_str = f'{q["answer"]})  {opts.get(q["answer"], "")}'
        user_str    = f'{a})  {opts.get(a, "")}' if a and not is_correct else ""
        topic_tag   = (f'<span style="font-size:11px;color:#505050;margin-left:8px">{e(q.get("topic",""))}</span>'
                       if state_key == "ft" else "")
        expl        = q.get("explanation") or ""
        expl_block  = (
            f'<div style="background:#1f1f1f;border:1px solid #2a2a2a;border-radius:6px;'
            f'padding:10px 12px;margin-top:8px;font-size:13px;color:#888880;'
            f'white-space:pre-wrap;line-height:1.65">{e(expl)}</div>'
            if expl else ""
        )

        st.markdown(
            f'<div style="background:#161616;border:1px solid #2a2a2a;border-radius:10px;'
            f'padding:18px 20px;margin-bottom:10px">'
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">'
            f'<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px;'
            f'color:{color};background:#1f1f1f;border:1px solid #2a2a2a">{status}</span>'
            f'{topic_tag}</div>'
            f'<div style="font-size:14px;color:#f0efe8;line-height:1.6;margin-bottom:8px">{e(q["question"])}</div>'
            f'<div style="font-size:13px;color:#888880">'
            f'Correct: <b style="color:#7acc7a">{e(correct_str)}</b>'
            + (f'&nbsp;&nbsp;Your answer: <b style="color:#cc7a7a">{e(user_str)}</b>' if user_str else "")
            + f'</div>{expl_block}</div>',
            unsafe_allow_html=True,
        )
        show_images(q)


# ── TOPIC-WISE TEST ───────────────────────────────────────────────────────────
def page_topic_test():
    tt = st.session_state.tt

    if tt is None:
        st.markdown(
            '<h2 style="font-size:22px;font-weight:600;color:#f0efe8;margin-bottom:4px">Topic-wise Test</h2>'
            '<p style="color:#888880;font-size:14px;margin-bottom:24px">Select a topic to begin a focused practice test</p>',
            unsafe_allow_html=True,
        )
        cols = st.columns(4)
        for i, t in enumerate(TOPICS):
            cnt = len(QDATA["topics"][t])
            with cols[i % 4]:
                if st.button(
                    f"**{t}**\n\n{cnt} questions",
                    key=f"tt_start_{t}",
                    use_container_width=True,
                ):
                    qs = random.sample(QDATA["topics"][t], len(QDATA["topics"][t]))
                    st.session_state.tt = {
                        "topic":     t,
                        "questions": qs,
                        "answers":   [None] * len(qs),
                        "current":   0,
                        "submitted": False,
                    }
                    st.rerun()

    elif tt["submitted"]:
        test_results("tt")

    else:
        # Exit button at the top
        if st.button("← Back to Topics", key="tt_exit"):
            st.session_state.tt = None
            st.rerun()
        test_ui("tt")


# ── FULL-LENGTH TEST ──────────────────────────────────────────────────────────
def page_full_test():
    ft = st.session_state.ft

    if ft is None:
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.markdown(
                '<div style="text-align:center;padding:50px 0 20px">'
                '<h2 style="font-size:28px;font-weight:700;color:#f0efe8;margin-bottom:10px">Full Length Test</h2>'
                '<p style="color:#888880;font-size:15px;margin-bottom:4px">'
                '50 randomized questions from all topics</p>'
                '<p style="color:#505050;font-size:13px;margin-bottom:28px">'
                'Auto-submits when the 60-minute timer expires</p></div>',
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns(3)
            c1.metric("Questions",  "50")
            c2.metric("Time Limit", "60 min")
            c3.metric("Topics",     len(TOPICS))
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Start Test", type="primary", use_container_width=True, key="ft_start"):
                qs  = random.sample(ALL_Q, min(50, len(ALL_Q)))
                now = time.time()
                st.session_state.ft = {
                    "questions":  qs,
                    "answers":    [None] * len(qs),
                    "current":    0,
                    "submitted":  False,
                    "start_time": now,
                    "deadline":   now + 3600,
                    "time_taken": None,
                }
                st.rerun()

    elif ft["submitted"]:
        test_results("ft")

    else:
        test_ui("ft")


# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<p style="font-size:16px;font-weight:600;color:#f0efe8;padding:14px 0 4px;margin:0">'
    'BSTS102P <span style="color:#505050;font-weight:400">Practice Portal</span></p>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["  Question Bank  ", "  Topic-wise Test  ", "  Full Length Test  "])

with tab1:
    page_qbank()

with tab2:
    page_topic_test()

with tab3:
    page_full_test()
