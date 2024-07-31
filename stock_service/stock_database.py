import sqlite3
from random import randint

# Conexão com o banco de dados SQLite. Se ele não existir, será criado.
conn = sqlite3.connect('stock_service/stock_database.db')

# Cria um objeto cursor usando o método cursor().
cursor = conn.cursor()

# Exclua a tabela se ela existir.
cursor.execute("DROP TABLE IF EXISTS STOCK_DATABASE")
cursor.execute("DROP TABLE IF EXISTS ORDER_DATABASE")

# Criação da tabela com os atributos.
sql1 = '''CREATE TABLE STOCK_DATABASE (
         id INTEGER PRIMARY KEY,
         name TEXT NOT NULL,
         quantity INTEGER NOT NULL,
         price FLOAT NOT NULL
         )'''
cursor.execute(sql1)

sql2 = '''CREATE TABLE ORDER_DATABASE (
         id INTEGER PRIMARY KEY,
         user_id INTEGER NOT NULL,
         product_id INTEGER NOT NULL,
         quantity INTEGER NOT NULL,
         status STRING NOT NULL
         )'''
cursor.execute(sql2)

# Lista de jogos com os seus preços
games = [
    {"name": "The Witcher 3: Wild Hunt", "price": 59.99},
    {"name": "Grand Theft Auto V", "price": 49.99},
    {"name": "Red Dead Redemption 2", "price": 54.99},
    {"name": "Cyberpunk 2077", "price": 39.99},
    {"name": "Assassin's Creed Valhalla", "price": 69.99},
    {"name": "FIFA 22", "price": 59.99},
    {"name": "Call of Duty: Modern Warfare", "price": 49.99},
    {"name": "Minecraft", "price": 29.99},
    {"name": "Among Us", "price": 4.99},
    {"name": "The Elder Scrolls V: Skyrim", "price": 39.99}
]

# Inserindo a lista de jogos e preços
for i in range(1, 11):
    name = games[i-1]['name']  # Pega o nome do jogo da lista
    price = games[i-1]['price'] # Pega o preço do jogo da lista
    quantity = randint(0, 15)  # Gera uma quantidade aleatória entre 0 e 15
    cursor.execute("INSERT INTO STOCK_DATABASE (id, name, quantity, price) VALUES (?, ?, ?, ?)", (i, name, quantity, price))

# Confirma as alterações no banco de dados.
conn.commit()

# Fecha a conexão.
conn.close()
