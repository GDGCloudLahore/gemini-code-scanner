FROM python:3.9

# Install dependencies
RUN pip install google-generativeai PyGithub loguru requests

# Copy the action code
COPY main.py .

# Set the entry point
ENTRYPOINT ["python", "main.py"]