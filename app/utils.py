import json
import urlparse
import psycopg2
import os

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
    game['players'] = []
    game['spectators'] = []
    for player in players:
        game['players'].append(parsePlayer(player))
    for spectator in spectators:
        game['spectators'].append(parseSpectator(spectator))

    return game

def eventInject(logger=False, db=False):
    def decorate(func):
        if db:
            dbInst = DatabaseService()
        @wraps(func)
        def wrapper(msg):
            print "%s request with payload: %s" % (func.__name__, msg)
            return func(msg, db=dbInst)
        if db:
            dbInst.close()
        return wrapper
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
