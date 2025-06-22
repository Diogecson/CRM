import sqlite3

conn = sqlite3.connect('base.db')  # ou 'DATABASE'
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    tipo TEXT NOT NULL
)
''')

conn.commit()
conn.close()
print("Tabela 'usuarios' criada com sucesso.")
