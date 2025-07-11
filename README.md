# Codebase Analyzer

A tool that scans project directories and generates AI-powered codebase review plans.

## Features

- 📁 Scans directory structure while respecting `.gitignore` files
- 🌳 Generates clean ASCII tree representation
- 🤖 Uses GPT-4o to create comprehensive code review plans
- 📄 Exports results to markdown files

## Files

- `app.py` - Main entry point
- `directory_scanner.py` - Directory scanning utilities 
- `llm_client.py` - LLM integration for review plan generation
- `igpt.py` - Reference implementation (for development)

## Usage

1. Set up environment variables for Intel's API:
   ```
   APIGEE_AUTH_URL=<your_auth_url>
   APIGEE_CLIENT_ID=<your_client_id>
   APIGEE_CLIENT_SECRET=<your_client_secret>
   ```

2. Update the project path in `app.py`

3. Run the analyzer:
   ```bash
   python app.py
   ```

## Dependencies

- `pathspec` - For .gitignore file parsing
- `openai` - For LLM integration
- `httpx` - HTTP client with proxy support
- `requests` - For authentication requests
