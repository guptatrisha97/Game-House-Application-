import socket
import sys


class ClientMain:
    def __init__(self, argv):
        self.addr = argv[1]
        self.port = int(argv[2])

    def client_run(self):
        # create socket and connect to server
        try:
            self.clientSocket = socket.socket()
            self.clientSocket.connect((self.addr, self.port))
        except socket.error as msg:
            print("Socket error: ", msg)
            sys.exit(1)

        print("Connection established. My socket address is", self.clientSocket.getsockname())
        authenticationMessage = self.authenticate()
        while authenticationMessage != "1001 Authentication successful":
            # If server disconnects before authentications
            if len(authenticationMessage) == 0:
                print("Server connection lost...Disconnecting!")
                sys.exit(1)
            authenticationMessage = self.authenticate()

        while True:
            # What about server disconnect before authentication?
            commandRun = self.command()
            if commandRun == "3011 Wait":
                try:
                    message = self.clientSocket.recv(1000).decode()
                    print(message)
                except socket.error as err:
                    print("Recv error: ", err)
                    sys.exit(1)
            if commandRun == "Wait for other player to guess":
                try:
                    message = self.clientSocket.recv(1000).decode()
                    print(message)
                except socket.error as err:
                    print("Recv error: ", err)
                    sys.exit(1)
            # if server shut down, disconnect the client also
            if len(commandRun) == 0:
                print("Server connection lost...Disconnecting!")
                sys.exit(1)


    def command(self):
        cd = input("Enter command: ")
        if cd == "/list":
            self.clientSocket.send(("/list").encode("ascii"))
            try:
                gameHall = self.clientSocket.recv(1000).decode()
            except socket.error as err:
                print("Recv error: ", err)
                sys.exit(1)
            print(gameHall)
            return gameHall
        elif cd.startswith("/enter") or cd.startswith("/guess"):
            self.clientSocket.send(cd.encode("ascii"))
            try:
                message = self.clientSocket.recv(1000).decode()
            except socket.error as err:
                print("Recv error: ", err)
                sys.exit(1)
            print(message)
            return message
        elif cd == "/exit":
            print("4001 Bye Bye")
            print("Client Ends")
            sys.exit(1)
        else:
            print("4002 Unrecognized message")
            return "4002 Unrecognized message"

    def authenticate(self):
        username = input("Please input your user name: ")
        password = input("Please input your password: ")
        self.clientSocket.send(("/login " + username + " " + password).encode("ascii"))
        try:
            message = self.clientSocket.recv(1000).decode()
        except socket.error as err:
            print("Recv error: ", err)
            sys.exit(1)
        print(message)
        return message


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 GameClient.py <Server_addr> <Server_port>")
        sys.exit(1)
    client = ClientMain(sys.argv)
    client.client_run()
