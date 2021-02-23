FROM python:3.5-alpine

LABEL maintainer="d-Rickyy-b <geizhalsbot@rico-j.de>"
LABEL site="https://github.com/d-Rickyy-b/Python-GeizhalsBot"

# Create bot & log directories
RUN mkdir -p /geizhalsbot/logs
WORKDIR /geizhalsbot

# Copy the source code to the container
COPY . /geizhalsbot

# Install dependencies needed for installing the python requirements
# In particular 'lxml' needs to be compiled first
# After installation of the packages all unnecessary dependencies are removed
RUN apk add -U --no-cache gcc build-base linux-headers python3-dev libffi-dev libressl-dev libxslt-dev \
    && pip3 install --no-cache -r requirements.txt \
    && apk del gcc build-base linux-headers python3-dev libffi-dev libressl-dev

# Start the main file when the container is started
ENTRYPOINT ["python3", "main.py"]
