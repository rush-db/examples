SELECT COUNT(*) AS loans FROM loan l JOIN district d ON l.district_id = d.district_id
WHERE d.name = 'Hl.m. Praha' AND l.status IN ('C', 'D')
