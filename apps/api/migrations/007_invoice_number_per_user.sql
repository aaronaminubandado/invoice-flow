-- Migration: scope invoice_number uniqueness per user instead of globally

ALTER TABLE invoices DROP CONSTRAINT IF EXISTS unique_invoice_number;
ALTER TABLE invoices DROP CONSTRAINT IF EXISTS invoices_invoice_number_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_invoices_user_invoice_number
    ON invoices (user_id, invoice_number)
    WHERE invoice_number IS NOT NULL;
