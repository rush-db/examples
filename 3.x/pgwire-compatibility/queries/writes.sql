INSERT INTO supplier (code, name, tier, region) VALUES ('S-401', 'Marsh Polymers (example)', 4, 'flood-zone-07');
UPDATE supplier SET tier = 3 WHERE code = 'S-401';
SELECT code, tier FROM supplier WHERE code = 'S-401';
DELETE FROM supplier WHERE code = 'S-401';
