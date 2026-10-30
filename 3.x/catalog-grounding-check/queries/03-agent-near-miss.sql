SELECT SUM(l.amount) AS total FROM loan l JOIN district d ON l.district_id = d.district_id
WHERE d.name = 'Brno-mesto'
