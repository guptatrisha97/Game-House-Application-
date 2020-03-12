import socket
import sys
import threading
import random
import errno

gameStates = {}
usersInfo = {}
numberOfRooms = 10
playerGuess = {}
lock = threading.Lock()

# Assuming that he is not allowed to "list" while in the room - Done
# Test server shutting down on server side - Not needed
# Test if thread is getting removed once client disconnects - Done
# Error 54 - Done
# Maybe need to change playerGuess coz of locks - Not needed as big critical section
# Implement locks - Done
# Test when client guesses and disconnects - Done
# Thread count not working
# What if system exits with lock not released? - sys.exit(1)
# Test exhaustively


class ServerThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.connectionSocket, self.addr = client
        # Reset roomNumber, playerGuess and GameState once the game is over
        self.roomNumber = -1
        self.otherPlayerDisconnected = False
        self.guessed = False
        # print("In Constructor ", self.addr)

    def run(self):
        while True:
            try:
                message = self.connectionSocket.recv(1000).decode()
                # When a client disconnects
                if not message:
                    currentPlayer = self
                    # Checking if the player is in the game hall
                    if self.roomNumber != -1:
                        # Only if there are 2 people in the room
                        lock.acquire()
                        if len(gameStates[self.roomNumber]) == 2:
                            if currentPlayer == gameStates[self.roomNumber][0]:
                                otherPlayer = gameStates[self.roomNumber][1]
                            else:
                                otherPlayer = gameStates[self.roomNumber][0]
                            # If the other person has guessed -
                            if otherPlayer.guessed:
                                otherPlayer.connectionSocket.send("3021 You are the winner".encode("ascii"))
                            # If not guessed, we wait for him to guess and then send winner, but roomNumber is -1
                            else:
                                otherPlayer.otherPlayerDisconnected = True
                            otherPlayer.roomNumber = -1
                            otherPlayer.guessed = False
                        # reset the room
                        # print("HI")
                        gameStates[self.roomNumber] = []
                        playerGuess[self.roomNumber] = []
                        lock.release()
                    print("Client has disconnected")  # if no data is received, then disconnect and close the port
                    break
            except socket.error as err:
                if isinstance(err.args, tuple):
                    print("Recv error number:", err.errno)
                    if err.errno == errno.EPIPE:
                        print("Detected remote disconnect")
                        sys.exit(1)
                    else:
                        print("Socket error 1 - Remote disconnect")
                        sys.exit(1)
                else:
                    print("Socket error 2 " + err.message)
                    sys.exit(1)

            print(message)
            print("Thread count = ", str(len(threading.enumerate())))

            # The current player's result will always be sent from here
            if message.startswith("/login"):
                result = self.authentication(message)
            elif message.startswith("/list"):
                lock.acquire()
                result = self.listRooms()
                lock.release()
            elif message.startswith("/enter"):
                lock.acquire()
                result = self.enterRoom(message)
                lock.release()
            elif message.startswith("/guess"):
                lock.acquire()
                result = self.getStatus(message)
                lock.release()

            self.connectionSocket.send(result.encode("ascii"))

        self.connectionSocket.close()

    def getStatus(self, message):
        message = message.split(" ")
        resultWon = "3021 You are the winner"
        resultLost = "3022 You lost this game"
        resultTie = "3023 The result is a tie"

        # Incorrect format, not 2 parameters
        if len(message) != 2:
            return "4002 Unrecognized message"

        currentGuess = message[1]

        # If the guesses are not valid
        if currentGuess != "true" and currentGuess != "false":
            return "4002 Unrecognized message"

        # If other player is disconnected, others have already been reset, just resetting otherPlayerDisconnected
        if self.otherPlayerDisconnected:
            self.otherPlayerDisconnected = False
            return resultWon

        # Player is not currently in a room but has guessed a value
        if self.roomNumber == -1:
            return "4002 Unrecognized message"

        #print(currentGuess)
        playerGuess[self.roomNumber].append(currentGuess)
        self.guessed = True

        # If only 1 player has guessed till now
        if len(playerGuess[self.roomNumber]) != 2:
            return ""

        currentPlayer = self
        if currentPlayer == gameStates[self.roomNumber][0]:
            otherPlayer = gameStates[self.roomNumber][1]
        else:
            otherPlayer = gameStates[self.roomNumber][0]

        # If the guesses are the same
        if playerGuess[self.roomNumber][0] == playerGuess[self.roomNumber][1]:
            result = resultTie
            otherPlayer.roomNumber = -1
            otherPlayer.connectionSocket.send(result.encode("ascii"))
        else:
            # generate random boolean value which is the answer
            random_bit = random.getrandbits(1)
            answer = bool(random_bit)
            print("answer is", answer)
            # If the current guess is the answer
            if str(currentGuess).casefold() == str(answer).casefold():
                #print("guess", str(currentGuess).casefold(), "ans",str(answer).casefold())
                result = resultWon
                otherPlayer.roomNumber = -1
                otherPlayer.connectionSocket.send(resultLost.encode("ascii"))
            else:
                #print("guess is", str(currentGuess).casefold(), "ans is",str(answer).casefold())
                result = resultLost
                otherPlayer.roomNumber = -1
                otherPlayer.connectionSocket.send(resultWon.encode("ascii"))

        # Resetting the values and returning the result
        # The other player room number is reset earlier to prevent race conditions
        self.guessed = False
        otherPlayer.guessed = False
        gameStates[self.roomNumber] = []
        playerGuess[self.roomNumber] = []
        self.roomNumber = -1
        return result

    def enterRoom(self, message):
        message = message.split(" ")
        # Incorrect format, not 2 parameters
        if len(message) != 2:
            return "4002 Unrecognized message"

        room = message[1]

        # Room number should be valid, the player should not already be in a room and enter again,
        # and if roomNumber is -1, other player should not be just disconnected
        if room.isnumeric() and 1 <= int(room) <= numberOfRooms and self.roomNumber == -1 and not self.otherPlayerDisconnected:
            room = int(room)-1
            # 1st player in the room
            if len(gameStates[room]) == 0:
                gameStates[room].append(self)
                self.roomNumber = room
                result = "3011 Wait"
            # 2nd Player in the room
            elif len(gameStates[room]) == 1:
                result = "3012 Game started. Please guess true or false"
                gameStates[room][0].connectionSocket.send(result.encode("ascii"))
                gameStates[room].append(self)
                self.roomNumber = room
            # Room is full
            else:
                result = "3013 The room is full"
        else:
            result = "4002 Unrecognized message"
        print(result)
        return result

    def authentication(self, message):
        params = message.split(" ")
        if params[1] in usersInfo and usersInfo[params[1]] == params[2]:
            return "1001 Authentication successful"
        else:
            return "1002 Authentication failed"

    def listRooms(self):
        if self.roomNumber != -1 or self.otherPlayerDisconnected:
            return "4002 Unrecognized message"
        else:
            result = "3001 " + str(numberOfRooms) + " "
            for i in range(0, numberOfRooms):
                result = result + str(len(gameStates[i])) + " "
            return result


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

        for line in lines.split("\n"):
            username, password = line.split(":")
            usersInfo[username] = password

        print(usersInfo)

        # Initializing the gameStates array, assuming 10 rooms
        # THe gameStates array stores the instances of the users in a particular room
        for i in range(0, numberOfRooms):
            gameStates[i] = []
            playerGuess[i] = []

        print("initial guess list", playerGuess)
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
