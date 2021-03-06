drop table if exists schedule;
create table schedule (
    id integer primary key autoincrement,
    day integer,
    hour integer,
    minute integer,
    action varchar(64),
    lastaction timestamp
);
drop table if exists playlist;
create table playlist (
    id integer primary key autoincrement,
    playorder integer,
    name varchar(32),
    path varchar(2048)
);
drop table if exists users;
create table users (
    id integer primary key autoincrement,
    username varchar(256),
    password varchar(256)
);