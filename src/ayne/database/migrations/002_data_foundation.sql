CREATE TABLE IF NOT EXISTS dataset_manifests (
    manifest_id VARCHAR PRIMARY KEY,
    schema_version INTEGER NOT NULL,
    source_commit VARCHAR NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    database_path VARCHAR NOT NULL,
    row_counts JSON NOT NULL,
    input_hashes JSON NOT NULL,
    manifest_sha256 VARCHAR NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_dataset_manifests_generated_at
    ON dataset_manifests (generated_at);
