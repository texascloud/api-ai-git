import os
import pickle
import requests
import click
import git
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
    intents_json = requests.get(BASE_URL+'intents', headers=API_AI_HEADERS).json()
    entities_json = requests.get(BASE_URL+'entities', headers=API_AI_HEADERS).json()
    intents = {}
    entities = {}
    for d in intents_json:
        intents[d['id']] = requests.get(BASE_URL+'intents/'+d['id'], headers=API_AI_HEADERS).json()

    for d in entities_json:
        entities[d['id']] = requests.get(BASE_URL+'entities/'+d['id'], headers=API_AI_HEADERS).json()

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
    if not commit_hash:
        commits = list(repo.iter_commits('master', max_count=10))
        for i, commit in enumerate(commits):
            print("{}  {}  {}".format(i, commit.hexsha, commit.message))
        num_pressed = int(input("Press number corresponding to which commit you'd like to rollback:"))
        print("{} corresponds to commit hash {}, is that correct?".format(num_pressed, commits[num_pressed].hexsha))
        commit_hash = commits[num_pressed].hexsha

    print('Loading entire state!')
    head_hash = repo.head.commit.hexsha
    repo.head.checkout(commit_hash)
    # 'rb' means read the files in binary mode
    with open('intents.pickle', 'rb') as f, open('entities.pickle', 'rb') as f2:
        intents = pickle.load(f)
        entities = pickle.load(f2)

    repo.head.checkout(head_hash)
    print(intents)
    print(entities)

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
