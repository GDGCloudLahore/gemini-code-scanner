import os
import json
import google.generativeai as genai
import requests
from loguru import logger

def check_required_env_vars():
    """Check required environment variables"""
    required_env_vars = ["GEMINI_API_KEY", "MY_GITHUB_TOKEN", "GITHUB_REPOSITORY"] 
    for env_var in required_env_vars:
        if not os.getenv(env_var):
            raise ValueError(f"{env_var} is not set")

def get_review(model, diff, review_prompt):
    """Get a review from the AI model"""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    gemini_client = genai.GenerativeModel()  # Create a Gemini client

    response = gemini_client.generate_text(  # Use gemini_client.generate_text()
        model=model,
        prompt=review_prompt + "\n\n" + diff,
        temperature=0.1,
        max_output_tokens=500
    )
    review_result = response.result  # Access the result
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
    github_token = os.getenv("MY_GITHUB_TOKEN")  
    repo = os.getenv("GITHUB_REPOSITORY")

    genai.configure(api_key=api_key)

    review_prompt = "Please review the following pull request changes and provide suggestions for improvement."
    diff = "Example code changes for the pull request"  # Replace with actual diff
    
    review = get_review(model="gemini-1.5-pro", diff=diff, review_prompt=review_prompt)

    logger.debug(f"Review result: {review}")

   

if __name__ == "__main__":
    main()