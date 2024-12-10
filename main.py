import os
import google.generativeai as genai
from github import Github
import requests

def check_required_env_vars():
    """Check if required environment variables are set."""
    # Reverted back to GITHUB_TOKEN
    required_env_vars = ["GEMINI_API_KEY", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]  
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def configure_genai():
    """Configure Google Generative AI API."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
    except Exception as e:
        raise ValueError(f"Failed to configure Generative AI: {e}")


def get_review(model_name, review_prompt, code):
    """Get a review from the AI model."""
    configure_genai()
    try:
        # Instantiate the GenerativeModel
        model = genai.GenerativeModel(model_name=model_name)
        
        # Generate content using the prompt and code
        response = model.generate_content(
            [review_prompt + "\n\n" + code] 
        )
        
        review_result = response.text  # Extract AI's response text
        return review_result
    except Exception as e:
        print(f"Error generating review from Generative AI: {e}")
        return "Error generating review from AI"


def create_a_comment_to_pull_request(github_token, github_repository, pull_request_number, body):
    """Create a comment on a pull request."""
    try:
        url = f"https://api.github.com/repos/{github_repository}/issues/{pull_request_number}/comments"
        headers = {"Authorization": f"Bearer {github_token}"}
        data = {"body": body}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 201:
            print(f"Failed to create a comment on the PR. Status: {response.status_code}, Response: {response.text}")
        
        return response
    except Exception as e:
        print(f"Error creating a comment on the PR: {e}")
        return None


def get_pull_request(gh, repo_name):
    """Get the most recent open pull request."""
    try:
        repo = gh.get_repo(repo_name)
        pulls = repo.get_pulls(state='open', sort='created', direction='desc')
        
        if not pulls:
            raise ValueError("No open pull requests found.")
        
        return pulls[0]  # Get the latest open PR
    except Exception as e:
        print(f"Error getting pull request: {e}")
        raise


def get_code_from_pull_request(repo, pr):
    """Get the code content from all files in the pull request."""
    code = ""
    try:
        files = pr.get_files()
        for file in files:
            try:
                file_content = repo.get_contents(file.filename, ref=pr.head.sha)
                content = file_content.decoded_content.decode('utf-8')
                code += f"```{file.filename}\n{content}\n```\n"
            except Exception as e:
                print(f"Error retrieving content for file {file.filename}: {e}")
    except Exception as e:
        print(f"Error getting files from PR: {e}")
    return code


def main():
    """Main function to handle the workflow."""
    try:
        # Step 1: Check for environment variables
        check_required_env_vars()

        # Step 2: Get tokens and repository name from environment
        github_token = os.getenv("GITHUB_TOKEN")   # Use GITHUB_TOKEN
        repo_name = os.getenv("GITHUB_REPOSITORY")

        # Step 3: Authenticate with GitHub
        gh = Github(github_token)

        # Step 4: Get the latest pull request
        pr = get_pull_request(gh, repo_name)
        print(f"Processing Pull Request: #{pr.number} - {pr.title}")

        # Step 5: Get the code from the pull request files
        repo = gh.get_repo(repo_name)
        code = get_code_from_pull_request(repo, pr)

        if not code:
            raise ValueError("No code changes were found in the pull request.")

        # Step 6: Review the code using Generative AI
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
* Provide clear and concise recommendations for fixing the vulnerability.

Code:
{code}
"""
        try:
            review = get_review(model_name="gemini-pro", review_prompt=review_prompt, code=code)
        except Exception as e:
            print(f"Error getting review from Generative AI: {e}")
            review = "Failed to get AI review."

        # Step 7: Create a comment on the pull request with the review result
        create_a_comment_to_pull_request(github_token, repo_name, pr.number, review)

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()