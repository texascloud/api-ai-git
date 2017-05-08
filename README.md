# api-ai-git
### Reason for creation:
This is a CLI tool to version control intents and entities in API.ai born out of a frustration of having them constantly mangled by other team members without a way to rollback to a working version.

### List of supported actions:
* Save current state of all Intents and Entities with the option to automatically commit and/or push the changes
* Load the state of Intents and Entities from a previous commit to API.ai

### Instructions for setup and use:
* pip install -r requirements.txt
* ./api-ai-versioner.py init <URL_to_repo>
* \# save state of all Intents/Entities and commit
* ./api-ai-versioner.py save_state --commit
* \# load a saved state from a specific commit hash
* ./api-ai-versioner.py load_state --commit-hash 123abc
* \# pick from a list of the last 10 commits to load a state
* ./api-ai-versioner.py load_state

