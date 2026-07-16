-- Indexes for metrics queries
CREATE INDEX IF NOT EXISTS idx_invoices_user_id_created_at ON invoices(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_user_id_status ON invoices(user_id, status);
