
An implementation of Hanabi, a popular board game. Starts with a web client, but can be integrated with multiple platforms through the server API.

# Dependencies

- PostgreSQL (Mac: install Postgres.app)
- virtualenv is recommended

# Set-up to Run Locally

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
    
The above response can be obtained through a `GET /api/get/4` call, a hanabi game that just begun. Some of the attributes are described below:

* `currentPlayer` indicates who's turn to play. The string will always match an element in `order` or `players`.
* `discarded` is the discard pile, which consists of a list of card objects with the stucture like: `{"number": 4, "suit": "BLUE"}`. `played` and players' `hand` contains cards that exhibit the same structure.
* `hasEnded` indicates the termination of the game. It will be set to true when an end game state has been detected.
* `hasStarted` indicates the status of the game. It will be set to true by the host once enough players has joined.
* `order` is set after the game has started. It is a random permutation of the players.
* `spectators` are users who are not participating in the game, but can message players and see the progression of the game. A user who enters the game will become a spectator first, and must join to become a player.
* `turnsLeft` indicates how many turns are remianing before the end-game state. It will be -1 throughout the game until being set to 3 once the last card has been dealt.

# API Calls

In construction
