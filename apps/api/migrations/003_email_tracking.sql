-- Migration: Add email tracking columns to invoices
-- Run this migration against the database

-- Add email status tracking columns
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS email_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS last_email_error TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS last_email_sent_at TIMESTAMP;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS email_resend_id VARCHAR(100);

-- Create index for email status queries
CREATE INDEX IF NOT EXISTS idx_invoices_email_status ON invoices(email_status);

-- Add email tracking to reminder_log
ALTER TABLE reminder_log ADD COLUMN IF NOT EXISTS email_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE reminder_log ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE reminder_log ADD COLUMN IF NOT EXISTS resend_id VARCHAR(100);
