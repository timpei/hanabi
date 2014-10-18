import json
import gevent

from flask_sockets import Sockets

class gameSocketClient(object):

    def __init__(self):
        self.clients = list()
        

def parsePlayer(playerRes):
    return {
        'name': playerRes[0],
        'hand': json.loads(playerRes[1])
    }

def parseSpectator(spectatorsRes):
    return {
        'name': spectatorsRes[0]
    }

def encapsulate(game, gameId, playersRes, spectatorsRes):
    game['id'] = gameId
    game['players'] = []
    game['spectators'] = []
    for player in playersRes:
        game['players'].append(parsePlayer(player))
    for spectator in spectatorsRes:
        game['spectators'].append(parseSpectator(spectator))

    return game