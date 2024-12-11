import os
import google.generativeai as genai
from github import Github
import requests
from loguru import logger

# Configure Loguru
logger.add("gemini_code_scan.log", rotation="10 MB", level="DEBUG") 

def check_required_env_vars():
    """Check if required environment variables are set."""
    required_env_vars = ["GEMINI_API_KEY", "MY_GITHUB_TOKEN", "GITHUB_REPOSITORY"]  
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def configure_genai():
    """Configure Google Generative AI API."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        logger.debug("Generative AI configured successfully.")
    except Exception as e:
        logger.exception(f"Failed to configure Generative AI: {e}")
        raise

def get_review(model_name, review_prompt, code):
    """Get a review from the AI model."""
    configure_genai()
    try:
        model = genai.GenerativeModel(model_name=model_name)
        logger.debug(f"Sending code to Gemini {model_name} for review...")
        response = model.generate_content([review_prompt + "\n\n" + code])
        logger.debug("Review received from Gemini.")
        return response.text
    except Exception as e:
        logger.exception(f"Error generating review from Generative AI: {e}")
        return "Error generating review from AI"

def create_a_comment_to_pull_request(github_token, github_repository, pull_request_number, body):
    """Create a comment on a pull request."""
    try:
        url = f"https://api.github.com/repos/{github_repository}/issues/{pull_request_number}/comments"
        headers = {"Authorization": f"Bearer {github_token}"}
        data = {"body": body}
        logger.debug(f"Posting review to GitHub PR #{pull_request_number}...")
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 201:
            logger.error(f"Failed to create a comment on the PR. Status: {response.status_code}, Response: {response.text}")
        else:
            logger.debug("Review posted successfully to GitHub PR.")
        return response
    except Exception as e:
        logger.exception(f"Error creating a comment on the PR: {e}")
        return None

def get_pull_request(gh, repo_name):
    """Get the most recent open pull request."""
    try:
        repo = gh.get_repo(repo_name)
        pulls = repo.get_pulls(state='open', sort='created', direction='desc')
        if not pulls:
            raise ValueError("No open pull requests found.")
        logger.debug(f"Found open pull request: #{pulls[0].number} - {pulls[0].title}")
        return pulls[0]
    except Exception as e:
        logger.exception(f"Error getting pull request: {e}")
        raise

def get_code_from_pull_request(repo, pr):
    """Get the code content from all files in the pull request."""
    code = ""
    try:
        files = pr.get_files()
        logger.debug(f"Retrieving code from {len(files)} files in the pull request...")
        for file in files:
            try:
                file_content = repo.get_contents(file.filename, ref=pr.head.sha)
                content = file_content.decoded_content.decode('utf-8')
                code += f"```{file.filename}\n{content}\n```\n"
            except Exception as e:
                logger.error(f"Error retrieving content for file {file.filename}: {e}")
    except Exception as e:
        logger.exception(f"Error getting files from PR: {e}")
    return code

def main():
    """Main function to handle the workflow."""
    try:
        check_required_env_vars()
        github_token = os.getenv("MY_GITHUB_TOKEN")   
        repo_name = os.getenv("GITHUB_REPOSITORY")
        gh = Github(github_token)
        pr = get_pull_request(gh, repo_name)
        print(f"Processing Pull Request: #{pr.number} - {pr.title}")
        repo = gh.get_repo(repo_name)
        code = get_code_from_pull_request(repo, pr)
        if not code:
            raise ValueError("No code changes were found in the pull request.")
        review_prompt = f"""
Please meticulously analyze the following code changes for potential security vulnerabilities line by line, and provide specific and actionable suggestions for improvement.

Specifically, look for:

* **Hardcoded secrets:** API keys, passwords, or other sensitive information embedded directly in the code.
* **Code injection vulnerabilities:**  SQL injection, command injection, cross-site scripting (XSS), etc.
* **Insecure data handling:**  Unencrypted storage of sensitive data, improper input validation, etc.
* **Authentication and authorization issues:** Weak password policies, missing or inadequate access controls.
* **Other common vulnerabilities:**  Outdated dependencies, insecure configurations, etc.

For each vulnerability found, please:

* Clearly identify the vulnerability type.
* Indicate the specific line(s) of code where the vulnerability exists.
* Mention the filename where the vulnerability is located. 
* Provide clear and concise recommendations for fixing the vulnerability.
* Include a relevant internet link for reference.
* Include a code improvement recommendation that you think this code can be well written with this recommendation with file name and line number 

Please present the vulnerabilities in a Markdown table with the following columns:

| Vulnerability Type | File | Line(s) | Description | Recommendation | Reference | Code Improvement|
|---|---|---|---|---|---|---|

After the analysis, please provide a summary with the following:

* Total number of vulnerabilities found.
* Number of high, medium, and low severity vulnerabilities.
* Overall status: "Pass" if no high severity vulnerabilities are found, "Fail" otherwise.
* Emojis representing the severity levels (e.g., 🚨 for high, ⚠️ for medium, ℹ️ for low).

Code:
{code}
"""
        try:
            review = get_review(model_name="gemini-1.5-pro", review_prompt=review_prompt, code=code)
        except Exception as e:
            print(f"Error getting review from Generative AI: {e}")
            review = "Failed to get AI review."

        # Use GITHUB_TOKEN for creating comments
        create_a_comment_to_pull_request(os.getenv("GITHUB_TOKEN"), repo_name, pr.number, review)  

    except Exception as e:
        logger.exception(f"Critical Error: {e}")  # Log critical errors

if __name__ == "__main__":
    main()