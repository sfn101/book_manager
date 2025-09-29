-- Migration: Add image_id column to authors table
-- Date: 2025-09-27

-- Add image_id column to store Open Library author photo IDs
ALTER TABLE authors ADD COLUMN IF NOT EXISTS image_id VARCHAR(50);

-- Create index for better performance on image_id lookups
CREATE INDEX IF NOT EXISTS idx_authors_image_id ON authors(image_id);

-- Update comment on authors table
COMMENT ON COLUMN authors.image_id IS 'Open Library author photo ID for profile images';