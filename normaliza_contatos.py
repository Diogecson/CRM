import sqlite3
from datetime import datetime
import locale

# Define o locale para pt_BR (se necessário)
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
except:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')  # Windows fallback

def obter_dia_semana(data_str):
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
    for fmt in formatos:
        try:
            data = datetime.strptime(data_str.strip(), fmt)
            return data.strftime("%A")  # Ex: quarta-feira
        except ValueError:
            continue
    return ""

def atualizar_coluna_data_com_dia_semana():
    conn = sqlite3.connect("base.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, Primeiro_contato FROM contatos")
    registros = cursor.fetchall()

    for id_, primeiro_contato in registros:
        dia_semana = obter_dia_semana(primeiro_contato)
        if dia_semana:
            cursor.execute("UPDATE contatos SET Data = ? WHERE id = ?", (dia_semana, id_))

    conn.commit()
    conn.close()
    print("✅ Coluna 'Data' atualizada com nomes dos dias da semana.")

if __name__ == "__main__":
    atualizar_coluna_data_com_dia_semana()
