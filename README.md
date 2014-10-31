
An implementation of Hanabi, a popular board game. Starts with a web client, but can be integrated with multiple platforms through the server API.

# Requirements

* Server
  * PostgreSQL (Mac: install Postgres.app)
  * virtualenv is recommended
* Client
  * Socket.IO

# Running Locally

To run on your local machine:

1. Create a virtual environment and start it:

    ```
    cd hanabi-isotrophic
    virtualenv hanabi-env
    source hanabi-env/bin/activate
    ```

2. Install python dependencies:

    ```
    pip install -r requirements.txt
    ```

3. Initiate database:

    PostgreSQL needs to be running and psql needs to point to the correct path.
    ```
    psql -d $(whoami) -a -f schema.sql
    ```

4. Setup environment:

    ```
    echo "export DATABASE_URL=postgres:///$(whoami)" > env.sh
    chmod +x env.sh
    . env.sh
    ```

* Running the app

    ```
    # make sure virtualenv is running
    python app.py
    ```

# Game JSON

API calls will often return a game object as the response. Here is one for example: 
        
    {
        "currentPlayer": "Tim",
        "discarded": [],
        "hasEnded": false,
        "hasStarted": true,
        "id": 4,
        "isRainbow": false,
        "numCardsRemaining": 34,
        "numHints": 7,
        "numLives": 3,
        "order": [
            "Curtis",
            "Jackie",
            "Tim"
        ],
        "played": [
            {"number": 1, "suit": "BLUE", "knownSuit": [], "knowNumber": true}
        ],
        "players": [
            {
                "hand": [
                    {"number": 5, "suit": "YELLOW", "knownSuit": [], "knowNumber": false},
                    {"number": 3, "suit": "BLUE", "knownSuit": [], "knowNumber": false},
                    {"number": 4, "suit": "YELLOW", "knownSuit": [], "knowNumber": false},
                    {"number": 1, "suit": "WHITE", "knownSuit": [], "knowNumber": true},
                    {"number": 1, "suit": "BLUE", "knownSuit": [], "knowNumber": true}
                ],
                "name": "Curtis"
            },
            {
                "hand": [
                    {"number": 2, "suit": "WHITE", "knownSuit": [], "knowNumber": false},
                    {"number": 1, "suit": "GREEN", "knownSuit": [], "knowNumber": false},
                    {"number": 1, "suit": "YELLOW", "knownSuit": [], "knowNumber": false},
                    {"number": 3, "suit": "GREEN", "knownSuit": [], "knowNumber": false},
                    {"number": 3, "suit": "WHITE", "knownSuit": [], "knowNumber": false}
                ],
                "name": "Tim"
            },
            {
                "hand": [
                    {"number": 2, "suit": "YELLOW", "knownSuit": [], "knowNumber": false},
                    {"number": 5, "suit": "BLUE", "knownSuit": [], "knowNumber": false},
                    {"number": 5, "suit": "WHITE", "knownSuit": [], "knowNumber": false},
                    {"number": 2, "suit": "BLUE", "knownSuit": [], "knowNumber": false},
                    {"number": 2, "suit": "RED", "knownSuit": [], "knowNumber": false}
                ],
                "name": "Jackie"
            }
        ],
        "score": 1,
        "spectators": [
            {"name": "Tony"},
            {"name": "Meng"}
        ],
        "turnsLeft": -1
    }
    
Here's a call that could have generated the above response: `GET /api/get/4`. Some of the JSON fields are further discussed below:

* `discarded` is the discard pile, which consists of a list of card objects with the stucture like: `{"number": 4, "suit": "BLUE", "knownSuit": [], "knowNumber": False}`. `knownSuit` represents the colours told to the player with that card, and `knowNumber` represents if the player holding the card know its number. `knownSuit` is a list since it is possible in a rainbow game to have a card be hinted multiple colours. `played` and players' `hand` contains cards that exhibit the same structure.
* `hasEnded` indicates the termination of the game. It will be set to true when an end game state has been detected.
* `hasStarted` indicates the status of the game. It will be set to true by the host once enough players has joined.
* `order` is a random permutation of the players, governing the playing order. It is set after the start of the game.
* `spectators` are users who are not participating in the game, but can message players and see the progression of the game. A user who enters the game will become a spectator first, and must join to become a player.
* `turnsLeft` indicates how many turns are remianing before the end-game state. It will be -1 throughout the game until being set to 3 once the last card has been dealt.

# API Calls

##REST

###Get Game
Get current game object.
* `GET /api/game/<int:gameId>`
* **Response**: a Game object

##Socket.IO

In order to receive websocket payloads from SocketIO, the client must connect to the socket once he/she creates or enters the game. The socket namespace is the global namespace: `http://<domain_name>`. All emits from the server will be sent with the 'message' event.

###Create Game
Create and join a new game.

* **Send**
```javascript
emit('createGame', {
    isRainbow: boolean
    name: string
}
```
* **Broadcast**
```javascript
{
    'event': 'enterGame',
    'payload' : {
        'name': string,
        'game': a Game object,
        }
}
```

###Enter Game
Enter a game room. Player will become a spectator.
* **Send**
```
emit('enterGame', {
    gameId: int
    name: string
}
```
* **Broadcast**
```javascript
{
    'event': 'enterGame',
    'payload' : {
        'name': string,
        'game': a Game object,
        }
}
```
* **Exception**
```javascript
{
    'error': {
        'event': 'enterGame',
        'reason': 'same name exists'
        }
}
```

###Resume Game
Resume or re-join a game. Player must be already a player or spectator prior to the call.
* **Send**
```
emit('resumeGame', {
    gameId: int
    name: string
}
```
* **Broadcast**
```javascript
{
    'event': 'resumeGame',
    'payload' : {
        'name': string,
        'game': a Game object,
        }
}
```
* **Exception**
```javascript
{
'error': {
    'event': 'resumeGame',
    'reason': 'no player with name exists'
    }
}
```
###Join Game
Join a game. Player must be a spectator prior to the call. Will fail if number of joined players is at max (5).
* **Send**
```
emit('joinGame', {
    gameId: int
    name: string
}
```
* **Broadcast**
```javascript
{
    'event': 'joinGame',
    'payload' : {
        'name': string,
        'game': a Game object,
        }
}
```
* **Exception**
```javascript
{
    'error': {
        'event': 'joinGame',
        'reason': 'max players exceeded'
        }
}
```

###Start Game
Start a game. Can only start a game that hasn't been started yet. This will create a deck and deal cards to players.
* **Send**
```
emit('startGame', {
    gameId: int
}
```
* **Broadcast**
```javascript
{
    'event': 'startGame',
    'payload' : {
        'game': a Game object,
        }
}
```
* **Exception**
```javascript
{
    'error': {
        'event': 'startGame',
        'reason': 'game already started'
        }
}
```

###Send Message
Send a message to everyone in the game.
* **Send**
```
emit('sendMessage', {
    gameId: int,
    name: string,
    message: string
}
```
* **Broadcast**
```javascript
{
    'event': 'sendMessage',
    'payload' : {
        'message': string,
        'name': string
        }
}
```

###Give Hint
Gives a hint to another player. Must be the player's turn to play. `hintType` can either be "number" or "colour".
* **Send**
```
emit('giveHint', {
    gameId: int,
    hintType: string,
    name: string,
    toName: string,
    hint: [string, int]
}
```
* **Broadcast**
```javascript
{
    'event': 'giveHint',
    'payload' : {
        "hintType": string,
        "hint": [string, int],
        "cardsHinted": list(int),
        "from": string,
        "to": string,
        "game": a Game object
        }
}
```
* **Exception**
```javascript
{
    'error': {
        'event': 'giveHint',
        'reason': 'invalid hint'
        }
}
```

###Discard Card
* **Send**
```
emit('discardCard', {
    gameId: int,
    name: string,
    cardIndex: int
}
```
* **Broadcast**
```javascript
{
    'event': 'discardCard',
    'payload' : {
        "name": string,
        "card": a Card object,
        "game": a Game object,
        }
}
```

###Play Card
* **Send**
```
emit('playCard', {
    gameId: int,
    name: string,
    cardIndex: int
}
```
* **Broadcast**
```javascript
{
    'event': 'playCard',
    'payload' : {
        "name": string,
        "card": a Card object,
        "game": a Game object,
        }
}
```

###End Game
* **Send**
```
emit('endGame', {
    gameId: int,
    name: string
}
```
* **Broadcast**
```javascript
{
    'event': 'endGame',
    'payload' : {
        'name': string
    }
}
```
