FROM python:3.10

# Install dependencies
RUN pip install google-generativeai==0.4.0 PyGithub loguru requests

# Copy the action code
COPY main.py .

# Set the entry point
ENTRYPOINT ["python", "main.py"]