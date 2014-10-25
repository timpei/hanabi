import os, sys
import json
import logging

from flask import Flask, jsonify, request, make_response
from flask.ext.socketio import SocketIO, send, join_room, leave_room

import hanabi
from utils import parsePlayer, DatabaseService, getGame

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
socketio = SocketIO(app)
logging.basicConfig()

@app.route('/api/game/<int:gameId>', methods=['GET'])
def loadGame(gameId):
    return jsonify(**getGame(gameId))

@socketio.on('createGame')
def createGame(msg):
    db = DatabaseService()
    rainbow = False if msg['rainbow'].lower() == "false" else True
    name = msg['name']

    game = hanabi.newGameObject(rainbow)
    gameId = db.executeWithId("INSERT INTO games (gameJSON) VALUES ('%s') RETURNING id" % json.dumps(game))
    db.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))
    db.close()

    join_room(gameId)
    game = getGame(gameId)
    send({
        'event': 'enterGame',
        'payload' : {
            'name': name,
            'game': game,
            }
        }, json=True, room=gameId)

@socketio.on('enterGame')
def enterGame(msg):
    db = DatabaseService()
    gameId = int(msg['gameId'])
    name = msg['name']

    sameNameExists = False
    players = [parsePlayer(i) for i in db.fetchall('SELECT name, handJSON FROM players WHERE gameId = %d; ' % gameId)]

    for player in players:
        if player['name'] == name:
            sameNameExists = True
            send({
                'error': {
                    'event': 'enterGame',
                    'reason': 'same name exists'
                    }
                }, json=True, room=gameId)
            break

    if sameNameExists:
        db.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))
        game = getGame(gameId)
        join_room(gameId)
        send({
            'event': 'enterGame',
            'payload' : {
                'name': name,
                'game': game,
                }
            }, json=True, room=gameId)

    db.close()

@socketio.on('joinGame')
def joinGame(msg):
    db = DatabaseService()
    gameId = msg['gameId']
    name = msg['name']

    numPlayers = db.fetchone('SELECT COUNT(id) FROM players WHERE gameId=%d AND joined=1; ' % gameId)[0]
    gameRes = db.fetchone('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    game = json.loads(gameRes[0])

    if numPlayers < hanabi.MAX_PLAYERS and not game['hasStarted']:
        db.execute("UPDATE players SET joined=1 WHERE gameId=%d AND name='%s'" % (gameId, name))
        
        game = getGame(gameId)
        send({
            'event': 'joinGame',
            'payload' : {
                'name': name,
                'game': game,
                }
            }, json=True, room=gameId)
    else:
        send({
            'error': {
                'event': 'joinGame',
                'reason': 'max players exceeded'
                }
            }, json=True, room=gameId)
        
    db.close()

@socketio.on('resumeGame')
def resumeGame(msg):
    db = DatabaseService()
    gameId = msg['gameId']
    name = msg['name']

    players = db.fetchall("SELECT name FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    db.close()
    
    if len(players) != 0:
        game = getGame(gameId)
        send({
            'event': 'resumeGame',
            'payload' : {
                'name': name,
                'game': game,
                }
            }, json=True, room=gameId)
    else:
        join_room(gameId)
        send({
            'error': {
                'event': 'resumeGame',
                'reason': 'no player with name exists'
                }
            }, json=True, room=gameId)

@socketio.on('startGame')
def startGame(msg):
    db = DatabaseService()
    gameId = msg['gameId']

    gameResult = db.fetchone('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    players = db.fetchall('SELECT name, handJSON FROM players WHERE gameId = %d AND joined=1; ' % gameId)
    game = json.loads(gameResult[0])
    players = [parsePlayer(i) for i in players]

    if (not game['hasStarted']) and len(players) > 1:
        game['hasStarted'] = True

        deck = hanabi.startGameAndGetDeck(game, players)
        queries = []
        for player in players:
            queries.append("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
            game['order'].append(player['name'])
        queries.append("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
        db.bulkExecute(queries)   

        game = getGame(gameId)
        send({
            'event': 'startGame',
            'payload' : {
                'game': game,
                }
            }, json=True, room=gameId)
    else:
        send({
            'error': {
                'event': 'startGame',
                'reason': 'game already started'
                }
            }, json=True, room=gameId)
        
    db.close()

@socketio.on('sendMessage')
def sendMessage(msg):
    gameId = msg['gameId']
    message = msg['message']
    name = msg['name']

    send({
        'event': 'sendMessage',
        'payload' : {
            'message': message,
            'name': name
            }
        }, json=True, room=gameId)

@socketio.on('giveHint')
def giveHint():
    db = DatabaseService()
    gameId = msg['gameId']
    hintType = msg['hintType']
    name = msg['name']
    toName = msg['toName']
    hint = int(msg['hint']) if hintType == 'number' else msg['hint']

    gameRes = db.fetchone('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    toPlayerRes = db.fetchone("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, toName))

    game = json.loads(gameRes[0])
    toPlayer = parsePlayer(toPlayerRes)

    if hanabi.canHint(game, name):
        cardsHinted = hanabi.giveHint(game, toPlayer, hintType, hint)

        db.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))

        game = getGame(gameId)
        send({
            'event': 'giveHint',
            'payload' : {
                "hintType": hintType,
                "hint": hint,
                "cardsHinted": cardsHinted,
                "from": name,
                "to": toName,
                "game": game
                }
            }, json=True, room=gameId)
    else:
        send({
            'error': {
                'event': 'giveHint',
                'reason': 'invalid hint'
                }
            }, json=True, room=gameId)
        
    db.close()

@socketio.on('discardCard')
def discardCard(msg):
    db = DatabaseService()
    gameId = msg['gameId']
    name = msg['name']
    cardIndex = int(msg['cardIndex'])

    gameRes = db.fetchone('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    playerRes = db.fetchone("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    
    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    hanabi.discardCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)

    queries = []
    queries.append("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
    queries.append("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
    db.bulkExecute(queries)
    db.close()

    game = getGame(gameId)
    send({
        'event': 'discardCard',
        'payload' : {
            "name": name,
            "cardIndex": cardIndex,
            "game": game,
            }
        }, json=True, room=gameId)

@socketio.on('playCard')
def playCard(gameId):
    db = DatabaseService()
    gameId = msg['gameId']
    name = msg['name']
    cardIndex = int(msg['cardIndex'])

    gameRes = db.fetchone('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    playerRes = db.fetchone("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))

    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    hanabi.playCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)
    
    queries = []
    queries.append("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
    queries.append("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
    db.bulkExecute(queries)
    db.close()
        
    db.close()

    game = getGame(gameId)
    send({
        'event': 'playCard',
        'payload' : {
            "name": name,
            "cardIndex": cardIndex,
            "game": game,
            }
        }, json=True, room=gameId)

@socketio.on('endGame')
def endGame(msg):
    db = DatabaseService()
    gameId = msg['gameId']

    gameRes = db.fetchone('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    game = json.loads(gameRes[0])

    hanabi.giveUp(game)
    db.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
    db.close()

    send({
        'event': 'endGame',
        'payload' : {}
        }, json=True, room=gameId)

@app.route('/')
def index():
    return make_response(open('app/templates/index.html').read())

def run():
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
