import sqlite3

# Conexão com o banco de dados SQLite. Se ele não existir, será criado.
conn = sqlite3.connect('payment_service/payment_database.db')

# Cria um objeto cursor usando o método cursor().
cursor = conn.cursor()

# Exclua a tabela se ela existir.
cursor.execute("DROP TABLE IF EXISTS PAYMENT_DATABASE")

# Criação da tabela com os atributos.
sql = '''CREATE TABLE PAYMENT_DATABASE (
         id INTEGER PRIMARY KEY,
         user_id INTEGER NOT NULL,
         price FLOAT NOT NULL,
         balance FLOAT NOT NULL,
         status STRING NOT NULL
         )'''
cursor.execute(sql)

# Confirma as alterações no banco de dados.
conn.commit()

# Fecha a conexão.
conn.close()
