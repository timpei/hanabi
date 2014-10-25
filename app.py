# all the imports
import os, sys
import psycopg2
import urlparse
import json
import logging

from threading import Thread
from flask import Flask, g, render_template, jsonify, request
from flask.ext.socketio import SocketIO, emit, send, join_room, leave_room

import hanabi
from app_utils import encapsulate, parsePlayer

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
socketio = SocketIO(app)
logging.basicConfig()

def connect_db():
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return conn

@app.before_request
def before_request():
    g.conn = connect_db()
    g.cur = g.conn.cursor()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
    cur = getattr(g, 'cur', None)
    if cur is not None:
        cur.close()

def getGame(gameId):
    g.cur.execute('SELECT gameJSON FROM games WHERE id = %d; ' % gameId)
    game = json.loads(g.cur.fetchone()[0])
    g.cur.execute('SELECT name, handJSON FROM players WHERE gameId = %d AND joined=1; ' % gameId)
    players = g.cur.fetchall()
    g.cur.execute('SELECT name FROM players WHERE gameId = %d AND joined=0; ' % gameId)
    spectators = g.cur.fetchall()

    return encapsulate(game, gameId, players, spectators)

@app.route('/api/game/<int:gameId>', methods=['GET'])
def loadGame(gameId):
    return jsonify(**getGame(gameId))

@socketio.on('createGame')
def createGame(msg):
    rainbow = False if msg['rainbow'].lower() == "false" else True
    name = msg['name']

    game = hanabi.newGameObject(rainbow)
    g.cur.execute("INSERT INTO games (gameJSON) VALUES ('%s') RETURNING id" % json.dumps(game))
    gameId = g.cur.fetchone()[0]
    g.conn.commit()

    g.cur.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))
    g.conn.commit()

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
    gameId = int(msg['gameId'])
    name = msg['name']

    sameNameExists = False

    g.cur.execute('SELECT name, handJSON FROM players WHERE gameId = %d; ' % gameId)
    players = [parsePlayer(i) for i in g.cur.fetchall()]

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
        g.cur.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))
        g.conn.commit()

        game = getGame(gameId)
        join_room(gameId)
        send({
            'event': 'enterGame',
            'payload' : {
                'name': name,
                'game': game,
                }
            }, json=True, room=gameId)

@socketio.on('joinGame')
def joinGame(msg):
    gameId = msg['gameId']
    name = msg['name']

    g.cur.execute('SELECT COUNT(id) FROM players WHERE gameId=%d AND joined=1; ' % gameId)
    numPlayers = g.cur.fetchone()[0]
    g.cur.execute('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    gameRes = g.cur.fetchone()
    game = json.loads(gameRes[0])

    if numPlayers < hanabi.MAX_PLAYERS and not game['hasStarted']:
        g.cur.execute("UPDATE players SET joined=1 WHERE gameId=%d AND name='%s'" % (gameId, name))
        g.conn.commit()
        
        game = getGame(gameId)
        send({
            'event': 'joinGame',
            'payload' : {
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

@socketio.on('resumeGame')
def resumeGame(msg):
    gameId = msg['gameId']
    name = msg['name']

    g.cur.execute("SELECT name FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    players = g.cur.fetchall()
    
    if len(players) != 0:
        game = getGame(gameId)
        send({
            'event': 'resumeGame',
            'payload' : {
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
    gameId = msg['gameId']

    g.cur.execute('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    gameResult = g.cur.fetchone()
    g.cur.execute('SELECT name, handJSON FROM players WHERE gameId = %d AND joined=1; ' % gameId)
    players = g.cur.fetchall()
    game = json.loads(gameResult[0])
    players = [parsePlayer(i) for i in players]

    if (not game['hasStarted']) and len(players) > 1:
        game['hasStarted'] = True

        deck = hanabi.startGameAndGetDeck(game, players)
        for player in players:
            g.cur.execute("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
            game['order'].append(player['name'])
        g.cur.execute("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
        g.conn.commit()   

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
    gameId = msg['gameId']
    hintType = msg['hintType']
    name = msg['name']
    toName = msg['toName']
    hint = int(msg['hint']) if hintType == 'number' else msg['hint']

    g.cur.execute('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    gameRes = g.cur.fetchone()
    g.cur.execute("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, toName))
    toPlayerRes = g.cur.fetchone()

    game = json.loads(gameRes[0])
    toPlayer = parsePlayer(toPlayerRes)

    if hanabi.canHint(game, name):
        cardsHinted = hanabi.giveHint(game, toPlayer, hintType, hint)

        g.cur.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
        g.conn.commit()

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

@socketio.on('discardCard')
def discardCard(msg):
    gameId = msg['gameId']
    name = msg['name']
    cardIndex = int(msg['cardIndex'])

    g.cur.execute('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    gameRes = g.cur.fetchone()
    g.cur.execute("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    playerRes = g.cur.fetchone()
    
    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    hanabi.discardCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)

    g.cur.execute("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
    g.cur.execute("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
    g.conn.commit()

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
    gameId = msg['gameId']
    name = msg['name']
    cardIndex = int(msg['cardIndex'])

    g.cur.execute('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    gameRes = g.cur.fetchone()
    g.cur.execute("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    playerRes = g.cur.fetchone()

    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    hanabi.playCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)
    
    g.cur.execute("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
    g.cur.execute("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
    g.conn.commit()

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
    gameId = msg['gameId']

    g.cur.execute('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    gameRes = g.cur.fetchone()
    game = json.loads(gameRes[0])

    hanabi.giveUp(game)
    g.cur.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
    g.conn.commit()

    send({
        'event': 'endGame',
        'payload' : {}
        }, json=True, room=gameId)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
