import sqlite3

# Conexão com o banco de dados SQLite. Se ele não existir, será criado.
conn = sqlite3.connect('shipping_service/shipping_database.db')

# Cria um objeto cursor usando o método cursor().
cursor = conn.cursor()

# Exclua a tabela se ela existir.
cursor.execute("DROP TABLE IF EXISTS SHIPPING_DATABASE")

# Criação da tabela com os atributos.
sql = '''CREATE TABLE SHIPPING_DATABASE (
         id INTEGER PRIMARY KEY,
         user_id INTEGER NOT NULL,
         country STRING NOT NULL,
         shipping_date DATE NOT NULL,
         shipping_time TIME NOT NULL,
         status STRING NOT NULL
         )'''
cursor.execute(sql)

# Confirma as alterações no banco de dados.
conn.commit()

# Fecha a conexão.
conn.close()
