from . import git_utils
from . import llm_integration
import os
import sys
import questionary
import argparse # Added
from dotenv import load_dotenv, set_key
import google.generativeai as genai
import datetime
import subprocess
import platform
from rich import print
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

console = Console()

def open_path(path):
    """Opens a file or directory in the default application in a cross-platform way."""
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", path], check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"[bold red]Error opening '{path}': {e}[/bold red]")

def setup_configuration(is_reconfig=False):
    """
    Handles API key and model name configuration.
    """
    script_dir = os.path.dirname(__file__)
    tool_root_dir = os.path.dirname(os.path.dirname(script_dir))
    dotenv_path = os.path.join(tool_root_dir, ".env")
    load_dotenv(dotenv_path=dotenv_path)

    # --- API Key Setup ---
    api_key = os.getenv("GEMINI_API_KEY")
    if is_reconfig or not api_key or api_key == "YOUR_API_KEY_HERE":
        if is_reconfig:
            print("Re-configuring Gemini API key.")
        else:
            print("Gemini API key not found or is invalid.")
        api_key_input = questionary.text("Please enter your Gemini API key:", default=api_key if api_key != "YOUR_API_KEY_HERE" else "").ask()
        if not api_key_input:
            print("API key is required. Exiting.")
            return False, None
        set_key(dotenv_path, "GEMINI_API_KEY", api_key_input)
        api_key = api_key_input
        print("API key saved to .env file.")
    
    try:
        genai.configure(api_key=api_key)
        if is_reconfig:
             print("Gemini API key configured successfully.")
    except Exception as e:
        print(f"Failed to configure Gemini API: {e}")
        return False, None

    # --- Model Name Setup ---
    model_name = os.getenv("GEMINI_MODEL")
    if is_reconfig or not model_name:
        if is_reconfig:
            print("\nRe-configuring model name.")
        else:
            print("\nModel name is not configured.")
        
        use_list = questionary.confirm("Would you like to select from a list of available models?").ask()

        if use_list:
            try:
                print("Fetching available models...")
                all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                if not all_models:
                    print("Could not find any supported models for your API key.")
                    return False, None

                # Sort to show pro models first, then flash, then others
                pro_models = sorted([m for m in all_models if 'pro' in m])
                flash_models = sorted([m for m in all_models if 'flash' in m])
                other_models = sorted([m for m in all_models if 'pro' not in m and 'flash' not in m])
                sorted_models = pro_models + flash_models + other_models

                model_name = questionary.select("Select a model:", choices=sorted_models, default=model_name).ask()

            except Exception as e:
                print(f"Could not fetch model list: {e}")
                model_name = questionary.text("Please enter the model name manually (e.g., gemini-1.5-pro-latest):", default=model_name or "").ask()
        else:
            model_name = questionary.text("Please enter the model name to use (e.g., gemini-1.5-pro-latest):", default=model_name or "").ask()

        if not model_name:
            print("Model name is required. Exiting.")
            return False, None
        
        set_key(dotenv_path, "GEMINI_MODEL", model_name)
        print(f"Model name '{model_name}' saved to .env file.")

    return True, model_name

def setup_project_path(is_reconfig=False):
    """Handles default project path configuration."""
    script_dir = os.path.dirname(__file__)
    tool_root_dir = os.path.dirname(os.path.dirname(script_dir))
    dotenv_path = os.path.join(tool_root_dir, ".env")
    load_dotenv(dotenv_path=dotenv_path)

    default_project_path = os.getenv("DEFAULT_PROJECT_PATH")
    project_path = None

    if is_reconfig:
        print("\nRe-configuring default project path.")
        project_path = questionary.text("Enter the new absolute path for your project:", default=default_project_path or "").ask()
    elif default_project_path and os.path.isdir(default_project_path):
        use_default = questionary.confirm(f"Use default project path: {default_project_path}?").ask()
        if use_default:
            project_path = default_project_path
        else:
            project_path = questionary.text("What is the absolute path to your project?").ask()
    else:
        project_path = questionary.text("What is the absolute path to your project?").ask()

    if not project_path or not os.path.isdir(project_path):
        print("Invalid project path provided. Exiting.")
        return None

    if project_path != default_project_path:
        save_as_default = questionary.confirm("Save this as default project path for future use?").ask()
        if save_as_default:
            set_key(dotenv_path, "DEFAULT_PROJECT_PATH", project_path)
            print(f"Default project path saved: {project_path}")
    
    return project_path

def _get_prompt(prompts_dir):
    """Constructs the full prompt from all .md files in the prompts directory."""
    prompt_parts = []
    try:
        for filename in os.listdir(prompts_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(prompts_dir, filename)
                with open(file_path, "r", encoding='utf-8') as f:
                    prompt_parts.append(f.read())
        if not prompt_parts:
            print(f"Warning: No prompt files (.md) found in {prompts_dir}")
            return ""
        return "\n\n".join(prompt_parts)
    except FileNotFoundError:
        print(f"Error: Could not find the prompts directory at {prompts_dir}")
        return None

def _save_review(review, results_dir, model_name, review_title="AI Code Review"):
    """Saves the review content to a timestamped markdown file."""
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_model_name = model_name.replace('/', '_')
    
    serial = 1
    while True:
        filename = f"{timestamp}_{sanitized_model_name}_{serial:03d}.md"
        file_path = os.path.join(results_dir, filename)
        if not os.path.exists(file_path):
            break
        serial += 1
    
    try:
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(f"# {review_title}\n\n")
            f.write(review)
        print("\n--- AI Review complete ---")
        print(f"Review saved to: {file_path}")
        print("--- End AI Review ---")

        open_path(results_dir)
        if questionary.confirm("Do you want to open the report file?").ask():
            open_path(file_path)
    except IOError as e:
        print(f"\nError saving review to file: {e}")
        print("\n--- AI Review ---")
        print(review)
        print("--- End AI Review ---")

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="AI Code Review Tool CLI.")
    parser.add_argument('--config', action='store_true', help='Enter configuration mode.')
    parser.add_argument('--setup', action='store_true', help='Enter setup mode (alias for --config).')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode to print diff and prompt without calling AI API.')
    args = parser.parse_args()

    # --- Handle Re-configuration Flag ---
    if args.config or args.setup:
        print("Entering setup mode...")
        setup_configuration(is_reconfig=True)
        setup_project_path(is_reconfig=True)
        print("\nConfiguration complete.")
        return
    
    debug_mode = args.debug

    if debug_mode:
        print("[bold yellow]DEBUG MODE ENABLED: AI API calls will be skipped.[/bold yellow]")

    print("Welcome to the AI Code Review Tool!")
    
    success, model_name = setup_configuration()
    if not success:
        return

    project_path = setup_project_path()
    if not project_path:
        return

    print(f"Analyzing project at: {project_path}")

    # --- Mode Selection ---
    review_mode_top = questionary.select(
        "Select the review mode:",
        choices=[
            "Git Mode (review commits)",
            "Folder Mode (review specific files/folders)"
        ]
    ).ask()

    script_dir = os.path.dirname(__file__)
    tool_root_dir = os.path.dirname(os.path.dirname(script_dir))
    prompts_dir = os.path.join(tool_root_dir, "prompts")
    results_dir = os.path.join(tool_root_dir, "results")

    # --- Git Mode ---
    if review_mode_top == "Git Mode (review commits)":
        if not git_utils.is_git_repository(project_path):
            print("[bold red]Error: 'Git Mode' was selected, but this is not a Git repository.[/bold red]")
            return

        print("This is a Git repository.")
        try:
            current_branch = git_utils.get_current_branch(project_path)
            if current_branch:
                print(f"Currently on branch: [bold cyan]{current_branch}[/bold cyan]")
        except Exception as e:
            print(f"[yellow]Could not determine the current branch: {e}[/yellow]")

        if questionary.confirm("Do you want to run 'git fetch' or 'git pull' to get the latest changes before proceeding?").ask():
            action = questionary.select(
                "Which command do you want to run?",
                choices=[
                    "git fetch",
                    "git pull",
                    "cancel"
                ]
            ).ask()

            if action == "git fetch":
                try:
                    print("Running 'git fetch'...")
                    git_utils.git_fetch(project_path)
                    print("[bold green]Fetch successful.[/bold green]")
                except subprocess.CalledProcessError as e:
                    print(f"[bold red]Error during git fetch:[/bold red]\n{e.stderr}")
            elif action == "git pull":
                try:
                    print("Running 'git pull'...")
                    git_utils.git_pull(project_path)
                    print("[bold green]Pull successful.[/bold green]")
                except subprocess.CalledProcessError as e:
                    print(f"[bold red]Error during git pull:[/bold red]\n{e.stderr}")

        branches = git_utils.get_branches(project_path)
        if not branches: return
        branch = questionary.select("Select the branch to review:", choices=branches).ask()
        if not branch: return

        review_mode_git = questionary.select(
            "How would you like to review commits?",
            choices=["Review a range of commits (cumulative diff)", "Review selected individual commits"]
        ).ask()

        prompt = _get_prompt(prompts_dir)
        if prompt is None: return

        if review_mode_git == "Review a range of commits (cumulative diff)":
            recent_commits = git_utils.get_recent_commits(project_path)
            if not recent_commits: return
            from_commit_str = questionary.select("Select the starting commit:", choices=recent_commits).ask()
            to_commit_str = questionary.select("Select the ending commit:", choices=recent_commits).ask()
            from_commit, to_commit = from_commit_str.split(' ')[0], to_commit_str.split(' ')[0]
            
            diff = git_utils.get_commit_diff(project_path, from_commit, to_commit) if from_commit != to_commit else git_utils.get_single_commit_changes(project_path, from_commit)
            
            if diff:
                with Live(Spinner("dots", text="Generating AI code review..."), console=console, transient=True):
                    review = llm_integration.get_code_review(diff, prompt, model_name, debug_mode=debug_mode)
                _save_review(review, results_dir, model_name, f"Review for {from_commit[:7]}..{to_commit[:7]}")
            else:
                print("Could not get diff for the selected range.")

        elif review_mode_git == "Review selected individual commits":
            recent_commits = git_utils.get_recent_commits(project_path)
            if not recent_commits: return
            selected_commit_strs = questionary.checkbox("Select individual commits:", choices=recent_commits).ask()
            if not selected_commit_strs: return

            selected_commit_hashes = [s.split(' ')[0] for s in selected_commit_strs]
            combined_review = []
            with Live(Spinner("dots", text=""), console=console, transient=True) as live:
                for i, commit_hash in enumerate(selected_commit_hashes):
                    live.update(Spinner("dots", text=f"({i+1}/{len(selected_commit_hashes)}) Reviewing: {commit_hash[:7]}"))
                    diff = git_utils.get_single_commit_changes(project_path, commit_hash)
                    
                    if not diff or 'diff --git' not in diff:
                        live.console.print(f"[yellow]Skipped commit {commit_hash[:7]}: No file changes found.[/yellow]")
                        review_part = f"## Review for Commit: {commit_hash}\n\nSkipped: No file changes found."
                    else:
                        individual_review = llm_integration.get_code_review(diff, prompt, model_name, debug_mode=debug_mode)
                        review_part = f"## Review for Commit: {commit_hash}\n\n{individual_review}"
                    combined_review.append(review_part)
            
            _save_review("\n\n---\n\n".join(combined_review), results_dir, model_name, "Individual Commits Review")

    # --- Folder Mode ---
    elif review_mode_top == "Folder Mode (review specific files/folders)":
        selected_paths = []
        current_path = project_path
        
        ignore_list = ".git", ".venv", "__pycache__", ".DS_Store", "node_modules", "build", "dist"

        while True:
            try:
                items = os.listdir(current_path)
                # Filter out ignored items
                items = [item for item in items if item not in ignore_list]
            except OSError as e:
                print(f"[bold red]Error reading directory {current_path}: {e}[/bold red]")
                break

            dirs = sorted([d for d in items if os.path.isdir(os.path.join(current_path, d))])
            files = sorted([f for f in items if os.path.isfile(os.path.join(current_path, f))])

            choices = [
                questionary.Choice("[DONE - Proceed to Review]", value="##DONE##"),
                questionary.Choice("[..] (Go Up)", value="##UP##")
            ]
            # Add directories and files as choices
            choices.extend([questionary.Choice(f"{d}/", value=d) for d in dirs])
            choices.extend([questionary.Choice(f, value=f) for f in files])

            selection = questionary.checkbox(
                f"Browsing: {os.path.relpath(current_path, project_path) or '.'}. Select items to review or a folder to enter.",
                choices=choices
            ).ask()

            if not selection:
                break
            
            if "##DONE##" in selection:
                break

            nav_dirs = [s for s in selection if s in dirs]
            
            if nav_dirs:
                if len(nav_dirs) > 1:
                    print("[bold yellow]Warning: Please select only one folder to navigate into at a time.[/bold yellow]")
                else:
                    current_path = os.path.join(current_path, nav_dirs[0])
                    # Don't add the navigated folder to selection, just change path
                    selection.remove(nav_dirs[0])

            if "##UP##" in selection:
                parent_path = os.path.dirname(current_path)
                if parent_path and parent_path != current_path:
                    current_path = parent_path
                selection.remove("##UP##")

            # Add remaining selected files/folders to the list
            for item in selection:
                if item in files:
                    full_path = os.path.join(current_path, item)
                    if full_path not in selected_paths:
                        selected_paths.append(full_path)
                        print(f"[green]Added file:[/green] {os.path.relpath(full_path, project_path)}")
                elif item in dirs: # This handles selecting a whole folder without entering it
                    full_path = os.path.join(current_path, item)
                    if full_path not in selected_paths:
                        selected_paths.append(full_path)
                        print(f"[green]Added folder:[/green] {os.path.relpath(full_path, project_path)}")


        if not selected_paths:
            print("No files or folders were selected for review.")
            return

        print("\n[bold]Selected paths for review:[/bold]")
        for path in selected_paths:
            print(f"- {os.path.relpath(path, project_path)}")

        content_parts = []
        with Live(Spinner("dots", text="Reading selected files..."), console=console, transient=True) as live:
            for path in selected_paths:
                if os.path.isfile(path):
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content_parts.append(f"--- File: {os.path.relpath(path, project_path)} ---\n\n{f.read()}")
                    except Exception as e:
                        live.console.print(f"[yellow]Could not read file {path}: {e}[/yellow]")
                elif os.path.isdir(path):
                    for root, _, files_in_dir in os.walk(path):
                        for file in files_in_dir:
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content_parts.append(f"--- File: {os.path.relpath(file_path, project_path)} ---\n\n{f.read()}")
                            except Exception as e:
                                live.console.print(f"[yellow]Could not read file {file_path}: {e}[/yellow]")
        
        if not content_parts:
            print("[bold red]Error: Could not read any content from the selected paths.[/bold red]")
            return

        full_content = "\n\n".join(content_parts)
        prompt = _get_prompt(prompts_dir)
        if prompt is None: return

        with Live(Spinner("dots", text="Generating AI code review..."), console=console, transient=True):
            review = llm_integration.get_code_review(full_content, prompt, model_name, debug_mode=debug_mode)
        
        _save_review(review, results_dir, model_name, "Folder Content Review")


if __name__ == "__main__":
    main()