DROP TABLE if exists games;
DROP TABLE if exists players;
CREATE TABLE games (
	id integer primary key autoincrement,
	gameJSON text,
	deckJSON text
);
CREATE TABLE players (
	id integer primary key autoincrement,
	gameId integer not null,
	name text not null,
	handJSON text,
	joined integer not null
);