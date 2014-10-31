import json
from random import shuffle

SUITS = ['WHITE', 'YELLOW', 'RED', 'BLUE', 'GREEN']
SUITS_WITH_RAINBOW =  ['WHITE', 'YELLOW', 'RED', 'BLUE', 'GREEN', 'RAINBOW']
NUMBERS = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
MAX_HINTS = 8
MAX_LIVES = 3
MAX_PLAYERS = 5
HAND_SIZE = {
    2: 5,
    3: 5,
    4: 4,
    5: 4
}

def newGameObject(isRainbow):
    newGame = {
        "numCardsRemaining": 0,
        "currentPlayer": "",
        "isRainbow": isRainbow,
        "hasStarted": False,
        "hasEnded": False,
        "turnsLeft": -1,
        "numHints": MAX_HINTS,
        "numLives": MAX_LIVES,
        "played": [],
        "discarded": [],
        "order": [],
        "score": 0
    }
    return newGame

def newCardObject(suit, number):
    newCard = {
        "suit": suit,
        "number": number,
        "knownSuit": [],
        "knowNumber": False
    }
    return newCard

def newShuffledDeck(isRainbow):
    deck = []
    suits = SUITS_WITH_RAINBOW if isRainbow else SUITS
    for suit in suits:
        for number in NUMBERS:
            deck.append(newCardObject(suit, number))

    shuffle(deck)
    return deck

def startGameAndGetDeck(game, players):
    deck = newShuffledDeck(game['isRainbow'])
    handSize = HAND_SIZE[len(players)]

    for i in xrange(handSize):
        for player in players:
            player['hand'].append(deck.pop())

    game['numCardsRemaining'] = len(deck)
    game['currentPlayer'] = players[0]['name']

    return deck

def canHint(game, fromPlayer):
    return game['numHints'] > 0

def giveHint(game, toPlayer, hintType, hint):
    cardsHinted = []
    for idx, card in enumerate(toPlayer['hand']):
        if hintType == 'suit' and (card['suit'] == hint or card['suit'] == "RAINBOW"):
            card['knownSuit'].append(hint)
            cardsHinted.append(idx)
        if hintType == 'number' and card['number'] == hint:
            card['knowNumber'] = True
            cardsHinted.append(idx)

    game['numHints'] -= 1
    game['currentPlayer'] = game['order'][(game['order'].index(game['currentPlayer']) + 1) % len(game['order'])]
    return cardsHinted

def discardCard(game, deck, player, cardIndex):
    card = player['hand'].pop(cardIndex)
    game['discarded'].append(card)
    if (game['numHints'] < MAX_HINTS):
        game['numHints'] += 1
    if game['numCardsRemaining'] != 0:
        game['numCardsRemaining'] -= 1
        player['hand'].insert(0, deck.pop())
    return card

def playCard(game, deck, player, cardIndex):
    playedCard = player['hand'].pop(cardIndex)
    suitFound = False

    for idx, card in enumerate(game['played']):
        if (card['suit'] == playedCard['suit']):
            suitFound = True
            if (card['number'] + 1 == playedCard['number']):
                game['played'][idx]['number'] += 1
                if (playedCard['number'] == 5 and game['numHints'] < MAX_HINTS):
                    game['numHints'] += 1
            else:
                game['discarded'].append(playedCard)
                game['numLives'] -= 1

    if not suitFound:
        if playedCard['number'] == 1:
            game['played'].append(playedCard)
        else:
            game['discarded'].append(playedCard)
            game['numLives'] -= 1
    
    if game['numCardsRemaining'] != 0:
        game['numCardsRemaining'] -= 1
        player['hand'].insert(0, deck.pop())
    return playedCard

def endTurn(game):
    game['currentPlayer'] = game['order'][(game['order'].index(game['currentPlayer']) + 1) % len(game['order'])]

    if game['numCardsRemaining'] == 0:
        if game['turnsLeft'] >= 0:
            game['turnsLeft'] -= 1
        else:
            game['turnsLeft'] = len(game['order'])

    game['score'] = 0
    for card in game['played']:
        game['score'] += card['number']

    if game['numLives'] == 0 or game['turnsLeft'] == 0 or (game['score'] == 25 and not game['isRainbow']) or game['score'] == 30:
        game['hasEnded'] = True

def giveUp(game):
    game['hasEnded'] = True