# api-ai-git
### Reason for creation:
This is a CLI tool to version control intents and entities in API.ai born out of a frustration of having them constantly mangled by other team members without a way to rollback to a working version.

### List of supported actions:
* Save current state of all Intents and Entities with the option to automatically commit and/or push the changes
* Load the state of Intents and Entities from a previous commit to API.ai

### Instructions for setup and use:
```
> pip install -r requirements.txt

Go into the API.ai dashboard, click the settings for your agent, and export the developer token as an environment variable
> export API_AI_DEV_TOKEN="<paste_token_here>"

Need to clone a submodule in current repo. The submodule is just another repo whose job is to only track API.ai changes
> api-ai-git.py init <URL_to_repo>

Save state of all Intents & Entities and commit
> api-ai-git.py save_state --commit

You can commit and push by giving just the --push flag
> api-ai-git.py save_state --push

Load a saved state from a specific commit hash
> api-ai-git.py load_state --commit-hash 11edc81f6d2a1e9ede198b75a90d021124c5207b

Or you can pick from a list of up to the last 10 commits to load a state
> api-ai-git.py load_state
(0)  2ee277719bff7d92ae4e27efd5ca2cb069e33fe3  # Intents: 3, # Entities: 1
(1)  fedb991cd6667e73c662ad74b03773955e189f9b  # Intents: 3, # Entities: 1
(2)  11edc81f6d2a1e9ede198b75a90d021124c5207b  test
(3)  520006c8aae7c632c7805c76f6668b27804813f9  Initial commit
Press number corresponding to which commit you'd like to load the state from:
```

