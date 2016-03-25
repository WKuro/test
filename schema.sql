drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  lat real not null,
  lng real not null,
  degree real not null,
  moment DATETIME DEFAULT CURRENT_TIMESTAMP
);
