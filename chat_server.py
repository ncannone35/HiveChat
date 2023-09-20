import threading
import socket
import time
import queue

def main():
    host = ''
    chatQueue = queue.Queue()

    # Set up threads to accept a connection and send data to main thread for handling when data is recieved
    def waitForNewConnection(port, queue):
        print("Thread: ", port, " Created!")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen()
        connection, address = sock.accept()
        connection.send(bytes('SEND-OK\n', 'utf-8'))
        queue.put((port, connection, address))
        print('Connection made by: ', address)
        sock.close()
    
    # Set up threads to recieve data from user, send to main thread and wait for response from main thread
    def sendAndRecData(port, address, socket, queue):
        print("New Established Connection")
        recieving = True
        while recieving:
            try:
                endOfMessage = False
                userData = b''
                while not endOfMessage:
                    userData += socket.recv(2)
                    if(b'\n' in userData):
                        endOfMessage = True
            except:
                print("Connection Closed")
                queue.put((port, address, socket, "CLOSE"))
                # add to queue to reomve from established connections and add a new wait for new connection thread along the same port
                break
            print('Recieved Data: ', address, userData)
            queue.put((address, userData))


    
    def handlePacket(senderName, senderAdd, senderSock, dataString):
        
        dataWords = dataString.split()
        header = dataWords[0]
        data = dataWords[1:]
        invalid_username = False
        if(header == 'HELLO-FROM'):
            if(len(data) > 1):
                senderSock.send(bytes("BAD-RQST-BDY\n", 'utf-8'))
            userName = dataString.split()[1]
            nonlocal currUsers
            numUsers = len(currUsers)
            if numUsers >= 64:
                # send BUSY\n if max users
                senderSock.send(bytes("BUSY\n", 'utf-8'))
            if userName not in currUsers:
                # attach to userList in the right index to be associatied with a connection
                currUsers.append(userName)
                # update connections to include username
                nonlocal establishedConnections
                IPAddresses = list(zip(*establishedConnections))[0]
                connectionIndex = IPAddresses.index(senderAdd)
                establishedConnections[connectionIndex][1] = userName
                senderSock.send(bytes("HELLO " + userName + '\n', 'utf-8'))
            else:
                # send IN-USE\n if username is already in use
                senderSock.send(bytes("IN-USE\n", 'utf-8'))

        # handle LIST\n
        elif(dataString == 'LIST\n'):
            usersString = "LIST-OK "
            for user in currUsers:
                usersString += user + ','
            usersString = usersString[:-1] + '\n' # remove last comma and replace with \n
            # send list of all logged in users
            senderSock.send(bytes(usersString, 'utf-8'))


        # handle SEND <user> <message>\n
        elif(header == 'SEND'):
            reciever = dataWords[1]
            userFound = False
            for user in establishedConnections:
                if user[1] == reciever:
                    userFound = True
                    message = "DELIVERY " + senderName + " "
                    for word in dataWords[2:]:
                        message += word + " "
                    user[3].send(bytes(message[:-1] + '\n', 'utf-8'))
                    senderSock.send(bytes("SEND-OK\n", 'utf-8'))
                    break
            if not userFound:
                senderSock.send(bytes("BAD-DEST-USER\n", 'utf-8'))
        else:
            senderSock.send(bytes("BAD-RQST-HDR\n", 'utf-8'))
        # send back BAD-RQST-HDR\n if error is in the header


    # Create threads for network connections
    waitingConnections = []
    for i in range(1, 3):
        currThread = threading.Thread(target=waitForNewConnection ,args=[i, chatQueue])
        currThread.start()
        waitingConnections.append((i, currThread))
    # Set up clients for testing
    # IPAdd = socket.gethostbyname(socket.gethostname())
    # print(IPAdd)
    # print(type(IPAdd))
    # sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock1.connect((IPAdd, 3))
    # sock1.send(bytes('HELLO-FROM TOBY\n', 'utf-8'))
    # sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock2.connect((IPAdd, 2))
    # sock2.send(bytes('HELLO-FROM OtherGuy\n', 'utf-8'))

    # sock1.send(bytes('LIST\n', 'utf-8'))
    # sock1.send(bytes('SEND OtherGuy hello!','utf-8'))
    
    # Set up server to handle recieved data
    establishedConnections  = [] # list of touples (IPAddress, userName, thread)
    currUsers = []
    startTime = time.time()
    while True:
        # wait for data to enter queue from threads
        currData = chatQueue.get()
        # check if new connection
        if(len(currData) == 4):
            # remove old thread and add new one
            port = currData[0]
            address = currData[1]
            for i, connection in enumerate(establishedConnections):
                if connection[0] == address:
                    currUsers.remove(connection[1])
                    establishedConnections.pop(i)
                    break
            # scan established connections for the connection that was closed
            # remove that connection
            # start new thread with same port, add
            # find username in established connections
            # remove that username from currUsers
            currThread = threading.Thread(target=waitForNewConnection ,args=[port, chatQueue])
            currThread.start()
            waitingConnections.append((i, currThread))
        elif (len(currData) == 3):
            address = currData[2]
            newSocket = currData[1]
            port = currData[0]
            newThread = threading.Thread(target=sendAndRecData, args=[port, address, newSocket, chatQueue])
            newThread.start()
            establishedConnections.append([address, "",newThread, newSocket])
        
        # data recieved from an established connection
        else:
            senderAddress = currData[0]
            IPAddresses = list(zip(*establishedConnections))[0]
            connectionIndex = IPAddresses.index(senderAddress)
            senderSocket = establishedConnections[connectionIndex][3]
            senderName = establishedConnections[connectionIndex][1]
            currString = currData[1].decode('utf-8')
            packets = currString.splitlines()
            print('Packets:', packets)
            for packet in packets:
                packet = packet + '\n'
                handlePacket(senderName, senderAddress, senderSocket,packet)



    
    for connection in establishedConnections:
        connection[2].join()

if __name__ == "__main__":
    main()
