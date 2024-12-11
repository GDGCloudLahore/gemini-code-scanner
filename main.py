import os
import google.generativeai as genai
from github import Github
import requests
from loguru import logger

# Configure Loguru
logger.add("gemini_code_scan.log", rotation="10 MB", level="DEBUG") 

def check_required_env_vars():
    """Check if required environment variables are set."""
    required_env_vars = ["GEMINI_API_KEY", "GITHUB_REPOSITORY"] 
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
        logger.debug("Retrieving code from files in the pull request...")
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

        # Use GITHUB_TOKEN for authentication
        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPOSITORY")

        gh = Github(github_token)
        pr = get_pull_request(gh, repo_name)
        print(f"Processing Pull Request: #{pr.number} - {pr.title}")

        repo = gh.get_repo(repo_name)
        code = get_code_from_pull_request(repo, pr)

        if not code:
            raise ValueError("No code changes were found in the pull request.")

        review_prompt = f"""
(Your detailed review prompt here - same as before)
"""

        try:
            review = get_review(model_name="gemini-1.5-pro", review_prompt=review_prompt, code=code)

            # Set the output variable for the comment action
            print(f"::set-output name=review::{review}") 

        except Exception as e:
            print(f"Error getting review from Generative AI: {e}")
            # Set an error message as the output variable
            print(f"::set-output name=review::Failed to get AI review: {e}")  

    except Exception as e:
        logger.exception(f"Critical Error: {e}")

if __name__ == "__main__":
    main()