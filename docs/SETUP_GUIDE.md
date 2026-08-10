# Setup Guide

## Folder Structure

```
openai_simple_chatbot/
├── src/                    # Source code
│   ├── __init__.py
│   ├── app.py             # Main Gradio application
│   ├── context.py         # System prompt and context loading
│   ├── tools.py           # Tool definitions for the AI
│   └── styles.py          # UI styling and themes
├── docs/                   # Documentation and user data
│   ├── resume.pdf         # Your resume (PDF)
│   ├── summary.txt        # Your professional summary
│   └── SETUP_GUIDE.md     # This file
├── .env                    # Environment variables (not in git)
├── .env.example            # Template for environment variables
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Project configuration
└── README.md               # Main documentation
```

## Preparing Your Files

### 1. Update summary.txt

Edit `docs/summary.txt` with your professional information:
- Full name and current title
- Years of experience
- Key skills and expertise
- Current projects and focus areas
- Notable achievements

### 2. Add Your Resume

Place your resume as `docs/resume.pdf`:
```bash
cp /path/to/your/resume.pdf docs/resume.pdf
```

The chatbot will extract text from this PDF to provide detailed context about your background.

## Running the Application

From the project root, choose one of these methods:

```bash
# Option 1: Using the CLI command (easiest)
uv run chatbot

# Option 2: Using Python module
uv run python -m src.app

# Option 3: Activate the virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m src.app
```

The application will start at `http://localhost:7860`
