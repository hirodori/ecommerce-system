import sqlite3

# Conexão com o banco de dados SQLite. Se ele não existir, será criado.
conn = sqlite3.connect('order_service/order_database.db')

# Cria um objeto cursor usando o método cursor().
cursor = conn.cursor()

# Exclua a tabela se ela existir.
cursor.execute("DROP TABLE IF EXISTS ORDER_DATABASE")

# Criação da tabela com os atributos.
sql = '''CREATE TABLE ORDER_DATABASE (
         id INTEGER PRIMARY KEY,
         user_id INTEGER NOT NULL,
         product_id INTEGER NOT NULL,
         quantity INTEGER NOT NULL,
         balance FLOAT NOT NULL,
         country STRING NOT NULL,
         status STRING NOT NULL
         )'''
cursor.execute(sql)

# Confirma as alterações no banco de dados.
conn.commit()

# Fecha a conexão.
conn.close()
