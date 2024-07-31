import pika
import sqlite3
import json

class Payment:
    def __init__(self, callback) -> None:
        self.__host = "localhost"
        self.__port = 5672
        self.__username = "guest"
        self.__password = "guest"
        self.__queue = "payment_queue"
        self.__stock_exchange = "stock_exchange"
        self.__shipping_exchange = "shipping_exchange"
        self.__commit_exchange = "commit_exchange"
        self.__routing_key = "stock_success"
        self.__shipping_fail_key = "shipping_fail"
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

        channel.exchange_declare(exchange=self.__stock_exchange, exchange_type='direct')  # Receber mensagem de Stock
        channel.exchange_declare(exchange=self.__shipping_exchange, exchange_type='direct')  # Receber mensagem de Shipping
        # channel.exchange_declare(exchange=self.__commit_exchange, exchange_type='direct')  # Receber mensagem de Order

        channel.queue_declare(queue=self.__queue,durable=True)
        
        channel.queue_bind(exchange=self.__stock_exchange, queue=self.__queue, routing_key=self.__routing_key)  # Receber mensagem de Stock com Sucesso no Estoque
        channel.queue_bind(exchange=self.__shipping_exchange, queue=self.__queue, routing_key=self.__shipping_fail_key)  # Receber do Shipping com Erro no Envio
        # channel.queue_bind(exchange=self.__commit_exchange, queue=self.__queue, routing_key=self.__commit_key)  # Receber de Order sobre a votação de commit

        channel.basic_consume(queue=self.__queue, auto_ack=True, on_message_callback=self.__callback)

        return channel

    # Função para consumir mensagens do RabbitMQ
    def start(self):
        print('Serviço de Pagamento')
        print('Escutando pelo RabbitMQ na Porta 5672')
        self.__channel.start_consuming()

# Callback para processar as mensagens recebidas
def callback(ch, method, properties, body):
    if method.routing_key == "stock_success":
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
        total = quantity * price
        print(f"Total a pagar {total}")
        
        conn = sqlite3.connect('payment_service/payment_database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO PAYMENT_DATABASE (id, user_id, price, balance, status) VALUES (?, ?, ?, ?, ?)", (order_id, user_id, total, user_balance, "pending"))
        if total <= user_balance:
            cursor.execute("UPDATE PAYMENT_DATABASE SET status = ? WHERE id = ?", ("payment confirmed", order_id))
            conn.commit()
            body_dict['final_balance'] = user_balance - total
            response = 'payment_success'
        else:
            cursor.execute("UPDATE PAYMENT_DATABASE SET status = ? WHERE id = ?", ("payment failed", order_id))
            conn.commit()
            response = 'payment_fail'
        conn.close()
        
        print('Enviando dados para a fila: ' + response)
        ch.basic_publish(exchange="payment_exchange", routing_key=response, body=json.dumps(body_dict))
    elif method.routing_key == "shipping_fail":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        order_id = body_dict['order_id']
        
        conn = sqlite3.connect('payment_service/payment_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE PAYMENT_DATABASE SET status = ? WHERE id = ?", ("shipping failed", order_id))
        conn.commit()
        conn.close()
        
        response = 'shipping_fail'
        print('Enviando dados para a fila: ' + response)
        ch.basic_publish(exchange="payment_exchange", routing_key=response, body=body)

payment = Payment(callback)
payment.start()
