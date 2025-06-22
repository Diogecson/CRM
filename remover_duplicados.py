import sqlite3
from datetime import datetime

def parse_data(d):
    if not d:
        return datetime.max
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(d.strip(), fmt)
        except ValueError:
            continue
    return datetime.max

conn = sqlite3.connect("base.db")
cursor = conn.cursor()

# Buscar todos os dados com telefone
cursor.execute("SELECT id, Telefone, Primeiro_contato FROM contatos WHERE Telefone IS NOT NULL AND Telefone != ''")
registros = cursor.fetchall()

# Organizar por telefone e manter o mais antigo
contatos_por_telefone = {}
for id_, telefone, primeiro_contato in registros:
    data = parse_data(primeiro_contato)
    if telefone not in contatos_por_telefone or data < contatos_por_telefone[telefone][1]:
        contatos_por_telefone[telefone] = (id_, data)

# Criar lista de IDs a manter
ids_para_manter = {info[0] for info in contatos_por_telefone.values()}

# Deletar os outros
todos_ids = {r[0] for r in registros}
ids_para_deletar = todos_ids - ids_para_manter

if ids_para_deletar:
    cursor.executemany("DELETE FROM contatos WHERE id = ?", [(i,) for i in ids_para_deletar])
    conn.commit()
    print(f"{len(ids_para_deletar)} duplicados removidos.")
else:
    print("Nenhum duplicado encontrado.")

conn.close()
