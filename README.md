# Resume Converter

Converts any PDF resume into the **Contractor Connect Skill Evaluation Sheet** format (3-page DOCX).

Built with Flask + Groq AI (llama-3.3-70b).

## Local Setup

```bash
pip install -r requirements.txt
# Add your key to .env:  GROQ_API_KEY=gsk_xxx
PORT=5008 python run.py
```

Open http://localhost:5008
