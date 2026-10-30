SELECT occupation,
       COUNT(*) AS people,
       COUNT(born) AS with_born,
       CAST(COUNT(born) AS DOUBLE) / COUNT(*) AS completeness
FROM person
GROUP BY occupation
ORDER BY occupation;
