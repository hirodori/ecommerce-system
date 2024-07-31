import subprocess

print("Executando client_database.py...")
subprocess.run(["python", "client_database.py"], check=True)

print("Executando order_database.py...")
subprocess.run(["python", "./order_service/order_database.py"], check=True)

print("Executando stock_database.py...")
subprocess.run(["python", "./stock_service/stock_database.py"], check=True)

print("Executando payment_database.py...")
subprocess.run(["python", "./payment_service/payment_database.py"], check=True)

print("Executando shipping_database.py...")
subprocess.run(["python", "./shipping_service/shipping_database.py"], check=True)

print("Todos os scripts foram executados com sucesso.")
