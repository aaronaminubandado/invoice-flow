-- Public share tokens for invoices
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS share_token TEXT;

UPDATE invoices
SET share_token = encode(gen_random_bytes(24), 'hex')
WHERE share_token IS NULL;

ALTER TABLE invoices ALTER COLUMN share_token SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_invoices_share_token ON invoices(share_token);
