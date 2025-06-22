from datetime import datetime
import sqlite3

conn = sqlite3.connect('base.db')
cursor = conn.cursor()

cursor.execute("SELECT id, Primeiro_contato FROM contatos WHERE Primeiro_contato IS NOT NULL AND Primeiro_contato LIKE '__/__/____%'")
rows = cursor.fetchall()

for row in rows:
    id, antigo = row
    try:
        convertido = datetime.strptime(antigo, "%d/%m/%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE contatos SET Primeiro_contato = ? WHERE id = ?", (convertido, id))
    except Exception as e:
        print(f"Erro ao converter ID {id}: {e}")

conn.commit()
conn.close()
print("Conversão finalizada.")
