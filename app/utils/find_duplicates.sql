SELECT * FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY kunta, cardType, cardid, substr(accessed_at, 1, 10)
            ORDER BY rowid
        ) AS rn
    FROM ledger
) t
WHERE rn > 1;