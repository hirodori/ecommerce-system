import sqlite3

# Conexão com o banco de dados SQLite. Se ele não existir, será criado.
conn = sqlite3.connect('client_database.db')

# Cria um objeto cursor usando o método cursor().
cursor = conn.cursor()

# Exclua a tabela se ela existir.
cursor.execute("DROP TABLE IF EXISTS CLIENT_DATABASE")

# Criação da tabela com os atributos.
sql = '''CREATE TABLE CLIENT_DATABASE (
         id INTEGER PRIMARY KEY,
         name INTEGER NOT NULL,
         country STRING NOT NULL,
         balance FLOAT NOT NULL
         )'''
cursor.execute(sql)

# Confirma as alterações no banco de dados.
conn.commit()

# Fecha a conexão.
conn.close()
