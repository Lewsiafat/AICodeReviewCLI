# Release Process

This document outlines the standard process for releasing a new version of the AI Code Review CLI.

## 1. Commit Feature Branch Changes (On Your Feature Branch)

Before merging, ensure all your work on the feature branch is committed with a clear and descriptive message.

1.  **Review Changes:** Check the files you have modified.
    ```bash
    git status
    ```

2.  **Prepare Commit Message:** Based on the changes, write a commit message following a clear standard (e.g., `feat: ...` for new features, `fix: ...` for bug fixes).

3.  **Confirm Message and Commit:**
    *   **Action:** Propose the commit message to the user (or team member).
    *   **Confirmation:** The user confirms the message is accurate.
    *   **Execution:** Once confirmed, stage and commit the files.
    ```bash
    # Stage the relevant files
    git add <file1> <file2> ...

    # Commit with the confirmed message
    git commit -m "feat: Your descriptive title" -m "Optional longer description body."
    ```

## 2. Merge Feature Branch into `master`

When development on the feature branch is complete and committed, merge it into the `master` branch.

1.  **Get Current Branch Name:**
    ```bash
    git branch --show-current
    ```

2.  **Switch to `master` and Merge:**
    ```bash
    # Switch to the master branch
    git checkout master

    # Pull the latest changes to ensure master is up-to-date
    git pull origin master

    # Merge your feature branch
    git merge <your-feature-branch-name>
    ```

## 3. Update Release Notes

On the `master` branch, document the changes in `releaseNote.md`.

1.  Open `releaseNote.md`.
2.  Add a new section for the upcoming version (e.g., `## 0.0.1bX`).
3.  Clearly list the new features, bug fixes, and any other notable changes.

## 4. Run the Version Bump Script

The `bump_version.py` script automates the rest of the process.

1.  **Execute the script using `python3`:**
    ```bash
    python3 bump_version.py
    ```

2.  **What the script does:**
    *   Automatically increments the beta version number (`bX`) in `pyproject.toml` and `src/codereview_tool/__init__.py`.
    *   Creates a single Git commit containing the changes to `releaseNote.md`, `pyproject.toml`, and `__init__.py`. The commit message will be `chore: Bump version to ...`.
    *   Creates a new Git tag for the new version (e.g., `v0.0.1bX`).

## 5. Push Changes and Tags

After the script completes, push your changes and the new tag to the remote repository.

```bash
# Push the commit on the master branch
git push origin master

# Push the new tag
git push origin <tag_name>  # e.g., git push origin v0.0.1b8
```