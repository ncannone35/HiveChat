import socket
import threading
import random
import string
import time
import queue
import checksum

def main():
    logging_in = True
    quit_key = ""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDPadd = ("143.47.184.219", 5382)

    DROP_RATE = 0.0
    FLIP_RATE = 0.000
    BURST_RATE = 0.000
    BURST_LENGTH = 3
    DELAY = .8
    DELAY_LENGTH_LOW = 3
    DELAY_LENGHT_HIGH = 5



    # make a dictionary of other users and initialize the seqence number to 0
    # when a message is sent, find the username in increment their sequence number
    ack_queue = queue.Queue()
    currSEQ = 0
 
        
    #handles non-login related responses
    def checkMsg(queue):
        userACKs = {}
        while(True): 
            currMSG = ''
            endOfMsg = False
            errorFound = False
            while not endOfMsg:
                try:
                    currBytes, addr= sock.recvfrom(1024)
                    currMSG += currBytes.decode('utf-8')
                    if('\n' in currMSG):
                        endOfMsg = True
                except:
                    errorFound = True
                    break
            if errorFound:
                continue
            message = currMSG
            if (message == "SEND-OK\n"):
                pass
            elif (message == "BAD-DEST-USER\n"):
                print("Message Send Failed: Invalid Username")
                ack_queue.put(-1)
            elif (len(message) != 0 and message.split()[0] == 'LIST-OK' and len(message.split()) > 1): # recieving list of users from server
                print("Current Users:")
                print(' ,'.join(map(str, message.split()[1:])))
                print()
                ack_queue.put(-1)
            elif (message == "BAD-RQST-BDY\n"):
                print("Ther was an error with your request. Please try again.")
            elif (message == "DELIVERY " + username + " " + quit_key + "\n"):
                ack_queue.put(-1)
                print('Closing...')
                return
            elif ("DELIVERY" in message and len(message.split())) > 2:
                sender = message.split()[1]
                text = message.split()[2:]
                initial_message = message.split('!checksum')[0].rstrip()
                #print(initial_message)
                check = ''
                for i in range(0, len(message.split()), 1):
                    if message.split()[i] == "!checksum":
                        check = message.split()[i+1]
                try: 
                    if checksum.check_for_error(initial_message, check):
                        
                        errorFound = True
                        continue
                except:
                        
                        errorFound = True
                        continue
                # check for errors. If we find an error, don't send anything and the first computer will retransmit on timeout
                if text[1] == 'MSG':
                    # check if this is a higher sequence number than the last one
                    # if it is, print the message, put it in the buffer and send an ack
                    #send back an ack
                   
                    message = "SEND " + sender + " " + text[0] + ' ACK'
                    expected = "DELIVERY " + sender + " " + text[0] + ' ACK'
                    check = checksum.compute_checksum(expected)
                    message = message + " " + "!checksum " + check + " " '\n'
                    sock.sendto(bytes(message, 'utf-8'), UDPadd)
                    if (sender in userACKs and (userACKs[sender] < int(text[0]))) or sender not in userACKs:
                        print("Incoming Message:")
                        print(sender + ": " + ' '.join(map(str, text[2:-2])))
                        print()
                        userACKs[sender] = int(text[0])
                elif text[1] == 'ACK':
                    initial_message = message.split('!checksum')[0].rsplit()
                    # put sequence number on the queue to be read and continue
                    ack_queue.put(int(text[0]))
                    continue

    # handles waiting for ACKS and retransmissions on timeout
    def searchForAck(message):
        lookingForAck = True
        nonlocal currSEQ
        while lookingForAck:
            try:
                num = ack_queue.get(timeout=.4)
                if num == currSEQ or num == -1:
                    lookingForAck = False
                    if num == currSEQ:
                        print("Message Delivered Successful1y")
            except:
                sock.sendto(bytes(message, 'utf-8'), ("143.47.184.219", 5382))
        currSEQ += 1

    #responsible for handling inputs and sending proper messages to the server
    def handleInput(input):
        if(input == '!quit'):
            nonlocal quit_key
            quit_key = ''.join(random.choices(string.ascii_lowercase, k=5))
            message = "SEND " + username + " " + quit_key + "\n"
            sock.sendto(bytes(message, 'utf-8'), ("143.47.184.219", 5382))
            searchForAck(message)
            nonlocal running
            running = False
        elif (input == '!who'):
            message = "LIST\n"
            sock.sendto(bytes(message, 'utf-8'), ("143.47.184.219", 5382))
            searchForAck(message)
        elif (len(input) != 0 and input[0] == '@' and len(input.split()) > 1):
        
        # TODO: put new stuff here
            words = input.split()
            recipient = words[0]
            recipient = recipient[1:]
            message = ""
            for word in words[1:]:
                message = message + word + " "
            message = message[:-1]
            nonlocal currSEQ

            print("Sending Message...")
            print()
            expected = "DELIVERY " + recipient + " " + str(currSEQ) + " MSG " + message
            message = "SEND " + recipient + " " + str(currSEQ) + " MSG " + message
            check = checksum.compute_checksum(expected.rstrip())
            message = message + " !checksum " + check + " " + '\n'
            sock.sendto(bytes(message, 'utf-8'), ("143.47.184.219", 5382))
            searchForAck(message)
        else:
            print("Invalid Input")
            print_commands()


                

    #takes login input from user
    def logInUser():
        nonlocal username
        #don't want blank usernmaes
        while True:
            username = input()
            if username:
                break
        print('You have entered: ', username)
        message = "HELLO-FROM " + username + "\n"
        sock.sendto(bytes(message, 'utf-8'), ("143.47.184.219", 5382))
        return username

    
    #prints commands to user
    def print_commands():
        print('To see all of the logged in users, type !who')
        print('To send a message to a user, type @username message where username is your friend\'s username and message is your message to them')
        print('To exit the chat client, type !quit')
        print()

    running = True
    username = ''
    #start of program
    print('Welcome to your chat messager!')
    print('To begin, please enter a username for yourself')

    #login validation proccess
    userName = logInUser()
    while(True):
        message, addr = sock.recvfrom(1024)
        message = str(message.decode('utf-8'))
        if (message == "IN-USE\n"):
            print("That username is already in use. Please try again.")
            logInUser()
            print()
        elif (message == "BUSY\n"):
            print("The server is busy, please wait before trying to login again.")
            logInUser()
            print()
        elif (message == "BAD-RQST-BODY\n"):
            print("There was an error with your request. Please try again.")
            logInUser()
            print()
        elif (len(message.split()) > 0 and message.split()[0] == "HELLO"):
            print("Login Successful!")
            print()
            break
    #login has been validated, proceeds to program
    print('Now that you are successfully logged here are some tips')
    print_commands()
    #chat_thread handles all server responses
    chat_thread = threading.Thread(target=checkMsg, args=([ack_queue]))
    chat_thread.start()

    # send the drop, flip, and burst rates to the server
    sock.sendto(bytes(f'SET DROP {DROP_RATE}\n', 'utf-8') , UDPadd)
    sock.sendto(bytes(f'SET FLIP {FLIP_RATE}\n', 'utf-8') , UDPadd)
    sock.sendto(bytes(f'SET BURST {BURST_RATE}\n', 'utf-8') , UDPadd)
    sock.sendto(bytes(f'SET BURST-LEN {BURST_LENGTH}\n', 'utf-8') , UDPadd)
    sock.sendto(bytes(f'SET DELAY-LEN {DELAY_LENGTH_LOW} {DELAY_LENGHT_HIGH}\n', 'utf-8') , UDPadd)
    sock.sendto(bytes(f'SET DELAY {DELAY}\n', 'utf-8') , UDPadd)


    # main loop of program
    while(running):
        userInput = ''
        while True:
            userInput = input()
            if userInput:
                break
        handleInput(userInput)

    #end of program, end thread and socket
    chat_thread.join()
    sock.close()

if __name__ == "__main__":
    main()