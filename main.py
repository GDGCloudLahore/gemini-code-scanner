import os
import google.generativeai as genai
from github import Github


def main():
    # Get inputs
    gemini_api_key = os.environ.get("INPUT_GEMINI_API_KEY")
    github_token = os.environ.get("INPUT_MY_GITHUB_TOKEN")  # Get the token from the env
    repo_name = os.environ.get("INPUT_REPO_NAME") or os.environ.get("GITHUB_REPOSITORY")
    branch_name = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME")

    # Check if all required environment variables are present
    if not gemini_api_key:
        raise ValueError("The environment variable 'INPUT_GEMINI_API_KEY' is missing.")
    if not github_token:
        raise ValueError("The environment variable 'INPUT_MY_GITHUB_TOKEN' is missing.")
    if not repo_name:
        raise ValueError("The environment variable 'INPUT_REPO_NAME' or 'GITHUB_REPOSITORY' is missing.")
    if not branch_name:
        raise ValueError("The environment variable 'GITHUB_HEAD_REF' or 'GITHUB_REF_NAME' is missing.")

    print(f"GitHub Token (First 5 chars): {github_token[:5]}")  # Mask the token for security
    print(f"Repo Name: {repo_name}")
    print(f"Branch Name: {branch_name}")

    # Authenticate with Gemini
    genai.configure(api_key=gemini_api_key)
    gemini_client = genai.GenerativeModel()

    # Authenticate with GitHub
    try:
        print(f"Attempting to access repository: {repo_name}")
        gh = Github(github_token)
        repo = gh.get_repo(repo_name)
    except Exception as e:
        print(f"Error accessing the repo {repo_name}: {e}")
        raise

    # Get the pull request associated with the branch
    try:
        pr = repo.get_pulls(state='open', head=f"{repo_name.split('/')[0]}:{branch_name}")[0]
    except Exception as e:
        print(f"Error fetching the pull request for branch {branch_name}: {e}")
        raise

    # Get the code changes from the pull request
    code_diff = ""
    try:
        files = pr.get_files()
        for file in files:
            code_diff += f"```diff\n--- a/{file.filename}\n+++ b/{file.filename}\n{file.patch}\n```\n"
    except Exception as e:
        print(f"Error getting code changes for PR: {e}")
        raise

    # Analyze the code with Gemini
    try:
        response = gemini_client.generate_text(
            prompt=f"Analyze this code and provide feedback:\n\n{code_diff}",
            model="gemini-pro",
            temperature=0.1,
            max_output_tokens=500
        )
        analysis = response.text
    except Exception as e:
        print(f"Error analyzing the code with Gemini: {e}")
        raise

    # Post the analysis as a comment on the pull request
    try:
        pr.create_issue_comment(f"**Gemini Code Analysis:**\n\n{analysis}")
    except Exception as e:
        print(f"Error creating comment on the PR: {e}")
        raise

if __name__ == "__main__":
    main()
