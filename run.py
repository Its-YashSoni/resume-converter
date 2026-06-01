"""
Run this file to start the Resume Converter server.

Usage:
  python run.py                    -> runs on port 5000
  PORT=5008 python run.py         -> runs on port 5008 (Mac/Linux)
  set PORT=5008 && python run.py  -> runs on port 5008 (Windows)
"""
import os
import sys

def load_env(filepath=".env"):
    if not os.path.exists(filepath):
        print("⚠️  .env file not found. Create one with: GROQ_API_KEY=your_key")
        return
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

load_env()

api_key = os.environ.get("GROQ_API_KEY", "")
if not api_key or api_key == "your_groq_api_key_here":
    print("\n" + "="*55)
    print("  ❌  GROQ_API_KEY is not set!")
    print("="*55)
    print("  1. Open the .env file in this folder")
    print("  2. Replace 'your_groq_api_key_here' with your key")
    print("  3. Get a free key at: https://console.groq.com")
    print("="*55 + "\n")
    sys.exit(1)

from app import app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*55)
    print("  ✅  Resume Converter is starting...")
    print(f"  🌐  Open in browser: http://localhost:{port}")
    print("  🛑  Press Ctrl+C to stop")
    print("="*55 + "\n")
    app.run(debug=False, port=port, host='0.0.0.0')
