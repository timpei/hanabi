import os
import redis

url = os.environ.get('HANABI_URL')
port = int(os.environ.get('HANABI_PORT'))
pw = os.environ.get('HANABI_PASS')

server = redis.Redis(host=url, port=port, password=pw)


