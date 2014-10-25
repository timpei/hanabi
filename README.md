
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
            {"number": 1, "suit": "BLUE"}
        ],
        "players": [
            {
                "hand": [
                    {"number": 5, "suit": "YELLOW"},
                    {"number": 3, "suit": "BLUE"},
                    {"number": 4, "suit": "YELLOW"},
                    {"number": 1, "suit": "WHITE"},
                    {"number": 1, "suit": "BLUE"}
                ],
                "name": "Curtis"
            },
            {
                "hand": [
                    {"number": 2, "suit": "WHITE"},
                    {"number": 1, "suit": "GREEN"},
                    {"number": 1, "suit": "YELLOW"},
                    {"number": 3, "suit": "GREEN"},
                    {"number": 3, "suit": "WHITE"}
                ],
                "name": "Tim"
            },
            {
                "hand": [
                    {"number": 2, "suit": "YELLOW"},
                    {"number": 5, "suit": "BLUE"},
                    {"number": 5, "suit": "WHITE"},
                    {"number": 2, "suit": "BLUE"},
                    {"number": 2, "suit": "RED"}
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

* `discarded` is the discard pile, which consists of a list of card objects with the stucture like: `{"number": 4, "suit": "BLUE"}`. `played` and players' `hand` contains cards that exhibit the same structure.
* `hasEnded` indicates the termination of the game. It will be set to true when an end game state has been detected.
* `hasStarted` indicates the status of the game. It will be set to true by the host once enough players has joined.
* `order` is a random permutation of the players, governing the playing order. It is set after the start of the game.
* `spectators` are users who are not participating in the game, but can message players and see the progression of the game. A user who enters the game will become a spectator first, and must join to become a player.
* `turnsLeft` indicates how many turns are remianing before the end-game state. It will be -1 throughout the game until being set to 3 once the last card has been dealt.

# API Calls

##REST

In order to receive websocket payloads from SocketIO, the client must connect to the socket once he/she creates or enters the game. The socket namespace will be `http://<domain_name>/socket/game/<game_id>`

###Get Game

Get current game object.

* `GET /api/game/<int:gameId>`
* **Response**: a Game object

###Create Game
Create and join a new game.
* `POST /api/create`
* **Request**
  * `isRainbow`: boolean
  * `name`: string
* **Response**
  * `success`: boolean
  * `game`: a Game object

##Socket.IO
###Enter Game
Enter a game room. Player will become a spectator.
* `POST /api/enter/<int:gameId>`
* **Request**
  * `name`: string
* **Response**
  * `success`: boolean
  * `game`: a Game object (only when successful)
* **SocketIO Response**
  * `enterGame`: string (spectators's name)
  * `game`: a Game object

###Resume Game
Resume or re-join a game. Player must be already a player or spectator prior to the call.
* `GET /api/enter/<int:gameId>`
* **Request**
  * `name`: string
* **Response**
  * `success`: boolean
  * `game`: a Game object (only when successful)
* **SocketIO Response**
  * `joinGame`: string (spectators's name)
  * `game`: a Game object

###Join Game
Join a game. Player must be a spectator prior to the call. Will fail if number of joined players is at max (5).
* `POST /api/join/<int:gameId>`
* **Request**
  * `name`: string
* **Response**
  * `success`: boolean
  * `game`: a Game object (only when successful)
* **SocketIO Response**
  * `resumeGame`: string (spectators's name)
  * `game`: a Game object

###Start Game
Start a game. Can only start a game that hasn't been started yet. This will create a deck and deal cards to players.
* `POST /api/start/<int:gameId>`
* **Response**
  * `success`: boolean
  * `game`: a Game object (only when successful)
* **SocketIO Response**
  * `gameStart`: boolean
  * `game`: a Game object

###Send Message
Send a message to everyone in the game.
* `POST /api/message/<int:gameId>`
* **Request**
  * `name`: string
  * `message`: string
* **Response**
  * `success`: boolean
* **SocketIO Response**
  * `sendMessage`: object with fields:
    * `message`: string
    * `name`: string

###Give Hint
Gives a hint to another player. Must be the player's turn to play. `hintType` can either be "number" or "colour".
* `POST /api/hint/<hintType>/<int:gameId>`
* **Request**
  * `name`: string
  * `toName`: string
  * `hint`: int/string
* **Response**
  * `success`: boolean
  * `cardsHinted`: list of ints (indices of the cards hinted)
* **SocketIO Response**
  * `giveHint`: object with fields:
    * `hintType`: string (number/color)
    * `hint`: int/string,
    * `cardsHinted`: list of ints (indices of the cards hinted),
    * `from`: string,
    * `to`: string,
    * `game`: a Game object

###Discard Card
* `POST /api/discard/<int:gameId>`
* **Request**
  * `name`: string
  * `cardIndex`: int
* **Response**
  * `success`: boolean
  * `game`: a Game object
* **SocketIO Response**
  * `discardCard`: object with fields:
    * `name`: string
    * `cardIndex`: int
    * `game`: a Game object

###Play Card
* `POST /api/play/<int:gameId>`
* **Request**
  * `name`: string
  * `cardIndex`: int
* **Response**
  * `success`: boolean
  * `game`: a Game object
* **SocketIO Response**
  * `playCard`: object with fields:
    * `name`: string
    * `cardIndex`: int
    * `game`: a Game object

###End Game
* `POST /api/end/<int:gameId>`
* **Response**
  * `success`: boolean
* **SocketIO Response**
  * `endGame`: boolean
