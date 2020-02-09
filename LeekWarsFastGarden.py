import os
import sys

##os.chdir("..")
print(os.getcwd())
sys.path.append(os.getcwd() + "/package")
from LeekSession import leekSession

BASE_URL = "https://leekwars.com/api/"

COMMAND_LIST = ["login", "start_solo_fight", "start_team_fight", "help", "quit"]


VERSION = "0.1"
AUTHOR = "marklinmax"
HEAD = """\nLeekWarsFastGarden v{} by {}\nEnter "help" to display the help.""".format(VERSION, AUTHOR)

HELP = """
Syntax: [command] [arg1] [arg2] [arg...]
Command summary:
    - login: Take two arguments [login] and [password]. This command should be the first one called.
    - start_solo_fight: Take one or two argumtents [leekName] [number]. [number] can be omitted or set to 0 to start the maximum amount of fights.
    - start_team_fight: Take one or two argumtents [compoName] [number]. [number] can be omitted or set to 0 to start the maximum amount of fights.
    - quit: Exit the script.
    - help: Display this help."""



session = leekSession(BASE_URL)


if __name__ == "__main__":

    print(HEAD)

    running = True
    
    while running:
        command = input(">>> ")
    
        args = command.split(" ")
        

        if len(args) > 0:
            if args[0] in COMMAND_LIST:
                if args[0] == "login" and len(args) == 3:
                    if not session.login(args[1], args[2]):
                        print("An error occured.")
                        
                elif args[0] == "start_solo_fight" and len(args) >= 2:
                    if session.connected:
                        if len(args) == 2:
                            if not session.startSoloFights(args[1]):
                                print("An error occured.")
                        else:
                            if not session.startSoloFights(args[1], int(args[2])):
                                print("An error occured.")
                    else:
                        print("You have to be logged in first!")
                            
                elif args[0] == "start_team_fight" and len(args) >= 2:
                    if session.connected:
                        if len(args) == 2:
                            if not session.startCompoFights(args[1]):
                                print("An error occured.")
                        else:
                            if not session.startCompoFights(args[1], int(args[2])):
                                print("An error occured.")
                    else:
                        print("You have to be logged in first!")
                        
                elif args[0] == "help":
                    print(HELP)

                elif args[0] == "quit":
                    session.logout()
                    running = False

                else:
                    print("""Wrong syntax...\nEnter "help" to display the help.""")
                        
            else:
                print("""Wrong syntax...\nEnter "help" to display the help.""")

session.logout()

