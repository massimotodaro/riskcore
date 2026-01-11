-- Add composite_figi to identifier_type enum
-- This is needed for OpenFIGI integration

ALTER TYPE identifier_type ADD VALUE IF NOT EXISTS 'composite_figi';
ALTER TYPE identifier_type ADD VALUE IF NOT EXISTS 'share_class_figi';
