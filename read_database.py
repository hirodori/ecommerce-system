import sqlite3

def read_database():
    db = int(input("(0) Cliente | (1) Pedido | (2) Estoque | (3) Pagamento | (4) Envio | (5) Pedidos-Estoque: "))
    if db == 0:
        DATABASE = "CLIENT_DATABASE"
        conn = sqlite3.connect('client_database.db')
        cursor = conn.cursor()
    elif db == 1:
        DATABASE = "ORDER_DATABASE"
        conn = sqlite3.connect('order_service/order_database.db')
        cursor = conn.cursor()
    elif db == 2:
        DATABASE = "STOCK_DATABASE"
        conn = sqlite3.connect('stock_service/stock_database.db')
        cursor = conn.cursor()
    elif db == 3:
        DATABASE = "PAYMENT_DATABASE"
        conn = sqlite3.connect('payment_service/payment_database.db')
        cursor = conn.cursor()
    elif db == 4:
        DATABASE = "SHIPPING_DATABASE"
        conn = sqlite3.connect('shipping_service/SHIPPING_database.db')
        cursor = conn.cursor()
    elif db == 5:
        DATABASE = "ORDER_DATABASE"
        conn = sqlite3.connect('stock_service/stock_database.db')
        cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {DATABASE}")
        resultados = cursor.fetchall()
        
        if resultados:
            print("-" * 60)
            for row in resultados:
                print(row)
        else:
            print("Não há dados na tabela.")
            
    except sqlite3.Error as e:
        print(f"Erro ao ler dados do banco de dados: {e}")
        
    finally:
        conn.close()

read_database()