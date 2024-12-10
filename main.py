import os
import google.generativeai as genai
from github import Github

def main():
    # Get inputs
    gemini_api_key = os.environ.get("INPUT_GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    # Get branch name from the environment
    branch_name = os.environ.get("GITHUB_HEAD_REF") 

    # Authenticate with Gemini
    genai.configure(api_key=gemini_api_key)
    gemini_client = genai.GenerativeModel()

    # Authenticate with GitHub
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)

    # Get the pull request associated with the branch
    pr = repo.get_pulls(state='open', head=branch_name)[0]

    # Get the code changes from the pull request
    files = pr.get_files()
    code_diff = ""
    for file in files:
        code_diff += f"```diff\n--- a/{file.filename}\n+++ b/{file.filename}\n{file.patch}\n```\n"

    # Analyze the code with Gemini
    response = gemini_client.generate_text(
        prompt=f"Analyze this code and provide feedback:\n\n{code_diff}",
        model="gemini-pro",
        temperature=0.1,
        max_output_tokens=500
    )
    analysis = response.text

    # Post the analysis as a comment on the pull request
    pr.create_issue_comment(f"**Gemini Code Analysis:**\n\n{analysis}")

if __name__ == "__main__":
    main()