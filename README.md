hanabi-isotropic
================

An implementation of Hanabi, a popular board game. Starts with a web client, but can be integrated with multiple platforms through the server API.

# Dependencies

- PostgreSQL (Mac: install Postgres.app)
- virtualenv is recommended

# Set-up to Run Locally

To run on your local machine:

1: Create a virtual environment and start it:

```
cd hanabi-isotrophic
virtualenv hanabi-env
source hanabi-env/bin/activate
```

2: Install python dependencies:

```
pip install -r requirements.txt
```

3: Initiate database:

PostgreSQL needs to be running and psql needs to point to the correct path.
```
psql -d timpei -a -f schema.sql
```

4: Setup environment:

```
echo "export DATABASE_URL=postgres:///$(whoami)" > env.sh
chmod +x env.sh
./env.sh
```

# Running the app

```
# make sure virtualenv is running
python app.py
```