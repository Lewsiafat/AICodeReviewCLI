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

def get_commit_diff(path: str, from_commit: str, to_commit: str) -> str | None:
    """Gets the diff between two commits."""
    try:
        result = subprocess.run(
            ['git', 'diff', from_commit, to_commit],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def get_branches(path: str) -> list[str]:
    """Gets all local and remote branches."""
    try:
        result = subprocess.run(
            ['git', 'branch', '-a'],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        branches = []
        for line in result.stdout.strip().split('\n'):
            # Clean up the branch name
            branch_name = line.strip()
            if '->' in branch_name:
                continue # Skip symbolic refs like HEAD -> master
            if branch_name.startswith('* '):
                branch_name = branch_name[2:]
            
            # Don't add remote branches that are already local
            if branch_name.startswith('remotes/origin/'):
                local_branch = branch_name.replace('remotes/origin/', '')
                if local_branch in branches:
                    continue

            branches.append(branch_name)
        return branches
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def get_recent_commits(path: str, num_commits: int = 20) -> list[str]:
    """Gets a list of recent commits with short hash and subject."""
    try:
        command = ['git', 'log', f'--pretty=format:%h %s', f'-n{num_commits}']
        result = subprocess.run(
            command,
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def get_single_commit_changes(path: str, commit: str) -> str | None:
    """Gets the changes introduced by a single commit."""
    try:
        result = subprocess.run(
            ['git', 'show', commit],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


