import os
import sys
import getpass

from package import LeekSession
from package import Updater


BASE_URL = "https://leekwars.com/api/"


ALLOWS_AUTO_UPDATE = True
CHECK_UPDATE_URL = "https://raw.githubusercontent.com/marklinmax/LeekWarsFastGarden/master/LeekWarsFastGarden.py"   ## URL to raw file containing version string on github
ARCHIVE_URL = "https://github.com/marklinmax/LeekWarsFastGarden/archive/master.zip"


COMMAND_LIST = ["login", "start_solo_fight", "start_team_fight", "start_fight", "start", "register_tournaments", "help", "quit"]


VERSION = "0.1.6"
AUTHOR = "marklinmax"
HEAD = """\nLeekWarsFastGarden v{} by {}\nEnter "help" to display the help.""".format(VERSION, AUTHOR)

HELP = """
Syntax: [command] [arg1] [arg2] [arg...]
Command summary:
    - login: Takes no arguments. Type in this command to start the login process. This should be the first command issued.
    - start_solo_fight: Takes from zero to two arguments. If no arguments passed, the maximum amount of fights will be split between all leeks. [leekName] can be passed as first argument to start fights for one specific leek. [number] can be passed as second argument to start a specified number of fights.
    - start_team_fight: Takes from zero to two arguments. If no arguments passed, the maximum amount of fights will be started for all compositions. [compoName] can be passed as first argument to start fights for one specific composition. [number] can be passed as second argument to start a specified number of fights.
    - quit: Exits the script.
    - help: Displays this help."""


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    
    updater = Updater.Updater(VERSION)
    if updater.checkForUpdates(CHECK_UPDATE_URL) and ALLOWS_AUTO_UPDATE:
        if not updater.update(ARCHIVE_URL, os.path.dirname(os.path.abspath(__file__+"/.."))):
            print("\nAn error occured during the update process. Check the error messages for more informations.")
    else:
        print(HEAD)

    session = LeekSession.LeekSession(BASE_URL)
    running = True

    params = sys.argv
    if len(params) == 3:
        running = False
        if session.login(params[1], params[2]):
            session.startAll()
        else:
            print("Couldn't login with the given credentials.")
    elif len(params) > 1:
        print("You need to give username and password, or nothing.")
        running = False

    while running:
        command = input(">>> ")
    
        args = command.split(" ")
        

        if len(args) > 0:
            if args[0] in COMMAND_LIST:
                if args[0] == "login":
                    user = input("Username: ")
                    password = getpass.getpass(prompt="Password: ")
                    if not session.login(user, password):
                        print("An error occured. Maybe you entered bad credentials.")
                        
                elif args[0] == "start_solo_fight":
                    if session.connected:
                        if len(args) == 2:
                            if not session.startSoloFights(args[1]):
                                print("An error occured.")
                        elif len(args) == 1:
                            if not session.startSoloFights():
                                print("An error occured.")
                        else:
                            if not session.startSoloFights(args[1], int(args[2])):
                                print("An error occured.")
                    else:
                        print("You have to be logged in first!")
                            
                elif args[0] == "start_team_fight":
                    if session.connected:
                        if len(args) == 2:
                            if not session.startCompoFights(args[1]):
                                print("An error occured.")
                        elif len(args) == 1:
                            if not session.startCompoFights():
                                print("An error occured.")
                        else:
                            if not session.startCompoFights(args[1], int(args[2])):
                                print("An error occured.")
                    else:
                        print("You have to be logged in first!")

                elif args[0] == "start_fight":
                    if session.connected:
                        session.startFights()
                    else:
                        print("You have to be logged in first!")
                        
                elif args[0] == "start":
                    if session.connected:
                        session.startAll()
                    else:
                        print("You have to be logged in first!")

                elif args[0] == "register_tournaments":
                    if session.connected:
                        session.registerTournaments()
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
