-- Add role column to users table
-- This migration adds role-based access control

-- Add role column with default value 'user'
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

-- Create enum-like constraint for roles
ALTER TABLE users ADD CONSTRAINT check_user_role CHECK (role IN ('admin', 'user'));

-- Update existing users - make first user admin, rest are users
UPDATE users SET role = CASE 
    WHEN id = (SELECT MIN(id) FROM users) THEN 'admin'
    ELSE 'user'
END WHERE role IS NULL OR role = 'user';

-- Add image_url column to authors table if it doesn't exist
ALTER TABLE authors ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);

-- Add index on role for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Show current users and their roles
SELECT id, username, email, role, created_at FROM users ORDER BY id;