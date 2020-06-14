CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE reviews(
    id SERIAL NOT NULL PRIMARY KEY,
    username VARCHAR NOT NULL,
    isbn VARCHAR,
    review TEXT,
    rating INTEGER NOT NULL
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    password VARCHAR NOT NULL
);



INSERT INTO users (username, password) VALUES ('guest', 'guest');




