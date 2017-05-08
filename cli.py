# Authored by Joshua Hurt 05/08/17
import os
import pickle
import requests
import click
from git import Repo

API_AI_HEADERS = None
BASE_URL = 'https://api.api.ai/v1/'
DEV_KEY = None
DEV_TOKEN_ENV_NAME = 'API_AI_DEV_TOKEN'
API_AI_HISTORY_DIR = 'api_ai_history'
API_AI_REPO = '{}/{}'.format(os.getcwd(), API_AI_HISTORY_DIR)

@click.group()
def cli():
    pass

@cli.command()
@click.argument('repo_url')
def init(repo_url):
    # TODO(jhurt): Handle private repos by using user's Github credentials
    if requests.head(repo_url).status_code != 200:
        print('Cannot reach this URL. Terminating.')
        return
    repo = Repo(os.getcwd())
    for module in repo.submodules:
        if module.name == API_AI_HISTORY_DIR:
            print('Submodule already exists!')
            return
    repo.create_submodule(API_AI_HISTORY_DIR, '{}/{}'.format(os.getcwd(), API_AI_HISTORY_DIR), url=repo_url, branch='master')

@cli.command()
@click.option('--push', default=False, help='Automatically push this commit if connected & configured to a remote repo')
def save_state(push):
    """
    Saves API.ai state (Intents/Entities) as serialized data to be loaded later
    """
    if not environment_valid():
        return
    print('Saving entire state!')
    intents = get_resource_dict('intents')
    entities = get_resource_dict('entities')
    # 'wb' means write the files in binary mode
    with open(API_AI_HISTORY_DIR + '/intents.pickle', 'wb') as f, open(API_AI_HISTORY_DIR + '/entities.pickle', 'wb') as f2:
        pickle.dump(intents, f)
        pickle.dump(entities, f2)
    repo = Repo(API_AI_REPO)
    repo.index.add([
        API_AI_REPO + '/intents.pickle',
        API_AI_REPO + '/entities.pickle'
    ])
    repo.index.commit('# Intents: {}, # Entities: {}'.format(len(intents), len(entities)))
    if push:
        repo.index.push()

@cli.command()
@click.option('--commit-hash', default=None, help="A commit hash to make the state of API.ai match.")
def load_state(commit_hash):
    """
    Restores state of all Intents/Entities from commit hash to API.ai
    """
    if not environment_valid():
        return
    repo = Repo(API_AI_REPO)
    target_commit = None
    # Get the Commit object based on the hash user provided
    if commit_hash:
        for c in repo.iter_commits():
            if c.hexsha == commit_hash:
                target_commit = c
                break
    # User didn't provide a commit hash so show last 10 for them to choose from
    if not commit_hash:
        # Show last 10 commits from CURRENT BRANCH
        commits = list(repo.iter_commits(max_count=10))
        for i, commit_obj in enumerate(commits):
            print("({})  {}  {}".format(i, commit_obj.hexsha, commit_obj.message))
        num_pressed = int(input("Press number corresponding to which commit you'd like to rollback:"))
        target_commit = commits[num_pressed]

    print('Loading entire state! Please be patient.')
    intents, entities = None, None
    # TODO(jhurt): make this only iterate through the API.ai specific pickle files.
    # Maybe put them in their own directory and limit the "tree" path to blobs in that path?
    for b in target_commit.tree.blobs:
        if b.name == "intents.pickle":
            intents = pickle.loads(b.data_stream.read())
        if b.name == "entities.pickle":
            entities = pickle.loads(b.data_stream.read())

    sync_api_ai(intents, entities)

def sync_api_ai(old_intents, old_entities):
    cur_intents = get_resource_dict('intents')
    cur_entities = get_resource_dict('entities')
    cur_intents_ids = { x['id'] for x in cur_intents.values() }
    cur_entities_ids = { x['id'] for x in cur_entities.values() }

    # TODO(jhurt): Currently deleting everything then recreating everything due to odd behavior regarding IDs.
    # Make this more efficient cuz numerous or large Intents/Entities could take a long time to send over the network.

    # DELETE all current Intents
    for intent_id in cur_intents_ids:
        requests.delete(BASE_URL+'intents/'+intent_id, headers=API_AI_HEADERS)

    # DELETE all current Entities
    for entity_id in cur_entities_ids:
        requests.delete(BASE_URL+'entities/'+entity_id, headers=API_AI_HEADERS)

    # CREATE all old Intents (will have new IDs now but that's okay)
    for intent in old_intents.values():
        # Intent object can't have the 'id' attribute for a POST
        if intent.get('id') is not None:
            del intent['id']
        requests.post(BASE_URL+'intents', headers=API_AI_HEADERS, json=intent)

    # CREATE all old Entities (will have new IDs now but that's okay)
    for entity in old_entities.values():
        # Entity object can't have the 'id' attribute for a POST
        if entity.get('id') is not None:
            del entity['id']
        requests.post(BASE_URL+'entities', headers=API_AI_HEADERS, json=entity)

def get_resource_dict(resource):
    """
    Meh.
    :param resource: either 'intents' or 'entities' as of right now
    :return: dict in form { 'id' : resource_dict }
    """
    resource_json = requests.get(BASE_URL+resource, headers=API_AI_HEADERS).json()
    resources = {}
    for d in resource_json:
        resources[d['id']] = requests.get(BASE_URL+resource+'/'+d['id'], headers=API_AI_HEADERS).json()
    return resources

def environment_valid():
    global API_AI_HEADERS
    global BASE_URL
    global DEV_KEY
    global DEV_TOKEN_ENV_NAME
    DEV_TOKEN_ENV_NAME = 'API_AI_DEV_TOKEN'
    DEV_KEY = os.getenv(DEV_TOKEN_ENV_NAME)
    if DEV_KEY is None:
        print("Please set environment variable {}".format(DEV_TOKEN_ENV_NAME))
        return False
    API_AI_HEADERS = {'Authorization' : 'Bearer {}'.format(DEV_KEY)}
    repo = Repo(os.getcwd())
    found_submodule = False
    for module in repo.submodules:
        if module.name == API_AI_HISTORY_DIR:
            found_submodule = True
    if not found_submodule:
        print("Re-run tool with 'init <REPO_URL>' command where <REPO_URL> is a "
              "public Github repo where you would like to save your API.ai history.")
        return False
    return True



if __name__ == '__main__':
    cli()
