import sys

help_message = '''
            
Available commands:
* "t [recepient_address] [amount]"                        Send `amount` NBC to `recepient` node
* "view"                                                  View transactions of the latest block
* "balance"                                               View balance of each wallet (last validated block)
* "help"                                                  Print this help message
* "exit"                                                  Exit client 
'''


PORT = int(sys.argv[1])
IP = str(sys.argv[2])
URL = 'http://' + str(IP) + ':' + str(PORT) + "/"


if len(sys.argv) < 3 or len(sys.argv) > 3:
    print("Invalid inputs! Please Type the command as: python cli.py <PORT> <IP>")
    sys.exit(0)

print("====================")
print(" WELCOME TO NOOBCASH")
print("====================")

while (1):
    print("Enter an action! Type help for more specific info")
    choice = input()

    # Transaction
    if choice.startswith('t'):
        print("hello1")

    # View last transaction
    elif choice == 'view':
        print("hello2")
    # Balance
    elif choice == 'balance':
        print("hello3")

    # Help
    elif choice == 'help':
        print(help_message)

    elif (choice == 'exit'):
        sys.exit(0)

    else:
        print("Invalid action")
