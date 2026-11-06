SELECT sku, try_cast(price AS DOUBLE) AS price FROM product WHERE try_cast(price AS DOUBLE) > 30 OR try_cast(price AS DOUBLE) IS NULL ORDER BY sku
