import os, json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# ---- env / keys ----
load_dotenv()  # reads .env if present
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # set this!

# ---- LLM (Gemini) ----
try:
    import google.generativeai as genai
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        GEMINI_OK = True
    else:
        GEMINI_OK = False
except Exception:
    GEMINI_OK = False

# ---- app ----
app = FastAPI(title="EduAI Backend", version="1.0.0")

# CORS: keep open for hackathon demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ---- models ----
class Inp(BaseModel):
    text: str

# ---- helpers ----
def strip_json_fences(s: str) -> str:
    return (s or "").replace("```json", "").replace("```", "").strip()

def gemini_json(prompt: str):
    """
    Call Gemini 1.5 Flash and parse JSON-only response.
    Raises on parse error to trigger graceful mock fallback.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    r = model.generate_content(prompt)
    raw = strip_json_fences(getattr(r, "text", "") or "")
    return json.loads(raw)

def mock_response():
    return {
        "bullets": [
            "5 crisp bullets auto-generated.",
            "Low-bandwidth friendly output.",
            "Multilingual support is easy to add.",
            "MCQs with explanations for practice.",
            "Tracks improvement (future roadmap)."
        ],
        "questions": [
            {
                "q": "Data science mainly focuses on?",
                "options": ["A) Cooking", "B) Insights from data", "C) Painting", "D) Hardware"],
                "answer": "B",
                "explanation": "Goal is extracting insights from data."
            },
            {
                "q": "Which technique is common in data science?",
                "options": ["A) Origami", "B) Machine learning", "C) Astrology", "D) Woodcutting"],
                "answer": "B",
                "explanation": "ML is core to modern data workflows."
            }
        ]
    }

# ---- routes ----
@app.get("/")
def root():
    mode = "GEMINI" if GEMINI_OK else "MOCK"
    return {"ok": True, "mode": mode, "msg": "Use POST /summarize"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/summarize")
def summarize(inp: Inp):
    """
    Input:  {"text": "<content>"}
    Output: {"bullets":[...], "questions":[{q,options[],answer,explanation}, ...]}
    Always returns valid data (falls back to mock if API/parse fails).
    """
    # If no key or SDK not available → guaranteed mock (never breaks demo)
    if not GEMINI_OK:
        return mock_response()

    try:
        # 1) Summary (exact 5 bullets as JSON)
        p1 = (
            'Return ONLY JSON exactly like: '
            '{"bullets":["...","...","...","...","..."]}. '
            'Use 5 short, clear bullets for undergraduate students. '
            'Keep each bullet to one sentence.\n\n'
            f'Content:\n{inp.text}'
        )
        summary = gemini_json(p1)  # -> {"bullets":[...]}

        # 2) MCQs (5 items JSON array)
        p2 = (
            "Create 5 multiple-choice questions from the same content. "
            "Each question must have 4 options labeled A) ... B) ... C) ... D) ... "
            "Include the correct option LETTER and a one-sentence explanation. "
            "Return ONLY JSON array like: "
            '[{"q":"...","options":["A) ...","B) ...","C) ...","D) ..."],'
            '"answer":"B","explanation":"one short line"}].\n\n'
            f'Content:\n{inp.text}'
        )
        questions = gemini_json(p2)  # -> list

        return {"bullets": summary.get("bullets", []), "questions": questions}

    except Exception as e:
        # Graceful fallback so your demo NEVER fails
        demo = mock_response()
        # Add a hint for you (optional)
        demo["bullets"][0] = f"Demo mode due to: {str(e)[:90]}"
        return demo

