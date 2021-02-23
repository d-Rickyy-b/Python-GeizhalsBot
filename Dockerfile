FROM python:3-slim

LABEL maintainer="d-Rickyy-b <geizhalsbot@rico-j.de>"
LABEL site="https://github.com/d-Rickyy-b/Python-GeizhalsBot"

# Create bot & log directories
RUN mkdir -p /geizhalsbot/logs
WORKDIR /geizhalsbot

# Copy the source code to the container
COPY . /geizhalsbot

RUN pip3 install --no-cache -r /geizhalsbot/requirements.txt

# Start the main file when the container is started
ENTRYPOINT ["python3", "main.py"]
