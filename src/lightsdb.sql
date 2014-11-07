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
)