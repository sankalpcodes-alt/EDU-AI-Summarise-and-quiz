import os, requests, streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
st.set_page_config(page_title="EduAI", page_icon="📚")
st.title("📚 EduAI – Smart Summarizer + Quiz")

def call_backend(txt: str):
    try:
        # NOTE: first try {"text": ...}. If 422, we'll try {"content": ...}
        r = requests.post(f"{BACKEND_URL}/summarize",
                          json={"text": txt}, timeout=90)
        if r.status_code == 422:
            r = requests.post(f"{BACKEND_URL}/summarize",
                              json={"content": txt}, timeout=90)
        return r
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")
        return None

txt = st.text_area("Paste your lecture notes here:", height=180,
                   value="Data science is an interdisciplinary field...")

if st.button("Summarize & Generate Quiz", type="primary"):
    if not txt.strip():
        st.warning("Kuch text daalo 🙂")
        st.stop()

    with st.spinner("Generating..."):
        r = call_backend(txt)

    if not r:
        st.stop()

    # Always show raw for debugging first
    st.caption("Raw API response (debug)")
    st.code(r.text, language="json")

    if r.status_code != 200:
        st.error(f"Backend error: {r.status_code}")
        st.stop()

    try:
        data = r.json()
    except Exception:
        st.error("Response JSON parse failed.")
        st.stop()

    # Flexible keys (handles different backend schemas)
    bullets = (
        data.get("bullets")
        or data.get("summary")
        or data.get("points")
        or data.get("highlights")
        or []
    )
    questions = (
        data.get("questions")
        or data.get("mcqs")
        or data.get("quiz")
        or []
    )

    st.subheader("Summary")
    if isinstance(bullets, list) and bullets:
        for b in bullets:
            st.write(f"- {b}")
    elif isinstance(bullets, str) and bullets:
        for line in bullets.split("\n"):
            st.write(f"- {line}")
    else:
        st.info("No summary found in response.")

    st.divider()
    st.subheader("Quiz Questions")
    if questions:
        for i, q in enumerate(questions, 1):
            qtext = q.get("q") or q.get("question") or ""
            opts  = q.get("options") or q.get("choices") or []
            ans   = q.get("answer") or q.get("correct") or ""
            exp   = q.get("explanation") or q.get("why") or ""
            st.markdown(f"**Q{i}. {qtext}**")
            for opt in opts:
                st.write(opt)
            if ans:
                st.caption(f"Answer: {ans} — {exp}")
    else:
        st.info("No questions found in response.")

