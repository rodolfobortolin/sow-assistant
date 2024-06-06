
# SOW Assistant

This repository contains scripts designed to retrieve Statements of Work (SOW) from Codex, summarize them using ChatGPT, and create an assistant for easy access to project information.

## Setup

### Install Required Python Modules
Install the necessary Python modules using pip:
```bash
pip install requests openai termcolor beautifulsoup4
```

## Available Scripts

### create-assistant.py

#### Overview
This script sets up an assistant using OpenAI's API, uploads SOW files to a vector store, and allows interaction with the assistant.

#### Configuration
Provide the following configurations in the script:

```python
OPENAI_API_KEY = "your-openai-api-key"
```

#### Execution
Run the script:
```shell
python create-assistant.py 
```

### get-sows-from-codex.py

#### Overview
This script retrieves SOWs from Codex, sends the content to ChatGPT for summarization, and saves the summaries to files.

#### Configuration
Provide the following configurations in the script:

```python
BASE_URL = "https://codex.valiantys.com"
BEARER_TOKEN = "your-codex-bearer-token"
OPENAI_API_KEY = "your-openai-api-key"
PARENT_PAGE_ID = "parent-page-id"
```

#### Execution
Run the script:
```shell
python get-sows-from-codex.py
```
