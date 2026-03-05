CREATE TABLE ledger (
    id UUID DEFAULT PRIMARY KEY,
    cardid INTEGER NOT NULL,
    accessed_at TIMESTAMP NOT NULL,
    page INTEGER NOT NULL,
    link VARCHAR NOT NULL,
    parsed BOOLEAN NOT NULL,
    visibility_parsed BOOLEAN NOT NULL
);