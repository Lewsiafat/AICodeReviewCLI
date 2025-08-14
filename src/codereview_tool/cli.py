from . import git_utils

def main():
    print("Welcome to the AI Code Review Tool!")
    # Hardcoded project path for non-interactive development
    project_path = "/Users/lewis.chan/Documents/workspaceProject/aiCodeReview/your_codereview_tool"
    print(f"Analyzing project at: {project_path}")

    if git_utils.is_git_repository(project_path):
        print("This is a Git repository.")
        branch = git_utils.get_current_branch(project_path)
        if branch:
            print(f"Current branch is: {branch}")
        else:
            print("Could not determine the current branch.")
    else:
        print("This is not a Git repository.")

if __name__ == "__main__":
    main()