FROM python:3.5-alpine

LABEL maintainer="d-Rickyy-b <bots@rickyy.de>"
LABEL site="https://github.com/d-Rickyy-b/Python-GeizhalsBot"

# Create bot & log directories
RUN mkdir -p /usr/src/bot/logs
WORKDIR /usr/src/bot

# Copy the source code to the container
COPY . /usr/src/bot

# Install dependencies needed for installing the python requirements
# In particular 'lxml' needs to be compiled first
# After installation of the packages all unnecessary dependencies are removed
RUN apk add -U --no-cache gcc build-base linux-headers python3-dev libffi-dev libressl-dev libxslt-dev \
    && pip3 install --no-cache -r requirements.txt \
    && apk del gcc build-base linux-headers python3-dev libffi-dev libressl-dev

# Start the main file when the container is started
ENTRYPOINT ["python3", "main.py"]
