import socket
import sys
import threading
import random

gameStates = {}
usersInfo = {}
numberOfRooms = 10
playerGuess = {}

class ServerThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.connectionSocket, self.addr = client
        # Reset roomNumber, playerGuess and GameState once the game is over
        # What if player guesses outside the room
        self.roomNumber = -1
        #self.lock = allocate_lock()
        print("In Constructor ", self.addr)

    def run(self):
        while True:
            try:
                message = self.connectionSocket.recv(1000).decode()
                # when a client disconnects
                if not message:
                    currentPlayer = self
                    # notify other player
                    if currentPlayer == gameStates[self.roomNumber][0]:
                        otherPlayer = gameStates[self.roomNumber][1]
                    else:
                        otherPlayer = gameStates[self.roomNumber][0]
                    result = "3021 You are the winner"
                    otherPlayer.connectionSocket.send(result.encode("ascii"))
                    # reset the room
                    print("Client has disconnected")  # if no data is received, then disconnect and close the port
                    gameStates[self.roomNumber] = []
                    playerGuess[self.roomNumber] = []
                    self.roomNumber = -1
                    break
            except socket.error as err:
                if isinstance(err.args, tuple):
                    print("Recv error number: %d " % err[0])
                    if err[0] == errno.EPIPE:
                        print ("Detected remote disconnect")
                        sys.exit(1)
                    else:
                        print ("Socket error 1")
                else:
                    print ("Socket error 2 " + err.message)
                    sys.exit(1)
            print(message)

            # The current player's result will always be sent from here
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
            elif message.startswith("/guess"):
                result = self.getStatus(message)
                self.connectionSocket.send(result.encode("ascii"))

        self.connectionSocket.close()

    def getStatus(self, message):
        # What if the second user gets disconnected after 1st user sends the message
        currentGuess = message.split(" ")[1]
        resultWon = "3021 You are the winner"
        resultLost = "3022 You lost this game"
        resultTie = "3023 The result is a tie"

        # Player is not currently in a room but has guessed a value
        if self.roomNumber == -1:
            return "4002 Unrecognized message"

        # If the guesses are not valid
        if currentGuess != "true" and currentGuess != "false":
            return "4002 Unrecognized message"

        print(currentGuess)
        playerGuess[self.roomNumber].append(currentGuess)

        # If only 1 player has guessed till now
        if len(playerGuess[self.roomNumber]) != 2:
            return "Wait for other player to guess"

        currentPlayer = self
        if currentPlayer == gameStates[self.roomNumber][0]:
            otherPlayer = gameStates[self.roomNumber][1]
        else:
            otherPlayer = gameStates[self.roomNumber][0]
        print(playerGuess[self.roomNumber][0], " ", playerGuess[self.roomNumber][1])

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
                print("guess", str(currentGuess).casefold(), "ans",str(answer).casefold())
                result = resultWon
                otherPlayer.roomNumber = -1
                otherPlayer.connectionSocket.send(resultLost.encode("ascii"))
            else:
                print("guess is", str(currentGuess).casefold(), "ans is",str(answer).casefold())
                result = resultLost
                otherPlayer.roomNumber = -1
                otherPlayer.connectionSocket.send(resultWon.encode("ascii"))

        # Resetting the values and returning the result
        # The other player room number is reset earlier to prevent race conditions
        gameStates[self.roomNumber] = []
        playerGuess[self.roomNumber] = []
        self.roomNumber = -1
        return result

    def enterRoom(self, message):
        # Check if invalid char or nothing is inputted
        room = message.split(" ")[1]
        if room.isnumeric() and 1 <= int(room) <= numberOfRooms:
            room = int(room)-1
            if len(gameStates[room]) == 0:
                # increase the number of players in the room by 1
                gameStates[room].append(self)
                self.roomNumber = room
                # debugging
                result = "3011 Wait"
                print(result)
            elif len(gameStates[room]) == 1:
                result = "3012 Game started. Please guess true or false"
                gameStates[room][0].connectionSocket.send(result.encode("ascii"))
                gameStates[room].append(self)
                self.roomNumber = room
            else:
                result = "3013 The room is full"
        else:
            # Should it be invalid room number or unrecognised message
            result = "4002 Unrecognized message"
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

        for line in lines.split("\n"):
            username, password = line.split(":")
            usersInfo[username] = password

        print(usersInfo)

        # Initializing the gameStates array, assuming 10 rooms atm
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
