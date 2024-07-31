from typing import Dict
import pika
import json
import os
from time import sleep
import sqlite3

class Client:
    def __init__(self) -> None:
        self.__host = "localhost"
        self.__port = 5672
        self.__username = "guest"
        self.__password = "guest"
        self.__exchange = "client_exchange"
        self.__order_exchange = "order_exchange"
        self.__routing_key = "order"
        self.__shipping_key = "shipping_success"
        self.__stock_fail_key = "stock_fail"
        self.__payment_fail_key = "payment_fail"
        self.__shipping_fail_key = "shipping_fail"
        self.__callback = callback
        self.__channel = self.__create_channel()
        self.__id = self.__define_user_id()
    
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
        
        queue = channel.queue_declare(queue='', exclusive=True)
        queue_name = queue.method.queue

        channel.queue_bind(exchange=self.__order_exchange, queue=queue_name, routing_key=self.__shipping_key)  # Receber mensagem de Order com Sucesso no Envio
        channel.queue_bind(exchange=self.__order_exchange, queue=queue_name, routing_key=self.__stock_fail_key)  # Receber mensagem de Order com Erro no Estoque
        channel.queue_bind(exchange=self.__order_exchange, queue=queue_name, routing_key=self.__payment_fail_key)  # Receber mensagem de Order com Erro no Pagamento
        channel.queue_bind(exchange=self.__order_exchange, queue=queue_name, routing_key=self.__shipping_fail_key)  # Receber mensagem de Order com Erro no Envio

        channel.basic_consume(queue=queue_name, on_message_callback=self.__callback, auto_ack=True)
        
        return channel
    
    # Função para definir o ID do usuário
    def __define_user_id(self):
        user = int(input("Já possui cadastro (0: Não | 1: Sim)? "))
        while user < 0 and user > 1:
            print("Opção inválida... Tente novamente.")
            sleep(1.5)
            os.system("cls")
            user = int(input("Já possui cadastro (0: Não | 1: Sim)? "))
        if user == 0:
            name = input("Insira o seu nome: ")
            country = input("Insira o seu país: ")
            balance = float(100.00)
            
            conn = sqlite3.connect('client_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM CLIENT_DATABASE")
            result = cursor.fetchone()
            id = result[0] + 1
            cursor.execute("INSERT INTO CLIENT_DATABASE (id, name, country, balance) VALUES (?, ?, ?, ?)", (id, name, country, balance))
            conn.commit()
            conn.close()
            
            print(f"O seu ID é {id}. O seu saldo inicial é {balance:.2f}!")
            return id
        elif user == 1:
            id = input("Insira o seu ID: ")
            
            conn = sqlite3.connect('client_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, balance FROM CLIENT_DATABASE WHERE id = ?", (id))
            result = cursor.fetchone()
            print(f"Bem-vindo, {result[0]}! O seu saldo atual é {result[1]:.2f}")
            conn.close()
            
            return id
    
    # Função para retornar o ID do usuário
    def get_user_id(self):
        return self.__id
    
    # Função para retornar o saldo do usuário
    def get_user_balance(self):
        id = self.get_user_id()
        
        conn = sqlite3.connect('client_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM CLIENT_DATABASE WHERE id = ?", (id, ))
        result = cursor.fetchone()
        balance = result[0]
        conn.close()
        
        return balance
    
    # Função para retornar o país do usuário
    def get_user_country(self):
        id = self.get_user_id()
        
        conn = sqlite3.connect('client_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT country FROM CLIENT_DATABASE WHERE id = ?", (id, ))
        result = cursor.fetchone()
        country = result[0]
        conn.close()
        
        return country
    
    # Função para enviar mensagem
    def send_message(self, body: Dict):
        print("Enviando pedido: " + str(body))
        self.__channel.basic_publish(
            exchange=self.__exchange,
            routing_key=self.__routing_key,
            body=json.dumps(body),
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    # Função para consumir mensagens do RabbitMQ
    def start(self):
        print('Escutando pelo RabbitMQ na Porta 5672')
        self.__channel.start_consuming()

# Callback para processar as mensagens recebidas
def callback(ch, method, properties, body):
    if method.routing_key == "shipping_success":
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        user_id = body_dict['user_id']
        balance = body_dict['final_balance']
        print("O seu pedido foi confirmado!")
        
        conn = sqlite3.connect('client_database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE CLIENT_DATABASE SET balance = ? WHERE id = ?", (balance, user_id))
        conn.commit()
        conn.close()
        
        print(f"Seu saldo final é {balance:.2f}")
    elif method.routing_key == "stock_fail":
        print("Erro no Estoque!")
    elif method.routing_key == "payment_fail":
        print("Erro no Pagamento!")
    elif method.routing_key == "shipping_fail":
        print("Erro no Envio!")

client = Client()
id_user = client.get_user_id()
user_balance = client.get_user_balance()
user_country = client.get_user_country()
id_product = input("Insira o ID do jogo que deseja comprar: ")
quantity = input("Insira a quantidade que deseja comprar: ")
order = {"user_id": id_user, "product_id": id_product, "quantity": quantity, "user_country": user_country, "balance": user_balance}
client.send_message(order)
client.start()
