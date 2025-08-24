import streamlit as st
import requests

st.title("📚 EduAI - Smart Summarizer + Quiz Generator")

# Text Input / File Upload
user_input = st.text_area("Paste your lecture notes here:")

if st.button("Summarize & Generate Quiz"):
    if user_input.strip() != "":
        # Call backend API
        response = requests.post("http://127.0.0.1:8000/summarize", 
                                 json={"text": user_input})
        
        if response.status_code == 200:
            data = response.json()
            
            # Show summary
            st.subheader("Summary")
            for bullet in data.get("bullets", []):
                st.write("- ", bullet)

            # Show quiz
            st.subheader("Quiz Questions")
            for i, q in enumerate(data.get("questions", []), 1):
                st.write(f"**Q{i}. {q['q']}**")
                for opt in q['options']:
                    st.write(opt)
                st.caption(f"Answer: {q['answer']} - {q['explanation']}")
        else:
            st.error("Backend error, please try again.")
