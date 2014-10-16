DROP TABLE if exists games;
DROP TABLE if exists players;
CREATE TABLE games (
	id serial primary key,
	gameJSON text,
	deckJSON text
);
CREATE TABLE players (
	id serial primary key,
	gameId integer not null,
	name text not null,
	handJSON text,
	joined integer not null
);