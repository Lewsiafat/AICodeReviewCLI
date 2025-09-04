# AI Code Review CLI

This is a powerful Command Line Interface (CLI) tool designed to automate and enhance your code review process using Artificial Intelligence. It integrates seamlessly with Git repositories and leverages Google Gemini's capabilities to provide insightful feedback on your code changes.

## Features

*   **Interactive Interface**: A user-friendly, menu-driven interface guides you through the review process.
*   **Git Integration**: Automatically detects Git repositories, fetches branches, and lists recent commits for easy selection.
*   **Flexible Review Modes**:
    *   **Cumulative Diff Review**: Review all changes within a specified range of commits (e.g., a feature branch).
    *   **Individual Commit Review**: Get separate AI feedback for multiple selected individual commits, combined into a single comprehensive report.
*   **AI-Powered Feedback**: Utilizes Google Gemini to analyze code differences and provide suggestions, identify potential bugs, and highlight style violations.
*   **Configurable AI Model**: Easily select and manage the Gemini model used for reviews.
*   **Customizable Prompts**: Tailor the AI's review instructions by modifying simple Markdown files.
*   **Organized Output**: Saves review reports as Markdown files in a dedicated `results/` directory, with clear, timestamped, and model-named filenames.
*   **Empty Diff Check**: Automatically detects and skips commits with no actual code changes during individual commit review, preventing unnecessary AI API calls.
*   **Debug Mode**: Provides a `--debug` option to simulate AI reviews by printing diffs and prompts without making actual API calls, useful for development and cost management.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Git**: Version control system. ([Download Git](https://git-scm.com/downloads))
*   **Python**: Version 3.9 or higher. ([Download Python](https://www.python.org/downloads/))
*   **uv**: A fast Python package installer and resolver. ([Install uv](https://astral.sh/uv/install.sh))

## Setup & Installation

Follow these steps to get the AI Code Review CLI up and running:

1.  **Clone the Repository** (if you haven't already):
    ```bash
    git clone <repository_url>
    cd AICodeReviewCLI
    ```
    *(Replace `<repository_url>` with the actual URL of this repository.)*

2.  **Navigate to the Project Directory**:
    ```bash
    cd /path/to/AICodeReviewCLI
    ```
    *(Replace `/path/to/AICodeReviewCLI` with the actual path where you cloned the repository.)*

3.  **Create and Activate Virtual Environment**:
    ```bash
    uv venv
    source .venv/bin/activate
    ```
    *(You should see `(.venv)` appear in your terminal prompt, indicating the virtual environment is active.)*

4.  **Install Dependencies**:
    ```bash
    uv pip install -e .
    ```

## Configuration

### `.env` File (API Key & Model Selection)

This tool uses a `.env` file at the project root (`AICodeReviewCLI/.env`) to manage your Google Gemini API key and preferred AI model. The first time you run the tool, it will guide you through the setup process:

*   **Gemini API Key (`GEMINI_API_KEY`)**:
    *   If not found or invalid, the tool will prompt you to enter your API key.
    *   Your key will be saved securely in the `.env` file.
    *   You can obtain a Gemini API key from the [Google AI Studio](https://aistudio.google.com/app/apikey).
*   **Gemini Model (`GEMINI_MODEL`)**:
    *   If not configured, the tool will offer to fetch a list of available models for you to choose from.
    *   Alternatively, you can manually enter a model name (e.g., `gemini-1.5-pro-latest`).
    *   Your chosen model will be saved in the `.env` file.

### Custom Prompts (`prompts/` Directory)

You can customize the instructions given to the AI model by modifying or adding Markdown files (`.md`) within the `AICodeReviewCLI/prompts/` directory.

*   The tool reads **all** `.md` files in this directory and concatenates their content to form the complete prompt for the AI.
*   This allows you to modularize your review instructions (e.g., one file for general style, another for security considerations).

## Usage

Once set up, run the tool from the project root directory:

```bash
python -m codereview_tool.cli [--debug]
```

*   **`--debug`**: (Optional) Enable debug mode. When active, the tool will print the code diff and the prompt that would be sent to the AI, but will skip the actual AI API call. This is useful for debugging and understanding the AI's input without incurring API costs.

The tool will then guide you through the following interactive steps:

1.  **Project Path**: Enter the absolute path to the Git repository you wish to review.
2.  **Branch Selection**: Choose the branch you want to review from a list of available branches.
3.  **Review Mode**: Select how you want to review commits:
    *   **Review a range of commits (cumulative diff)**: You'll select a starting and ending commit from a list of recent commits. The AI will review all changes between these two points.
    *   **Review selected individual commits**: You'll select multiple specific commits from a list. The AI will review each selected commit individually, and all reviews will be combined into one report.
4.  **Commit Selection**: Depending on the review mode, you'll either select a range or individual commits from a list that includes their short hash and commit message.

## Output

After the AI review is complete, the report will be saved as a Markdown file in the `AICodeReviewCLI/results/` directory.

*   **Filename Format**: `YYYYMMDD_HHMMSS_model-name_serial.md`
    *   Example: `20250814_143000_gemini-1.0-pro_001.md`

