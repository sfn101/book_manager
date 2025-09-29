-- Migration: Change authors.image_id to authors.image_url
-- This migration changes the column to store full image URLs instead of OLID

-- Rename the column and change its type to accommodate full URLs
ALTER TABLE authors RENAME COLUMN image_id TO image_url;

-- Increase the column size to accommodate full URLs
ALTER TABLE authors ALTER COLUMN image_url TYPE VARCHAR(500);

-- Update existing OLID values to full URLs
UPDATE authors 
SET image_url = 'https://covers.openlibrary.org/a/olid/' || image_url || '-L.jpg'
WHERE image_url IS NOT NULL 
  AND image_url != '' 
  AND image_url NOT LIKE 'http%';

-- Add a comment to document the change
COMMENT ON COLUMN authors.image_url IS 'Full URL to author profile image';