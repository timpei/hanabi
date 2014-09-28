import json

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