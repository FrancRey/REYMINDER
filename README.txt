REYMINDER — beginner starter project
====================================

REQUIREMENTS
- Python 3.10 or newer
- Visual Studio Code
- Python extension for VS Code (Microsoft)
- Internet is only needed to install Flask the first time.

SETUP (Windows)
1. Extract this folder somewhere easy to find, such as Documents.
2. Open VS Code -> File -> Open Folder -> choose the REYMINDER folder.
3. Open Terminal -> New Terminal.
4. Create a virtual environment:
       py -m venv .venv
5. Activate it in PowerShell:
       .\.venv\Scripts\Activate.ps1
   If PowerShell blocks activation, use Command Prompt terminal and run:
       .venv\Scripts\activate.bat
6. Install Flask:
       python -m pip install -r requirements.txt
7. Run the site:
       python app.py
8. Open this address in your browser:
       http://127.0.0.1:5000

FIRST TEST
- Click Create account and register with a test email and a password of 8+ characters.
- Log in.
- Add a reminder with a title and date/time.
- Mark it complete or delete it.
- Try the light/dark toggle.
- Try Forgot password. For this local demo, the reset link is printed in the VS Code terminal. No email is sent.

IMPORTANT SECURITY NOTES
- This is a learning prototype, not production-ready authentication.
- Before deployment, set a strong random REYMINDER_SECRET_KEY environment variable, disable debug mode, use HTTPS, and configure real password-reset email delivery.
- Never commit .venv, reyminder.db, secrets, or real personal data to a public repository.
- Use test information for your class demonstration.
- Passwords are stored as hashes, not plain text.
- Reminder access is scoped to the logged-in user.
- The password reset link is for local testing only; do not deploy this reset flow publicly.
- SQLite data lives in reyminder.db in this project folder. Some free hosting platforms have ephemeral storage, so use a managed database for a persistent deployed version.

PROJECT FILES
app.py                    Python backend and routes
templates/                HTML pages
static/css/style.css      Styling and light/dark themes
static/js/main.js         Password visibility and theme toggle
reyminder.db              Created automatically when you run app.py
