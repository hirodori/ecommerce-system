import pika
import sqlite3
import json
from datetime import datetime

class Shipping:
    def __init__(self, callback) -> None:
        self.__host = "localhost"
        self.__port = 5672
        self.__username = "guest"
        self.__password = "guest"
        self.__queue = "shipping_queue"
        self.__payment_exchange = "payment_exchange"
        self.__commit_exchange = "commit_exchange"
        self.__routing_key = "payment_success"
        self.__commit_key = "commit"
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

        channel.exchange_declare(exchange=self.__payment_exchange, exchange_type='direct')  # Receber mensagem de Payment
        # channel.exchange_declare(exchange=self.__commit_exchange, exchange_type='direct')  # Receber mensagem de Order

        channel.queue_declare(queue=self.__queue,durable=True)
        
        channel.queue_bind(exchange=self.__payment_exchange, queue=self.__queue, routing_key=self.__routing_key)  # Receber mensagem de Payment com Sucesso no Pagamento
        # channel.queue_bind(exchange=self.__commit_exchange, queue=self.__queue, routing_key=self.__commit_key)  # Receber de Order sobre a votação de commit
        
        channel.basic_consume(queue=self.__queue, auto_ack=True, on_message_callback=self.__callback)

        return channel

    # Função para consumir mensagens do RabbitMQ
    def start(self):
        print('Serviço de Envio')
        print('Escutando pelo RabbitMQ na Porta 5672')
        self.__channel.start_consuming()

# Callback para processar as mensagens recebidas
def callback(ch, method, properties, body):
    if method.routing_key == "payment_success":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        user_id = body_dict['user_id']
        product_id = body_dict['product_id']
        quantity = int(body_dict['quantity'])
        user_country = body_dict['user_country']
        user_balance = float(body_dict['balance'])
        price = float(body_dict['price'])
        print(f"Pedido {order_id} recebido do usuário {user_id}: ID do produto = {product_id}, quantidade = {quantity}, país = {user_country}, saldo = {user_balance}, total = {price})")
        date_now = datetime.now()
        date = date_now.strftime('%Y-%m-%d')
        time = date_now.strftime('%H:%M:%S')
        
        conn = sqlite3.connect('shipping_service/shipping_database.db')
        cursor = conn.cursor()
        if user_country.lower() == "brasil":
            cursor.execute("INSERT INTO SHIPPING_DATABASE (id, user_id, country, shipping_date, shipping_time, status) VALUES (?, ?, ?, ?, ?, ?)", (order_id, user_id, user_country, date, time, "partially confirmed"))
            conn.commit()
            response = 'shipping_success'
        else:
            cursor.execute("INSERT INTO SHIPPING_DATABASE (id, user_id, country, shipping_date, shipping_time, status) VALUES (?, ?, ?, ?, ?, ?)", (order_id, user_id, user_country, date, time, "shipping failed"))
            conn.commit()
            response = 'shipping_fail'
        conn.close()
        
        print('Enviando dados para a fila: ' + response)
        ch.basic_publish(exchange="shipping_exchange", routing_key=response, body=body)
    
shipping = Shipping(callback)
shipping.start()
