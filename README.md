# OpenAI Simple Chatbot

A digital twin chatbot web application powered by OpenAI that answers questions about a person's career, background, and experience.

## Overview

This project is a Gradio-based chatbot that uses OpenAI's API to create an AI representation of a person. It extracts information from a resume PDF and personal summary to provide context-aware responses about the person's professional background.

## Prerequisites

- **Python 3.12+** (required)
- **uv** package manager ([install here](https://docs.astral.sh/uv/getting-started/))
- OpenAI API key
- Pushover account credentials (optional, for notifications)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd openai-simple-chatbot
```

### 2. Install Dependencies

Using `uv` (recommended):

```bash
uv sync
```

This will:
- Create a virtual environment
- Install all dependencies from `pyproject.toml`
- Install the project in editable mode

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Add the following variables:

```env
# OpenAI Configuration
MODEL_NAME=gpt-4o  # or your preferred model (gpt-4, gpt-3.5-turbo, etc.)
OPENAI_API_KEY=sk-...  # Your OpenAI API key

# Pushover Notifications (optional)
PUSHOVER_USER=your_pushover_user_key
PUSHOVER_TOKEN=your_pushover_app_token
```

**How to get these values:**
- **OPENAI_API_KEY**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **PUSHOVER_USER & PUSHOVER_TOKEN** (optional): Get from [Pushover.net](https://pushover.net/) for push notifications

### 4. Prepare Your Files

Edit the files in the `docs/` folder:

- **`docs/resume.pdf`** — Your resume in PDF format. The chatbot extracts text from this for context about your background.
- **`docs/summary.txt`** — Your professional summary and key information. See the file for the template.

### 5. Run the Application

Choose one of these methods:

**Option 1: Using the CLI command (easiest)**
```bash
uv run chatbot
```

**Option 2: Using Python module**
```bash
uv run python -m src.app
```

**Option 3: Activate environment first**
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m src.app
```

The application will start at `http://localhost:7860`

## Project Structure

```
openai-simple-chatbot/
├── src/                       # Source code (Python package)
│   ├── __init__.py
│   ├── app.py                # Main Gradio application
│   ├── context.py            # System prompt and context loading
│   ├── tools.py              # Tool definitions and handlers
│   └── styles.py             # CSS and JavaScript styling
├── docs/                      # Documentation and user data
│   ├── resume.pdf            # Your resume (PDF) — replace with your file
│   ├── summary.txt           # Your professional summary — edit this file
│   └── SETUP_GUIDE.md        # Setup instructions
├── .env                       # Environment variables (NOT in git)
├── .env.example               # Template for .env
├── .gitignore                 # Git ignore rules
├── pyproject.toml             # Project configuration and dependencies
└── README.md                  # This file
```

## How It Works

1. **Context Loading** (`src/context.py`):
   - Extracts text from `docs/resume.pdf` using PyPDF
   - Reads `docs/summary.txt` for personal background
   - Constructs the system prompt with this information

2. **Chat Processing** (`src/app.py`):
   - Sends user messages to OpenAI's Chat Completion API
   - Handles tool calls (e.g., recording user contact info)
   - Maintains conversation history

3. **Tools** (`src/tools.py`):
   - Records user contact information
   - Records questions the AI couldn't answer
   - Sends Pushover notifications for follow-up items

4. **Styling** (`src/styles.py`):
   - Custom CSS for professional appearance
   - Responsive dark/light mode support
   - Example questions for users

## Configuration

### Changing the Model

Edit your `.env` file:

```env
# Available options: gpt-4o, gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.
MODEL_NAME=gpt-4o
```

### Customizing the UI

Edit `src/styles.py` to change:
- Color scheme (gold, blue, purple)
- Example questions
- CSS styling
- JavaScript behavior

### Modifying System Prompt

Edit `src/context.py` to adjust:
- The chatbot's personality and instructions
- How it uses the resume and summary
- Tool usage rules

## Development

### Install with Dev Dependencies

```bash
uv sync --with dev
```

### Run Tests

```bash
uv run pytest
```

### Adding Dependencies

```bash
uv add package-name
```

This will update `pyproject.toml` automatically.

## Troubleshooting

### "Missing resume.pdf"
Add your resume to `docs/`:
```bash
cp /path/to/your/resume.pdf docs/resume.pdf
```

### "OPENAI_API_KEY not found"
Make sure:
1. You have a `.env` file in the project root
2. It contains `OPENAI_API_KEY=sk-...`
3. The file is in `.gitignore` (not tracked in git)

### "Module not found" errors
Ensure dependencies are installed:
```bash
uv sync
```

### Port 7860 already in use
Gradio will use the next available port. Check the console output for the actual URL.

## Security Notes

- **Never commit `.env`** to git — it contains API keys.
- **Never commit `docs/resume.pdf` or `docs/summary.txt`** if they contain sensitive information.
- **Rotate API keys regularly** for security.
- Only share Pushover tokens with trusted systems.

## Dependencies

- **requests** — HTTP library
- **gradio** — Web UI framework
- **pypdf** — PDF text extraction
- **openai** — OpenAI Python client
- **python-dotenv** — Environment variable management

See `pyproject.toml` for version constraints.

## Contributing

When contributing:
1. Keep code compatible with Python 3.12+
2. Update `pyproject.toml` for new dependencies
3. Run tests before submitting
4. Document environment variables in `.env.example`

## License

[Add your license here]

## Support

For issues:
1. Check the Troubleshooting section
2. Verify dependencies: `uv sync`
3. Ensure `.env` is properly configured
4. Check [OpenAI API status](https://status.openai.com)
