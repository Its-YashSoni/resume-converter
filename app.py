import os
import json
import uuid
import traceback
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import pdfplumber
from groq import Groq
from docx_builder import build_resume_docx

# Use absolute paths so Flask always finds static/templates
# regardless of which directory the server is launched from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'static'),
    template_folder=os.path.join(BASE_DIR, 'templates')
)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")
    return Groq(api_key=api_key)

def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()

def extract_resume_data_with_groq(raw_text):
    client = get_groq_client()

    prompt = f"""You are a resume parser. Extract all information from the resume text below and return it as a valid JSON object with exactly this structure. Fill every field with whatever is in the resume. If a field is not found, use an empty string "" or empty array [].

RESUME TEXT:
{raw_text}

Return ONLY a raw JSON object. No markdown, no code fences, no explanation. Start directly with {{ and end with }}.

{{
  "full_name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "github": "",
  "portfolio": "",
  "total_experience": "",
  "notice_period": "15 Days",
  "profile_summary": "",
  "education": [
    {{
      "institution": "",
      "degree": "",
      "year": "",
      "score": ""
    }}
  ],
  "skills": [
    {{
      "category": "",
      "items": ""
    }}
  ],
  "experience": [
    {{
      "company": "",
      "role": "",
      "duration": "",
      "location": "",
      "bullets": []
    }}
  ],
  "projects": [
    {{
      "title": "",
      "tech_stack": "",
      "date": "",
      "description": "",
      "bullets": []
    }}
  ],
  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "description": ""
    }}
  ],
  "co_curriculum": [],
  "extra_curriculum": [],
  "soft_skills": [],
  "languages": [],
  "training": [],
  "candidate_skills_for_table": [
    {{
      "skill_name": "",
      "projects_used": "",
      "years": "",
      "description": ""
    }},
    {{
      "skill_name": "",
      "projects_used": "",
      "years": "",
      "description": ""
    }},
    {{
      "skill_name": "",
      "projects_used": "",
      "years": "",
      "description": ""
    }}
  ]
}}

Rules:
- For total_experience: use "FRESHER" if no work experience, otherwise "1 YEAR", "2 YEARS" etc.
- For candidate_skills_for_table: pick the 3 most important skills. For years use "< 1 Yr" for freshers/interns, "1.0 Yrs" for 1 year.
- Keep all text concise and clean.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000,
    )

    content = response.choices[0].message.content.strip()

    if "```" in content:
        parts = content.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                content = part
                break

    start = content.find('{')
    end   = content.rfind('}')
    if start != -1 and end != -1:
        content = content[start:end+1]

    return json.loads(content)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/test')
def test_groq():
    try:
        client = get_groq_client()
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
        )
        return jsonify({"status": "ok", "response": resp.choices[0].message.content})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/convert', methods=['POST'])
def convert():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return jsonify({'error': 'GROQ_API_KEY is not set. Add it in your .env file or Render environment variables.'}), 500

    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    filename   = secure_filename(file.filename)
    unique_id  = str(uuid.uuid4())[:8]
    saved_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
    file.save(saved_path)

    try:
        raw_text = extract_text_from_pdf(saved_path)
        if not raw_text or len(raw_text.strip()) < 50:
            return jsonify({'error': 'Could not extract text from this PDF. Make sure it is a text-based PDF (not a scanned image).'}), 400

        resume_data = extract_resume_data_with_groq(raw_text)

        out_name = f"{unique_id}_converted.docx"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)
        build_resume_docx(resume_data, out_path)

        return jsonify({
            'success': True,
            'download_id': unique_id,
            'filename': out_name,
            'name': resume_data.get('full_name', 'Candidate')
        })

    except json.JSONDecodeError as e:
        return jsonify({'error': f'AI returned invalid data. Please try again. Detail: {str(e)}'}), 500
    except Exception as e:
        print("ERROR:\n", traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(saved_path):
            os.remove(saved_path)


@app.route('/download/<unique_id>')
def download(unique_id):
    for fname in os.listdir(OUTPUT_FOLDER):
        if fname.startswith(unique_id):
            path = os.path.join(OUTPUT_FOLDER, fname)
            return send_file(
                path,
                as_attachment=True,
                download_name=fname.replace(f"{unique_id}_", ""),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
    return jsonify({'error': 'File not found or expired'}), 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
