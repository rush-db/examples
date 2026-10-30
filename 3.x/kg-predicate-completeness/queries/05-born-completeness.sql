SELECT COUNT(*) AS total,
       COUNT(born) AS with_born,
       CAST(COUNT(born) AS DOUBLE) / COUNT(*) AS completeness
FROM person;
