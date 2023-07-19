CREATE TABLE IF NOT EXISTS issued_tokens (
    token text,
    me text,
    created text,
    client_id text,
    expires int,
    app_item text
);

CREATE TABLE IF NOT EXISTS revoked_tokens(
    token text
);
