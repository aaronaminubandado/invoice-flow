-- Client email unique per user, not globally
ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_email_key;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'clients_user_id_email_key'
    ) THEN
        ALTER TABLE clients ADD CONSTRAINT clients_user_id_email_key UNIQUE (user_id, email);
    END IF;
END $$;
