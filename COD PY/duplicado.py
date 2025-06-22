import sqlite3

conn = sqlite3.connect("base.db")
cursor = conn.cursor()

query = """
SELECT
    LOWER(TRIM(usuario)) AS nome_normalizado,
    COUNT(*) AS total,
    GROUP_CONCAT(id) AS ids_duplicados
FROM usuarios
GROUP BY nome_normalizado
HAVING COUNT(*) > 1
"""

cursor.execute(query)
for row in cursor.fetchall():
    print(row)

conn.close()
