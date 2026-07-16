-- Migration: Add invoice_number and reminder_count columns
-- Run this migration against the database

-- Add columns to invoices table
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50) UNIQUE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS reminder_count INTEGER DEFAULT 0;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_user_id_invoice_number ON invoices(user_id, invoice_number);

-- Create sequence table for generating sequential invoice numbers
CREATE TABLE IF NOT EXISTS invoice_number_sequence (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_number INTEGER NOT NULL DEFAULT 0,
    prefix VARCHAR(10) DEFAULT 'INV',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, prefix)
);

-- Create index for sequence lookups
CREATE INDEX IF NOT EXISTS idx_invoice_number_sequence_user ON invoice_number_sequence(user_id);

-- Add unique constraint on invoice_number at table level (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_invoice_number'
    ) THEN
        ALTER TABLE invoices ADD CONSTRAINT unique_invoice_number UNIQUE (invoice_number);
    END IF;
END $$;
