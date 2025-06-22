import sqlite3

conn = sqlite3.connect("base.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE contatos ADD COLUMN Data TEXT")
    print("✅ Coluna 'Data' adicionada com sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao adicionar coluna: {e}")

conn.commit()
conn.close()
