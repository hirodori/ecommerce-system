import pika
import sqlite3
import json

class Stock:
    def __init__(self, callback) -> None:
        self.__host = "localhost"
        self.__port = 5672
        self.__username = "guest"
        self.__password = "guest"
        self.__queue = "stock_queue"
        self.__order_exchange = "order_exchange"
        self.__payment_exchange = "payment_exchange"
        self.__commit_exchange = "commit_exchange"
        self.__routing_key = "order"
        self.__payment_fail_key = "payment_fail"
        self.__shipping_fail_key = "shipping_fail"
        self.__callback = callback
        self.__channel = self.__create_channel()

    def __create_channel(self):
        connection_parameters = pika.ConnectionParameters(
            host=self.__host,
            port=self.__port,
            credentials=pika.PlainCredentials(
                username=self.__username,
                password=self.__password
            )
        )
        channel = pika.BlockingConnection(connection_parameters).channel()

        channel.exchange_declare(exchange=self.__order_exchange, exchange_type='direct')  # Receber mensagem de Order
        channel.exchange_declare(exchange=self.__payment_exchange, exchange_type='direct')  # Receber mensagem de Payment
        channel.exchange_declare(exchange=self.__commit_exchange, exchange_type='direct')  # Receber a chamada para votação do commit

        channel.queue_declare(queue=self.__queue,durable=True)
        
        channel.queue_bind(exchange=self.__order_exchange, queue=self.__queue, routing_key=self.__routing_key)  # Receber o Pedido de Order
        channel.queue_bind(exchange=self.__payment_exchange, queue=self.__queue, routing_key=self.__payment_fail_key)  # Receber mensagem de Payment com Erro no Pagamento
        channel.queue_bind(exchange=self.__payment_exchange, queue=self.__queue, routing_key=self.__shipping_fail_key)  # Receber mensagem de Payment com Erro no Envio

        channel.basic_consume(queue=self.__queue, auto_ack=True, on_message_callback=self.__callback)

        return channel

    # Função para consumir mensagens do RabbitMQ
    def start(self):
        print('Serviço de Estoque')
        print('Escutando pelo RabbitMQ na Porta 5672')
        self.__channel.start_consuming()

# Função para verificar o estoque de um Produto com base em seu ID
def get_quantity_by_id(item_id, quantity):
    conn = sqlite3.connect('stock_service/stock_database.db')
    cursor = conn.cursor()
    query = "SELECT quantity FROM STOCK_DATABASE WHERE id = ?"
    cursor.execute(query, (item_id,))

    result = cursor.fetchone()
    if result:
        new_quantity = result[0] - quantity
        if new_quantity >= 0:
            update_query = "UPDATE STOCK_DATABASE SET quantity = ? WHERE id = ?"
            cursor.execute(update_query, (new_quantity, item_id))
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False

# Função para verificar o preço de um Produto com base em seu ID
def get_price_by_id(item_id):
    conn = sqlite3.connect('stock_service/stock_database.db')
    cursor = conn.cursor()
    query = "SELECT price FROM STOCK_DATABASE WHERE id = ?"
    cursor.execute(query, (item_id,))
    result = cursor.fetchone()
    price = result[0]
    conn.close()
    
    return price

# Função de rollback para reverter a quantidade de um produto antes de confirmar o estoque
def rollback(item_id, quantity):
    conn = sqlite3.connect('stock_service/stock_database.db')
    cursor = conn.cursor()
    query = "SELECT quantity FROM STOCK_DATABASE WHERE id = ?"
    cursor.execute(query, (item_id,))

    result = cursor.fetchone()
    if result:
        new_quantity = result[0] + quantity
        update_query = "UPDATE STOCK_DATABASE SET quantity = ? WHERE id = ?"
        cursor.execute(update_query, (new_quantity, item_id))
        conn.commit()
    conn.close()

# Callback para processar as mensagens recebidas
def callback(ch, method, properties, body):
    if method.routing_key == "order":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        user_id = body_dict['user_id']
        product_id = body_dict['product_id']
        quantity = int(body_dict['quantity'])
        user_country = body_dict['user_country']
        user_balance = body_dict['balance']
        print(f"Pedido {order_id} recebido do usuário {user_id}: ID do produto = {product_id}, quantidade = {quantity}, país = {user_country}, saldo = {user_balance})")
        
        conn = sqlite3.connect('stock_service/stock_database.db')
        cursor = conn.cursor()
        if quantity > 0:
            quantity_ok = get_quantity_by_id(product_id, quantity)
            if quantity_ok:
                cursor.execute("INSERT INTO ORDER_DATABASE (id, user_id, product_id, quantity, status) VALUES (?, ?, ?, ?, ?)", (order_id, user_id, product_id, quantity, "partially confirmed"))
                conn.commit()
                response = 'stock_success'
                body_dict['price'] = get_price_by_id(product_id)
            else:
                cursor.execute("INSERT INTO ORDER_DATABASE (id, user_id, product_id, quantity, status) VALUES (?, ?, ?, ?, ?)", (order_id, user_id, product_id, quantity, "stock failed"))
                conn.commit()
                response = 'stock_fail'
            print('Enviando dados para a fila: ' + response)
            ch.basic_publish(exchange="stock_exchange", routing_key=response, body=json.dumps(body_dict))
        conn.close()
    elif method.routing_key == "payment_fail":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        product_id = body_dict['product_id']
        quantity = int(body_dict['quantity'])
        
        conn = sqlite3.connect('stock_service/stock_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE ORDER_DATABASE SET status = ? WHERE id = ?", ("payment failed", order_id))
        conn.commit()
        conn.close()
        
        rollback(product_id, quantity)
        response = 'payment_fail'
        print('Enviando dados para a fila: ' + response)
        ch.basic_publish(exchange="stock_exchange", routing_key=response, body=body)
    elif method.routing_key == "shipping_fail":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        product_id = body_dict['product_id']
        quantity = int(body_dict['quantity'])
        
        conn = sqlite3.connect('stock_service/stock_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE ORDER_DATABASE SET status = ? WHERE id = ?", ("shipping failed", order_id))
        conn.commit()
        conn.close()
        
        rollback(product_id, quantity)
        response = 'shipping_fail'
        print('Enviando dados para a fila: ' + response)
        ch.basic_publish(exchange="stock_exchange", routing_key=response, body=body)

rabitmq_consumer = Stock(callback)
rabitmq_consumer.start()
