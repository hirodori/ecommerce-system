import subprocess

commands = [
    "python order_service\order.py",
    "python stock_service\stock.py",
    "python payment_service\payment.py",
    "python shipping_service\shipping.py",
    "python client.py"
]

def run_command_in_terminal(cmd):
    command = f'start cmd /k "{cmd} & pause"'
    subprocess.Popen(command, shell=True)

for cmd in commands:
    run_command_in_terminal(cmd)
    