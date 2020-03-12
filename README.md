# Game-House-Application-
Implementing a simple game house application using Python socket programming. 
A game house is an application in which multiple clients connect to a game server, get authorized, and then select a game room to enter and play a game with another player in the same room. 
The game house application consists of two parts: the server program and the client program. 
The server program should always be running and use a welcome socket to wait for connection requests from clients.
The client programs establish TCP connections with the server program. After a connection is set up, the client needs to send its user name and password to the server, and can enter the game hall after successful authentication. 
An authenticated user is able to query the status of the game rooms, and then pick a room to enter. To start a game, there should be exactly two players in the same room. Therefore, if the entering player is the first one in the room, the player has to wait; otherwise, the game starts. 
After the game has started, the server generates a random boolean value and each player is invited to guess the boolean value; the player who guesses the same as the randomly generated value is the winner, and the game results in a tie if the two players’ guesses are the same. 
After notifying both players the game result, the game is over and both players return to the game hall. A user may leave the system when the user is in the game hall. 

# Important notes for use-
For now we have let the number of rooms in the game hall to be 10.

If P1 and P2 are in a Game room and P1 loses it's connection, then P2 gets the notification after he makes the guess and the number of clients in the room ends up being 0

For the locks, we are acquiring the lock before any function that modifies the shared variables. We could reduce the critical section, by acquiring the lock inside the function, but in that case the complexity would increase without significant performance improvement

# How to Use-
Python v: 3.6 In order to run the program, run the server "python3 GameServer.py [port] [UserInfo text file]" and then the client(s) "python3 GameClient.py localhost [port]" while in the source folder.

# Working- 
Once the server is running, the client can connect to it and get a successful authentication by entering his credentials.
Once the client is successfully authenticated, he/she can give the following commands to the server - 

/list (shows the state of each room in the game hall) - 3001 number_of_all_rooms number_of_players_in_room1 ... number_of_players_in_roomn

/enter room_number (the server first checks if the target room number is valid or not. If it is valid, the server checks if the target room is empty or not. If the room is empty, the server responds with the following message: 3011 Wait
Upon receiving the above message, the client waits for the server to send the message with status code 3012.
If the target room is not empty, i.e., there is another user waiting, the server notifies the waiting user and the currently entering user with the following message and then enters the stage of “playing a game” described next.
3012 Game started. Please guess true or false
If the room has already been occupied by two players, the entering player will receive the following message from the server and stay in the game hall:
3013 The room is full

Upon receiving a message 3012 from the server, the client waits for the user to enter a boolean value, i.e., true or false, and then sends the input to the server via the following message:
/guess true_or_false
(Note: true_or_false should be replaced by the entered true (or false).)
Upon receiving /guess messages from both of the players, if their guesses are the same, the result is a tie, and the server sends the following message to both players:
3023 The result is a tie
Otherwise, the server generates a random Boolean value, r. The player whose guess is r becomes the winner, and the other loses the game. The server sends the following the message to the winner:
3021 You are the winner
The server sends the following message to the loser:
3022 You lost this game
After receiving any of the above messages, the game ends and the states of both players return to “in the game hall”.

/exit - 4001 Bye bye
Upon receiving the response from the server, the client program closes its socket and then quits.
Whenever a player exits from the system, the server thread (that handles the user’s connection) updates the room member list, closes the corresponding socket and then ends.

# Exception Handling implemented-
1. Player A has not made a guess, player B has not made a guess.
2. Player A has not made a guess, player B has made a guess.
3. Player A has made a guess, player B has not made a guess.
4. player A exits abnormally when in the game hall, the server should detect an exception and end the corresponding server thread
5. If player A exits abnormally when waiting in a game room for the other player to enter, the server should clear the room state before ending the corresponding server thread.
6. TCP connection may be broken, or a remote end host may suddenly leave the system at any step of the dialog. 


