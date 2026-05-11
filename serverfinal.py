import socket
import threading
import time
from cryptography.fernet import Fernet
from datetime import datetime

with open("key.key", "rb") as f:
    key = f.read()

fernet = Fernet(key)

host = '0.0.0.0'
port = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((host, port))

server.listen()

print("Server running...")

clients = {}


# TIME

def current_time():

    return datetime.now().strftime("%I:%M %p")


# SEND ONLINE USERS

def send_user_list():

    user_list = "USERS:" + ",".join(clients.keys())

    encrypted = fernet.encrypt(user_list.encode())

    for client in clients.values():

        try:
            client.send(encrypted)
        except:
            pass


# SYSTEM NOTIFICATIONS

def broadcast_system(message):

    msg = f"[{current_time()}] SYSTEM: {message}"

    encrypted = fernet.encrypt(msg.encode())

    for client in clients.values():

        try:
            client.send(encrypted)
        except:
            pass


# HANDLE CLIENT

def handle(client, username):

    while True:

        try:

            encrypted_msg = client.recv(4096)

            if not encrypted_msg:
                break

            # SHOW ENCRYPTED DATA ONLY ON SERVER
            print("Encrypted:", encrypted_msg)

            msg = fernet.decrypt(encrypted_msg)

            # EXIT
            if msg == b"/exit":
                break

            # PRIVATE FILE
            elif msg.startswith(b"PFILE:"):

                parts = msg.split(b":", 3)

                target = parts[1].decode()

                filename = parts[2]

                filedata = parts[3]

                if target in clients:

                    send_data = (
                        b"PFILE:"
                        + username.encode()
                        + b":"
                        + filename
                        + b":"
                        + filedata
                    )

                    encrypted = fernet.encrypt(send_data)

                    clients[target].send(encrypted)

            # BROADCAST FILE
            elif msg.startswith(b"FILE:"):

                parts = msg.split(b":", 2)

                filename = parts[1]

                filedata = parts[2]

                send_data = (
                    b"FILE:"
                    + username.encode()
                    + b":"
                    + filename
                    + b":"
                    + filedata
                )

                encrypted = fernet.encrypt(send_data)

                for user, sock in clients.items():

                    if user != username:
                        sock.send(encrypted)

            # TEXT MESSAGES
            else:

                decoded = msg.decode()

                # PRIVATE MESSAGE
                if decoded.startswith("@"):

                    target, message = decoded.split(" ", 1)

                    target = target[1:]

                    if target in clients:

                        send_msg = (
                            f"[{current_time()}] "
                            f"{username} (private): {message}"
                        )

                        encrypted = fernet.encrypt(
                            send_msg.encode()
                        )

                        clients[target].send(encrypted)

                # NORMAL MESSAGE
                else:

                    send_msg = (
                        f"[{current_time()}] "
                        f"{username}: {decoded}"
                    )

                    encrypted = fernet.encrypt(
                        send_msg.encode()
                    )

                    for user, sock in clients.items():

                        if user != username:
                            sock.send(encrypted)

        except:
            break

    # REMOVE USER
    if username in clients:
        del clients[username]

    client.close()

    print(username, "disconnected")

    # LEAVE NOTIFICATION
    broadcast_system(f"{username} left the chat")

    time.sleep(0.1)

    send_user_list()


# ACCEPT CLIENTS

while True:

    client, address = server.accept()

    # USERNAME CHECK
    while True:

        username = client.recv(1024).decode()

        if username in clients:

            client.send(
                fernet.encrypt(b"TAKEN")
            )

        else:

            client.send(
                fernet.encrypt(b"OK")
            )

            clients[username] = client

            break

    print(f"{username} connected from {address}")

    # JOIN NOTIFICATION
    broadcast_system(f"{username} joined the chat")

    time.sleep(0.1)

    send_user_list()

    thread = threading.Thread(
        target=handle,
        args=(client, username)
    )

    thread.start()