CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" TEXT NOT NULL,
    "hash" TEXT NOT NULL
);
CREATE UNIQUE INDEX "username" ON "users"("username");

CREATE TABLE IF NOT EXISTS "decks" (
    "id" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "learned" INTEGER NOT NULL,
    "total" INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES users(id)
);
CREATE UNIQUE INDEX "name" ON "decks"("name");

CREATE TABLE IF NOT EXISTS "cards" (
    "id" INTEGER NOT NULL,
    "card_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "front" TEXT,
    "back" TEXT,
    "deck" TEXT NOT NULL,
    "learned" BIT,
    "time" DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id) REFERENCES users(id)
);