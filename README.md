# AI Code Review CLI

This is a powerful Command Line Interface (CLI) tool designed to automate and enhance your code review process using Artificial Intelligence. It works seamlessly with both **Git repositories** and **local directories**, leveraging large language models from providers like **Google** and **OpenAI** to provide insightful feedback on your code.

## Features

*   **Multi-Provider Support**: Natively supports different AI providers, starting with Google (Gemini models) and OpenAI (GPT models).
*   **Interactive Interface**: A user-friendly, menu-driven interface guides you through the entire setup and review process.
*   **Dual Review Modes**: Choose the mode that fits your needs:
    *   **Git Mode**: Analyzes code changes based on Git history. Perfect for reviewing feature branches or individual commits.
    *   **Folder Mode**: Directly reviews files and folders from your local filesystem. Ideal for projects not under version control or for getting feedback on uncommitted code.
*   **Flexible Configuration & Usage**:
    *   **Provider-First Setup**: Interactively configure your default AI provider, API key, and model.
    *   **Runtime Model Selection**: For any given review, choose to use your default model or temporarily select a different provider or model for a single session.
    *   **Save on the Fly**: If you like the model you used in a session, you can save it as your new default.
*   **Customizable Prompts**: Tailor the AI's review instructions by modifying simple Markdown files in the `prompts/` directory.
*   **Efficiency & Control**:
    *   *Empty Diff Check*: Automatically skips commits with no code changes to save time and API calls.
    *   *Debug Mode*: A `--debug` option lets you see the exact data sent to the AI without making an API call.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Python**: Version 3.9 or higher. ([Download Python](https://www.python.org/downloads/))
*   **uv**: A fast Python package installer and resolver. ([Install uv](https://astral.sh/uv/install.sh))
*   **Git**: Required for using the Git-based review mode. ([Download Git](https://git-scm.com/downloads))

## Setup & Installation

Follow these steps to get the AI Code Review CLI up and running:

1.  **Clone the Repository**
2.  **Navigate to the Project Directory**
3.  **Create and Activate Virtual Environment**:
    ```bash
    uv venv
    source .venv/bin/activate
    ```
4.  **Install Dependencies**: This command installs all necessary packages, including `google-generativeai` and `openai`.
    ```bash
    uv pip install -e .
    ```

## Configuration

The tool uses a `.env` file to store your configuration. The first time you run the tool or when using the `--config` flag, you'll be guided through an interactive setup:

1.  **Select Default Provider**: Choose your preferred default AI provider (e.g., "Google" or "OpenAI").
2.  **Enter API Key**: Provide the API key for the provider you selected. This will be stored securely in your `.env` file (e.g., as `GOOGLE_API_KEY` or `OPENAI_API_KEY`).
3.  **Select Default Model**: Choose a default model from a list fetched directly from the provider.

Your `.env` file will be automatically managed by the tool.

## Usage

Once set up, run the tool from the project root directory:

```bash
python -m codereview_tool.cli [--debug] [--config]
```

The tool will then guide you through the following interactive steps:

1.  **Confirm or Select AI Model**: You'll be asked if you want to use your saved default model. If you say no, you can choose a different provider and model for the current session.
2.  **Select Project Path**: Enter the absolute path to the project you wish to review.
3.  **Select Review Mode**: Choose between **Git Mode** and **Folder Mode**.
4.  **Follow-up Steps**: Depending on the mode, you will be guided through further selections (e.g., choosing commits in Git Mode or files in Folder Mode).

## Output

After the AI review is complete, the report will be saved as a Markdown file in the `AICodeReviewCLI/results/` directory.

*   **Filename Format**: `YYYYMMDD_HHMMSS_model-name_serial.md`
    *   Example: `20250814_143000_gemini-1.0-pro_001.md`

