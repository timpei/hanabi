
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

# Server Response

The server will *always* return socket payloads in a consistent structure:
	
```javascript
{
	'event': event String,
	'game': game Object,
	'message': message Object
}
```
	
## Game Object

API calls will often return a game object as the response. Here is one for example: 
        
```javascript
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
```
    
Some of the JSON fields are further discussed below:

* `discarded` is the discard pile, which consists of a list of card objects with the stucture like: `{"number": 4, "suit": "BLUE", "knownSuit": [], "knowNumber": False}`. `knownSuit` represents the colours told to the player with that card, and `knowNumber` represents if the player holding the card know its number. `knownSuit` is a list since it is possible in a rainbow game to have a card be hinted multiple colours. `played` and players' `hand` contains cards that exhibit the same structure.
* `hasEnded` indicates the termination of the game. It will be set to true when an end game state has been detected.
* `hasStarted` indicates the status of the game. It will be set to true by the host once enough players has joined.
* `order` is a random permutation of the players, governing the playing order. It is set after the start of the game.
* `spectators` are users who are not participating in the game, but can message players and see the progression of the game. A user who enters the game will become a spectator first, and must join to become a player.
* `turnsLeft` indicates how many turns are remianing before the end-game state. It will be -1 throughout the game until being set to 3 once the last card has been dealt.


## Message Object

A message object contains information about the broadcased event:

	{
		'name': sender name String,
		'type': message type,
		'time': timestamp,
		'message': pre-constructed message string,
		'elements': supplimentary data object
	}
	
* `type` can be 'ROOM', 'HINT', 'PLAY', 'DISCARD' or 'MESSAGE' depending on the message provided. ROOM indicates a change in room status. MESSAGE indicates a sent message.
* `elements` is custom based on the event sent.


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

###Enter Game
Enter a game room. Player will become a spectator.

* **Send**

	```javascript
	emit('enterGame', {
	    gameId: int
	    name: string
	}
	```

* **Message Element**

	```javascript
	{
	   "messages": list of Message Objects
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

	```javascript
	emit('resumeGame', {
	    gameId: int
	    name: string
	    quiet: boolean (Optional: message broadcast is skipped if true)
	}
	```
* **Message Element**

	```javascript
	{
	   "messages": list of Message Objects
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

	```javascript
	emit('joinGame', {
	    gameId: int
	    name: string
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

###Leave Game
Leave the game, i.e. not receiving future socket messages from the game room. Player can always resume game later.

* **Send**

	```javascript
	emit('leaveGame', {
	    gameId: int
	    name: string
	}
	```

###Start Game
Start a game. Can only start a game that hasn't been started yet. This will create a deck and deal cards to players.

* **Send**

	```javascript
	emit('startGame', {
	    gameId: int
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

	```javascript
	emit('sendMessage', {
	    gameId: int,
	    name: string,
	    message: string
	}
	```

###Give Hint
Gives a hint to another player. Must be the player's turn to play. `hintType` can either be "number" or "colour".

* **Send**

	```javascript
	emit('giveHint', {
		gameId: int,
		hintType: string,
		name: string,
		toName: string,
		hint: [string, int]
	}
	```

* **Message Element**

	```javascript
	{
	   "hintType": string,
	   "hint": [string, int],
	   "cardsHinted": list(int),
	   "to": string,
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

	```javascript
	emit('discardCard', {
	    gameId: int,
	    name: string,
	    cardIndex: int
	}
	```

* **Message Element**

	```javascript
	{
		card: a Card Object
	}
	```

###Play Card
* **Send**

	```javascript
	emit('playCard', {
	    gameId: int,
	    name: string,
	    cardIndex: int
	}
	```

* **Message Element**

    ```javascript
    {
        card: a Card Object
    }
    ```

###End Game
* **Send**

	```javascript
	emit('endGame', {
	    gameId: int,
	    name: string
	}
	```
