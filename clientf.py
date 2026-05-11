import socket
import threading
from cryptography.fernet import Fernet

with open("key.key", "rb") as f:
    key = f.read()

fernet = Fernet(key)

# SAME COMPUTER:
# host = '127.0.0.1'

# DIFFERENT COMPUTERS SAME WIFI:
host = '127.0.0.1'

port = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((host, port))


# USERNAME

while True:

    username = input("Enter username: ")

    client.send(username.encode())

    response = client.recv(1024)

    status = fernet.decrypt(response).decode()

    if status == "OK":

        print("Connected as", username)

        break

    else:

        print("Username already taken")


# RECEIVE

def receive():

    while True:

        try:

            encrypted_msg = client.recv(4096)

            if not encrypted_msg:
                break

            msg = fernet.decrypt(encrypted_msg)

            # PRIVATE FILE
            if msg.startswith(b"PFILE:"):

                parts = msg.split(b":", 3)

                sender = parts[1].decode()

                filename = parts[2].decode()

                filedata = parts[3]

                with open(
                    "received_" + filename,
                    "wb"
                ) as f:

                    f.write(filedata)

                print(
                    f"\n📁 Private file received "
                    f"from {sender}: {filename}"
                )

            # BROADCAST FILE
            elif msg.startswith(b"FILE:"):

                parts = msg.split(b":", 3)

                sender = parts[1].decode()

                filename = parts[2].decode()

                filedata = parts[3]

                with open(
                    "received_" + filename,
                    "wb"
                ) as f:

                    f.write(filedata)

                print(
                    f"\n📁 File received "
                    f"from {sender}: {filename}"
                )

            else:

                text = msg.decode()

                # ONLINE USERS
                if text.startswith("USERS:"):

                    users = text.replace(
                        "USERS:",
                        ""
                    ).split(",")

                    print(
                        "\n👥 Online Users:",
                        users
                    )

                else:

                    print("\n" + text)

        except:

            print("Disconnected from server")

            client.close()

            break


# SEND

def write():

    while True:

        message = input("You: ")

        # EXIT
        if message == "/exit":

            client.send(
                fernet.encrypt(b"/exit")
            )

            client.close()

            break

        # PRIVATE FILE
        elif (
            message.startswith("@")
            and "/send " in message
        ):

            try:

                target = message.split(" ")[0][1:]

                filename = message.split(
                    "/send ",
                    1
                )[1]

                with open(filename, "rb") as f:

                    data = f.read()

                packet = (
                    b"PFILE:"
                    + target.encode()
                    + b":"
                    + filename.encode()
                    + b":"
                    + data
                )

                encrypted = fernet.encrypt(packet)

                client.send(encrypted)

                print(
                    f"📤 Private file sent "
                    f"to {target}: {filename}"
                )

            except:

                print("File not found")

        # BROADCAST FILE
        elif message.startswith("/send "):

            filename = message.split(
                " ",
                1
            )[1]

            try:

                with open(filename, "rb") as f:

                    data = f.read()

                packet = (
                    b"FILE:"
                    + filename.encode()
                    + b":"
                    + data
                )

                encrypted = fernet.encrypt(packet)

                client.send(encrypted)

                print("📤 File sent:", filename)

            except:

                print("File not found")

        # NORMAL MESSAGE
        else:

            encrypted = fernet.encrypt(
                message.encode()
            )

            try:

                client.send(encrypted)

            except:

                print("Connection lost")

                break

# THREADS
threading.Thread(
    target=receive,
    daemon=True
).start()

threading.Thread(
    target=write
).start()