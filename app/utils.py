import json
import urlparse
import psycopg2
import os
import time

from functools import wraps

def parsePlayer(playerRes):
    return {
        'name': playerRes[0],
        'hand': json.loads(playerRes[1])
    }

def parseSpectator(spectatorsRes):
    return {
        'name': spectatorsRes[0]
    }

def getGame(gameId):
    db = DatabaseService()
    game = json.loads(db.fetchone('SELECT gameJSON FROM games WHERE id = %d; ' % gameId)[0])
    players = db.fetchall('SELECT name, handJSON FROM players WHERE gameId = %d AND joined=1; ' % gameId)
    spectators = db.fetchall('SELECT name FROM players WHERE gameId = %d AND joined=0; ' % gameId)
    db.close()

    game['id'] = gameId
    game['spectators'] = []
    if game['hasStarted']:
        game['players'] = [None for i in players]   # preinitialize players array to preserve order
        for player in players:
            player = parsePlayer(player)
            for idx, name in enumerate(game['order']):
                if player['name'] == name:
                    game['players'][idx] = player
    else:
        game['players'] = []
        for player in players:
            player = parsePlayer(player)
            game['players'].append(player)
    for spectator in spectators:
        game['spectators'].append(parseSpectator(spectator))

    return game

def eventInject(logger=False, db=False):
    def decorate(func):
        if db:
            dbInst = DatabaseService()
        @wraps(func)
        def wrapper(msg):
            print "%s [socketio]: %s request with payload: %s" % (time.asctime(time.localtime(time.time())), func.__name__, msg)
            if db:
                result = func(msg, db=dbInst)
            else:
                result = func(msg)
            return result
        return wrapper
        if db:
            dbInst.close()
    return decorate


class DatabaseService:
    def connect_db(self):
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

    def __init__(self):
        self.conn = self.connect_db()
        self.cur = self.conn.cursor()

    def fetchone(self, query):
        self.cur.execute(query)
        return self.cur.fetchone()

    def fetchall(self, query):
        self.cur.execute(query)
        return self.cur.fetchall()

    def execute(self, query):
        self.cur.execute(query)
        self.conn.commit()

    def bulkExecute(self, queries):
        for query in queries:
            self.cur.execute(query)
        self.conn.commit()

    def executeWithId(self, query):
        self.cur.execute(query)
        ret = self.cur.fetchone()[0]
        self.conn.commit()
        return ret

    def close(self):
        self.conn.close()
        self.cur.close()
