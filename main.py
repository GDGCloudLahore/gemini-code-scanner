import os
import google.generativeai as genai
from github import Github

def check_required_env_vars():
    """Check required environment variables"""
    required_env_vars = ["GEMINI_API_KEY", "MY_GITHUB_TOKEN", "GITHUB_REPOSITORY"] 
    for env_var in required_env_vars:
        if not os.getenv(env_var):
            raise ValueError(f"{env_var} is not set")

def get_review(model, review_prompt, code):  # Updated function signature
    """Get a review from the AI model"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    gemini_client = genai.GenerativeModel(model=model)

    response = gemini_client.generate_content(  
        prompt=review_prompt + "\n\n" + code,  # Use code directly in the prompt
    )
    review_result = response.text
    return review_result

# ... (create_a_comment_to_pull_request function remains the same)

def main():
    check_required_env_vars()
    api_key = os.getenv("GEMINI_API_KEY")
    github_token = os.getenv("MY_GITHUB_TOKEN")  
    repo_name = os.getenv("GITHUB_REPOSITORY")

    genai.configure(api_key=api_key)

    gh = Github(github_token)
    repo = gh.get_repo(repo_name)

    # Get the pull request (you'll need to determine how to get the correct PR)
    # For example, get the latest open PR:
    pulls = repo.get_pulls(state='open', sort='created', direction='desc')
    pr = pulls[0] 

    # Get the code from the pull request files
    files = pr.get_files()
    code = ""
    for file in files:
        code += f"```{file.filename}\n{file.contents}\n```\n"

    review_prompt = "Please review the following pull request changes and provide suggestions for improvement."
    
    review = get_review(model="gemini-1.5-pro", review_prompt=review_prompt, code=code)  # Pass the code

    # ... (Call create_a_comment_to_pull_request if needed)

if __name__ == "__main__":
    main()