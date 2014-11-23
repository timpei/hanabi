import os, sys
import json
import logging
import time

from flask import Flask, jsonify, request, make_response
from flask.ext.socketio import SocketIO, send, join_room, leave_room

import hanabi
from utils import parsePlayer, parseMessage, getGame, eventInject

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
socketio = SocketIO(app)
logging.basicConfig()


@app.route('/api/game/<int:gameId>', methods=['GET'])
def loadGame(gameId):
    return jsonify(**getGame(db, gameId))


@socketio.on('createGame')
@eventInject()
def createGame(msg, db, gameMsg):
    rainbow = msg['isRainbow']
    name = msg['name']

    game = hanabi.newGameObject(rainbow)
    gameId = db.executeWithId("INSERT INTO games (gameJSON) VALUES ('%s') RETURNING id" % json.dumps(game))
    db.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))

    join_room(gameId)
    game = getGame(db, gameId)
    gameMsg.buildEnterGame()
    send({
        'event': 'enterGame',
        'message' : gameMsg.message,
        'game': game
        }, json=True, room=gameId)


@socketio.on('enterGame')
@eventInject()
def enterGame(msg, db, gameMsg):
    gameId = msg['gameId']
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
                }, json=True)
            break
    if not sameNameExists:
        db.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))
        game = getGame(db, gameId)
        gameMsg.buildEnterGame()
        send({
            'event': 'enterGame',
            'message' : gameMsg.message,
            'game': game
            }, json=True, room=gameId)
        join_room(gameId)
        messages = [parseMessage(i) for i in db.fetchall("SELECT name, type, messageJSON, time FROM messages WHERE gameId = %d; " % gameId)]
        gameMsg.message['elements']['messages'] = messages
        send({
            'event': 'enterGame',
            'message' : gameMsg.message,
            'game': game
            }, json=True)

@socketio.on('joinGame')
@eventInject()
def joinGame(msg, db, gameMsg):
    gameId = msg['gameId']
    name = msg['name']

    numPlayers = db.fetchone('SELECT COUNT(id) FROM players WHERE gameId=%d AND joined=1; ' % gameId)[0]
    gameRes = db.fetchone('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    game = json.loads(gameRes[0])

    if numPlayers < hanabi.MAX_PLAYERS and not game['hasStarted']:
        db.execute("UPDATE players SET joined=1 WHERE gameId=%d AND name='%s'" % (gameId, name))
        
        game = getGame(db, gameId)
        gameMsg.buildJoinGame()
        send({
            'event': 'joinGame',
            'message' : gameMsg.message,
            'game': game
            }, json=True, room=gameId)
    else:
        send({
            'error': {
                'event': 'joinGame',
                'reason': 'max players exceeded'
                }
            }, json=True)
        

@socketio.on('resumeGame')
@eventInject()
def resumeGame(msg, db, gameMsg):
    gameId = msg['gameId']
    name = msg['name']

    players = db.fetchall("SELECT name FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    
    if len(players) != 0:
        game = getGame(db, gameId)
        gameMsg.buildResumeGame()
        send({
            'event': 'resumeGame',
            'message' : gameMsg.message,
            'game': game
            }, json=True, room=gameId)
        join_room(gameId)
        messages = [parseMessage(i) for i in db.fetchall("SELECT name, type, messageJSON, time FROM messages WHERE gameId = %d; " % gameId)]
        gameMsg.message['elements']['messages'] = messages
        send({
            'event': 'resumeGame',
            'message' : gameMsg.message,
            'game': game
            }, json=True)
    else:
        send({
            'error': {
                'event': 'resumeGame',
                'reason': 'no player with name exists'
                }
            }, json=True)


@socketio.on('leaveGame')
@eventInject()
def leaveGame(msg, db, gameMsg):
    gameId = msg['gameId']
    name = msg['name']

    leave_room(gameId)
    gameMsg.buildLeaveGame()
    send({
        'event': 'leaveGame',
        'message' : gameMsg.message,
        'game': None          # no game returned since it doesn't change the game state
        }, json=True)
    send({
        'event': 'leaveGame',
        'message' : gameMsg.message,
        'game': None          # no game returned since it doesn't change the game state
        }, json=True, room=gameId)


@socketio.on('startGame')
@eventInject()
def startGame(msg, db, gameMsg):
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
            queries.append("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" 
                    % (json.dumps(player['hand']), gameId, player['name']))
        queries.append("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" 
                % (json.dumps(game), json.dumps(deck), gameId))
        db.bulkExecute(queries)   

        game = getGame(db, gameId)
        gameMsg.buildStartGame()
        send({
            'event': 'startGame',
            'message' : gameMsg.message,
            'game': game
            }, json=True, room=gameId)
    else:
        send({
            'error': {
                'event': 'startGame',
                'reason': 'game already started'
                }
            }, json=True)
        

@socketio.on('sendMessage')
@eventInject()
def sendMessage(msg, db, gameMsg):
    gameId = msg['gameId']
    message = msg['message']
    name = msg['name']

    gameMsg.buildMsg(message)
    send({
        'event': 'sendMessage',
        'message' : gameMsg.message,
        'game': None
        }, json=True, room=gameId)


@socketio.on('giveHint')
@eventInject()
def giveHint(msg, db, gameMsg):
    gameId = msg['gameId']
    hintType = msg['hintType']
    name = msg['name']
    toName = msg['toName']
    hint = int(msg['hint']) if hintType == 'NUMBER' else msg['hint']

    gameRes = db.fetchone('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    toPlayerRes = db.fetchone("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, toName))

    game = json.loads(gameRes[0])
    toPlayer = parsePlayer(toPlayerRes)

    if hanabi.canHint(game, name):
        cardsHinted = hanabi.giveHint(game, toPlayer, hintType, hint)

        db.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
        db.execute("UPDATE players SET handJSON='%s' WHERE name='%s'" % (json.dumps(toPlayer['hand']), toPlayer['name']))

        game = getGame(db, gameId)
        gameMsg.buildHint(toName, hintType, hint, cardsHinted)
        send({ 
            'event': 'giveHint',
            'message' : gameMsg.message,
            'game': game
            }, json=True, room=gameId)
    else:
        send({
            'error': {
                'event': 'giveHint',
                'reason': 'invalid hint'
                }
            }, json=True)
        

@socketio.on('discardCard')
@eventInject()
def discardCard(msg, db, gameMsg):
    gameId = msg['gameId']
    name = msg['name']
    cardIndex = msg['cardIndex']

    gameRes = db.fetchone('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    playerRes = db.fetchone("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    
    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    discardedCard = hanabi.discardCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)

    queries = []
    queries.append("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" 
            % (json.dumps(game), json.dumps(deck), gameId))
    queries.append("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" 
            % (json.dumps(player['hand']), gameId, player['name']))
    db.bulkExecute(queries)

    game = getGame(db, gameId)
    gameMsg.buildDiscard(discardedCard)
    send({
        'event': 'discardCard',
        'message' : gameMsg.message,
        'game': game
        }, json=True, room=gameId)

@socketio.on('playCard')
@eventInject()
def playCard(msg, db, gameMsg):
    gameId = msg['gameId']
    name = msg['name']
    cardIndex = msg['cardIndex']

    gameRes = db.fetchone('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    playerRes = db.fetchone("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))

    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    playedCard = hanabi.playCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)
    
    queries = []
    queries.append("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
    queries.append("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" 
            % (json.dumps(player['hand']), gameId, player['name']))
    db.bulkExecute(queries)
        
    game = getGame(db, gameId)
    gameMsg.buildPlay(playedCard)
    send({
        'event': 'playCard',
        'message' : gameMsg.message,
        'game': game
        }, json=True, room=gameId)

@socketio.on('endGame')
@eventInject()
def endGame(msg, db, gameMsg):
    gameId = msg['gameId']

    gameRes = db.fetchone('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    game = json.loads(gameRes[0])

    hanabi.giveUp(game)
    db.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
    
    gameMsg.buildEndGame()
    send({
        'event': 'endGame',
        'message' : gameMsg.message,
        'game': game
        }, json=True, room=gameId)

@app.route('/')
def index():
    return make_response(open('%s/templates/index.html' % BASE_DIR).read())

@app.route('/test')
def test():
    return make_response(open('%s/templates/test.html' % BASE_DIR).read())

def run():
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
