--PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
--CREATE TABLE IF NOT EXISTS "fixpol_location" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "desc" varchar(80) NOT NULL, "date_added" datetime NOT NULL, "govlevel" varchar(80) NOT NULL, "shortname" varchar(20) NOT NULL, "hierarchy" varchar(200) NOT NULL UNIQUE, "parent_id" integer NULL REFERENCES "fixpol_location" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO fixpol_location (
    id,
    "desc",
    date_added,
    govlevel,
    shortname,
    hierarchy,
    parent_id
  )
VALUES (3,'world','2020-08-03 05:07:12.060299','global','tucson','world',NULL);
INSERT INTO fixpol_location (
    id,
    "desc",
    date_added,
    govlevel,
    shortname,
    hierarchy,
    parent_id
  )
VALUES (4,'United States','2020-08-03 05:07:36.507308','country','tucson','world.usa',3);
INSERT INTO fixpol_location (
    id,
    "desc",
    date_added,
    govlevel,
    shortname,
    hierarchy,
    parent_id
  )
VALUES (5,'Arizona, USA','2020-08-03 05:07:52.073199','state','tucson','world.usa.arizona',4);
INSERT INTO fixpol_location (
    id,
    "desc",
    date_added,
    govlevel,
    shortname,
    hierarchy,
    parent_id
  )
VALUES (6,'Pima County, AZ','2020-08-03 05:08:13.831021','county','tucson','world.usa.arizona.pima',5);
INSERT INTO fixpol_location (
    id,
    "desc",
    date_added,
    govlevel,
    shortname,
    hierarchy,
    parent_id
  )
VALUES (7,'Tucson, Arizona','2020-08-03 05:08:38.982510','city','tucson','world.usa.arizona.pima.tucson',6);
COMMIT;
