DROP TABLE if exists games;
DROP TABLE if exists players;
DROP TABLE if exists messages;
DROP TYPE if exists msgType;
CREATE TYPE msgType AS ENUM ('MESSAGE', 'HINT', 'CARD', 'ROOM');

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

CREATE TABLE messages (
	id serial primary key,
	gameId integer not null,
	name text not null,
	type msgType not null,
	messageJSON text not null,
	time integer not null
);