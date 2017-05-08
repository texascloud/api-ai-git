import os
import pickle
import requests
import click
import json
from git import Repo

API_AI_HEADERS = None
BASE_URL = 'https://api.api.ai/v1/'
DEV_KEY = None
DEV_TOKEN_ENV_NAME = 'API_AI_DEV_TOKEN'

@click.group()
def cli():
    pass

@cli.command()
@click.option('--push', default=False, help='Automatically push this commit if connected & configured to a remote repo')
def save_state(push):
    """
    Saves API.ai state (intents and entities) and commits them for version controlling.
    """
    if not environment_valid():
        return
    print('Saving entire state!')
    intents = get_resource_dict('intents')
    entities = get_resource_dict('entities')
    # 'wb' means write the files in binary mode
    with open('intents.pickle', 'wb') as f, open('entities.pickle', 'wb') as f2:
        pickle.dump(intents, f)
        pickle.dump(entities, f2)
    print(intents)
    print(entities)
    if push:
        print('Pushing committed changes to remote repo')
    elif not push:
        print('Not pushing anything!')

@cli.command()
@click.option('--commit-hash', default=None, help="A commit hash to make the state of API.ai match.")
def load_state(commit_hash):
    """
    Loads all intents to API.ai from current commit
    """
    if not environment_valid():
        return
    repo = Repo(os.getcwd())
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
            print("{}  {}  {}".format(i, commit_obj.hexsha, commit_obj.message))
        num_pressed = int(input("Press number corresponding to which commit you'd like to rollback:"))
        print("{} corresponds to commit hash {}, is that correct?".format(num_pressed, commits[num_pressed].hexsha))
        target_commit = commits[num_pressed]

    print('Loading entire state!')
    intents, entities = None, None
    # TODO(jhurt): make this only iterate through the API.ai specific pickle files.
    # Maybe put them in their own directory and limit the "tree" path to blobs in that path?
    for b in target_commit.tree.blobs:
        if b.name == "intents.pickle":
            intents = pickle.loads(b.data_stream.read())
        if b.name == "entities.pickle":
            entities = pickle.loads(b.data_stream.read())

    # Take a diff of the keys for both intents/entities.
    # Delete from API.ai the intents/entities NOT present in our "old" intent/entity data
    sync_api_ai(intents, entities)
    print(intents)
    print(entities)

def sync_api_ai(old_intents, old_entities):
    cur_intents = get_resource_dict('intents')
    cur_entities = get_resource_dict('entities')
    cur_intents_ids = { x['id'] for x in cur_intents.values() }
    cur_entities_ids = { x['id'] for x in cur_entities.values() }
    old_intents_ids = { x['id'] for x in old_intents.values() }
    old_entities_ids = { x['id'] for x in old_entities.values() }

    # DELETE all current Intents
    intents_to_delete = cur_intents_ids - old_intents_ids
    if len(intents_to_delete) > 0:
        for intent_id in intents_to_delete:
            requests.delete(BASE_URL+'intents/'+intent_id, headers=API_AI_HEADERS)

    # DELETE all current Entities
    # for entity_id in cur_entities_ids:
    #     requests.delete(BASE_URL+'entity/'+entity_id, headers=API_AI_HEADERS)

    # CREATE all old intents (will have new IDs now but that's okay)
    for intent in old_intents.values():
        # Intent object can't have the 'id' attribute for a POST
        if intent.get('id') is not None:
            del intent['id']
        requests.post(BASE_URL+'intents', headers=API_AI_HEADERS, json=intent)

    # DELETE all Intents whose ID is not in the old Intent data
    # intents_to_delete = cur_intents_ids - old_intents_ids
    # if len(intents_to_delete) > 0:
    #     for intent_id in intents_to_delete:
    #         # make REST call to delete intent
    #         resp = requests.delete(BASE_URL+'intents/'+intent_id, headers=API_AI_HEADERS)
    #         print(resp.status_code)

    # CREATE new Intents for IDs that appear in the old data but is not currently in API.ai (meaning they were deleted)
    # intents_to_create = old_intents_ids - cur_intents_ids
    # if len(intents_to_create) > 0:
    #     for intent_id in intents_to_create:
    #         # make REST call to delete intent
    #         requests.post(BASE_URL+'intents/'+intent_id, headers=API_AI_HEADERS, data=json.dumps(old_intents[intent_id]))

    # UPDATE the Intents in API.ai whose ID appears in the old data to be equivalent to the old data
    for intent_id in cur_intents_ids & old_intents_ids:
        if cur_intents[intent_id] != old_intents[intent_id]:
            resp = requests.put(BASE_URL+'intents/'+intent_id, headers=API_AI_HEADERS, json=old_intents[intent_id])
            print(resp.status_code)


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

@cli.command()
def save_all_intents():
    """
    Saves all intents from API.ai and commits them to the current git repo we're in.
    """
    if not environment_valid():
        return
    print('Saving them!')
    req = requests.get(BASE_URL+'intents', headers=API_AI_HEADERS)
    intents = req.json()
    with open('intents.pickle', 'wb') as f:
        pickle.dump(intents, f)
    print(intents)

@cli.command()
def load_all_intents():
    """
    Loads all intents to API.ai from current commit
    """
    if not environment_valid():
        return
    print('Saving them!')
    req = requests.get(BASE_URL+'intents', headers=API_AI_HEADERS)
    intents = req.json()
    with open('intents.pickle', 'wb') as f:
        pickle.dump(intents, f)
    print(intents)

@cli.command()
def main():
    if not environment_valid():
        return
    req = requests.get(BASE_URL+'intents', headers=API_AI_HEADERS)
    intents = req.json()
    print(intents)

def send_request(rest_type, endpoint):
    dev_key = os.getenv(DEV_TOKEN_ENV_NAME)
    if not dev_key:
        print("Please set environment variable {}".format(DEV_TOKEN_ENV_NAME))
        return None
    api_ai_headers = {'Authorization' : 'Bearer {}'.format(dev_key)}
    if rest_type is 'GET':
        req = requests.get(BASE_URL+endpoint, headers=api_ai_headers)
        return req.json()


    print('nah')


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
    return True



if __name__ == '__main__':
    cli()
