# all the imports
import os
import psycopg2
import urlparse
import json
from flask import Flask, request, Response, session, g, redirect, url_for, abort, render_template, flash, jsonify

import hanabi
from app_utils import encapsulate, parsePlayer

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

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

@app.route('/api/create', methods=['POST'])
def createGame():

    game = hanabi.newGameObject()
    game['isRainbow'] = False if request.form['rainbow'] == "false" else True
    g.cur.execute("INSERT INTO games (gameJSON) VALUES ('%s') RETURNING id" % json.dumps(game))
    gameId = g.cur.fetchone()[0]
    g.conn.commit()

    g.cur.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, request.form['name'], '[]'))
    g.conn.commit()

    return jsonify(**getGame(gameId))

@app.route('/api/enter/<int:gameId>', methods=['POST'])
def enterGame(gameId):
    name = request.form['name']

    g.cur.execute('SELECT name, handJSON FROM players WHERE gameId = %d; ' % gameId)
    players = [parsePlayer(i) for i in g.cur.fetchall()]

    for player in players:
        if player['name'] == name:
            return jsonify(**{'success': False})

    g.cur.execute("INSERT INTO players (gameId, name, handJSON, joined) VALUES (%d, '%s', '%s', 0)" % (gameId, name, '[]'))
    g.conn.commit()
    # TODO: poll msg (id, enter-nw)
    return jsonify(**{'success': True, 'game': getGame(gameId)})

@app.route('/api/join/<int:gameId>', methods=['POST'])
def joinGame(gameId):

    g.cur.execute('SELECT COUNT(id) FROM players WHERE gameId=%d AND joined=1; ' % gameId)
    numPlayers = g.cur.fetchone()[0]
    g.cur.execute('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    gameRes = g.cur.fetchone()
    game = json.loads(gameRes[0])

    if numPlayers < 5 and not game['hasStarted']:
        g.cur.execute("UPDATE players SET joined=1 WHERE gameId=%d AND name='%s'" % (gameId, request.form['name']))
        g.conn.commit()
        # TODO: poll msg (id, join-new)
        return jsonify(**{'success': True, 'game': getGame(gameId)})
    else:
        return jsonify(**{'success': False})

@app.route('/api/enter/<int:gameId>', methods=['GET'])
def resumeGame(gameId):
    name = request.form['name']

    g.cur.execute("SELECT name FROM players WHERE gameId = %d AND name='%s'" % (gameId, name))
    players = g.cur.fetchall()
    
    if len(players) != 0:
        # TODO: poll msg (id, resume)
        return jsonify(**{'success': True, 'game': getGame(gameId)})
    else:
        return jsonify(**{'success': False})

@app.route('/api/start/<int:gameId>', methods=['POST'])
def startGame(gameId):

    g.cur.execute('SELECT gameJSON FROM games WHERE id=%d; ' % gameId)
    gameResult = g.cur.fetchone()
    g.cur.execute('SELECT name, handJSON FROM players WHERE gameId = %d AND joined=1; ' % gameId)
    players = g.cur.fetchall()
    game = json.loads(gameResult[0])
    players = [parsePlayer(i) for i in players]

    if (not game['hasStarted']) and len(players) > 1:
        game['hasStarted'] = True
        #g.cur.execute("UPDATE games SET gameJSON='%s' WHERE id=%d" % (json.dumps(game), gameId))
        #g.conn.commit()

        deck = hanabi.startGameAndGetDeck(game, players)

        for player in players:
            g.cur.execute("UPDATE players SET handJSON='%s' WHERE gameId=%d AND name='%s'" % (json.dumps(player['hand']), gameId, player['name']))
            game['order'].append(player['name'])
        g.cur.execute("UPDATE games SET gameJSON='%s', deckJSON='%s' WHERE id=%s" % (json.dumps(game), json.dumps(deck), gameId))
        g.conn.commit()   

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
        # TODO: pool msg (id, hint, colored hint msg)
        return jsonify(**{'success': True, 'cardsHinted': cardsHinted})
    else:
        return jsonify(**{'success': False})

@app.route('/api/discard/<int:gameId>', methods=['POST'])
def discardCard(gameId):

    name = request.form['name']
    cardIndex = int(request.form['cardIndex'])

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

    # TODO: poll msg (id, discard msg)
    return jsonify(**{'success': True, 'game': getGame(gameId)})

@app.route('/api/play/<int:gameId>', methods=['POST'])
def playCard(gameId):

    name = request.form['name']
    cardIndex = int(request.form['cardIndex'])

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
    # TODO: poll msg (id, discard msg)
    return jsonify(**{'success': True, 'game': getGame(gameId)})

@app.route('/api/end/<int:gameId>', methods=['POST'])
def endGame(gameId):

    g.cur.execute('SELECT gameJSON, deckJSON FROM games WHERE id=%d; ' % gameId)
    gameRes = g.cur.fetchone()
    game = json.loads(gameRes[0])

    hanabi.giveUp(game)
    g.cur.execute("UPDATE games SET gameJSON='%s' WHERE id=%s" % (json.dumps(game), gameId))
    g.conn.commit()
    # TODO: pool msg(id, ended game)
    return jsonify(**{'success': True})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ["HANABI_PORT"]))