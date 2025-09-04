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
    
    debug_mode = args.debug # Get debug mode status

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

    if git_utils.is_git_repository(project_path):
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
                    questionary.Choice("git fetch", value="fetch"),
                    questionary.Choice("git pull", value="pull"),
                    questionary.Choice("cancel", value="cancel")
                ]
            ).ask()

            if action == "fetch":
                try:
                    print("Running 'git fetch'...")
                    git_utils.git_fetch(project_path)
                    print("[bold green]Fetch successful.[/bold green]")
                except subprocess.CalledProcessError as e:
                    print(f"[bold red]Error during git fetch:[/bold red]\n{e.stderr}")
            elif action == "pull":
                try:
                    print("Running 'git pull'...")
                    git_utils.git_pull(project_path)
                    print("[bold green]Pull successful.[/bold green]")
                except subprocess.CalledProcessError as e:
                    print(f"[bold red]Error during git pull:[/bold red]\n{e.stderr}")

        branches = git_utils.get_branches(project_path)
        if not branches:
            print("No branches found.")
            return

        branch = questionary.select("Select the branch to review:", choices=branches).ask()

        if branch:
            print(f"Current branch is: {branch}")
            
            review_mode = questionary.select(
                "How would you like to review commits?",
                choices=["Review a range of commits (cumulative diff)", "Review selected individual commits"]
            ).ask()

            if review_mode == "Review a range of commits (cumulative diff)":
                recent_commits = git_utils.get_recent_commits(project_path)
                if not recent_commits:
                    print("No recent commits found.")
                    return

                from_commit_str = questionary.select(
                    "Select the starting commit:", choices=recent_commits
                ).ask()
                to_commit_str = questionary.select(
                    "Select the ending commit:", choices=recent_commits
                ).ask()

                from_commit = from_commit_str.split(' ')[0]
                to_commit = to_commit_str.split(' ')[0]

                if from_commit == to_commit:
                    diff = git_utils.get_single_commit_changes(project_path, from_commit)
                else:
                    diff = git_utils.get_commit_diff(project_path, from_commit, to_commit)
                
                if diff:
                    script_dir = os.path.dirname(__file__)
                    tool_root_dir = os.path.dirname(os.path.dirname(script_dir))
                    prompts_dir = os.path.join(tool_root_dir, "prompts")
                    
                    prompt_parts = []
                    try:
                        for filename in os.listdir(prompts_dir):
                            if filename.endswith(".md"):
                                file_path = os.path.join(prompts_dir, filename)
                                with open(file_path, "r") as f:
                                    prompt_parts.append(f.read())
                    except FileNotFoundError:
                        print(f"Error: Could not find the prompts directory at {prompts_dir}")
                        return
                    
                    prompt = "\n\n".join(prompt_parts)
                    if not prompt:
                        print("Error: No prompt content found in the prompts directory.")
                        return

                    with Live(Spinner("dots", text="Generating AI code review, please wait..."), console=console, transient=True):
                        review = llm_integration.get_code_review(diff, prompt, model_name, debug_mode=debug_mode)
                    
                    results_dir = os.path.join(tool_root_dir, "results")
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
                        with open(file_path, "w") as f:
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

                else:
                    print("Could not get diff for the selected range.")

            elif review_mode == "Review selected individual commits":
                recent_commits = git_utils.get_recent_commits(project_path)
                if not recent_commits:
                    print("No recent commits found.")
                    return

                selected_commit_strs = questionary.checkbox(
                    "Select individual commits to review:", choices=recent_commits
                ).ask()

                if not selected_commit_strs:
                    print("No commits selected for individual review.")
                    return
                
                selected_commit_hashes = [s.split(' ')[0] for s in selected_commit_strs]

                combined_review_content = []
                spinner = Spinner("dots", text="Generating AI code reviews...")
                with Live(spinner, console=console, transient=True) as live:
                    for i, commit_hash in enumerate(selected_commit_hashes):
                        live.update(Spinner("dots", text=f"({i+1}/{len(selected_commit_hashes)}) Reviewing commit: {commit_hash}"))
                        
                        single_commit_diff = git_utils.get_single_commit_changes(project_path, commit_hash)

                        # If diff is None (error) or contains no actual file changes
                        if not single_commit_diff or 'diff --git' not in single_commit_diff:
                            live.console.print(f"[bold yellow]提示：[/bold yellow]提交 [cyan]{commit_hash[:7]}[/cyan] 沒有實際的程式碼變更，已跳過。")
                            combined_review_content.append(f"## Review for Commit: {commit_hash}\n\n此提交沒有實際的程式碼變更，已跳過 (Skipped as this commit contains no file changes).\n\n---")
                            continue

                        # If we are here, the diff is valid and has content
                        script_dir = os.path.dirname(__file__)
                        tool_root_dir = os.path.dirname(os.path.dirname(script_dir))
                        prompts_dir = os.path.join(tool_root_dir, "prompts")
                        prompt_parts = []
                        try:
                            for filename in os.listdir(prompts_dir):
                                if filename.endswith(".md"):
                                    file_path = os.path.join(prompts_dir, filename)
                                    with open(file_path, "r") as f:
                                        prompt_parts.append(f.read())
                        except FileNotFoundError:
                            print(f"Error: Could not find the prompts directory at {prompts_dir}")
                            return
                        prompt = "\n\n".join(prompt_parts)

                        individual_review = llm_integration.get_code_review(single_commit_diff, prompt, model_name, debug_mode=debug_mode)
                        combined_review_content.append(f"## Review for Commit: {commit_hash}\n\n{individual_review}\n\n---")
                
                review = "\n\n".join(combined_review_content)
                
                results_dir = os.path.join(tool_root_dir, "results")
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
                    with open(file_path, "w") as f:
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
    else:
        print("This is not a Git repository.")

if __name__ == "__main__":
    main()