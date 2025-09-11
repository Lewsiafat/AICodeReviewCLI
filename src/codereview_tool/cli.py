from . import git_utils
from .llm_integration import SUPPORTED_PROVIDER_NAMES, get_provider_from_name
import os
import re
import questionary
import argparse
from dotenv import load_dotenv, set_key
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

def _get_tool_root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def _get_dotenv_path():
    return os.path.join(_get_tool_root_dir(), ".env")

def _sanitize_for_env(name):
    """Sanitizes a string to be a valid environment variable name."""
    return re.sub(r'[^A-Z0-9_]', '', re.sub(r'[\s\(\)]', '_', name).upper()).rstrip('_')

def setup_configuration(is_reconfig=False):
    """Handles multi-provider API key and model name configuration."""
    dotenv_path = _get_dotenv_path()
    load_dotenv(dotenv_path=dotenv_path)

    provider_name = os.getenv("DEFAULT_PROVIDER")
    if is_reconfig or not provider_name:
        if is_reconfig: print("\n[bold]Re-configuring default provider.[/bold]")
        provider_name = questionary.select("Select the default AI provider:", choices=SUPPORTED_PROVIDER_NAMES).ask()
        if not provider_name: return False
        set_key(dotenv_path, "DEFAULT_PROVIDER", provider_name)

    api_key_var = f"{_sanitize_for_env(provider_name)}_API_KEY"
    api_key = os.getenv(api_key_var)
    if is_reconfig or not api_key:
        if is_reconfig: print(f"\n[bold]Re-configuring {provider_name} API key.[/bold]")
        api_key_input = questionary.text(f"Please enter your {provider_name} API key:").ask()
        if not api_key_input: return False
        set_key(dotenv_path, api_key_var, api_key_input)
        api_key = api_key_input

    try:
        print(f"Initializing {provider_name} to fetch models...")
        provider = get_provider_from_name(provider_name, api_key)
        models = provider.get_models()
        if not models:
            print(f"[bold red]No models found for {provider_name}. Please check your API key.[/bold red]")
            return False
    except Exception as e:
        print(f"[bold red]Failed to connect to {provider_name}: {e}[/bold red]")
        return False

    default_model = os.getenv("DEFAULT_MODEL")
    if is_reconfig or not default_model or default_model not in models:
        if is_reconfig: print("\n[bold]Re-configuring default model.[/bold]")
        default_model = questionary.select("Select a default model:", choices=models).ask()
        if not default_model: return False
        set_key(dotenv_path, "DEFAULT_MODEL", default_model)

    print("\n[bold green]Configuration successful.[/bold green]")
    return True

def setup_project_path(is_reconfig=False):
    dotenv_path = _get_dotenv_path()
    load_dotenv(dotenv_path=dotenv_path)
    default_project_path = os.getenv("DEFAULT_PROJECT_PATH")
    project_path = None
    if is_reconfig:
        project_path = questionary.text("Enter the new absolute path for your project:", default=default_project_path or "").ask()
    elif default_project_path and os.path.isdir(default_project_path):
        if questionary.confirm(f"Use default project path: {default_project_path}?").ask():
            project_path = default_project_path
        else:
            project_path = questionary.text("What is the absolute path to your project?").ask()
    else:
        project_path = questionary.text("What is the absolute path to your project?").ask()
    if not project_path or not os.path.isdir(project_path):
        print("Invalid project path provided. Exiting.")
        return None
    if project_path != default_project_path:
        if questionary.confirm("Save this as default project path for future use?").ask():
            set_key(dotenv_path, "DEFAULT_PROJECT_PATH", project_path)
            print(f"Default project path saved: {project_path}")
    return project_path

def _get_prompt(prompts_dir):
    prompt_parts = []
    try:
        for filename in os.listdir(prompts_dir):
            if filename.endswith(".md"):
                with open(os.path.join(prompts_dir, filename), "r", encoding='utf-8') as f:
                    prompt_parts.append(f.read())
        return "\n\n".join(prompt_parts)
    except FileNotFoundError:
        return None

def _save_review(review, results_dir, model_name, review_title):
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_model_name = model_name.replace('/', '_').replace(':', '_')
    serial = 1
    while True:
        filename = f"{timestamp}_{sanitized_model_name}_{serial:03d}.md"
        file_path = os.path.join(results_dir, filename)
        if not os.path.exists(file_path): break
        serial += 1
    try:
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(f"# {review_title}\n\n{review}")
        print(f"\n[green]Review saved to: {file_path}[/green]")
        open_path(results_dir)
        if questionary.confirm("Do you want to open the report file?").ask():
            open_path(file_path)
    except IOError as e:
        print(f"\n[red]Error saving review: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="AI Code Review Tool CLI.")
    parser.add_argument('--config', '--setup', action='store_true', help='Enter configuration mode.')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode.')
    args = parser.parse_args()
    dotenv_path = _get_dotenv_path()

    if args.config:
        setup_configuration(is_reconfig=True)
        setup_project_path(is_reconfig=True)
        return

    if args.debug: print("[yellow]DEBUG MODE ENABLED[/yellow]")
    print("Welcome to the AI Code Review Tool!")
    load_dotenv(dotenv_path=dotenv_path)
    
    if not os.getenv("DEFAULT_PROVIDER") or not os.getenv("DEFAULT_MODEL"):
        print("Default provider or model not configured. Running setup...")
        if not setup_configuration(is_reconfig=True): return
        load_dotenv(dotenv_path=dotenv_path)

    default_provider = os.getenv("DEFAULT_PROVIDER")
    default_model = os.getenv("DEFAULT_MODEL")
    session_provider, session_model = default_provider, default_model

    if not questionary.confirm(f"Use default model? (Provider: {default_provider}, Model: {default_model})").ask():
        session_provider = questionary.select("Select AI provider for this session:", choices=SUPPORTED_PROVIDER_NAMES, default=default_provider).ask()
        api_key_var = f"{_sanitize_for_env(session_provider)}_API_KEY"
        api_key = os.getenv(api_key_var)
        if not api_key:
            api_key = questionary.text(f"Please enter your {session_provider} API key for this session:").ask()
            if not api_key: return
        try:
            provider_instance = get_provider_from_name(session_provider, api_key)
            models = provider_instance.get_models()
            if not models: return
            session_model = questionary.select("Select model for this session:", choices=models).ask()
            if not session_model: return
        except Exception as e:
            print(f"[red]Error setting up provider: {e}[/red]")
            return

    api_key_var = f"{_sanitize_for_env(session_provider)}_API_KEY"
    api_key = os.getenv(api_key_var)
    if not api_key:
        print(f"[red]API key for {session_provider} not found. Please run --config.[/red]")
        return
    try:
        provider = get_provider_from_name(session_provider, api_key)
    except Exception as e:
        print(f"[red]Could not initialize provider {session_provider}: {e}[/red]")
        return

    project_path = setup_project_path()
    if not project_path: return
    tool_root_dir = _get_tool_root_dir()
    prompts_dir = os.path.join(tool_root_dir, "prompts")
    results_dir = os.path.join(tool_root_dir, "results")
    prompt = _get_prompt(prompts_dir)
    if not prompt: 
        print("[red]Could not load any prompts from the prompts directory.[/red]")
        return

    content, title = None, "AI Code Review"
    mode = questionary.select("Select review mode:", choices=["Git Mode", "Folder Mode"]).ask()

    if mode == "Git Mode":
        if not git_utils.is_git_repository(project_path):
            print("[red]Error: 'Git Mode' requires a Git repository.[/red]")
            return
        review_mode_git = questionary.select("How would you like to review commits?", choices=["Review a range of commits", "Review selected individual commits"]).ask()
        if review_mode_git == "Review a range of commits":
            recent_commits = git_utils.get_recent_commits(project_path)
            if not recent_commits: return
            from_commit_str = questionary.select("Select the starting commit:", choices=recent_commits).ask()
            to_commit_str = questionary.select("Select the ending commit:", choices=recent_commits).ask()
            from_commit, to_commit = from_commit_str.split(' ')[0], to_commit_str.split(' ')[0]
            content = git_utils.get_commit_diff(project_path, from_commit, to_commit) if from_commit != to_commit else git_utils.get_single_commit_changes(project_path, from_commit)
            title = f"Review for {from_commit[:7]}..{to_commit[:7]}"
        elif review_mode_git == "Review selected individual commits":
            recent_commits = git_utils.get_recent_commits(project_path)
            if not recent_commits: return
            selected_commit_strs = questionary.checkbox("Select individual commits:", choices=recent_commits).ask()
            if not selected_commit_strs: return
            hashes = [s.split(' ')[0] for s in selected_commit_strs]
            reviews = []
            with Live(Spinner("dots", text=""), console=console, transient=True) as live:
                for i, chash in enumerate(hashes):
                    live.update(Spinner("dots", text=f"({i+1}/{len(hashes)}) Reviewing: {chash[:7]}"))
                    diff = git_utils.get_single_commit_changes(project_path, chash)
                    if not diff or 'diff --git' not in diff:
                        review_part = f"## Review for Commit: {chash}\n\nSkipped: No file changes found."
                    else:
                        individual_review = provider.generate_review(diff, prompt, session_model, args.debug)
                        review_part = f"## Review for Commit: {chash}\n\n{individual_review}"
                    reviews.append(review_part)
            content = "\n\n---\n\n".join(reviews)
            title = "Individual Commits Review"

    elif mode == "Folder Mode":
        selected_paths = []
        current_path = project_path
        ignore_list = {".git", ".venv", "__pycache__", ".DS_Store", "node_modules", "build", "dist"}
        while True:
            try:
                items = [item for item in os.listdir(current_path) if item not in ignore_list]
            except OSError as e:
                print(f"[red]Error reading directory {current_path}: {e}[/red]")
                break
            dirs = sorted([d for d in items if os.path.isdir(os.path.join(current_path, d))])
            files = sorted([f for f in items if os.path.isfile(os.path.join(current_path, f))])
            choices = [
                questionary.Choice("[DONE - Proceed to Review]", value="##DONE##"), 
                questionary.Choice("[..] (Go Up)", value="##UP##")]
            choices.extend([questionary.Choice(f"{d}/", value=d) for d in dirs])
            choices.extend([questionary.Choice(f, value=f) for f in files])
            selection = questionary.checkbox(f"Browsing: {os.path.relpath(current_path, project_path) or '.'}", choices=choices).ask()
            
            if not selection: # If user cancels with Ctrl+C
                break

            should_break = "##DONE##" in selection
            if should_break:
                selection.remove("##DONE##")

            should_go_up = "##UP##" in selection
            if should_go_up:
                selection.remove("##UP##")

            nav_dir = next((d for d in selection if d in dirs), None)
            if nav_dir:
                selection = [s for s in selection if s != nav_dir]

            for item in selection:
                full_path = os.path.join(current_path, item)
                if full_path not in selected_paths:
                    selected_paths.append(full_path)
                    print(f"[green]Added:[/green] {os.path.relpath(full_path, project_path)}")
            
            if should_break:
                break

            if nav_dir:
                current_path = os.path.join(current_path, nav_dir)
            elif should_go_up:
                parent = os.path.dirname(current_path)
                if parent and parent != current_path:
                    current_path = parent

        parts = []
        if selected_paths:
            with Live(Spinner("dots", text="Reading files..."), console=console, transient=True):
                for path in selected_paths:
                    if os.path.isfile(path):
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                parts.append(f"--- File: {os.path.relpath(path, project_path)} ---\n\n{f.read()}")
                        except Exception as e:
                            console.print(f"[yellow]Could not read file {path}: {e}[/yellow]")
                    elif os.path.isdir(path):
                        for root, _, files_in_dir in os.walk(path):
                            for file in files_in_dir:
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        parts.append(f"--- File: {os.path.relpath(file_path, project_path)} ---\n\n{f.read()}")
                                except Exception as e:
                                    console.print(f"[yellow]Could not read file {file_path}: {e}[/yellow]")
            content = "\n\n".join(parts)
            title = "Folder Content Review"

    if content:
        with Live(Spinner("dots", text=f"Generating review with {session_provider}..."), console=console, transient=True):
            review = provider.generate_review(content, prompt, session_model, args.debug)
        _save_review(review, results_dir, session_model, title)
        if session_provider != default_provider or session_model != default_model:
            if questionary.confirm("Save this session's model as the new default?").ask():
                set_key(dotenv_path, "DEFAULT_PROVIDER", session_provider)
                set_key(dotenv_path, "DEFAULT_MODEL", session_model)
                print("[green]New default model saved.[/green]")
    else:
        print("[yellow]No content selected for review.[/yellow]")

if __name__ == "__main__":
    main()
