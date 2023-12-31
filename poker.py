from abc import abstractmethod
import random
from operator import attrgetter
from tkinter import *
import tkinter as tk
import os
import sys
import socket
import threading
from turtle import width
import random
import time
import hashlib
#import psycopg2
from configparser import ConfigParser

class Server:
  
  # server program data
  usernames_passwords_bankrolls = []
  activePlayersAndAddresses = []
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  connections = []
  table_players = [] # list of tuples (ip, port)

  def __init__(self):

    #load user file data into server program data upon initialization
    file = open("users.txt", "r")
    fileData = file.readlines()
    file.close()
    check = 0
    tempUser = ''
    tempPassword = ''
    tempBankroll = ''

    #parsing and formatting logic to store file data
    for string in fileData:
      for character in string:
        if(character == ')'):
          check = 0
          break
        if(character == ' ' and check == 2):
          check = 3
          continue
        if(character == ' '):
          check = 2
          continue
        if(character == ','):
          continue
        if(check == 1):
          tempUser += character
        if(check == 2):
          tempPassword += character
        if(check == 3):
          tempBankroll += character
        if(character == '('):
          check = 1
      self.usernames_passwords_bankrolls.append((tempUser, tempPassword, int(tempBankroll)))
      tempUser = ''
      tempPassword = ''
      tempBankroll = ''

    # build table
    self.players = []
    self.deck = Deck()
    self.table = ServerTable(self.deck, self.connections, 9, self.players)
    self.started = False

    # table.deal()

    # bind server to host and port for listening
    self.sock.bind(('localhost', 19447))
    self.sock.listen(1)

  # how connections will be handeled based on data recieved by server from connection
  # user command function implementations will be marked with #############<function>#############
  def handler(self, c,a):
    while True:
      try:
        # recieve data
        data = c.recv(1024)
      except:
        # close connection
        print(str(a[0])+ ':' + str(a[1]) +  " disconnected")
        self.connections.remove(c)
        c.close()
        break
      if not data:
        # close connection
        print(str(a[0])+ ':' + str(a[1]) +  " disconnected")
        self.connections.remove(c)
        c.close()
        break
 
      #tokenize message recieved by server
      message = str(data, 'utf-8')
      print(message)
      tokens = message.split(' ')

      # format message
      formattedMessage = ""
      x = 0
      for i in tokens:
        if(x!=0 and x!=1):
          formattedMessage+=i+' '
        x+=1




      #############if we are logging out#############
      userlogincheck = False
      if(tokens[0]=="logout"):

        #is this account logged in
        for j in self.activePlayersAndAddresses:
          if(j[1]==str(a[0])):
            if(j[2]==a[1]):
              userlogincheck=True
              print(j[0]+" logout.")

              #respond to all clients with logout message
              for connection in self.connections:
                connection.send(bytes((j[0]+" left"), 'utf-8'))
              self.activePlayersAndAddresses.remove(j)
        if(userlogincheck == False):
          print("You are not logged in")



      #############if we are creating a new User#############
      checkuserlogin = False
      lengthCheck = False
      tokencheck = False
      if(tokens[0] == "newuser"):
        checker = 0

        #check if sender is logged in
        for connectioniterator in self.activePlayersAndAddresses:
          if(connectioniterator[1] == str(a[0])):
            if(connectioniterator[2] == a[1]):
              checkuserlogin=True
              break

        #check if tokens include all parameters
        if(len(tokens)>=3):
          tokencheck = True


        #check to see if all necessary tokens have been inputted    
        if(tokencheck == True):

          # if this username is not already in use in the usernames and passwords list of tuples
          for userAndPass in self.usernames_passwords_bankrolls:
            if(userAndPass[0] == tokens[1]):
              checker = 1

          #check username and password length
          if(len(tokens[1])>=3 and len(tokens[1])<=32 and len(tokens[2])>=4 and len(tokens[2])<=8):
            lengthCheck = True

        if(checker == 0 and checkuserlogin==False and lengthCheck == True):

          # add user to usernames and passwords list of tuples
          if(len(tokens) > 2):
            newUsername = tokens[1]
            newPassword = tokens[2]
            self.usernames_passwords_bankrolls.append((newUsername, newPassword, 10000))
            file = open("users.txt", "a")
            file.write('\n'+'('+newUsername+','+' ' + newPassword + ','+' '+ '10000'+')')
            file.close()

            # find client that sent this packet and respond 
            for connection in self.connections:
              if(connection.getpeername()[0] == str(a[0])):
                if(connection.getpeername()[1] == a[1]):
                    connection.send(bytes("New user account created. Please login.", 'utf-8'))
                    print("New user account created.")

          else:
            print("must enter username and password to create a new user account")
        if(checkuserlogin == True):
          print("you must logout before creating a new account")
        if(checker == 1):
          # find client that sent this packet and respond 
          for connection in self.connections:
            if(connection.getpeername()[0] == str(a[0])):
              if(connection.getpeername()[1] == a[1]):
                  connection.send(bytes("Denied. User account already exists.", 'utf-8'))
        if(lengthCheck== False):
          # find client that sent this packet and respond 
          for connection in self.connections:
            if(connection.getpeername()[0] == str(a[0])):
              if(connection.getpeername()[1] == a[1]):
                  connection.send(bytes("Denied. Username must be 3-32 characters. Password must be 4-8 characters.", 'utf-8'))
        

      #############if we are logging in#############
      checklogin = False
      loginchecker = False
      tokenschecker = False
      if(tokens[0] == "login"):

        #check if user inputted a password
        if(len(tokens)>= 3):
          tokenschecker=True

        if(tokenschecker==True):
          #check if sender is logged in
          for connectioniterator in self.activePlayersAndAddresses:
            #print(connectioniterator[1],str(a[0]),connectioniterator[2],a[1])
            if(connectioniterator[0]==tokens[1]):
              checklogin = True
              break
            if(connectioniterator[1] == str(a[0])):
              if(connectioniterator[2] == a[1]):
                checklogin=True
                break

        #login
        for users in self.usernames_passwords_bankrolls:
          if(checklogin==True or tokenschecker==False):
            break
          if(tokens[1] == users[0]):
            if(tokens[2] == users[1]):
              self.activePlayersAndAddresses.append((tokens[1], str(a[0]), a[1]))
              
              # find client that sent this packet and respond 
              for connection in self.connections:
                if(connection.getpeername()[0] == str(a[0])):
                  if(connection.getpeername()[1] == a[1]):
                      connection.send(bytes("login confirmed", 'utf-8'))
                      print(tokens[1]+" login")
                      loginchecker = True
                      break
              break
        if(checklogin==True):
          pass
          #print("you are already logged in")
        if(checklogin==False and loginchecker == False):
          # find client that sent this packet and respond 
          for connection in self.connections:
            if(connection.getpeername()[0] == str(a[0])):
              if(connection.getpeername()[1] == a[1]):
                  connection.send(bytes("Denied. User name or password incorrect.", 'utf-8'))


      #############if we are sending to all users#############
      loggedIn=False
      lengthchecker= False
      if(tokens[0] == "send"):

        #check if sender is logged in
        for connectioniterator in self.activePlayersAndAddresses:
          if(connectioniterator[1] == str(a[0])):
            if(connectioniterator[2] == a[1]):
              senderName = connectioniterator[0]
              loggedIn=True

              # check to see if message length is 1-256 characters
              if((len(formattedMessage)-1)>=1 and (len(formattedMessage)-1)<=256):
                lengthchecker = True
                
                if(tokens[1] == "all"):
                  # send to all users that are logged in
                  print(senderName + ": " + formattedMessage)
                  for connection in self.connections:
                    for x in self.activePlayersAndAddresses:
                      if(x[1]==connection.getpeername()[0]):
                        if(x[2]==connection.getpeername()[1]):              
                          connection.send(bytes((senderName + ": " + formattedMessage), 'utf-8'))
                else:
                  #check to see if user is online
                  for tmp in self.activePlayersAndAddresses:
                    if(tokens[1]==tmp[0]):

                      #send direct message to specified user
                      for connection in self.connections:

                        #find user's address and port
                        if(tmp[1] == connection.getpeername()[0] and tmp[2] == connection.getpeername()[1]):

                          #send message
                          connection.send(bytes((senderName + ": " + formattedMessage), 'utf-8'))
                          print(senderName+" (to " + tokens[1] + "):" + formattedMessage)



        #if user is not logged in
        if(loggedIn==False):

          # find client that sent this packet and respond 
          for connection in self.connections:
            if(connection.getpeername()[0] == str(a[0])):
              if(connection.getpeername()[1] == a[1]):
                  connection.send(bytes("Denied. Please login first.", 'utf-8'))
        
        # if the message is too short or to long
        elif(lengthchecker == False):

           # find client that sent this packet and respond 
          for connection in self.connections:
            if(connection.getpeername()[0] == str(a[0])):
              if(connection.getpeername()[1] == a[1]):
                  connection.send(bytes("Denied. Message must be between 1-256 characters.", 'utf-8'))



      #############if we are viewing the list of active users#############
      loggedIn=False
      serverList = ""
      if(tokens[0] == "who"):

        #check if sender is logged in
        for connectioniterator in self.activePlayersAndAddresses:
          if(connectioniterator[1] == str(a[0])):
            if(connectioniterator[2] == a[1]):
              loggedIn=True
              for temp in self.activePlayersAndAddresses:
                serverList+=temp[0] + ", "
              # find client that sent this packet and respond 
              for connection in self.connections:
                if(connection.getpeername()[0] == str(a[0])):
                  if(connection.getpeername()[1] == a[1]):
                      connection.send(bytes(serverList[:-2], 'utf-8'))
      
      #############if a player makes a decision#############
      if(tokens[0]=='decision'):
        pass
        loggedIn=False
        #check if sender is logged in
        for connectioniterator in self.activePlayersAndAddresses:
          if(connectioniterator[1] == str(a[0])):
            if(connectioniterator[2] == a[1]):
              loggedIn=True
        if(loggedIn == True):
          # check if sender belongs to table
          onTable = False
          for player in self.table_players:
            if(player[0] == str(a[0]) and player[1] == str(a[1])):
              onTable = True
              id = player[2]

        if(loggedIn == True and onTable == True):
          # check if sender has action
          for player in self.table.players:
            if(player.player_id == id):
              if(player.action == True):
                choice = tokens[1]
                if choice == 'bet':
                  amount = int(tokens[2])
                  self.table.process_decision(id, choice, amount)
                  self.table.print_table()
                  self.table.iterate_action()
                if choice == 'call':
                  amount = player.owed - player.money_out
                  self.table.process_decision(id, choice, amount)
                  self.table.print_table()
                  self.table.iterate_action()
                  
                if choice == 'check':
                  self.table.iterate_action()
                  self.table.process_decision(id, choice)
                  self.table.print_table()
                
                if choice == 'fold':
                  # end hand if only one playuer remains
                  active_player_count = 0
                  for plyr in self.table.players:
                    if plyr.status != 'out':
                      active_player_count +=1
                  
                  if active_player_count != 2:
                    self.table.iterate_action()
                  self.table.process_decision(id, choice)
                  self.table.print_table()

      #############if we are starting a game#############
      if(tokens[0] == "start"):
        self.started = True
        initial_action = random.randint(1,len(self.table.players))
        for player in self.table.players:
          if(player.seat_number == initial_action):
            player.action = True
        self.table.deal()


      #############if we are joining a table#############
      loggedIn=False
      if(tokens[0] == "join"):
        buy_in = int(tokens[1])
        #check if sender is logged in
        for connectioniterator in self.activePlayersAndAddresses:
          if(connectioniterator[1] == str(a[0])):
            if(connectioniterator[2] == a[1]):
              loggedIn=True

              #if the table is not full
              if(len(self.table.players)<9):

                #create a new player and append to table list
                plyr_id = connectioniterator[0]
                seat_num = len(self.table.players)+1
                player = Player(plyr_id, seat_num, buy_in, None)
                self.table.players.append(player)
                self.table_players.append((str(a[0]), str(a[1]), plyr_id))
                # send table.players [] data to connections that are on the table



                # send to all users that are logged in and on table
                for connection in self.connections:
                  for x in self.activePlayersAndAddresses:
                    if(x[1]==connection.getpeername()[0]):
                      if(x[2]==connection.getpeername()[1]):
                        for p in self.table.players:
                          if(p.player_id == x[0]):
                            player_list = ""
                            for k in self.table.players:
                              player_list += Player.__str__(k)
                            connection.send(bytes("joined {}{}".format(player.player_id, player_list), 'utf-8'))

              else:
                print("table is full")
        for j in self.table.players:
          print("{} [Stack: {}] (Seat: {})".format(j.player_id, j.stack, j.seat_number))

  #infinitely looping run scope that utilizes threads and our handeler function to accept new connections
  def run(self):
    while True:
      c, a = self.sock.accept()
      cThread = threading.Thread(target = self.handler, args = (c, a))
      cThread.daemon = True
      cThread.start()
      self.connections.append(c)
      print(str(a[0])+ ':' + str(a[1]) +  " connected")
      #self.table.players.append(Player(1, 1, 200, None))
      #for player in self.table.players:
      #  print("Player {}[Stack {}]: {}".format(player.player_id, player.stack, player.hand))

#client object
class Client:

  # instantiate socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  def sendMsg(self, msg):
      self.sock.send(bytes(msg, 'utf-8'))

  def receive_loop(self):
    while True:
      try:
        data = self.sock.recv(1024)
      except:
        print("connection to server was lost")
        break
      if not data:
        break
      print(str(data, 'utf-8'))

      message = str(data, 'utf-8')
      tokens = message.split(' ')

      # format message
      formattedMessage = ""
      x = 0
      for i in tokens:
        if(x!=0 and x!=1):
          formattedMessage+=i+' '
        x+=1
      if tokens[0] == 'Win:':
        self.table.print_all_players()

      if(tokens[0] == "Action:"):
        for player in self.table.players:
          #find player whos turn it is
          if(int(tokens[1]) == player.seat_number):       
            # is that player on this client
            if(player.player_id == self.this_player):  
              print("you have the action {}, Stack: {}".format(player.player_id, player.stack))


      # if cards have been dealt to players
      if(tokens[0] == "Dealt:"):
        #load cards in player objects within client
        for player in self.table.players:
          if(int(tokens[1]) == player.seat_number):
            try:
              weight = int(tokens[2])
            except:
              #deal with face cards
              face_card_weights = {
                'J':11,
                'Q':12,
                'K':13,
                'A':14
              }
              weight = face_card_weights[tokens[2]]
            card1 = Card(tokens[2], tokens[3], weight)
            try:
              weight = int(tokens[4])
            except:
              #deal with face cards
              face_card_weights = {
                'J':11,
                'Q':12,
                'K':13,
                'A':14
              }
              weight = face_card_weights[tokens[4]]
            card2 = Card(tokens[4], tokens[5], weight)
            player.hand = Hand(card1, card2)

      # if someone joins the table
      if(tokens[0] == "joined"):
        self.deck = Deck()
        # create a table
        if self.table == None:
          self.table = ClientTable(self.deck, 9, self.players)
        print("table joined")

        # find player whom client belongs to
        if(self.this_player == ''):
          for c in tokens[1]:
            if(c == '('):
              break
            else:
              self.this_player+= c
        check = 0
        temp_player_id = ""
        temp_stack = ""
        temp_player_seat = 0

        # parse all other player data
        for c in message:
          if(c == ')'):
            check = 0
            tmp_player = Player(temp_player_id, int(temp_player_seat), int(temp_stack), None)
            already_seated = False
            for seated_player in self.table.players:
              if seated_player.player_id == tmp_player.player_id:
                already_seated = True
            if(already_seated == False):
              self.table.players.append(tmp_player)
            temp_player_id = ""
            temp_stack = ""
            temp_player_seat = 0
            continue
          if(c == '('):
            check = 1
            continue
          if(c == ' '):
            continue
          if(c == ',' and check == 1):
            check = 2
            continue
          if(c == ',' and check == 3):
            check = 4
            continue
          if(c == ',' and check == 4):
            check = 5
          if(check == 1):
            temp_player_id += c
          if(check == 2):
            temp_player_seat = c
            check = 3
            continue
          if(check == 4):
            temp_stack += c
          if(check == 5):
            continue
      # for player in players:
      #   if player not in self.table.players:
      #     print("hello")
      #     self.table.players.append(player)
    
        
        
      if tokens[0] == "Decision:":
        temp_player_id = tokens[2]
        choice = tokens[3]

        if choice == 'bet':
          # convert amount to int
          amount = int(tokens[4])
          # increment pot
          self.table.pot += amount
          for player in self.table.players:
            if player.player_id == temp_player_id:
              player.stack -= amount
              player.status = "in (money not owed)"

          self.table.print_all_players()

        if choice == 'call':
          amount = int(tokens[4])
          self.table.pot += amount
          for player in self.table.players:
            if player.player_id == temp_player_id:
              player.stack -= amount
              player.status = "in (money not owed)"
          
          self.table.print_all_players()
        
        if choice == 'check':
          for player in self.table.players:
            if player.player_id == temp_player_id:
              player.status = "in (money not owed)"

          self.table.print_all_players()
        
        if choice == 'fold':
          for player in self.table.players:
            if player == temp_player_id:
              player.status = "out"

  def run_gui(self):
    while True:
      if self.gui_thread_check == True:
        self.gui.mainloop()

  def login(self, username, password):
    msg = "login {} {}".format(username, password)
    self.sendMsg(msg)

  def create_login_view(self):
    #log-in frame
    login_frame = Frame(self.top_frame, width=400, height=600, bg = "#35654d")
    login_frame.place(relx=0.5, rely=0.5, anchor="c")

    lbframe_app_name = LabelFrame(login_frame, bg="#35654d", relief="groove")
    lb_app_name = Label(lbframe_app_name, bg="#35654d", text="Poker App", font="Helvetica 32 bold")
    lb_username = Label(login_frame, bg="#35654d", text="Username:", font="Helvetica 16 bold")
    #ADD validation
    entry_username = Entry(login_frame, width=20)
    lb_password = Label(login_frame, bg="#35654d", text="Password:", font="Helvetica 16 bold")
    entry_password = Entry(login_frame, width=20)
    bttn_register = Button(login_frame, image=self.Images.register, borderwidth=0, bg="#35654d", activebackground="#35654d")
    bttn_log_in = Button(login_frame, image=self.Images.log_in, borderwidth=0, bg="#35654d", activebackground="#35654d", command=lambda:self.login(entry_username.get(), entry_password.get()))
    lb_error_alert = Label(login_frame, bg="#E69394", font="Helvetica 12 bold", fg="#8E282A")
    
    lbframe_app_name.grid(row=0, column=0, columnspan=2, pady=32)
    lb_app_name.pack(anchor="c", padx=10, pady=10)
    lb_username.grid(row=1, column=0, columnspan=2, pady=5)
    entry_username.grid(row=2, column=0, columnspan=2, pady=5)
    lb_password.grid(row=3, column=0, columnspan=2, pady=5)
    entry_password.grid(row=4, column=0, columnspan=2, pady=5)
    bttn_register.grid(row=5, column=0, padx=15, pady=15)
    bttn_log_in.grid(row=5, column=1, padx=15, pady=15)

  #instantiate thread
  def __init__(self, address):
     #GUI window
    self.gui = Tk()
    self.canvas = Canvas()
    self.gui.title("Poker App")
    self.gui.config(bg="#D3D3D3")
    self.gui.geometry("1200x800")
    self.gui.resizable(False, False)
    self.gui.iconbitmap("img/app_icon.ico")
    self.top_frame = Frame(self.gui, width=1200, height=800)
    self.top_frame.pack()
    self.top_frame.config(bg = "#35654d")
     #initialize images
    self.Images = Assets()
    self.Images.register = PhotoImage(file="img/register.png")
    self.Images.log_in = PhotoImage(file="img/log_in.png")
    self.Images.join_table = PhotoImage(file="img/join_table.png")
    self.Images.leave_table = PhotoImage(file="img/leave_table.png")
    self.Images.buy_in = PhotoImage(file="img/buy_in.png")
    self.Images.cash_out = PhotoImage(file="img/cash_out.png")
    self.Images.chips = PhotoImage(file="img/chips.png")
    self.Images.pot = PhotoImage(file="img/pot.png")
    self.Images.card_back = PhotoImage(file="img/card_back.png")
    self.Images.fold = PhotoImage(file="img/fold.png")
    self.Images.check = PhotoImage(file="img/check.png")
    self.Images.call = PhotoImage(file="img/call.png")
    self.Images.bet = PhotoImage(file="img/bet.png")
    self.Images.raise_img = PhotoImage(file="img/raise.png")
    self.Images.reraise= PhotoImage(file="img/re-raise.png")
    self.Images.card_images = initialize_card_images()
    self.create_login_view()


    self.this_player = ''
    self.table = None
    self.deck = None
    self.players = []
    addressAndPort = address.split(':')
    try:
      self.sock.connect((addressAndPort[0], int(addressAndPort[1])))
      iThread = threading.Thread(target=self.receive_loop)
      iThread.daemon = True
      iThread.start()
    except:
      print("attempt to connect to server was unsuccessful")
      exit(0)

    self.gui.mainloop()
          

class Card:
  #constructor
  def __init__(self, value, suit, weight = -1):
    self.value = value
    self.suit = suit
    self.weight = weight

  def __repr__(self):
        return '{' + self.value + ', ' + self.suit + ', ' + str(self.weight) + '}'


#add shuffle
class Deck:
  values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
  suits = ['heart', 'club', 'diamond', 'spade']
  def __init__(self):
    self.cards = []
    for i in self.values:
      for j in self.suits:
        # get card weights
        try:
          # deal with numerical card values
          k = int(i)
        except:
          #deal with face cards
          face_card_weights = {
            'J':11,
            'Q':12,
            'K':13,
            'A':14
          }
          k = face_card_weights[i]
        card = Card(i, j, k)
        self.cards.append(card)
  
  def shuffle(self):
    random.shuffle(self.cards)

  def print_cards_remaining(self):
    for card in self.cards:
      print("{} {} {}".format(card.value, card.suit, card.weight))

class Hand:
  def __init__(self, card1, card2):
    self.card1 = card1
    self.card2 = card2

  def __str__(self):
    return "{} {} {} {}".format(self.card1.value, self.card1.suit, self.card2.value, self.card2.suit)

#add must be able to handle players playing through hands. most code will be here  
class Table:
  cap = 10000
  def __init__(self, deck, total_seats,players = None, button_seat_number = 1):
    self.total_seats = total_seats
    self.button_seat_number = button_seat_number
    self.deck = deck
    self.action = -1
    self.pot = 0
    self.active_players = []
    self.community_cards = []

    if players == None:
      self.players = []
      self.players = players
    else:
      self.players = players
  
  @abstractmethod
  def deal(self):
    pass

  def print_table(self):
    print("Pot: ${}".format(self.pot))
    for player in self.active_players:
      if(player.status != "out"):
        print("Player {} [Stack: ${}]: {}{} {}{}".format(player.player_id, player.stack, player.hand.card1.value, player.hand.card1.suit[0], player.hand.card2.value, player.hand.card2.suit[0]))


  def print_all_players(self):
    print("Pot: ${}".format(self.pot))
    for player in self.players:
      if(True):
        print("Player {} [Stack: ${}]: {}{} {}{}".format(player.player_id, player.stack, player.hand.card1.value, player.hand.card1.suit[0], player.hand.card2.value, player.hand.card2.suit[0]))
    

  def reset_player_round_amounts(self):
    for player in self.active_players:
      player.money_out = 0
      player.owed = 0

  def print_community_cards(self):
    for i in self.community_cards:
      print("{}{}".format(i.value, i.suit[0]))

  def showdown(self):

    # # test data (delete later)
    # test_card1 = Card('A', 'diamond', 14)
    # test_card2 = Card('5', 'spade', 5)
    # hand1 = Hand(test_card1, test_card2)

    # test_card3 = Card('K', 'club', 13)
    # test_card4 = Card('K', 'spade', 13)
    # hand2 = Hand(test_card3, test_card4)

    # test_card5 = Card('9', 'heart', 9)
    # test_card6 = Card('10', 'heart', 10)
    # hand3 = Hand(test_card5, test_card6)

    # test_card7 = Card('4', 'heart', 4)
    # test_card8 = Card('5', 'heart', 4)
    # test_card9 = Card('6', 'heart', 6)
    # test_card10 = Card('7', 'heart', 7)
    # test_card11 = Card('8', 'heart', 8)
    # self.community_cards = [test_card7, test_card8, test_card9, test_card10, test_card11]

    # self.players[0].hand = hand1
    # self.players[1].hand = hand2
    # self.players[2].hand = hand3

    # test (delete this later)
    for player in self.players:
      print("Player {} [Stack: ${}]: {}{} {}{}".format(player.player_id, player.stack, player.hand.card1.value, player.hand.card1.suit[0], player.hand.card2.value, player.hand.card2.suit[0]))

    print("Community Cards: ")
    print(*self.community_cards)    

    # iterate through all players
    for player in self.players:

      # check to see if player folded before showdown
      if(player.status != "out"):

        # assign all of their hand rankings
        player.hand_data+=self.assign_hand_ranking(player)
    
    top_hand_rank = -1
    winning_player = Player()
    tie = False
    for player in self.players:
      if(player.status!="out"):
        if(player.hand_rank == top_hand_rank):
          tie = True
        if(player.hand_rank>top_hand_rank):
          winning_player = player
          top_hand_rank = player.hand_rank
          tie = False
    
    #  if one player has a clear win (higher hand type than all other players)
    if(tie == False):
      # give them the pot
      winning_player.stack += self.pot
      self.pot = 0

      # test (delete this later)
      for player in self.players:
        print("Player {} [Stack: ${}]: {}{} {}{}".format(player.player_id, player.stack, player.hand.card1.value, player.hand.card1.suit[0], player.hand.card2.value, player.hand.card2.suit[0]))
    
    # if  two players tie for best hand type
    else:
      # locate players that tie and load to list
      tie_players = []
      for player in self.players:
        if player.hand_rank == winning_player.hand_rank:
          tie_players.append(player)


      # flush analysis [5]
      if winning_player.hand_rank == 5:
        nested_tie = False
        nested_tie_players = []
        highest_player = None
        highest_weight = -1
        for player in tie_players:
          total_weight = 0
          for card in player.hand_data[1]:
            total_weight += card.weight
          if total_weight>highest_weight:
            highest_weight = total_weight
            highest_player = player
            nested_tie = False
            nested_tie_players = [player]
            continue
          if total_weight == highest_weight:
            nested_tie = True
            nested_tie_players.append(player)
        # if only one player wins, give them the entire pot
        if nested_tie == False:
          highest_player.stack += self.pot
          self.pot = 0
        # if multiple players win, divide the pot and increment their stacks
        else:
          total_tie_players = len(nested_tie_players)
          for player in nested_tie_players:
            player.stack+=(self.pot/total_tie_players)
          self.pot = 0


      # straight analysis (straight, straight flush) [8, 4]
      if winning_player.hand_rank in [8, 4]:
        nested_tie_players = []
        nested_tie = False
        highest_straight = -1
        highest_player = None
        # iterate through tie players
        for player in tie_players:
          # strip hand_data for high value in integer format
          tokenized_hand_data = player.hand_data[0].split(' ')
          for index, token in enumerate(tokenized_hand_data):
            if token == 'high':
              high_card = tokenized_hand_data[index-1]
              try:
                high_value = int(high_card)
              except:
                card_dict = {
                  'J':11,
                  'Q':12,
                  'K':13,
                  'A':14
                }
                high_value = card_dict[high_card]
          if high_value > highest_straight:
            highest_straight = high_value
            highest_player = player
            nested_tie = False
            nested_tie_players = [player]
            continue
          if high_value == highest_straight:
            nested_tie = True
            nested_tie_players.append(player)
        # if only one player wins, give them the entire pot
        if nested_tie == False:
          highest_player.stack += self.pot
          self.pot = 0
        # if multiple players win, divide the pot and increment their stacks
        else:
          total_tie_players = len(nested_tie_players)
          for player in nested_tie_players:
            player.stack+=(self.pot/total_tie_players)
          self.pot = 0
      

      # two pair analysis [2]
      if winning_player.hand_rank == 2:
        highest_player = None
        highest_kicker = -1
        highest_pair = -1
        lowest_pair = -1
        nested_tie_players = []
        nested_tie = False
        for player in tie_players:
          two_pair_values = []
          tokenized_hand_data = player.hand_data[0].split(' ')
          kicker_value = ''
          kicker_int = -1
          high_pair = -1
          low_pair = -1
          for index, token in enumerate(tokenized_hand_data):
            if '\'s' in token:
              two_pair_values.append(token.split('\'')[0])
            if token == 'kicker':
              kicker_value = tokenized_hand_data[index-1]

          # convert kicker to int
          try:
            kicker_int = int(kicker_value)
          except:
            card_dict = {
              'J':11,
              'Q':12,
              'K':13,
              'A':14
            }
            kicker_int = card_dict[kicker_value]

          # convert one pair to int
          pair1 = two_pair_values[0]
          pair2 = two_pair_values[1]
          try:
            pair1_int = int(pair1)
          except:
            card_dict = {
              'J':11,
              'Q':12,
              'K':13,
              'A':14
            }
            pair1_int = card_dict[pair1]

          # convert second pair to int
          try:
            pair2_int = int(pair2)
          except:
            card_dict = {
              'J':11,
              'Q':12,
              'K':13,
              'A':14
            }
            pair2_int = card_dict[pair2]
          
          if pair1_int>pair2_int:
            high_pair = pair1_int
            low_pair = pair2_int
          else:
            high_pair = pair2_int
            low_pair = pair1_int
          
          # check highest pair
          if high_pair>highest_pair:
            highest_player = player
            highest_pair = high_pair
            lowest_pair = low_pair
            highest_kicker = kicker_int
            nested_tie = False
            nested_tie_players = [player]
            continue
          elif high_pair < highest_pair:
            continue

          # check lowest pair
          if low_pair>lowest_pair:
            highest_player = player
            highest_pair = high_pair
            lowest_pair = low_pair
            highest_kicker = kicker_int
            nested_tie = False
            nested_tie_players = [player]
            continue
          elif low_pair<lowest_pair:
            continue

          # check kicker
          if kicker_int > highest_kicker:
            highest_player = player
            highest_pair = high_pair
            lowest_pair = low_pair
            highest_kicker = kicker_int
            nested_tie = False
            nested_tie_players = [player]
            continue

          # tie condition
          elif kicker_int == highest_kicker:
            nested_tie = True
            nested_tie_players.append(player)

        # if only one player wins, give them the entire pot
        if nested_tie == False:
          highest_player.stack += self.pot
          self.pot = 0
        # if multiple players win, divide the pot and increment their stacks
        else:
          total_tie_players = len(nested_tie_players)
          for player in nested_tie_players:
            player.stack+=(self.pot/total_tie_players)
          self.pot = 0

          
      # kicker analysis (four of a kind)  [7]
      if winning_player.hand_rank == 7:
        highest_player = None
        highest_kicker = -1
        nested_tie_players = []
        nested_tie = False
        for player in tie_players:
          tokenized_hand_data = player.hand_data[0].split(' ')
          for index, token in enumerate(tokenized_hand_data):
            if token == 'kicker':
              kicker_value = tokenized_hand_data[index-1]
              try:
                kicker_int = int(kicker_value)
              except:
                card_dict = {
                  'J':11,
                  'Q':12,
                  'K':13,
                  'A':14
                }
                kicker_int = card_dict[kicker_value]
              if kicker_int == highest_kicker:
                nested_tie = True
                nested_tie_players.append(player)
              if kicker_int > highest_kicker:
                highest_player = player
                highest_kicker = kicker_int
                nested_tie = False
                nested_tie_players = [player]
        # if only one player wins, give them the entire pot
        if nested_tie == False:
          highest_player.stack += self.pot
          self.pot = 0
        # if multiple players win, divide the pot and increment their stacks
        else:
          total_tie_players = len(nested_tie_players)
          for player in nested_tie_players:
            player.stack+=(self.pot/total_tie_players)
          self.pot = 0

      # full house analysis (full house) [6]
      if winning_player.hand_rank == 6:
        highest_player = None
        highest_trips = -1
        highest_pair = -1
        nested_tie_players = []
        nested_tie = False
        for player in tie_players:
          trips_pair_values = []
          tokenized_hand_data = player.hand_data[0].split(' ')
          kicker_int = -1
          high_pair = -1
          low_pair = -1
          for index, token in enumerate(tokenized_hand_data):
            if '\'s' in token:
              trips_pair_values.append(token.split('\'')[0])
          # convert trips to int
          trips = trips_pair_values[0]
          pair = trips_pair_values[1]
          try:
            trips_int = int(trips)
          except:
            card_dict = {
              'J':11,
              'Q':12,
              'K':13,
              'A':14
            }
            trips_int = card_dict[trips]
          pair_int=-1
          # convert pair to int
          try:
            pair_int = int(pair)
          except:
            card_dict = {
              'J':11,
              'Q':12,
              'K':13,
              'A':14
            }
            pair_int = card_dict[pair]
          # check trips
          if trips_int > highest_trips:
            highest_player = player
            highest_trips = trips_int
            highest_pair = pair_int
            nested_tie = False
            nested_tie_players = [player]
            continue
          if trips_int == highest_trips:
            if pair_int > highest_pair:
              highest_player = player
              highest_trips = trips_int
              highest_pair = pair_int
              nested_tie = False
              continue
              nested_tie_players = [player]
            if pair_int == highest_pair:
              nested_tie = True
              nested_tie_players.append(player)
        # if only one player wins, give them the entire pot
        if nested_tie == False:
          highest_player.stack += self.pot
          self.pot = 0
        # if multiple players win, divide the pot and increment their stacks
        else:
          total_tie_players = len(nested_tie_players)
          for player in nested_tie_players:
            player.stack+=(self.pot/total_tie_players)
          self.pot = 0
        
      # high card analysis (high card, pair, three of a kind) [0, 1, 3]
      if winning_player.hand_rank == 0:
        highest_weight = -1
        highest_player = None
        nested_tie = False
        nested_tie_players = []
        for player in tie_players:
          total_weight = 0
          for card in player.hand_data[1]:
            total_weight += card.weight
          if total_weight > highest_weight:
            highest_player = player
            highest_weight = total_weight
            nested_tie = False
            nested_tie_players = [player]
            continue
          if total_weight == highest_weight:
            nested_tie = True
            nested_tie_players.append(player)
        # if only one player wins, give them the entire pot
        if nested_tie == False:
          highest_player.stack += self.pot
          self.pot = 0
        # if multiple players win, divide the pot and increment their stacks
        else:
          total_tie_players = len(nested_tie_players)
          for player in nested_tie_players:
            player.stack+=(self.pot/total_tie_players)
          self.pot = 0
      
      if winning_player.hand_rank in [1,3]:
        highest_pair = -1
        highet_weight = -1
        highest_player = None
        nested_tie = False
        nested_tie_players = []
        for player in tie_players:
          total_weight = 0
          tokenized_hand_data = player.hand_data[0].split(' ')
          for index, token in enumerate(tokenized_hand_data):
            if '\'s' in token:
              pair = token.split('\'')[0]
          try:
            int_pair = int(pair)
          except:
            card_dict = {
              'J':11,
              'Q':12,
              'K':13,
              'A':14
            }
            int_pair = card_dict[pair]
          for card in player.hand_data[1]:
            total_weight+=card.weight
          
          if int_pair > highest_pair:
            highest_pair = int_pair
            highest_weight = total_weight
            highest_player = player
            nested_tie = False
            nested_tie_players = [player]
            continue
          if int_pair == highest_pair:
            if total_weight > highest_weight:
              highest_pair = int_pair
              highest_weight = total_weight
              highest_player = player
              nested_tie = False
              nested_tie_players = [player]
              continue
            if total_weight == highest_weight:
              nested_tie = True
              nested_tie_players.append(player)
        # if only one player wins, give them the entire pot
        if nested_tie == False:
          highest_player.stack += self.pot
          self.pot = 0
        # if multiple players win, divide the pot and increment their stacks
        else:
          total_tie_players = len(nested_tie_players)
          for player in nested_tie_players:
            player.stack+=(self.pot/total_tie_players)
          self.pot = 0

    # test (delete this later)
    for player in self.players:
      print("Player {} [Stack: ${}]: {}{} {}{}".format(player.player_id, player.stack, player.hand.card1.value, player.hand.card1.suit[0], player.hand.card2.value, player.hand.card2.suit[0]))

  # helper function
  @staticmethod
  def find_high_cards(all_cards, x, excluded_value):
    # default to high card
    high = ''
    high_cards = []
    count = 0
    for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']:
      for card in all_cards:

        #start condition
        if(high == '' and count == 0 and card.value == val and val != excluded_value):
          high = card.value
          count += 1
          high_cards.append(card)
          continue
        
        
        if(card.value == val and val != excluded_value):
          count +=1
          high_cards.append(card)
          if(count == x):
            return high_cards

  #input: table.communitycards, player.hand
  #output: hand rank (royal flush, pair of Aces king kicker, straight to 9, 2s full of threes, ace high flush,)
  def assign_hand_ranking(self, player):
    all_cards = []
    all_cards.append(player.hand.card1)
    all_cards.append(player.hand.card2)
    for card in self.community_cards:
      all_cards.append(card)

    all_cards.sort(key=lambda x: x.weight)

    #print(all_cards)

    #good
    # check for royal flush
    for suit in Deck.suits:
      suit_live = True
      for val in ['10','J','Q','K','A']:
        if(suit_live == True):
          suit_live = False
          for card in all_cards:
            if(card.value == val and card.suit == suit and card.value == 'A'):
              player.hand_rank = 9
              return ["Royal Flush {}".format(card.suit)]
            if(card.value == val and card.suit == suit):
              suit_live = True

    #good
    # check for straight flush
    for suit in Deck.suits:
      count = 0
      high = ''
      for val in ['K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2', 'A']:
        card_found = False
        for card in all_cards:
          if(card_found ==True):
            break
          if(card.value == val and card.suit == suit and count == 0):
            high = card.value
            card_found = True
            count += 1
            continue
          if(card.value == val and card.suit == suit):
            count += 1
            card_found = True
            if(count == 5):
              player.hand_rank = 8
              return ["Straight Flush {} high".format(high)]
            continue
        if(card_found == False):
          count = 0
          high = ''

              
    # good
    # check for 4 of a kind
    for card in all_cards:
      pair_counter = 0
      for i in all_cards:
        if(card.value == i.value):
          pair_counter += 1
          if(pair_counter == 4):
            kicker_weight = 0
            for j in all_cards:
              if(kicker_weight < j.weight):
                kicker = j
                kicker_weight = j.weight

            player.hand_rank = 7
            return ["4 of a kind ({}'s) {} kicker".format(card.value, kicker.value)]
            #return kicker
    
    # done
    # check for full house
    trips = ''
    pair = ''

    # find three of a kind
    for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']:
      pair_counter = 0
      for card in all_cards:
        if (card.value == val):
          pair_counter += 1
          if(pair_counter == 3):
            trips = card.value
    
    # find pair
    for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']:
      pair_counter = 0
      for card in all_cards:
        if(card.value == trips):
          continue
        if (card.value == val):
          pair_counter += 1
          if(pair_counter == 2):
            pair = card.value

    if(trips != '' and pair != ''):
      player.hand_rank = 6
      return ["Full House {}'s full of {}'s".format(trips, pair)]

    #done
    # check for flush
    for suit in Deck.suits:
      high = ''
      flush_cards = []
      count = 0
      for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']:
        for card in all_cards:

          #start condition
          if(high == '' and count == 0 and card.suit == suit and card.value == val):
            high = card.value
            count += 1
            flush_cards.append(card)
            continue
          
          
          if(card.suit == suit and card.value == val):
            count +=1
            flush_cards.append(card)

            # stop condition
            if(count == 5):
              player.hand_rank = 5
              return ["Flush {} high".format(high), flush_cards]




    #done
    # check for straight
    count = 0
    high = ''
    for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2', 'A']:
      card_found = False
      for card in all_cards:
        if(card_found ==True):
          break

        # start condition
        if(card.value == val and count == 0):
          high = card.value
          card_found = True
          count += 1
          continue
        if(card.value == val):
          count += 1
          card_found = True

          # stop condition
          if(count == 5):
            player.hand_rank = 4
            return ["Straight {} high".format(high)]
          continue
        
      if(card_found == False):
        count = 0
        high = ''

    # done     
    # check for 3 of a kind
    for card in all_cards:
      pair_counter = 0
      for i in all_cards:
        if(card.value == i.value):
          pair_counter += 1
          if(pair_counter == 3):
            player.hand_rank = 3
            return ["3 of a kind {}'s".format(card.value), self.find_high_cards(all_cards, 2, card.value)]
            

    # check for 2 pair
    pair1 = ''
    pair2 = ''

    # find pair 1
    for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']:
      pair_counter = 0
      for card in all_cards:
        if (card.value == val):
          pair_counter += 1
          if(pair_counter == 2):
            pair1 = card.value
    
    # find pair 2
    for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']:
      pair_counter = 0
      for card in all_cards:
        if(card.value == pair1):
          continue
        if (card.value == val):
          pair_counter += 1
          if(pair_counter == 2):
            pair2 = card.value



    if(pair1 != '' and pair2 != ''):
      for val in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']:
        for card in all_cards:
          if (card.value == val and card.value != pair1 and card.value != pair2):
            kicker = card
            player.hand_rank = 2
            return ["Two Pair {}'s and {}'s {} kicker".format(pair1, pair2, kicker.value)]

    # done
    # check for pair
    for card in all_cards:
      pair_counter = 0
      for i in all_cards:
        if(card.value == i.value):
          pair_counter += 1
          if(pair_counter == 2):
            player.hand_rank = 1
            return ["Pair of {}'s".format(card.value), self.find_high_cards(all_cards, 3, card.value)]

    #done
    # default to high card
    high_cards = self.find_high_cards(all_cards, 5, '')
    player.hand_rank = 0
    return ["High card {}".format(high_cards[0].value), high_cards]


class ServerTable(Table):
  def __init__(self, deck, connections,  total_seats,players = None, button_seat_number = 1):
    super().__init__(deck, total_seats, players, button_seat_number)
    self.connections = connections
    self.betting_rounds = ["preflop", "flop", "turn", "river"]
    self.current_betting_round = ""

  def iterate_action(self):
    active_player_list = []
    for player in self.players:
      if player.status != "out":
        active_player_list.append(player)

    for index, player in enumerate(active_player_list):
      # find playter who just made a decision
      if player.action == True:
        # take action away from client who jsut made a decision
        for pl in self.players:
          if pl.player_id == player.player_id:
            pl.action = False

        player.action = False
        # give action to next player that is not out
        if((index+1) <= len(active_player_list)-1):
          for p in self.players:
            if p.player_id == active_player_list[index+1].player_id:
              p.action = True
              self.send_action()
              return
        else:
          for p in self.players:
            if p.player_id == active_player_list[0].player_id:
              p.action = True
              self.send_action()
              return

  def is_round_over(self):
    for player in self.players:
      if(player.status == "in (money owed)" or player.status == "starting round"):
        return False
    return True
  
  def increment_betting_round(self):
    for index, rnd in enumerate(self.betting_rounds):
      if rnd == self.current_betting_round:
        if rnd != 'river':
          self.current_betting_round = self.betting_rounds[index + 1]
          break
        else:
          self.current_betting_round = 'showdown'
    
    if self.current_betting_round == 'flop':
      self.flop()
    
    if self.current_betting_round == 'turn':
      self.turn()
    
    if self.current_betting_round == 'river':
      self.river()
    
    if self.current_betting_round == 'showdown':
      print("Showdown")
      self.showdown()


  def process_decision(self, id, choice, amount = 0):
    for player in self.players:
      if player.player_id == id:
        if choice == 'bet':
          self.pot += amount
          player.stack -= amount
          player.money_out += amount
          player.status = "in (money not owed)"
          # set owed for other players
          for plyr in self.players:
            if(plyr == player):
              continue
            if(plyr.status != "out"):
              plyr.owed = player.money_out
              plyr.status = "in (money owed)"
          server_response = "Decision: Player {} {} {}".format(id, choice, amount)
          for connection in self.connections:
            connection.send(bytes(server_response, 'utf-8'))

        if choice == 'check':
          player.status = "in (money not owed)"
          server_response = "Decision: Player {} {}".format(id, choice)
          for connection in self.connections:
            connection.send(bytes(server_response, 'utf-8'))
          if(self.is_round_over() == True):
            print("{} betting round is over".format(self.current_betting_round))
            self.increment_betting_round()

        if choice == 'fold':
          player.status = "out"
          active_players = []
          # count how many players remain in hand
          for plyr in self.players:
            if plyr.status != 'out':
              active_players.append(plyr)
          # if only one player remains, they win without showdown
          if len(active_players) == 1:
            active_players[0].stack += self.pot
            server_response = "Decision: Player {} {}\nWin: Player {} wins ${}".format(id, choice, active_players[0].player_id, self.pot)
            for connection in self.connections:
              connection.send(bytes(server_response, 'utf-8'))
            self.pot = 0
          else:
            server_response = "Decision: Player {} {}".format(id, choice)
            for connection in self.connections:
              connection.send(bytes(server_response, 'utf-8'))
            if(self.is_round_over() == True):
              print("{} betting round is over".format(self.current_betting_round))
              self.increment_betting_round()

        if choice == 'call':
          for player in self.players:
            if player.player_id == id:
              self.pot += amount
              player.stack -= amount
              player.owed = 0
              player.money_out += amount
              player.status = "in (money not owed)"

          server_response = "Decision: Player {} {} {}".format(id, choice, amount)
          for connection in self.connections:
            connection.send(bytes(server_response, 'utf-8'))
          if(self.is_round_over() == True):
            print("{} betting round is over".format(self.current_betting_round))
            self.increment_betting_round()

  def send_action(self):
  
    # find player whos turn it is
    for player in self.players:
      if player.action == True:
        for connection in self.connections:
          connection.send(bytes("Action: {}".format(player.seat_number),'utf-8'))
        break
    # tell all clients whos turn it is
  
  def preflop(self):
    self.current_betting_round = 'preflop'
    # add all players that are dealt in to the active players list
    for player in self.players:
      player.status = "starting round"
      self.active_players.append(player)
    #self.print_table()
    self.send_action()
  
  def flop(self):
    self.community_cards.append(self.deck.cards[0])
    self.community_cards.append(self.deck.cards[1])
    self.community_cards.append(self.deck.cards[2])

    self.deck.cards.remove(self.deck.cards[0])
    self.deck.cards.remove(self.deck.cards[1])
    self.deck.cards.remove(self.deck.cards[2])

    server_response = "Flop: {}{} {}{} {}{}".format(self.community_cards[0].value, self.community_cards[0].suit[0], self.community_cards[1].value, self.community_cards[1].suit[0], self.community_cards[2].value, self.community_cards[2].suit[0])

    for connection in self.connections:
      connection.send(bytes(server_response, 'utf-8'))
    
    time.sleep(0.1)

    self.reset_player_round_amounts()
    self.active_players = []
    for player in self.players:
      if player.status != "out":
        player.status = "starting round"
        self.active_players.append(player)
    self.send_action()

  def turn(self):
    self.reset_player_round_amounts()

    self.community_cards.append(self.deck.cards[0])
    self.deck.cards.remove(self.deck.cards[0])

    server_response = "Turn: {}{} {}{} {}{} {}{}".format(self.community_cards[0].value, self.community_cards[0].suit[0], self.community_cards[1].value, self.community_cards[1].suit[0], self.community_cards[2].value, self.community_cards[2].suit[0], self.community_cards[3].value, self.community_cards[3].suit[0])

    for connection in self.connections:
      connection.send(bytes(server_response, 'utf-8'))
    
    time.sleep(0.1)

    self.reset_player_round_amounts()
    self.active_players = []
    for player in self.players:
      if player.status != "out":
        player.status = "starting round"
        self.active_players.append(player)
    self.send_action()
  
  def river(self):
    self.reset_player_round_amounts()
    #self.print_table()

    self.community_cards.append(self.deck.cards[0])
    self.deck.cards.remove(self.deck.cards[0])

    server_response = "River: {}{} {}{} {}{} {}{} {}{}".format(self.community_cards[0].value, self.community_cards[0].suit[0], self.community_cards[1].value, self.community_cards[1].suit[0], self.community_cards[2].value, self.community_cards[2].suit[0], self.community_cards[3].value, self.community_cards[3].suit[0], self.community_cards[4].value, self.community_cards[4].suit[0])

    for connection in self.connections:
      connection.send(bytes(server_response, 'utf-8'))
    
    time.sleep(0.1)

    self.reset_player_round_amounts()
    self.active_players = []
    for player in self.players:
      if player.status != "out":
        player.status = "starting round"
        self.active_players.append(player)
    self.send_action()
  
  def deal(self):
    # shuffle and deal
    self.deck.shuffle()
    seats_and_hands = []
    for player in self.players:
      player.hand = Hand(self.deck.cards[0], self.deck.cards[len(self.players)])
      self.deck.cards.remove(self.deck.cards[0])
      self.deck.cards.remove(self.deck.cards[len(self.players)-1])
      seats_and_hands.append((player.seat_number, Hand.__str__(player.hand)))
    for connection in self.connections:
      for i in seats_and_hands:
        connection.send(bytes("Dealt: {} {}".format(i[0], i[1]), 'utf-8'))
        time.sleep(0.1)
    
    self.preflop()

class ClientTable(Table):
  def __init__(self, deck, total_seats,players = None, button_seat_number = 1):
    super().__init__(deck, total_seats, players, button_seat_number)
  
  def decision(self):
  
    # circle action around and track decisions, until stop conditions are met
    while(True):
      for player in self.active_players:
        # stop condition
        stop = True
        for plyr in self.active_players:
          if(plyr.status == "starting round"):
            stop = False
          if(plyr.status == "in (money owed)"):
            stop = False
        
        if(stop == True):
          print("betting round is over")
          for plyr in self.active_players:
            if(plyr.status == "in (money not owed)"):
              plyr.status = "starting round"
          return

        if(player.status == "out"):
          continue
        self.print_table()
        
        # make a decision 
        choice, amount = player.handle_action()

        # change their status to folded
        if(choice == "fold"):
          player.status = "out"
        if(choice == "bet"):
          self.pot += amount
          # change players amount owed
          for plyr in self.active_players:
            if(plyr == player):
              continue
            if(plyr.status != "out"):
              plyr.owed = player.money_out
              plyr.status = "in (money owed)"
        if(choice == "call"):
          self.pot += amount
        if(choice == "check"):
          pass
  
  def preflop(self):
    # add all players that are dealt in to the active players list
    for player in self.players:
      player.status = "starting round"
      self.active_players.append(player)
    #self.print_table()
    self.decision()
  
  def flop(self):
    self.reset_player_round_amounts()

    # deal 3 community cards
    self.community_cards.append(self.deck.cards[0])
    self.community_cards.append(self.deck.cards[1])
    self.community_cards.append(self.deck.cards[2])
    self.deck.cards.remove(self.deck.cards[2])
    self.deck.cards.remove(self.deck.cards[1])
    self.deck.cards.remove(self.deck.cards[0])

    self.print_community_cards()

    self.decision()

  def turn(self):
    self.reset_player_round_amounts()

    self.community_cards.append(self.deck.cards[0])
    self.deck.cards.remove(self.deck.cards[0])

    self.print_community_cards()


    #self.print_table()
    self.decision()
  
  def river(self):
    self.reset_player_round_amounts()
    #self.print_table()

    self.community_cards.append(self.deck.cards[0])
    self.deck.cards.remove(self.deck.cards[0])


    self.print_community_cards()

    self.decision()

    # # # delete this later (testing hand assign hand rankings function)
    # for player in self.players:
    #   player.hand.card1 = Card('8', 'diamond',8)
    #   player.hand.card2 = Card('3', 'diamond',3)

    #   self.community_cards[0] = Card('A', 'heart', 14)
    #   self.community_cards[1] = Card('5', 'spade', 5)
    #   self.community_cards[2] = Card('A', 'diamond', 14)
    #   self.community_cards[3] = Card('8', 'heart', 8)
    #   self.community_cards[4] = Card('9', 'spade', 9)

    #   print('{}'.format(self.assign_hand_ranking(player)))
  
  def deal(self):
    # shuffle and deal
    self.deck.shuffle()
    for player in self.players:
      # change all players status
      player.status = "in"

      player.hand = Hand(self.deck.cards[0], self.deck.cards[len(self.players)])
      self.deck.cards.remove(self.deck.cards[0])
      self.deck.cards.remove(self.deck.cards[len(self.players)-1])
    
    # add condition to see if everyone folded ex: if len(active_players > 1)
    self.preflop()
    self.flop()
    self.turn()
    self.river()
    self.showdown()
  
  




# add rebuy(amount)
class Player:
  num_of_players = 0
  def __init__(self, player_id = -1, seat_number = -1, stack = -1, hand = None):
    self.action = False
    self.player_id = player_id
    self.seat_number = seat_number
    self.stack = stack
    self.hand = hand
    self.status = "out" # out (folded), starting round, in (money owed), in (money not owed), all in
    self.owed = 0
    self.money_out = 0
    self.hand_rank = 0
    self.hand_data = []
  
  # check to see if player has action (is it my turn?) if they do have the action, give them the ability to check, bet, fold, call, etc
  def handle_action(self):
    # check status
    if(self.status == "in (money not owed)" or self.status == "starting round" or self.status == "in (money owed)"):
      # player decision
      choice = input("Player {} has the action: ".format(self.player_id))
      # if player checks
      x = -1
      if(choice == "call"):
        return "call",self.call()
      if(choice[0]=='c'):
        return "check",self.check()
      if(choice[0]=='f'):
        return "fold",self.fold()
      if(choice[0]=='b'):
        c, amount = choice.split(' ')
        self.bet(amount)
        return "bet",int(amount)
      #input to test gui
      if(choice =='gui'):
        gui()
      else:
        return 0
    # if all in or out (folded), skip player
    # if(self.status == "all in" or self.status == "out"):
     
    # pass
    
    else:
      return 0
  
  def check(self):
    print("Player {} checks".format(self.player_id))
    self.status = "in (money not owed)"
    return 0
  
  def fold(self):
    self.status = "out"
    print("Player {} folds".format(self.player_id))
    return 'f'

  def bet(self, amount):
    bet = int(amount)
    # check if player stack is less than owed plus attempted bet
    # if (self.stack < self.owed+bet)
      #  return "[insert faiure]"
    print("Player {} bets {}".format(self.player_id, amount))
    #change player stack
    self.stack -= int(amount)
    #change player owed
    self.money_out += bet
    #change player status
    if (self.stack == 0):
      self.status = "all in"
    else:
      self.status = "in (money not owed)"
    return bet
    
  def call(self):
    amount = self.owed - self.money_out
    #change player stack
    self.stack -= amount
    #change owed
    self.owed = 0
    self.money_out += amount
    #change status
    print("Player {} calls {}".format(self.player_id, amount))
    if (self.stack == 0):
      self.status = "all in"
    else:
      self.status = "in (money not owed)"
    return amount
  
  def __str__(self):
    return "({}, {}, {}, {})".format(self.player_id, self.seat_number, self.stack, self.hand)

class PlayerGUI:
  def __init__(self, room_frame, x, y, img_chips, img_card_back, img_buy_in):
    #frame for each player
    player_frame = Frame(room_frame, bg="#505b62", width=104, height=140)
    player_frame.place(x=x, y=y)

    card_one_frame = return_card_frame(player_frame, "gray")
    card_two_frame = return_card_frame(player_frame, "gray")
    
    card_one_frame.grid(row=0,column=0)
    card_two_frame.grid(row=0,column=1)

    lb_img_chips = Label(player_frame, bg="#505b62", image=img_chips)
    lb_img_chips.grid(row=2, column=0)

    #player frame widgets
    #if player is seated, display player info
    #ADD if player is seated AND seat is empty, display empty seat
    player_is_seated = True
    if player_is_seated == True:
      lb_img_card_one = Label(card_one_frame, bg="#505b62", image=img_card_back)
      lb_img_card_two = Label(card_two_frame, bg="#505b62", image=img_card_back)
      lb_player_name = Label(player_frame, bg="#505b62", text="Test Player Name", font="Helvetica 10 bold")
      lb_player_stack = Label(player_frame, bg="#505b62", text="$200", font="Helvetica 10 bold")
      lb_player_action = Label(player_frame, bg="#505b62", text="Action", font="Helvetica 10 bold")

      lb_player_name.grid(row=1, column=0, columnspan=2)
      lb_player_stack.grid(row=2, column=1)
      lb_player_action.grid(row=3, column=1)

      lb_img_card_one.pack()
      lb_img_card_two.pack()
    else:
      #player is not seated, allow buy-in
      bttn_buy_in = Button(player_frame, image=img_buy_in, borderwidth=0, bg="#505b62", activebackground="#505b62")
      entry_buy_in = Entry(player_frame, width=6, bg="#505b62")
      buy_in_min = 10
      entry_buy_in.insert(0, str(buy_in_min))
      #ADD validation and dynamic value if player bank < max buyin, buy_in_max = bank 
      buy_in_max = 200
      buy_in_range = "$" + str(buy_in_min) + "-" + "$" + str(buy_in_max)
      lb_buy_in_range = Label(player_frame, bg="#505b62", text=buy_in_range, font="Helvetica 10 bold")
      
      bttn_buy_in.grid(row=1, column=0, columnspan=2)
      entry_buy_in.grid(row=2, column=1)
      lb_buy_in_range.grid(row=3, column=1)
    lb_player_seat = Label(player_frame, bg="#505b62", text="Seat #")
    lb_player_seat.grid(row=3, column=0)

class Assets:
  pass

def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return db

def initialize_card_images():
  card_images = {}
  suits = ("h", "d", "c", "s")
  for suit in suits:
    for n in range(1,14):
      card_name = suit+str(n)
      file_string = "img/cards/" + card_name + ".png"
      card_images[card_name] = PhotoImage(file=file_string)
  return card_images

def return_card_frame(parent, color):
  if color == "gray":
    #room frame background color (gray)
    bg = "#505b62"
  else:
    #table frame background color (felt green)
    bg = "#35654d"
  card_frame = LabelFrame(parent, bg=bg, width=50, height=68, borderwidth=2, relief="groove")
  return card_frame

def clear_frame(frame):
  for widget in frame.winfo_children():
    widget.destroy()

def validate_username(username):

    # Validate username length
    len_username = len(username)
    if len_username < 4 or len_username > 32:
      return "length"

    # Validate username characters
    if not username.isalnum():
      return "alphanumeric"

    # Validated username
    else: 
      return "validated"

def validate_password(password):

  # Validate password length
  len_password = len(password)
  if len_password < 8 or len_password > 32:
    return "length"
  
  # Validate password characters
  accepted_special_characters = ["@", "%", "+", "/", "'", "!", "#", "$", "^", "?", ":", ",", ")", "(", "{", "}", "[", "]", "`", "-", "_", "."]
  # Remove any accepted special characters from password
  temp_password = password
  for char in accepted_special_characters:
    temp_password = temp_password.replace(char, "")
  # Check if resulting password is alphanumeric
  if not temp_password.isalnum():
    return "character"
  
  # Validated password
  else:
    return "validated"

def authenticate_password(username, password):

  # Retrieve stored key and salt from database
  login_info = retrieve_login_info(username)

  # If None returned, there is no user with that username in the database
  if login_info == None:
    return "nouser"

  key, salt = login_info
  key = bytes(key)

  # Generate new key based on submitted password
  new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=128)

  if new_key == key:
    return "authenticated"
  else:
    return "wrong"

def set_login_error(lb_error_alert, entry_type, error_type):

  if entry_type == "username":
    if error_type == 'length':
      error_text = "Username must be between 4 and 32 characters"
    if error_type == 'alphanumeric':
      error_text = "Username must be alphanumeric"

  if entry_type == "password":
    if error_type == 'length':
      error_text = "Password must be between 8 and 32 characters"
    if error_type == 'character':
      error_text = "Password must only use letters, numbers, and certain special characters"

  if entry_type == "authentication":
    if error_type == "nouser":
      error_text = "There is no user with that username"
    if error_type == "wrong":
      error_text = "Incorrect password"

  #set error label text and place on grid
  lb_error_alert.config(text = error_text)
  lb_error_alert.grid(row=6, column=0, columnspan=2, padx=15, pady=15, ipadx=3, ipady=3)

def check_login(username, password, top_frame, lb_error_alert, Images):

  username_error = validate_username(username)
  if username_error == "validated":

    #Remove any previous error label due to username validation failure
    lb_error_alert.grid_forget()

    #Validate submitted password
    password_error = validate_password(password)
    if password_error == "validated":
      
      #Remove any previous error label due to password validation failure
      lb_error_alert.grid_forget()

      authentication_error = authenticate_password(username, password)
      if authentication_error == "authenticated":
        create_dashboard_view(top_frame, Images)
      
      # Authentication failed
      else:
        set_login_error(lb_error_alert, "authentication", authentication_error)

    # Password failed validation
    else:
      set_login_error(lb_error_alert, "password", password_error)

  # Username failed validation
  else:
    set_login_error(lb_error_alert, "username", username_error)

def retrieve_login_info(username):
  conn = None
  try:
        params = config()
        conn = psycopg2.connect(**params)

        cur = conn.cursor()

        sql = '''SELECT password_key, password_salt
	            FROM public.users WHERE LOWER(username)=LOWER(%s);'''

        cur.execute(sql, (username,))
        login_info = cur.fetchone()

        conn.close()

        return login_info
        
  except (Exception, psycopg2.DatabaseError) as error:
      print(error)
  finally:
      if conn is not None:
          conn.close()
      

def create_dashboard_view(top_frame, Images):
  clear_frame(top_frame)
  top_frame.config(bg="#ffffff")
  #Label(top_frame, bg="#35654d", text="Poker App", font="Helvetica 32 bold").pack()
  bttn_join_table = Button(top_frame, image=Images.join_table, command=lambda:create_table_view(top_frame, Images))
  bttn_join_table.place(relx=0.5, rely=0.5, anchor="c")

def create_table_view(top_frame, Images):
  clear_frame(top_frame)
   #window widgets
  top_frame.config(bg="")
  #room frame
  room_frame = Frame(top_frame, bg="#505b62", width=1200, height=600)
  room_frame.place(x=0, y=0, anchor="nw")

  #table frame
  table_frame = Canvas(room_frame, bg="#505b62", width=800, height=300, highlightthickness=0)
  table_frame.create_oval(0, 0, 800, 300, outline = "#65354d", fill = "#35654d",width = 2)
  table_frame.place(relx=0.5, rely=0.5, anchor="c")

  lb_img_pot = Label(table_frame, bg="#35654d", image=Images.pot)
  lb_pot = Label(table_frame, bg="#35654d", text="$1000", font="Helvetica 16 bold")

  lb_img_pot.place(x=400, y=80, anchor="c")
  lb_pot.place(x=400, y=120, anchor="c")

  #Display community cards
  community_cards_frame = Frame(table_frame, bg="#35654d", width=300, height=72)
  community_cards_frame.place(x=400, y=185, anchor="c")

  lbframe_community_card1 = return_card_frame(community_cards_frame, "green")
  lbframe_community_card2 = return_card_frame(community_cards_frame, "green")
  lbframe_community_card3 = return_card_frame(community_cards_frame, "green")
  lbframe_community_card4 = return_card_frame(community_cards_frame, "green")
  lbframe_community_card5 = return_card_frame(community_cards_frame, "green")

  lbframe_community_card1.grid(row=0, column=0)
  lbframe_community_card2.grid(row=0, column=1)
  lbframe_community_card3.grid(row=0, column=2)
  lbframe_community_card4.grid(row=0, column=3)
  lbframe_community_card5.grid(row=0, column=4)

  img_community_card1 = Label(lbframe_community_card1, bg="#35654d", image=Images.card_images["d3"])
  img_community_card2 = Label(lbframe_community_card2, bg="#35654d", image=Images.card_images["h13"])
  img_community_card3 = Label(lbframe_community_card3, bg="#35654d", image=Images.card_images["s1"])
  img_community_card4 = Label(lbframe_community_card4, bg="#35654d", image=Images.card_images["s6"])
  img_community_card5 = Label(lbframe_community_card5, bg="#35654d", image=Images.card_images["c11"])

  img_community_card1.pack()
  img_community_card2.pack()
  img_community_card3.pack()
  img_community_card4.pack()
  img_community_card5.pack()

  #Coordinates of each player frame
  coord_list = [(548, 458), (268, 438), (48, 258), (190, 40), (428, 6), (668, 6), (906, 40), (1048, 258), (828, 438)] 

  #Loop to create frame for each player
  player_gui_list = []
  for x, y in coord_list:
    player_gui_list.append(PlayerGUI(room_frame, x, y, Images.chips, Images.card_back, Images.buy_in))
  
  #Chat frame
  chat_frame = Frame(top_frame, bg="#ffffff", width=796, height=196)
  chat_frame.place(x=2, y=798, anchor="sw")

  #Frame for action buttons
  action_frame = Frame(top_frame, width=396, height=196)
  action_frame.place(x=1198, y=798, anchor="se")

  is_player_turn = False
  #if player's turn allow action buttons
  if is_player_turn:
    action_status = NORMAL
  #else disable action buttons
  else:
    action_status = DISABLED

  bttn_action1 = Button(action_frame, image=Images.fold, borderwidth=0, state=action_status)

  table_bet_status = 0
  #if no bets yet: show check/bet buttons
  if table_bet_status == 0:
    action_2 = Images.check
    action_3 = Images.bet
  #if one bet on table: raise instead of bet button
  if table_bet_status == 1:
    action_2 = Images.call
    action_3 = Images.raise_img
  #if someone has raised: re-raise button instead of raise
  if table_bet_status == 2:
    action_2 = Images.call
    action_3 = Images.reraise

  bttn_action2 = Button(action_frame, image=action_2, borderwidth=0, state=action_status)
  bttn_action3 = Button(action_frame, image=action_3, borderwidth=0, state=action_status)
  # Bet/Raise/Re-raise amount Entry box
  #ADD validation, dynamic min/max values
  entry_bet_amount = Entry(action_frame, width=6)
  bet_min = 2
  bet_max = 200
  entry_bet_amount.insert(0, str(bet_min))
  bet_range = "$" + str(bet_min) + "-" + "$" + str(bet_max)
  lb_bet_range = Label(action_frame, text=bet_range, font="Helvetica 10 bold")

  player_is_seated = True
  #if player is seated: show cash out button
  if player_is_seated == True:
    action_4 = Images.cash_out
  #else player is not seated: show leave table button
  else:
    action_4 = Images.leave_table
  bttn_action4 = Button(action_frame, image=action_4, borderwidth=0)

  bttn_action1.place(x=100, y=25, anchor="n")
  bttn_action2.place(x=200, y=25, anchor="n")
  bttn_action3.place(x=300, y=25, anchor="n")
  bttn_action4.place(x=200, y=171, anchor="s")
  entry_bet_amount.place(x=300, y=70, anchor="n")
  lb_bet_range.place(x=300, y= 100, anchor="n")

def gui():
  #GUI window
  gui = Tk()
  canvas = Canvas()
  gui.title("Poker App")
  gui.config(bg="#D3D3D3")
  gui.geometry("1200x800")
  gui.resizable(False, False)
  gui.iconbitmap("img/app_icon.ico")

  top_frame = Frame(gui, width=1200, height=800)
  top_frame.pack()

  #initialize images
  Images = Assets()
  Images.register = PhotoImage(file="img/register.png")
  Images.log_in = PhotoImage(file="img/log_in.png")
  Images.join_table = PhotoImage(file="img/join_table.png")
  Images.leave_table = PhotoImage(file="img/leave_table.png")
  Images.buy_in = PhotoImage(file="img/buy_in.png")
  Images.cash_out = PhotoImage(file="img/cash_out.png")
  Images.chips = PhotoImage(file="img/chips.png")
  Images.pot = PhotoImage(file="img/pot.png")
  Images.card_back = PhotoImage(file="img/card_back.png")
  Images.fold = PhotoImage(file="img/fold.png")
  Images.check = PhotoImage(file="img/check.png")
  Images.call = PhotoImage(file="img/call.png")
  Images.bet = PhotoImage(file="img/bet.png")
  Images.raise_img = PhotoImage(file="img/raise.png")
  Images.reraise= PhotoImage(file="img/re-raise.png")
  Images.card_images = initialize_card_images()
  
  top_frame.config(bg = "#35654d")

  #log-in frame
  login_frame = Frame(top_frame, width=400, height=600, bg = "#35654d")
  login_frame.place(relx=0.5, rely=0.5, anchor="c")

  lbframe_app_name = LabelFrame(login_frame, bg="#35654d", relief="groove")
  lb_app_name = Label(lbframe_app_name, bg="#35654d", text="Poker App", font="Helvetica 32 bold")
  lb_username = Label(login_frame, bg="#35654d", text="Username:", font="Helvetica 16 bold")
  #ADD validation
  entry_username = Entry(login_frame, width=20)
  lb_password = Label(login_frame, bg="#35654d", text="Password:", font="Helvetica 16 bold")
  entry_password = Entry(login_frame, width=20)
  bttn_register = Button(login_frame, image=Images.register, borderwidth=0, bg="#35654d", activebackground="#35654d")
  bttn_log_in = Button(login_frame, image=Images.log_in, borderwidth=0, bg="#35654d", activebackground="#35654d", command=lambda:check_login(entry_username.get(), entry_password.get(), top_frame, lb_error_alert, Images))
  lb_error_alert = Label(login_frame, bg="#E69394", font="Helvetica 12 bold", fg="#8E282A")
  
  lbframe_app_name.grid(row=0, column=0, columnspan=2, pady=32)
  lb_app_name.pack(anchor="c", padx=10, pady=10)
  lb_username.grid(row=1, column=0, columnspan=2, pady=5)
  entry_username.grid(row=2, column=0, columnspan=2, pady=5)
  lb_password.grid(row=3, column=0, columnspan=2, pady=5)
  entry_password.grid(row=4, column=0, columnspan=2, pady=5)
  bttn_register.grid(row=5, column=0, padx=15, pady=15)
  bttn_log_in.grid(row=5, column=1, padx=15, pady=15)

  gui.mainloop()

class GUI:
  def __init__(self):
     #GUI window
    self.gui = Tk()
    self.canvas = Canvas()
    self.gui.title("Poker App")
    self.gui.config(bg="#D3D3D3")
    self.gui.geometry("1200x800")
    self.gui.resizable(False, False)
    self.gui.iconbitmap("img/app_icon.ico")
    self.top_frame = Frame(self.gui, width=1200, height=800)
    self.top_frame.pack()
    self.top_frame.config(bg = "#35654d")
     #initialize images
    self.Images = Assets()
    self.Images.register = PhotoImage(file="img/register.png")
    self.Images.log_in = PhotoImage(file="img/log_in.png")
    self.Images.join_table = PhotoImage(file="img/join_table.png")
    self.Images.leave_table = PhotoImage(file="img/leave_table.png")
    self.Images.buy_in = PhotoImage(file="img/buy_in.png")
    self.Images.cash_out = PhotoImage(file="img/cash_out.png")
    self.Images.chips = PhotoImage(file="img/chips.png")
    self.Images.pot = PhotoImage(file="img/pot.png")
    self.Images.card_back = PhotoImage(file="img/card_back.png")
    self.Images.fold = PhotoImage(file="img/fold.png")
    self.Images.check = PhotoImage(file="img/check.png")
    self.Images.call = PhotoImage(file="img/call.png")
    self.Images.bet = PhotoImage(file="img/bet.png")
    self.Images.raise_img = PhotoImage(file="img/raise.png")
    self.Images.reraise= PhotoImage(file="img/re-raise.png")
    self.Images.card_images = initialize_card_images()

  def create_login_view(self):
    #log-in frame
    login_frame = Frame(self.top_frame, width=400, height=600, bg = "#35654d")
    login_frame.place(relx=0.5, rely=0.5, anchor="c")

    lbframe_app_name = LabelFrame(login_frame, bg="#35654d", relief="groove")
    lb_app_name = Label(lbframe_app_name, bg="#35654d", text="Poker App", font="Helvetica 32 bold")
    lb_username = Label(login_frame, bg="#35654d", text="Username:", font="Helvetica 16 bold")
    #ADD validation
    entry_username = Entry(login_frame, width=20)
    lb_password = Label(login_frame, bg="#35654d", text="Password:", font="Helvetica 16 bold")
    entry_password = Entry(login_frame, width=20)
    bttn_register = Button(login_frame, image=self.Images.register, borderwidth=0, bg="#35654d", activebackground="#35654d")
    bttn_log_in = Button(login_frame, image=self.Images.log_in, borderwidth=0, bg="#35654d", activebackground="#35654d", command=lambda:check_login(entry_username.get(), entry_password.get(), self.top_frame, lb_error_alert, self.Images))
    lb_error_alert = Label(login_frame, bg="#E69394", font="Helvetica 12 bold", fg="#8E282A")
    
    lbframe_app_name.grid(row=0, column=0, columnspan=2, pady=32)
    lb_app_name.pack(anchor="c", padx=10, pady=10)
    lb_username.grid(row=1, column=0, columnspan=2, pady=5)
    entry_username.grid(row=2, column=0, columnspan=2, pady=5)
    lb_password.grid(row=3, column=0, columnspan=2, pady=5)
    entry_password.grid(row=4, column=0, columnspan=2, pady=5)
    bttn_register.grid(row=5, column=0, padx=15, pady=15)
    bttn_log_in.grid(row=5, column=1, padx=15, pady=15)

def main():
  #instantiate server
  if (len(sys.argv)>1):
    client = Client(sys.argv[1])
    
  #instantiate client
  else:
    server = Server()
    server.run()

main()