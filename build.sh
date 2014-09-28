virtualenv --no-site-package hanabi-env
pip install flask
pip install pysqlite
pip install gevent-socketio

mkdir db
sqlite3 db/hanabi.db < schema.sql