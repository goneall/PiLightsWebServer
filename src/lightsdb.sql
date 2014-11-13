drop table if exists schedule;
create table schedule (
    id integer primary key autoincrement,
    day integer,
    hour integer,
    minute integer,
    turnon boolean,
    turnoff boolean,
    startplaylist boolean,
    stopplaylist boolean
);
drop table if exists playlist;
create table playlist (
    id integer primary key autoincrement,
    playorder integer,
    name varchar(32),
    path varchar(2048),
    active boolean
);