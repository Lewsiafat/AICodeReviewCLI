import subprocess
import re

def is_git_repository(path: str) -> bool:
    """Checks if the given path is a Git repository."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() == 'true'
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_current_branch(path: str) -> str | None:
    """Gets the current branch name."""
    return run_git_command(path, ["branch", "--show-current"])

def get_commit_diff(path: str, from_commit: str, to_commit: str) -> str | None:
    """Gets the diff between two commits."""
    return run_git_command(path, ["diff", from_commit, to_commit])

def get_branches(path: str) -> list[str]:
    """Gets all local and remote branches."""
    output = run_git_command(path, ['branch', '-a'])
    if not output:
        return []
    
    branches = []
    for line in output.strip().split('\n'):
        branch_name = line.strip()
        if '->' in branch_name:
            continue
        if branch_name.startswith('* '):
            branch_name = branch_name[2:]
        
        if branch_name.startswith('remotes/origin/'):
            local_branch = branch_name.replace('remotes/origin/', '')
            if local_branch in branches:
                continue

        branches.append(branch_name)
    return branches

def get_recent_commits(path: str, num_commits: int = 20) -> list[str]:
    """Gets a list of recent commits with short hash and subject."""
    command = ['log', f'--pretty=format:%h %s', f'-n{num_commits}']
    output = run_git_command(path, command)
    return output.strip().split('\n') if output else []

def get_single_commit_changes(path: str, commit: str) -> str | None:
    """Gets the changes introduced by a single commit."""
    return run_git_command(path, ["show", commit])

def run_git_command(path, command_args):
    """Helper to run a git command and return its stripped stdout."""
    try:
        result = subprocess.run(
            ['git'] + command_args,
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {' '.join(command_args)}\n{e.stderr}")
        return None
    except FileNotFoundError:
        print("Git command not found. Is Git installed and in your PATH?")
        return None

def git_fetch(path):
    """
    Runs 'git fetch' in the specified directory.
    Raises subprocess.CalledProcessError on failure.
    """
    subprocess.run(
        ['git', 'fetch', '--all'],
        cwd=path,
        check=True,
        capture_output=True,
        text=True
    )

def git_pull(path):
    """
    Runs 'git pull' in the specified directory.
    Raises subprocess.CalledProcessError on failure.
    """
    subprocess.run(
        ['git', 'pull'],
        cwd=path,
        check=True,
        capture_output=True,
        text=True
    )