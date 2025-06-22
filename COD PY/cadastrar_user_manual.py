import sqlite3
from werkzeug.security import generate_password_hash  # se estiver usando werkzeug
# ou
# import bcrypt
# def gerar_hash(senha): return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

CONSULTOR_LIST = [
    "Andreza Pinheiro de Lima", "Beatriz Alves Santos", "Dominik Ferreira Josue Silva",
    "Fernanda Souza Ferreira", "Pedro Henrique Gonzaga de Souza", "Raissa da Silva Bueno",
    "IGOR", "Vanessa Aparecida da Silva de Faria", "Erica Ravene Andrade Almeida",
    "Rafaela Lacerda Alves", "Ana Luisa Fonseca de Campos de Oliveira", "Andre Luiz Reis Rezende Filho",
    "Diogecson Soares Bispo dos Santos", "Evelyn Rainha dos Santos", "Isabela de araujo evangelista",
    "Vanessa Alves", "Juliana Pereira de Moraes Santos", "Lidya Leonice Silva Gonçalves",
    "Raffaela Alves da Silva", "BOT", "Emilly de Oliveira Zanelato"
]

def cadastrar_consultores():
    conn = sqlite3.connect('base.db')
    cursor = conn.cursor()

    for nome in CONSULTOR_LIST:
        senha_hash = generate_password_hash("123")  # ou usar gerar_hash("123") se for bcrypt
        try:
            cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
                           (nome, senha_hash, 'consultor'))
        except Exception as e:
            print(f"Erro ao inserir {nome}: {e}")

    conn.commit()
    conn.close()
    print("Todos os consultores foram cadastrados.")
