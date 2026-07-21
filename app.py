from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests
import streamlit as st

API_URL = os.getenv("MEDICAL_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="MediGuide | Clinical Support",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
  --navy: #083344;
  --teal: #0f766e;
  --cyan: #06b6d4;
  --mist: #ecfeff;
  --surface: rgba(255,255,255,.94);
  --muted: #5f7480;
  --danger: #b91c1c;
}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 0% 0%, rgba(34,211,238,.17), transparent 28rem),
    linear-gradient(145deg, #f8fdff 0%, #eef9f8 48%, #f8fafc 100%);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #073642 0%, #0f4c5c 60%, #0f766e 100%);
}
[data-testid="stSidebar"] * { color: #f0fdfa !important; }
.block-container { max-width: 1480px; padding-top: 1.6rem; padding-bottom: 3rem; }
.hero {
  background: linear-gradient(135deg, rgba(8,51,68,.98), rgba(15,118,110,.94));
  color: white; border-radius: 28px; padding: 2rem 2.2rem;
  box-shadow: 0 24px 60px rgba(8,51,68,.18); margin-bottom: 1.2rem;
}
.hero h1 { margin: 0; font-size: clamp(2rem, 4vw, 3.5rem); letter-spacing: -.04em; }
.hero p { margin: .55rem 0 0; color: #ccfbf1; font-size: 1.08rem; max-width: 760px; }
.eyebrow { font-size: .78rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; color: #67e8f9; }
.med-card {
  background: var(--surface); border: 1px solid rgba(15,118,110,.12); border-radius: 20px;
  padding: 1.1rem 1.2rem; box-shadow: 0 12px 30px rgba(8,51,68,.07); height: 100%;
}
.med-card h3 { margin: 0 0 .45rem; color: var(--navy); }
.metric-label { color: var(--muted); font-size: .82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
.metric-value { color: var(--navy); font-size: 1.75rem; line-height: 1.2; font-weight: 800; }
.urgency-Emergency { border-left: 6px solid #dc2626; background: #fff1f2; }
.urgency-Urgent { border-left: 6px solid #f97316; background: #fff7ed; }
.urgency-Soon { border-left: 6px solid #eab308; background: #fefce8; }
.urgency-Routine { border-left: 6px solid #10b981; background: #ecfdf5; }
.disclaimer { border: 1px solid #bae6fd; background: #f0f9ff; color: #0c4a6e; border-radius: 16px; padding: .9rem 1rem; }
.stButton > button { border-radius: 12px; font-weight: 750; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #0f766e, #0891b2); border: 0; }
[data-baseweb="tab-list"] { gap: .5rem; }
[data-baseweb="tab"] { background: rgba(255,255,255,.76); border-radius: 12px; padding: .45rem 1rem; }
[data-baseweb="tab"][aria-selected="true"] { background: #0f766e; color: white; }
footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


def api(method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=25, **kwargs)
        if response.status_code == 204:
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            try:
                detail = f" — {exc.response.json().get('detail', '')}"
            except Exception:
                detail = f" — {exc.response.text[:180]}"
        raise RuntimeError(f"Backend request failed{detail}") from exc


@st.cache_data(ttl=300)
def get_symptoms() -> list[str]:
    return api("GET", "/api/symptoms")["symptoms"]


@st.cache_data(ttl=300)
def get_first_aid() -> dict[str, list[str]]:
    return api("GET", "/api/first-aid")


def backend_health() -> dict[str, Any] | None:
    try:
        return api("GET", "/api/health")
    except RuntimeError:
        return None


def render_result(result: dict[str, Any]) -> None:
    urgency = result["urgency"]
    st.markdown(
        f"""
        <div class="med-card urgency-{urgency}">
          <div class="eyebrow">Assessment #{result['id']} · {urgency}</div>
          <h3>{result['probable_condition']}</h3>
          <p><strong>Pattern confidence:</strong> {result['confidence']:.0%}</p>
          <p>{result['guidance']['interpretation']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if result["red_flags"]:
        st.error("\n\n".join(result["red_flags"]))
    st.markdown("#### Recommended next step")
    st.write(result["guidance"]["next_steps"])
    left, right = st.columns(2)
    with left:
        st.markdown("#### Supportive care")
        for item in result["guidance"]["self_care"]:
            st.markdown(f"- {item}")
    with right:
        st.markdown("#### Other possible patterns")
        for item in result["alternatives"]:
            st.write(f"{item['condition']} · {item['confidence']:.0%}")
    st.info(result["guidance"]["medication_safety"])


health = backend_health()
with st.sidebar:
    st.markdown("## 🩺 MediGuide")
    st.caption("Clinical decision support")
    if health:
        st.success("Backend connected")
        st.caption(f"Model validation: {health['validation_accuracy']:.0%}")
        st.caption(f"{health['symptom_count']} symptoms · {health['condition_count']} patterns")
    else:
        st.error("Backend unavailable")
        st.code("uvicorn backend.main:app --reload")
    st.markdown("---")
    st.markdown("**Emergency warning**")
    st.caption("Severe breathing difficulty, chest pain, stroke signs, heavy bleeding, loss of consciousness, or rapidly worsening symptoms require immediate local emergency care.")
    st.markdown("---")
    st.caption("Educational support only — not a diagnosis or prescription.")

st.markdown(
    """
<div class="hero">
  <div class="eyebrow">Medical expert system · Version 2</div>
  <h1>Clearer health guidance, built around safety.</h1>
  <p>Explore symptom patterns, assess urgency, keep a private local history, and organize health information in one calm clinical workspace.</p>
</div>
""",
    unsafe_allow_html=True,
)

if not health:
    st.error("Start the FastAPI backend before using the dashboard. See the README for one-command startup.")
    st.stop()

try:
    history = api("GET", "/api/assessments?limit=100")
    medications = api("GET", "/api/medications")
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

m1, m2, m3, m4 = st.columns(4)
metrics = [
    (m1, "Assessments", str(len(history))),
    (m2, "Active medications", str(sum(1 for item in medications if item["active"]))),
    (m3, "Model patterns", str(health["condition_count"])),
    (m4, "Model validation", f"{health['validation_accuracy']:.0%}"),
]
for column, label, value in metrics:
    with column:
        st.markdown(f'<div class="med-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tabs = st.tabs(["Overview", "Symptom check", "History", "Medications", "Profile", "First aid"])

with tabs[0]:
    left, right = st.columns([1.2, .8])
    with left:
        st.markdown("### Recent clinical activity")
        if history:
            for item in history[:5]:
                when = datetime.fromisoformat(item["created_at"]).strftime("%d %b %Y · %H:%M")
                st.markdown(
                    f'<div class="med-card urgency-{item["urgency"]}"><strong>{item["probable_condition"]}</strong><br><small>{when} · {item["urgency"]} · confidence {item["confidence"]:.0%}</small></div><br>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No assessments yet. Start with the Symptom check tab.")
    with right:
        st.markdown("### Safety principles")
        st.markdown(
            """
<div class="med-card">
<strong>1. Triage before prediction</strong><p>Emergency warning signs always take priority over the model result.</p>
<strong>2. No automatic prescribing</strong><p>Medication decisions stay with qualified clinicians and pharmacists.</p>
<strong>3. Private local storage</strong><p>Your profile, medication list, and assessment history remain in the local SQLite database.</p>
</div>
""",
            unsafe_allow_html=True,
        )

with tabs[1]:
    st.markdown("### Symptom assessment")
    st.markdown('<div class="disclaimer">This tool compares symptom patterns in a training dataset. It cannot confirm a diagnosis or replace examination, testing, or professional care.</div>', unsafe_allow_html=True)
    symptoms = get_symptoms()
    with st.form("assessment_form"):
        selected = st.multiselect(
            "Select at least two symptoms",
            symptoms,
            placeholder="Search symptoms such as headache, nausea, chest pain...",
        )
        duration = st.selectbox(
            "How long have symptoms been present?",
            ["Less than 6 hours", "6–24 hours", "2–3 days", "4–7 days", "1–4 weeks", "More than 1 month"],
        )
        severity: dict[str, int] = {}
        if selected:
            st.markdown("#### Severity")
            columns = st.columns(2)
            for index, symptom in enumerate(selected):
                with columns[index % 2]:
                    severity[symptom] = st.slider(symptom, 1, 10, 5, key=f"severity_{symptom}")
        submitted = st.form_submit_button("Run safety-first assessment", type="primary", use_container_width=True)
    if submitted:
        if len(selected) < 2:
            st.warning("Select at least two symptoms.")
        else:
            try:
                result = api(
                    "POST",
                    "/api/assessments",
                    json={"symptoms": selected, "severity": severity, "duration": duration},
                )
                st.session_state["active_assessment"] = result
                st.success("Assessment saved to your local history.")
            except RuntimeError as exc:
                st.error(str(exc))
    result = st.session_state.get("active_assessment")
    if result:
        st.markdown("---")
        render_result(result)
        st.markdown("### Ask about this result")
        messages = api("GET", f"/api/assessments/{result['id']}/chat")
        for message in messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        question = st.chat_input("Ask what this result means or what to discuss with a clinician")
        if question:
            api("POST", f"/api/assessments/{result['id']}/chat", json={"question": question})
            st.rerun()

with tabs[2]:
    st.markdown("### Assessment history")
    if not history:
        st.info("No saved assessments.")
    for item in history:
        title = f"{item['created_at'][:10]} · {item['probable_condition']} · {item['urgency']}"
        with st.expander(title):
            render_result(item)
            st.write("**Symptoms:** " + ", ".join(item["symptoms"]))
            if st.button("Delete assessment", key=f"delete_assessment_{item['id']}"):
                api("DELETE", f"/api/assessments/{item['id']}")
                if st.session_state.get("active_assessment", {}).get("id") == item["id"]:
                    st.session_state.pop("active_assessment", None)
                st.rerun()

with tabs[3]:
    st.markdown("### Medication organizer")
    st.caption("Record what a clinician has advised. This feature does not recommend medicines or doses.")
    with st.form("medication_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Medication name")
        dosage = c2.text_input("Dose as written on the label")
        schedule = st.text_input("Schedule", placeholder="For example: after breakfast")
        notes = st.text_area("Notes", placeholder="Prescriber, purpose, refill date, or cautions")
        add_med = st.form_submit_button("Add medication", type="primary")
    if add_med:
        if not name.strip() or not dosage.strip() or not schedule.strip():
            st.warning("Name, dose, and schedule are required.")
        else:
            api("POST", "/api/medications", json={"name": name, "dosage": dosage, "schedule": schedule, "notes": notes, "active": True})
            st.rerun()
    if medications:
        for med in medications:
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{med['name']}**  \n{med['dosage']} · {med['schedule']}  \n{med['notes'] or 'No notes'}")
                if c2.button("Remove", key=f"remove_med_{med['id']}"):
                    api("DELETE", f"/api/medications/{med['id']}")
                    st.rerun()
    else:
        st.info("No medications recorded.")

with tabs[4]:
    st.markdown("### Health profile")
    profile = api("GET", "/api/profile")
    sex_options = ["Female", "Male", "Intersex", "Prefer not to say"]
    blood_options = ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    with st.form("profile_form"):
        c1, c2, c3 = st.columns(3)
        full_name = c1.text_input("Full name", profile.get("full_name", ""))
        age_value = profile.get("age") if profile.get("age") is not None else 30
        age = c2.number_input("Age", 0, 120, int(age_value))
        sex_current = profile.get("sex", "Prefer not to say")
        sex = c3.selectbox("Sex", sex_options, index=sex_options.index(sex_current) if sex_current in sex_options else 3)
        blood_current = profile.get("blood_group", "Unknown")
        blood_group = st.selectbox("Blood group", blood_options, index=blood_options.index(blood_current) if blood_current in blood_options else 0)
        conditions = st.text_area("Existing conditions", profile.get("conditions", ""))
        allergies = st.text_area("Allergies", profile.get("allergies", ""))
        emergency_contact = st.text_input("Emergency contact", profile.get("emergency_contact", ""))
        save = st.form_submit_button("Save profile", type="primary")
    if save:
        api("PUT", "/api/profile", json={"full_name": full_name, "age": age, "sex": sex, "blood_group": blood_group, "conditions": conditions, "allergies": allergies, "emergency_contact": emergency_contact})
        st.success("Profile saved.")

with tabs[5]:
    st.markdown("### First-aid quick guides")
    guides = get_first_aid()
    topic = st.selectbox("Choose a topic", list(guides))
    st.markdown(f"#### {topic}")
    for index, step in enumerate(guides[topic], start=1):
        st.markdown(f"**{index}.** {step}")
    st.warning("These are general educational steps. Call local emergency services for severe or life-threatening symptoms.")
