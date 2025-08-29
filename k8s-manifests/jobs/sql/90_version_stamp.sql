-- PK per bootstrap.migrations
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM   pg_constraint c
    JOIN   pg_class t ON t.oid = c.conrelid
    JOIN   pg_namespace n ON n.oid = t.relnamespace
    WHERE  c.contype = 'p'
      AND  n.nspname = 'bootstrap'
      AND  t.relname = 'migrations'
  ) THEN
    ALTER TABLE bootstrap.migrations
      ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);
  END IF;
END $$;

-- version stamp (audit)
INSERT INTO bootstrap.migrations(id) VALUES ('schema-core-v1')
ON CONFLICT DO NOTHING;
