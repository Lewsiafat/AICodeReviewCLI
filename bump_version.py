import os
import re
import subprocess

def get_project_root():
    script_dir = os.path.dirname(__file__)
    return os.path.abspath(script_dir)

def get_current_version(root_dir):
    pyproject_path = os.path.join(root_dir, "pyproject.toml")
    with open(pyproject_path, "r") as f:
        for line in f:
            if line.strip().startswith("version ="):
                match = re.search(r'version\s*=\s*"(.*?)"', line)
                if match:
                    return match.group(1)
    raise ValueError("Version not found in pyproject.toml")

def update_version_files(root_dir, new_version):
    # Update pyproject.toml
    pyproject_path = os.path.join(root_dir, "pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()
    content = re.sub(r'^(version\s*=\s*\")[^\"]*(")', r'\g<1>' + new_version + r'\g<2>', content, flags=re.MULTILINE)
    with open(pyproject_path, "w") as f:
        f.write(content)
    print(f"Updated pyproject.toml to version {new_version}")

    # Update __init__.py
    init_path = os.path.join(root_dir, "src", "codereview_tool", "__init__.py")
    with open(init_path, "r") as f:
        content = f.read()
    # CORRECTED REGEX: Removed the trailing '|'
    content = re.sub(r'^__version__\s*=\s*"[^"]*"', f'__version__ = "{new_version}"', content, flags=re.MULTILINE)
    with open(init_path, "w") as f:
        f.write(content)
    print(f"Updated __init__.py to version {new_version}")

def commit_files(root_dir, file_paths, commit_message):
    """Adds and commits a list of files to Git."""
    try:
        if not isinstance(file_paths, list):
            file_paths = [file_paths]
        
        subprocess.run(['git', 'add'] + file_paths, cwd=root_dir, check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=root_dir, check=True)
        print(f"Successfully committed: {', '.join(file_paths)}")
    except subprocess.CalledProcessError as e:
        print(f"Error during git operation: {e}")
        exit(1)

def create_git_tag(root_dir, new_version):
    tag_name = f"v{new_version}"
    try:
        subprocess.run(['git', 'tag', tag_name], cwd=root_dir, check=True)
        print(f"Created Git tag: {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating Git tag: {e}")
        exit(1)

def bump_beta_version():
    root_dir = get_project_root()
    current_version = get_current_version(root_dir)

    match = re.match(r'(\d+\.\d+\.\d+)b(\d+)', current_version)
    if not match:
        raise ValueError(f"Invalid beta version format: {current_version}")

    base_version = match.group(1)
    beta_num = int(match.group(2)) + 1
    new_version = f"{base_version}b{beta_num}"

    # Update version in files
    update_version_files(root_dir, new_version)

    # CORRECTED: Commit all files together
    files_to_commit = [
        os.path.join(root_dir, 'releaseNote.md'),
        os.path.join(root_dir, "pyproject.toml"),
        os.path.join(root_dir, "src", "codereview_tool", "__init__.py")
    ]
    commit_files(root_dir, files_to_commit, f"chore: Bump version to {new_version}")

    # Create git tag
    create_git_tag(root_dir, new_version)
    
    print(f"\nVersion bump complete. New version: {new_version}")

if __name__ == "__main__":
    bump_beta_version()
