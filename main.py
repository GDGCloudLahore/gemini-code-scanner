import os
import json
import google.generativeai as genai
import requests
from loguru import logger

def check_required_env_vars():
    """Check required environment variables"""
    required_env_vars = ["GEMINI_API_KEY", "GITHUB_TOKEN", "GITHUB_REPOSITORY", "GITHUB_PULL_REQUEST_NUMBER", "GIT_COMMIT_HASH"]
    for env_var in required_env_vars:
        if not os.getenv(env_var):
            raise ValueError(f"{env_var} is not set")

def get_review(model, diff, review_prompt):
    """Get a review from the AI model"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    genai_model = genai.start_chat(
        model=model,
        history=[{"role": "user", "content": review_prompt}]
    )

    convo_response = genai_model.send_message(diff)
    review_result = convo_response.text
    logger.debug(f"Response from AI: {review_result}")
    return review_result

def create_a_comment_to_pull_request(github_token, github_repository, pull_request_number, body):
    """Create a comment on a pull request"""
    url = f"https://api.github.com/repos/{github_repository}/issues/{pull_request_number}/comments"
    headers = {"Authorization": f"Bearer {github_token}"}
    data = {"body": body}
    response = requests.post(url, headers=headers, json=data)
    logger.debug(f"Comment Response: {response.status_code} - {response.text}")
    return response

def main():
    check_required_env_vars()
    api_key = os.getenv("GEMINI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("GITHUB_PULL_REQUEST_NUMBER"))

    genai.configure(api_key=api_key)

    review_prompt = "Please review the following pull request changes and provide suggestions for improvement."
    diff = "Example code changes for the pull request"
    review = get_review(model="gpt-3.5-turbo", diff=diff, review_prompt=review_prompt)

    logger.debug(f"Review result: {review}")

    create_a_comment_to_pull_request(
        github_token=github_token,
        github_repository=repo,
        pull_request_number=pr_number,
        body=review
    )

if __name__ == "__main__":
    main()
