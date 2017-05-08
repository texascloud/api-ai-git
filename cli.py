import os
import sys


def main(args):
    DEV_TOKEN_ENV_NAME = 'API_AI_DEV_TOKEN'
    dev_key = os.getenv(DEV_TOKEN_ENV_NAME)
    if not dev_key:
        print("Please set environment variable {}".format(DEV_TOKEN_ENV_NAME))
        return

    print('nah')




if __name__ == '__main__':
    main(sys.argv)
