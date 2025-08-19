# Release Notes

This release introduces significant enhancements to the AI Code Review CLI, focusing on improved user experience, flexibility, and robustness.

## New Features & Improvements

### Interactive User Experience

*   **Default Project Path Management**: The tool now remembers your preferred project path. On subsequent runs, it will prompt you to use the saved default or enter a new one.
*   **Interactive API Key & Model Setup**: Streamlined initial setup for Gemini API key and model selection. If not configured, the tool interactively guides you through the process and saves your choices to the `.env` file.
*   **Dynamic Model Selection**: When configuring the Gemini model, you can now choose from a dynamically fetched list of available models, ensuring compatibility with your API key.
*   **Model Name Highlighting**: The selected Gemini model name is now displayed in a conspicuous color in the console for better visibility.

### Flexible Code Review Modes

*   **Multiple Review Modes**: Introduced two distinct ways to review commits:
    *   **Review a Range of Commits (Cumulative Diff)**: Review all changes between a selected start and end commit, providing a single comprehensive review.
    *   **Review Selected Individual Commits**: Review multiple specific commits individually, with all separate reviews combined into one detailed report.
*   **Enhanced Commit Selection**: When specifying commit ranges or individual commits, the tool presents a user-friendly list of recent commits, including their short hash and commit message.
*   **Single Commit Review**: Improved handling for reviewing changes introduced by a single commit when the start and end commits are identical.

### Output & Reporting

*   **Modular Prompt Loading**: The AI prompt is now constructed by concatenating the content of all Markdown files within the `prompts/` directory, allowing for highly customizable and modular review instructions.
*   **Automated Report Saving**: AI review reports are automatically saved as Markdown files in a dedicated `results/` directory.
    *   **Structured Filenames**: Reports are named using a clear format: `YYYYMMDD_HHMMSS_model-name_serial.md` (e.g., `20250814_143000_gemini-1.0-pro_001.md`), including a serial number to prevent overwrites.

## Bug Fixes

*   **Python Version Compatibility**: Addressed syntax errors related to Python 2.7 by ensuring the tool explicitly requires and guides users to Python 3.9+.
*   **Prompt File Path Resolution**: Corrected the logic for locating the `prompts/` directory, resolving `FileNotFoundError` issues.
*   **API Key Handling**: Fixed `AttributeError` when `model_name` was `None` due to incorrect environment variable loading.

## Project Management & Cleanup

*   **Project Renaming**: The project directory was renamed from `your_codereview_tool` to `AICodeReviewCLI` for clarity.
*   **Git Repository Cleanup**: Cleaned up the Git repository by removing previously tracked files that should have been ignored (e.g., `.env`, `__pycache__`, `uv.lock`, build artifacts), ensuring `.gitignore` functions correctly.
*   **Removed Packaging Script**: The `package.sh` script and related documentation were removed as per user request.

---

Thank you for using the AI Code Review CLI!

---
## 0.0.1b2
- **Author:** Lewis
- **Date:** 2025-08-19 11:25:52 +0800
- **Changes:**
  - Implement default project path management

---
## 0.0.1b5
- **Features:**
  - Displays the current Git branch upon startup.
  - Prompts the user to run `git fetch` or `git pull` before selecting a branch to ensure local refs are up-to-date.
- **Fixes:**
  - Added `rich` to dependencies to resolve `ModuleNotFoundError`.
  - Corrected a bug that caused a `git git branch -a` invalid command error.