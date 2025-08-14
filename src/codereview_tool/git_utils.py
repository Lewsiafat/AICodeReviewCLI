import subprocess

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
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None