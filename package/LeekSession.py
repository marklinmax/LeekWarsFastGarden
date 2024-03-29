import requests
import json
import time
import os
import threading


class LeekSession:

    def __init__(self, base_url):
        self.BASE_URL = base_url

        self.connected = False
        self.token = {"token" : ""}     ## The token cookie that will be sent for identification
        self.farmer = {}
        self.fight_delay = 0.2 ## Time between two combat requests in second.
        self.win_loose_score = 10
        self.tied_score = 5

        self.enemy_stats = {}
        self.enemy_compo_stats = {}
        self.stats_lock = threading.Lock()

        self.thread_running = True
        self.thread_count = 0
        self.count_lock = threading.Lock()


## ================= LOGIN =================

    ## Connect the user and retrieve the corresponding token
    def login(self, login, password):
        r = requests.get(self.BASE_URL + "farmer/login-token/{}/{}".format(login, password))
        result = r.json()
        if type(result) == dict:
            if "token" in result.keys():
                self.token = {"token" : result["token"]}    ## Store the token as a cookie for future use
                self.farmer = result["farmer"]
                self.connected = True

                self.loadStats()
                for leek_id in self.getFarmerLeeks():
                    if not str(leek_id) in self.enemy_stats.keys():
                        self.enemy_stats.update({str(leek_id) : {"id" : leek_id, "name" : self.getLeekName(leek_id)}})

                for compo_id in self.getTeamCompositionsId():
                    if not str(compo_id) in self.enemy_compo_stats.keys():
                        self.enemy_compo_stats.update({str(compo_id) : {"id" : compo_id, "name" : self.getCompositionName(compo_id), "data" : {}}})

                self.thread_running = True

                print("Logged in successfully!")
                return True
            else:
                print("The token could not be retrieved.")
        return False


    ## Disconnect the user
    def logout(self):
        if self.connected == True:
            if self.thread_count != 0:
                print("Waiting for threads to terminate...")
            x = 0
            while self.thread_count != 0:
                x += 1
                if x >= 30:
                    print("Some threads are stuck, skipping them...")
                    self.thread_running = False
                    break
                time.sleep(1)

            requests.post(self.BASE_URL + "farmer/disconnect", cookies=self.token)
            print("Saving stats...")
            self.saveStats()
            print("Stats saved!")
            self.connected = False

    def loadStats(self):
        if not "stats" in os.listdir():
            os.mkdir("stats")
            
        filename = "stats/ennemy_stats-{}.json".format(self.farmer["id"])
        if filename.split("/")[1] in os.listdir("stats/"):
            with open(filename) as file:
                self.enemy_stats = json.load(file)
        else:
            with open(filename,"w") as file:
                file.write("")

        compo_filename = "stats/compo_stats-{}.json".format(self.farmer["id"])
        if compo_filename.split("/")[1] in os.listdir("stats/"):
            with open(compo_filename) as file:
                self.enemy_compo_stats = json.load(file)
        else:
            with open(filename,"w") as file:
                file.write("")

    def saveStats(self):
        filename = "stats/ennemy_stats-{}.json".format(self.farmer["id"])
        with open(filename, "w") as file:
            json.dump(self.enemy_stats, file)

        compo_filename = "stats/compo_stats-{}.json".format(self.farmer["id"])
        with open(compo_filename, "w") as file:
            json.dump(self.enemy_compo_stats, file)


## ================= GARDEN =================

    ## Return the user's garden.
    def getGarden(self):
        return requests.get(self.BASE_URL + "garden/get", cookies=self.token).json()["garden"]

    ## Return the garden for the specified composition
    def getTeamCompositionGarden(self, compoId):
        compos_garden = requests.get(self.BASE_URL + "garden/get", cookies=self.token).json()["garden"]['my_compositions']

        for garden in compos_garden:
            if garden["id"] == compoId:
                return garden
        return False

## ================= FARMER LEEKS =================

    ## Return the name for the specified leek ID
    def getLeekName(self, leekId):
        if len(self.farmer.keys()) != 0:
            if leekId in self.farmer["leeks"].keys():
                return self.farmer["leeks"][leekId]["name"]
        return False

    ## Return the specified leek level
    def getLeekLevel(self, leekId):
        if len(self.farmer.keys()) != 0:
            if leekId in self.farmer["leeks"].keys():
                return int(self.farmer["leeks"][leekId]["level"])
        return False

    ## Return the farmer's leeks ID list.
    def getFarmerLeeks(self):
        if len(self.farmer.keys()) != 0:
            leeks = []
            for keys in self.farmer["leeks"]:
                leeks.append(keys)
            return leeks
        return False

    ## Return the farmer's leeks name list
    def getFarmerLeeksNames(self):
        leeks = self.getFarmerLeeks()
        if leeks != -1:
            leeksName = []
            for leek in leeks:
                leeksName.append(self.getLeekName(leek))
            return leeksName
        return False

    ## Return the ID for the specified leek name
    def getFarmerLeekId(self, leekName):
        leeks = self.getFarmerLeeks()
        for ID in leeks:
            if self.farmer["leeks"][ID]["name"] == leekName:
                return ID
        return False

    ## Return the leek with the smallest value of talent in the specified list
    ## The talent value is modified if we already encountered that leek
    def findWeakestLeek(self, leeks, my_leek):
        if len(leeks) > 0:
            leek_dict = self.enemy_stats[str(my_leek)]
            weakest = leeks[0]
            if str(weakest["id"]) in leek_dict.keys():
                weakest["talent"] = weakest["talent"] - leek_dict[str(weakest["id"])]["score"]
            for leek in leeks:
                if str(leek["id"]) in leek_dict.keys():
                    leek["talent"] = leek["talent"] - leek_dict[str(leek["id"])]["score"]
                    
                if leek["talent"] < weakest["talent"]:
                    weakest = leek
                elif leek["talent"] == weakest["talent"]:
                    if leek["level"] < weakest["level"]:
                        weakest = leek
                        
            return weakest
        return False

    def registerLeekTournament(self, leekName=""):
        if leekName == "":
            names = self.getFarmerLeeksNames()

            for leek in names:
                self.registerLeekTournament(leek)
            
        elif leekName in self.getFarmerLeeksNames():
            leekId = self.getFarmerLeekId(leekName)
            requests.post(self.BASE_URL + "leek/register-tournament", data={"leek_id" : str(leekId)}, cookies=self.token)
            print("{} registered for solo tournament".format(leekName))
            
        else:
            print("No leek named {} found".format(leekName))

    def registerFarmerTournament(self):
        res = requests.post(self.BASE_URL + "farmer/register-tournament", cookies=self.token)
        print("Farmer registered for tournament")

## ================= COMPOSITIONS =================

    ## Return the compositions list
    def getTeamCompositions(self):
        out = []
        compositions = requests.get(self.BASE_URL + "team-composition/get-farmer-compositions", cookies=self.token).json()
        for key, val in compositions.items():
            out.append(val)
        return out

    ## Return the compositions id list
    def getTeamCompositionsId(self):
        out = []
        compositions = self.getTeamCompositions()
        for compo in compositions:
            out.append(compo["id"])
        return out

    ## Return the compositions name list
    def getTeamCompositionsNames(self):
        out = []
        compositions = self.getTeamCompositions()
        for compo in compositions:
            out.append(compo["name"])
        return out

    ## Return the corresponding composition name
    def getCompositionName(self, compo_id):
        out = ""
        compositions = self.getTeamCompositions()
        for compo in compositions:
            if compo["id"] == compo_id:
                out = compo["name"]
        return out

    ## Return the composition name ID for the specified composition name
    def getTeamCompositionId(self, compoName):
        compos = self.getTeamCompositions()
        for compo in compos:
            if compo["name"] == compoName:
                return compo["id"]
        return False

    ## Return the specified leek's composition id
    def getCompoIdFromLeek(self, leek_id):
        compos = self.getTeamCompositions()
        for compo in compos:
            for leek in compo["leeks"]:
                if leek["id"] == leek_id:
                    return compo["id"]
        return False

    ## Return the composition with the smallest value of talent in the specified list
    ## The talent value is modified if we already encountered that composition
    def findWeakestComposition(self, compos, my_compo):
        if len(compos) > 0:
            compo_dict = self.enemy_compo_stats[str(my_compo)]["data"]
            weakest = compos[0]
            if str(weakest["id"]) in compo_dict.keys():
                weakest["talent"] -= compo_dict[str(weakest["id"])]["score"]
            for compo in compos:
                if str(compo["id"]) in compo_dict.keys():
                     compo["talent"] -= compo_dict[str(compo["id"])]["score"]
                
                if compo["talent"] < weakest["talent"]:
                    weakest = compo
                elif compo["talent"] == weakest["talent"]:
                    if compo["level"] < weakest["level"]:
                        weakest = compo
            return weakest
        return False

    def registerCompositionTournament(self, compoName=""):
        if compoName == "":            
            names = self.getTeamCompositionsNames()

            for compo in names:
                self.registerCompositionTournament(compo)

        elif compoName in self.getTeamCompositionsNames():
            compoId = self.getTeamCompositionId(compoName)
            requests.post(self.BASE_URL + "team/register-tournament", data={"composition_id" : str(compoId)}, cookies=self.token)
            print("{} registered for team tournament".format(compoName))
        else:
            print("No composition named {} found".format(compoName))


## ================= FIGHTS =================

    ## Thread that will wait and process the solo fight data
    def waitForFightData(self, fight_id):
        response = requests.get(self.BASE_URL + "fight/get/{}".format(fight_id),cookies=self.token)
        fight_data = response.json()

        while fight_data["winner"] == -1 and self.thread_running == True:   ## While fight not processed
            time.sleep(self.fight_delay)    ## Try not flooding the server
            response = requests.get(self.BASE_URL + "fight/get/{}".format(fight_id),cookies=self.token)
            fight_data = response.json()

        if self.thread_running == True:
            winner = fight_data["winner"]


            my_win = 0
            
            if winner != 0:
                winner_farmer_id = fight_data["leeks{}".format(winner)][0]["farmer"]
                my_win = -1
                if winner_farmer_id == self.farmer["id"]:
                    my_win = 1

            if str(fight_data["leeks1"][0]["id"]) in self.getFarmerLeeks():
                my_leek_id = fight_data["leeks1"][0]["id"]
                enemy_leek_id = fight_data["leeks2"][0]["id"]
                enemy_leek_name = fight_data["leeks2"][0]["name"]
            else:
                my_leek_id = fight_data["leeks2"][0]["id"]
                enemy_leek_id = fight_data["leeks1"][0]["id"]
                enemy_leek_name = fight_data["leeks1"][0]["name"]



            self.updateEnemyStats(enemy_leek_id, enemy_leek_name, my_leek_id, my_win)

        self.count_lock.acquire()
        self.thread_count -= 1
        self.count_lock.release()

    ## Update enemy stats dict with the solo fight result
    def updateEnemyStats(self, enemy_id, enemy_name, my_leek_id, my_win):
        self.stats_lock.acquire()
        
        my_leek = self.enemy_stats[str(my_leek_id)]
        if str(enemy_id) in my_leek.keys():
            if my_win == 0:
                if my_leek[str(enemy_id)]["score"] > (-100 + self.tied_score):
                    my_leek[str(enemy_id)]["score"] = my_leek[str(enemy_id)]["score"] - self.tied_score
            elif my_win == 1:
                if my_leek[str(enemy_id)]["score"] < (100 - self.win_loose_score):
                    my_leek[str(enemy_id)]["score"] = my_leek[str(enemy_id)]["score"] + self.win_loose_score
            else:
                if my_leek[str(enemy_id)]["score"] > (-100 + self.win_loose_score):
                    my_leek[str(enemy_id)]["score"] = my_leek[str(enemy_id)]["score"] - self.win_loose_score
        else:
            if my_win == 0:
                my_leek.update({enemy_id : {"id" : enemy_id, "name" : enemy_name, "score" : self.tied_score*(-1)}})
            elif my_win == 1:
                my_leek.update({enemy_id : {"id" : enemy_id, "name" : enemy_name, "score" : self.win_loose_score}})
            else:
                my_leek.update({enemy_id : {"id" : enemy_id, "name" : enemy_name, "score" : self.win_loose_score*(-1)}})
            
        self.stats_lock.release()

    ## Thread that will wait and process the team fight data
    def waitForTeamFightData(self, fight_id):
        response = requests.get(self.BASE_URL + "fight/get/{}".format(fight_id),cookies=self.token)
        fight_data = response.json()

        while fight_data["winner"] == -1 and self.thread_running == True:   ## While fight not processed
            time.sleep(self.fight_delay)    ## Try not flooding the server
            response = requests.get(self.BASE_URL + "fight/get/{}".format(fight_id),cookies=self.token)
            fight_data = response.json()


        if self.thread_running == True:
            winner = fight_data["winner"]

            my_win = 0

            self.getCompoIdFromLeek(0)

            if winner != 0:
                winner_farmers = fight_data["farmers{}".format(winner)]
                my_win = -1
                if str(self.farmer["id"]) in winner_farmers.keys():
                    my_win = 1

            ## Search for my composition id
            my_compo_id = False
            for leek in fight_data["leeks1"]:
                my_compo_id = self.getCompoIdFromLeek(leek["id"])
                if my_compo_id:
                    enemy_team_id = fight_data["team2"]
                    enemy_team_name = fight_data["team2_name"]
                    break
            if not my_compo_id:
                for leek in fight_data["leeks2"]:
                    my_compo_id = self.getCompoIdFromLeek(leek["id"])
                    if my_compo_id:
                        enemy_team_id = fight_data["team1"]
                        enemy_team_name = fight_data["team1_name"]
                        break

            ## Uses enemy team id instead of composition id.
            ## Best solution would be to internally keep track of different known compositions
            ## based on the enemy leeks list and assign them a local id
            self.updateTeamFightStats(enemy_team_id, enemy_team_name, my_compo_id, my_win)

        self.count_lock.acquire()
        self.thread_count -= 1
        self.count_lock.release()

    ## Update the composition fight dict with the team fight result
    def updateTeamFightStats(self, enemy_compo_id, enemy_compo_name, my_compo_id, my_win):
        self.stats_lock.acquire()
        
        my_compo = self.enemy_compo_stats[str(my_compo_id)]
        if str(enemy_compo_id) in my_compo["data"].keys():
            if my_win == 0:
                    my_compo["data"][str(enemy_compo_id)]["score"] -= self.tied_score
            elif my_win == 1:
                if my_compo["data"][str(enemy_compo_id)]["score"] < (100 - self.win_loose_score):
                    my_compo["data"][str(enemy_compo_id)]["score"] += self.win_loose_score
            else:
                if my_compo["data"][str(enemy_compo_id)]["score"] > (-100 + self.win_loose_score):
                    my_compo["data"][str(enemy_compo_id)]["score"] -= self.win_loose_score
        else:
            if my_win == 0:
                my_compo["data"].update({enemy_compo_id : {"id" : enemy_compo_id, "name" : enemy_compo_name, "score" : self.tied_score*(-1)}})
            elif my_win == 1:
                my_compo["data"].update({enemy_compo_id : {"id" : enemy_compo_id, "name" : enemy_compo_name, "score" : self.win_loose_score}})
            else:
                my_compo["data"].update({enemy_compo_id : {"id" : enemy_compo_id, "name" : enemy_compo_name, "score" : self.win_loose_score*(-1)}})
                
        self.stats_lock.release()


    ## Both starts fights and registers to tournaments
    def startAll(self):
        self.startFights()
        self.registerTournaments()

    ## Registers to every tournaments
    def registerTournaments(self):
        print("")
        self.registerLeekTournament()
        self.registerCompositionTournament()
        self.registerFarmerTournament()

    ## Starts all fights
    def startFights(self):
        if not self.startSoloFights():
            print("An error occured during solo fights.")
        if not self.startCompoFights():
            print("An error occured during team fights.")

    ## Starts solo fights for the leek of name leekName.
    ## The number of fights to start can be specified. Let number to 0 for max combat available.
    def startSoloFights(self, leekName="", number=0):
        if leekName == "":
            success = True
            
            ids = self.getFarmerLeeks()
            garden = self.getGarden()
            total_fights = garden["fights"]

            names = []
            for leek_id in ids:
                if self.getLeekLevel(leek_id) != 301:
                    names.append(self.getLeekName(leek_id))

            if total_fights % len(names) == 0:
                for leek in names:
                    success = success and self.startSoloFights(leek, int(total_fights/len(names)))
            else:
                success = success and self.startSoloFights(names[0], int(total_fights/len(names))+1)
                for x in range(1, len(names)):
                    success = success and self.startSoloFights(names[x], int(total_fights/len(names)))

            return success

        elif leekName in self.getFarmerLeeksNames():
            leekId = self.getFarmerLeekId(leekName)
            garden = self.getGarden()
            
            if number <= 0 or number > garden["fights"]:
                number = garden["fights"]
                
            print("\n == Starting {} solo fights... == ".format(number))
            for x in range(0, number):
                oppo_obj = requests.get(self.BASE_URL + "garden/get-leek-opponents/{}".format(leekId), cookies=self.token)
                oppo_cookie = oppo_obj.cookies              ## Retrieve the cookie that will be sent to start a fight
                opponents = oppo_obj.json()["opponents"]    ## Retrieve the opponents list
                
                weakest = self.findWeakestLeek(opponents, leekId)
                if weakest:
                    response = requests.post(self.BASE_URL + "garden/start-solo-fight", data={"leek_id" : str(leekId), "target_id" : str(weakest["id"])}, cookies=oppo_cookie)
                    fight_id = response.json()["fight"]

                    
                    t = threading.Thread(target=self.waitForFightData, args=[fight_id])
                    self.count_lock.acquire()
                    self.thread_count += 1
                    self.count_lock.release()
                    t.start()
                    
                    print("  Fight started between {} and {}".format(leekName, weakest["name"]))

                    garden = self.getGarden()   ## Refresh the garden

                    print("    -{} total solo fights remaining.".format(garden["fights"]))
                    time.sleep(self.fight_delay)
                else:
                    break

            print(" == Solo fights finished! == ")
            return True
        else:
            print("No leek named {} found".format(leekName))
        return False

    ## Start team fights for the composition of name compoName.
    ## The number of fights to start can be specified. Let number to 0 for max combat available.
    def startCompoFights(self, compoName="", number=0):
        if compoName == "":
            success = True
            
            names = self.getTeamCompositionsNames()

            for compo in names:
                success = success and self.startCompoFights(compo)

            return success
        
        elif compoName in self.getTeamCompositionsNames():
            compoId = self.getTeamCompositionId(compoName)
            garden = self.getTeamCompositionGarden(compoId)

            if garden:
                if number <= 0 or number > garden["fights"]:
                    number = garden["fights"]

                print("\n == Starting {} team fights with composition {} == ".format(number, compoName))
                initial_state = garden["fights"]
                while number > initial_state - garden["fights"]:
                    oppo_obj = requests.get(self.BASE_URL + "garden/get-composition-opponents/{}".format(compoId), cookies=self.token)
                    oppo_cookie = oppo_obj.cookies
                    opponents = oppo_obj.json()["opponents"]
                    
                    weakest = self.findWeakestComposition(opponents, compoId)
                    if weakest:
                        response = requests.post(self.BASE_URL + "garden/start-team-fight", data={"composition_id" : str(compoId), "target_id" : str(weakest["id"])}, cookies=oppo_cookie)
                        fight_id = response.json()["fight"]

                        t = threading.Thread(target=self.waitForTeamFightData, args=[fight_id])
                        self.count_lock.acquire()
                        self.thread_count += 1
                        self.count_lock.release()
                        t.start()
                        
                        print("  Fight started between {} and {}".format(compoName, weakest["name"]))
                        

                        garden = self.getTeamCompositionGarden(compoId) ## Refresh the garden

                        print("    -{} fights remaining for {}.".format(garden["fights"], compoName))
                        time.sleep(self.fight_delay)
                    else:
                        break

                print(" == Team fights finished! == ")       
                return True
        else:
            print("No composition named {} found".format(compoName))
        return False
