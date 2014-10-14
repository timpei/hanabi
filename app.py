# all the imports
import sqlite3
import json
from flask import Flask, request, Response, session, g, redirect, url_for, abort, render_template, flash, jsonify

import hanabi
from app_utils import encapsulate, parsePlayer

DATABASE = 'db/hanabi.db'
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def getGame(gameId):
    gameResult = g.db.execute('SELECT gameJSON FROM games WHERE id = %d' % gameId).fetchall()[0]
    game = json.loads(gameResult[0])
    players = g.db.execute('SELECT name, handJSON FROM players WHERE gameId = %d AND joined=1' % gameId).fetchall()
    spectators = g.db.execute('SELECT name FROM players WHERE gameId = %d AND joined=0' % gameId).fetchall()

    return encapsulate(game, gameId, players, spectators)

@app.route('/api/game/<int:gameId>', methods=['GET'])
def loadGame(gameId):
    return jsonify(**getGame(gameId))

@app.route('/api/create', methods=['POST'])
def createGame():
    cursor = g.db.cursor()

    game = hanabi.newGameObject()
    game['isRainbow'] = False if request.form['rainbow'] == "false" else True
    cursor.execute("INSERT INTO games (gameJSON) VALUES ('%s')" % json.dumps(game))
    g.db.commit()

    gameId = cursor.lastrowid
    cursor.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, request.form['name'], '[]'))
    g.db.commit()

    return jsonify(**getGame(gameId))

@app.route('/api/enter/<int:gameId>', methods=['POST'])
def enterGame(gameId):
    cursor = g.db.cursor()
    name = request.form['name']

    players = g.db.execute('SELECT name, handJSON FROM players WHERE gameId = %d' % gameId).fetchall()
    players = [parsePlayer(i) for i in players]

    for player in players:
        if player['name'] == name:
            return jsonify(**{'success': False})

    cursor.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))
    g.db.commit()
    # TODO: poll msg (id, enter-nw)
    return jsonify(**{'success': True, 'game': getGame(gameId)})

@app.route('/api/join/<int:gameId>', methods=['POST'])
def joinGame(gameId):
    cursor = g.db.cursor()

    numPlayers = g.db.execute('SELECT COUNT(id) FROM players WHERE gameId=%d AND joined=1' % gameId).fetchall()[0][0]
    gameRes = g.db.execute('SELECT gameJSON FROM games WHERE id=%d' % gameId).fetchall()[0]
    game = json.loads(gameRes[0])

    if numPlayers < 5 and not game['hasStarted']:
        cursor.execute("UPDATE players SET joined=1 WHERE gameId=%d AND name='%s'" % (gameId, request.form['name']))
        g.db.commit()
        # TODO: poll msg (id, join-new)
        return jsonify(**{'success': True, 'game': getGame(gameId)})
    else:
        return jsonify(**{'success': False})

@app.route('/api/enter/<int:gameId>', methods=['GET'])
def resumeGame(gameId):
    name = request.form['name']

    players = g.db.execute("SELECT name FROM players WHERE gameId = %d AND name='%s'" % (gameId, name)).fetchall()
    
    if len(players) != 0:
        # TODO: poll msg (id, resume)
        return jsonify(**{'success': True, 'game': getGame(gameId)})
    else:
        return jsonify(**{'success': False})

@app.route('/api/start/<int:gameId>', methods=['POST'])
def startGame(gameId):
    cursor = g.db.cursor()

    gameResult = g.db.execute('SELECT gameJSON FROM games WHERE id=%d' % gameId).fetchall()[0]
    players = g.db.execute('SELECT name, handJSON FROM players WHERE gameId = %d AND joined=1' % gameId).fetchall()
    game = json.loads(gameResult[0])
    players = [parsePlayer(i) for i in players]

    if (not game['hasStarted']) and len(players) > 1:
        game['hasStarted'] = True
        #cursor.execute("UPDATE games SET gameJSON='%s' WHERE id=%d" % (json.dumps(game), gameId))
        #g.db.commit()

        deck = hanabi.startGameAndGetDeck(game, players)

        for player in players:
            cursor.execute("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
            game['order'].append(player['name'])
        cursor.execute("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
        g.db.commit()   

        # TODO: poll msg (id, game-start)

        return jsonify(**{'success': True, 'game': getGame(gameId)})
    else:
        return jsonify(**{'success': False})

@app.route('/api/message/<int:gameId>', methods=['POST'])
def sendMessage(gameId):
    message = request.form['message']
    name = request.form['name']

    # TODO: pool msg (id, message, msg)
    return jsonify(**{'success': True})

@app.route('/api/hint/<hintType>/<int:gameId>', methods=['POST'])
def giveHint(hintType, gameId):
    name = request.form['name']
    toName = request.form['toName']
    hint = int(request.form['hint']) if hintType == 'number' else request.form['hint']


    gameRes = g.db.execute('SELECT gameJSON FROM games WHERE id=%d' % gameId).fetchall()[0]
    toPlayerRes = g.db.execute("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, toName)).fetchall()[0]

    game = json.loads(gameRes[0])
    toPlayer = parsePlayer(toPlayerRes)

    if hanabi.canHint(game, name):
        cardsHinted = hanabi.giveHint(game, toPlayer, hintType, hint)
        cursor = g.db.cursor()
        cursor.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
        g.db.commit()
        # TODO: pool msg (id, hint, colored hint msg)
        return jsonify(**{'success': True, 'cardsHinted': cardsHinted})
    else:
        return jsonify(**{'success': False})

@app.route('/api/discard/<int:gameId>', methods=['POST'])
def discardCard(gameId):
    cursor = g.db.cursor()

    name = request.form['name']
    cardIndex = int(request.form['cardIndex'])

    gameRes = g.db.execute('SELECT gameJSON, deckJSON FROM games WHERE id=%d' % gameId).fetchall()[0]
    playerRes = g.db.execute("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name)).fetchall()[0]
    
    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    hanabi.discardCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)

    cursor.execute("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
    cursor.execute("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
    g.db.commit()

    # TODO: poll msg (id, discard msg)
    return jsonify(**{'success': True, 'game': getGame(gameId)})

@app.route('/api/play/<int:gameId>', methods=['POST'])
def playCard(gameId):
    cursor = g.db.cursor()

    name = request.form['name']
    cardIndex = int(request.form['cardIndex'])

    gameRes = g.db.execute('SELECT gameJSON, deckJSON FROM games WHERE id=%d' % gameId).fetchall()[0]
    playerRes = g.db.execute("SELECT name, handJSON FROM players WHERE gameId = %d AND name='%s'" % (gameId, name)).fetchall()[0]
    
    game = json.loads(gameRes[0])
    deck = json.loads(gameRes[1])
    player = parsePlayer(playerRes)

    hanabi.playCard(game, deck, player, cardIndex)
    hanabi.endTurn(game)
    
    cursor.execute("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
    cursor.execute("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
    g.db.commit()
    # TODO: poll msg (id, discard msg)
    return jsonify(**{'success': True, 'game': getGame(gameId)})

@app.route('/api/end/<int:gameId>', methods=['POST'])
def endGame(gameId):
    cursor = g.db.cursor()

    gameRes = g.db.execute('SELECT gameJSON, deckJSON FROM games WHERE id=%d' % gameId).fetchall()[0]
    game = json.loads(gameRes[0])

    cursor = g.db.cursor()
    hanabi.giveUp(game)
    cursor.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
    g.db.commit()
    # TODO: pool msg(id, ended game)
    return jsonify(**{'success': True})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')