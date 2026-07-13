-- ============================================================
-- Fix RLS Security for LG Smart Factory Operations
-- Run this in Supabase SQL Editor (https://supabase.com)
-- ============================================================

-- ============================================================
-- 1. production table
-- ============================================================
ALTER TABLE production ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on production" ON production;
CREATE POLICY "Allow all on production" ON production
  FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 2. warehouse table
-- ============================================================
ALTER TABLE warehouse ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on warehouse" ON warehouse;
CREATE POLICY "Allow all on warehouse" ON warehouse
  FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 3. maintenance table
-- ============================================================
ALTER TABLE maintenance ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on maintenance" ON maintenance;
CREATE POLICY "Allow all on maintenance" ON maintenance
  FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 4. quality table
-- ============================================================
ALTER TABLE quality ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on quality" ON quality;
CREATE POLICY "Allow all on quality" ON quality
  FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 5. safety table
-- ============================================================
ALTER TABLE safety ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on safety" ON safety;
CREATE POLICY "Allow all on safety" ON safety
  FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 6. incident_log table
-- ============================================================
ALTER TABLE incident_log ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on incident_log" ON incident_log;
CREATE POLICY "Allow all on incident_log" ON incident_log
  FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- 7. users table — READ ONLY (no writing passwords from app)
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read on users" ON users;
CREATE POLICY "Allow read on users" ON users
  FOR SELECT USING (true);
