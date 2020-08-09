PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "fixpol_impact" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "date_added" datetime NOT NULL, "text" varchar(80) NOT NULL UNIQUE);
INSERT INTO fixpol_impact VALUES(1,'2020-07-31 18:36:42.997580','Healthcare');
INSERT INTO fixpol_impact VALUES(2,'2020-07-31 18:36:48.869139','Safety');
INSERT INTO fixpol_impact VALUES(3,'2020-07-31 18:37:05.254302','Environment');
INSERT INTO fixpol_impact VALUES(4,'2020-07-31 18:37:11.749787','Transportation');
INSERT INTO fixpol_impact VALUES(5,'2020-07-31 18:37:50.229026','Jobs');
COMMIT;
