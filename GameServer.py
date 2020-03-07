import socket
import sys
import threading

gameStates = {}
usersInfo = {}
numberOfRooms = 10

class ServerThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.connectionSocket, self.addr = client
        print("In Constructor ", self.addr)

    def run(self):
        while True:
            try:
                message = self.connectionSocket.recv(1000).decode()
            except socket.error as err:
                print("Recv error: ", err)
                sys.exit(1)
            print(message)

            if message.startswith("/login"):
                result = self.authentication(message)
                self.connectionSocket.send(result.encode("ascii"))
            elif message.startswith("/list"):
                result = ""
                for i in range (0, numberOfRooms):
                    result = result + str(len(gameStates[i])) + " "
                self.connectionSocket.send(result.encode("ascii"))
            elif message.startswith("/enter"):
                result = self.enterRoom(message)
                self.connectionSocket.send(result.encode("ascii"))

        self.connectionSocket.close()

    def enterRoom(self, message):
        # Check if invalid char or nothing is inputted
        room = message.split(" ")[1]
        print(room)
        if room.isnumeric() and 1 <= int(room) <= numberOfRooms:
            room = int(room)-1
            if len(gameStates[room]) == 0:
                # increase the number of players in the room by 1
                gameStates[room].append(self)
                # debugging
                result = "3011 Wait"
                print(result)
            elif len(gameStates[room]) == 1:
                result = "3012 Game started. Please guess true or false"
                gameStates[room][0].connectionSocket.send(result.encode("ascii"))
                gameStates[room].append(self)
            else:
                result = "3013 The room is full"
        else:
            result = "Invalid room number"
        return result

    def authentication(self, message):
        params = message.split(" ")
        if params[1] in usersInfo and usersInfo[params[1]] == params[2]:
            return "1001 Authentication successful"
        else:
            return "1002 Authentication failed"


class ServerMain:
    def __init__(self, argv):
        self.port = int(argv[1])
        self.usersInfoPath = argv[2]

    def server_run(self):
        serverPort = self.port
        try:
            usersInfoFile = open(self.usersInfoPath, 'r')
        except IOError as msg:
            print("File open error: ", msg)
            sys.exit(1)

        lines = usersInfoFile.read()
        # Dictionary to store the username and passwords

        for line in lines.split("\n"):
            username, password = line.split(":")
            usersInfo[username] = password

        print(usersInfo)

        # Initializing the gameStates array, assuming 10 rooms atm
        # THe gameStates array stores the instances of the users in a particular room
        for i in range(0, numberOfRooms):
            gameStates[i] = []

        # create socket and bind
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serverSocket.bind(("localhost", serverPort))
        except socket.error as err:
            print("Bind error: ", err)
            sys.exit(1)

        serverSocket.listen(5)
        print("The server is ready to receive ", serverSocket.getsockname())

        usersInfoFile.close()

        while True:
            try:
                client = serverSocket.accept()
            except socket.error as msg:
                print("Socket accept error: ", msg)
                sys.exit(1)

            newthd = ServerThread(client)
            newthd.start()

        serverSocket.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 GameServer.py <Server_port> <Path to UserInfo.txt File>")
        sys.exit(1)
    server = ServerMain(sys.argv)
    server.server_run()
