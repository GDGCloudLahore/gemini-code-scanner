FROM python:3.9

# Install dependencies
RUN pip install google-generativeai github3.py

# Copy the action code
COPY main.py .

# Set the entry point
ENTRYPOINT ["python", "main.py"]