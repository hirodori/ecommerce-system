import pika
import json
import sqlite3

class Order:
    def __init__(self, callback) -> None:
        self.__host = "localhost"
        self.__port = 5672
        self.__username = "guest"
        self.__password = "guest"
        self.__exchange = "order_exchange"
        self.__client_exchange = "client_exchange"
        self.__shipping_exchange = "shipping_exchange"
        self.__stock_exchange = "stock_exchange"
        self.__routing_key = "order"
        self.__shipping_success_key = "shipping_success"
        self.__stock_fail_key = "stock_fail"
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

        channel.exchange_declare(exchange=self.__client_exchange, exchange_type='direct')  # Receber mensagens de Client
        channel.exchange_declare(exchange=self.__shipping_exchange, exchange_type='direct')  # Receber mensagens de Shipping
        channel.exchange_declare(exchange=self.__stock_exchange, exchange_type='direct')  # Receber mensagens de Stock
        
        queue = channel.queue_declare(queue='', exclusive=True)
        queue_name = queue.method.queue

        channel.queue_bind(exchange=self.__client_exchange, queue=queue_name, routing_key=self.__routing_key)  # Receber o Pedido do Client
        channel.queue_bind(exchange=self.__shipping_exchange, queue=queue_name, routing_key=self.__shipping_success_key)  # Receber mensagem de Shipping com Sucesso no Envio
        channel.queue_bind(exchange=self.__stock_exchange, queue=queue_name, routing_key=self.__stock_fail_key)  # Receber mensagem de Stock com Falha no Estoque
        channel.queue_bind(exchange=self.__stock_exchange, queue=queue_name, routing_key=self.__payment_fail_key)  # Receber mensagem de Stock com Falha no Pagamento
        channel.queue_bind(exchange=self.__stock_exchange, queue=queue_name, routing_key=self.__shipping_fail_key)  # Receber mensagem de Stock com Falha no Envio

        channel.basic_consume(queue=queue_name, on_message_callback=self.__callback, auto_ack=True)

        return channel

    # Função para consumir mensagens do RabbitMQ
    def start(self):
        print('Serviço de Pedidos')
        print('Escutando pelo RabbitMQ na Porta 5672')
        self.__channel.start_consuming()
        
# Callback para processar as mensagens recebidas
def callback(ch, method, properties, body):
    if method.routing_key == "order":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        user_id = body_dict['user_id']
        product_id = body_dict['product_id']
        quantity = body_dict['quantity']
        user_country = body_dict['user_country']
        user_balance = body_dict['balance']
        print(f"Pedido recebido do usuário {user_id}: ID do produto = {product_id}, quantidade = {quantity}, país = {user_country}, saldo = {user_balance})")
        
        conn = sqlite3.connect('order_service/order_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ORDER_DATABASE")
        result = cursor.fetchone()
        if result:
            id = result[0] + 2
        else:
            id = 1
        cursor.execute("INSERT INTO ORDER_DATABASE (id, user_id, product_id, quantity, balance, country, status) VALUES (?, ?, ?, ?, ?, ?, ?)", (id, user_id, product_id, quantity, user_balance, user_country, "Pending"))
        conn.commit()
        conn.close()
        
        body_dict['order_id'] = id
        ch.basic_publish(exchange="order_exchange", routing_key="order", body=json.dumps(body_dict))
        print("Pedido enviado para o gerenciador de estoque: " + str(body))
    elif method.routing_key == "shipping_success":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        user_id = body_dict['user_id']
        product_id = body_dict['product_id']
        quantity = body_dict['quantity']
        user_country = body_dict['user_country']
        user_balance = body_dict['balance']
        print(f"Pedido {order_id} do usuário {user_id} confirmado: ID do produto = {product_id}, quantidade = {quantity}, país = {user_country}, saldo = {user_balance})")
        
        conn = sqlite3.connect('order_service/order_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE ORDER_DATABASE SET status = ? WHERE id = ?", ("partially confirmed", order_id))
        conn.commit()
        conn.close()
        
        response = "shipping_success"
        ch.basic_publish(exchange="order_exchange", routing_key=response, body=body)
        print("Pedido confirmado para o cliente: " + str(body))
    elif method.routing_key == "stock_fail":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        user_id = body_dict['user_id']
        
        conn = sqlite3.connect('order_service/order_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE ORDER_DATABASE SET status = ? WHERE id = ?", ("stock failed", order_id))
        conn.commit()
        conn.close()
        
        response = "stock_fail"
        ch.basic_publish(exchange="order_exchange", routing_key=response, body=body)
        print(f"Pedido {order_id} do usuário {user_id} falhou no Estoque")
    elif method.routing_key == "payment_fail":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        user_id = body_dict['user_id']
        
        conn = sqlite3.connect('order_service/order_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE ORDER_DATABASE SET status = ? WHERE id = ?", ("payment failed", order_id))
        conn.commit()
        conn.close()
        
        response = "payment_fail"
        ch.basic_publish(exchange="order_exchange", routing_key=response, body=body)
        print(f"Pedido {order_id} do usuário {user_id} falhou no Pagamento")
    elif method.routing_key == "shipping_fail":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        user_id = body_dict['user_id']
        
        conn = sqlite3.connect('order_service/order_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE ORDER_DATABASE SET status = ? WHERE id = ?", ("shipping failed", order_id))
        conn.commit()
        conn.close()
        
        response = "shipping_fail"
        ch.basic_publish(exchange="order_exchange", routing_key=response, body=body)
        print(f"Pedido {order_id} do usuário {user_id} falhou no Envio")
            
order = Order(callback)
order.start()
