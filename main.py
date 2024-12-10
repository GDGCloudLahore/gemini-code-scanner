import os
import google.generativeai as genai
from github import Github
import requests

def check_required_env_vars():
    """Check required environment variables"""
    required_env_vars = ["GEMINI_API_KEY", "MY_GITHUB_TOKEN", "GITHUB_REPOSITORY"] 
    for env_var in required_env_vars:
        if not os.getenv(env_var):
            raise ValueError(f"{env_var} is not set")

def get_review(model, review_prompt, code):
    """Get a review from the AI model"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Start a chat session
    chat = genai.start_chat(
        model=model,  # Use the model name like "gpt-3.5-turbo" or "text-bison-001"
        history=[{"role": "user", "content": review_prompt}]  # Initial context for the chat
    )

    # Send the code changes as part of the chat
    response = chat.send_message(code)
    review_result = response.text  # Extract AI's response text
    return review_result

def create_a_comment_to_pull_request(github_token, github_repository, pull_request_number, body):
    """Create a comment on a pull request"""
    url = f"https://api.github.com/repos/{github_repository}/issues/{pull_request_number}/comments"
    headers = {"Authorization": f"Bearer {github_token}"}
    data = {"body": body}
    response = requests.post(url, headers=headers, json=data)
    return response

def main():
    check_required_env_vars()
    api_key = os.getenv("GEMINI_API_KEY")
    github_token = os.getenv("MY_GITHUB_TOKEN")  
    repo_name = os.getenv("GITHUB_REPOSITORY")

    genai.configure(api_key=api_key)

    gh = Github(github_token)
    repo = gh.get_repo(repo_name)

    # Get the pull request (you'll need to determine how to get the correct PR)
    pulls = repo.get_pulls(state='open', sort='created', direction='desc')
    pr = pulls[0]  # Get the latest PR

    # Get the code from the pull request files
    files = pr.get_files()
    code = ""

    for file in files:
        try:
            file_content = repo.get_contents(file.filename, ref=pr.head.sha)
            content = file_content.decoded_content.decode('utf-8')
            code += f"```{file.filename}\n{content}\n```\n"
        except Exception as e:
            print(f"Error retrieving content for file {file.filename}: {e}")

    review_prompt = "Please review the following pull request changes and provide suggestions for improvement."
    
    try:
        review = get_review(model="gpt-3.5-turbo", review_prompt=review_prompt, code=code)
    except Exception as e:
        print(f"Error getting review from Generative AI: {e}")
        review = "Failed to get AI review."

    try:
        create_a_comment_to_pull_request(github_token, repo_name, pr.number, review)
    except Exception as e:
        print(f"Error creating a comment on the PR: {e}")

if __name__ == "__main__":
    main()
