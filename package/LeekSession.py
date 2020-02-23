import requests
import json
import time

FIGHT_DELAY = 0.2 ## Time between two combat requests in second.


LOGIN = ""
PASSWORD = ""


class LeekSession:

    def __init__(self, base_url):
        self.BASE_URL = base_url

        self.connected = False
        self.TOKEN = {"token" : ""}     ## The token cookie that will be sent for identification
        self.farmer = {}


## ================= LOGIN =================

    ## Connect the user and retrieve the corresponding token
    def login(self, login, password):
        r = requests.get(self.BASE_URL + "farmer/login-token/{}/{}".format(login, password))
        result = r.json()
        if type(result) == dict:
            if "token" in result.keys():
                self.TOKEN = {"token" : result["token"]}    ## Store the token as a cookie for future use
                self.farmer = result["farmer"]
                self.connected = True
                print("Logged in successfully!")
                return True
            else:
                print("The token could not be retrieved.")
        return False
    
    ## Disconnect the user
    def logout(self):
        if self.connected == True:
            requests.post(self.BASE_URL + "farmer/disconnect", cookies=self.TOKEN)
            self.connected = False


## ================= FARMER LEEKS =================

    ## Return the name for the specified leek ID
    def getLeekName(self, leekId):
        if len(self.farmer.keys()) != 0:
            if leekId in self.farmer["leeks"].keys():
                return self.farmer["leeks"][leekId]["name"]
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
    def findWeakestLeek(self, leeks):
        if len(leeks) > 0: 
            weakest = leeks[0]
            for leek in leeks:
                if leek["talent"] < weakest["talent"]:
                    weakest = leek
                elif leek["talent"] == weakest["talent"]:
                    if leek["level"] < weakest["level"]:
                        weakest = leek
                        
            return weakest
        return False


## ================= COMPOSITIONS =================

    ## Return the compositions list
    def getTeamCompositions(self):
        compositions = requests.get(self.BASE_URL + "team-composition/get-farmer-compositions", cookies=self.TOKEN).json()
        out = []
        for key, val in compositions.items():
            out.append(val)
        return out

    ## Return the compositions name list
    def getTeamCompositionsNames(self):
        compositions = self.getTeamCompositions()
        out = []
        for compo in compositions:
            out.append(compo["name"])
        return out

    ## Return the composition name ID for the specified composition name
    def getTeamCompositionId(self, compoName):
        compos = self.getTeamCompositions()
        for compo in compos:
            if compo["name"] == compoName:
                return compo["id"]
        return False

    ## Return the garden for the specified composition
    def getTeamCompositionGarden(self, compoId):
        compos_garden = requests.get(self.BASE_URL + "garden/get", cookies=self.TOKEN).json()["garden"]['my_compositions']

        for garden in compos_garden:
            if garden["id"] == compoId:
                return garden
        return False

    ## Return the composition with the smallest value of talent in the specified list
    def findWeakestComposition(self, compos):
        if len(compos) > 0: 
            weakest = compos[0]
            for compo in compos:
                if compo["talent"] < weakest["talent"]:
                    weakest = compo
                elif compo["talent"] == weakest["talent"]:
                    if compo["level"] < weakest["level"]:
                        weakest = compo
            return weakest
        return False


## ================= FIGHTS =================

    ## Start solo fights for the leek of name leekName.
    ## The number of fights to start can be specified. Let number to 0 for max combat available.
    def startSoloFights(self, leekName, number=0):
        if leekName in self.getFarmerLeeksNames():
            leekId = self.getFarmerLeekId(leekName)
            garden = requests.get(self.BASE_URL + "garden/get", cookies=self.TOKEN).json()["garden"]
            
            if number <= 0 or number > garden["fights"]:
                number = garden["fights"]
                
            print("\n == Starting {} solo fights... == ".format(number))
            for x in range(0, number):
                oppo_obj = requests.get(self.BASE_URL + "garden/get-leek-opponents/{}".format(leekId), cookies=self.TOKEN)##["opponents"]
                oppo_cookie = oppo_obj.cookies  ## Retrieve the cookie that will be sent to start a fight
                opponents = oppo_obj.json()["opponents"]    ## Retrieve the opponents list
                
                weakest = self.findWeakestLeek(opponents)
                if weakest:
                    requests.post(self.BASE_URL + "garden/start-solo-fight", data={"leek_id" : str(leekId), "target_id" : str(weakest["id"])}, cookies=oppo_cookie)
                    print("  Fight started between {} and {}".format(leekName, weakest["name"]))

                    new_garden = requests.get(self.BASE_URL + "garden/get", cookies=self.TOKEN).json()["garden"]
                    ## This part is not yet functional
                    ##if garden["fights"] - 1 > new_garden["fights"]:       ## If the fight count changed from an external source
                    ##    x += garden["fights"] - new_garden["fights"] - 1  ## we add the difference to x to skip some fights.
                    garden = new_garden

                    print("    -{} total solo fights remaining.".format(garden["fights"]))
                    time.sleep(FIGHT_DELAY)
                else:
                    break

            print(" == Solo fights finished! == ")
            return True
        else:
            print("No leek named {} found".format(leekName))
        return False

    ## Start team fights for the composition of name compoName.
    ## The number of fights to start can be specified. Let number to 0 for max combat available.
    def startCompoFights(self, compoName, number=0):
        if compoName in self.getTeamCompositionsNames():
            compoId = self.getTeamCompositionId(compoName)
            garden = self.getTeamCompositionGarden(compoId)

            if garden:
                if number <= 0 or number > garden["fights"]:
                    number = garden["fights"]

                print("\n == Starting {} team fights with composition {} == ".format(number, compoName))
                for x in range(0, number):
                    oppo_obj = requests.get(self.BASE_URL + "garden/get-composition-opponents/{}".format(compoId), cookies=self.TOKEN)
                    oppo_cookie = oppo_obj.cookies
                    opponents = oppo_obj.json()["opponents"]
                    
                    weakest = self.findWeakestComposition(opponents)
                    if weakest:
                        requests.post(self.BASE_URL + "garden/start-team-fight", data={"composition_id" : str(compoId), "target_id" : str(weakest["id"])}, cookies=oppo_cookie)
                        print("  Fight started between {} and {}".format(compoName, weakest["name"]))
                        

                        new_garden = self.getTeamCompositionGarden(compoId)
                        ## This part is not yet functional
                        ##if garden["fights"] - 1 > new_garden["fights"]:       ## If the fight count changed from an external source
                        ##    x += garden["fights"] - new_garden["fights"] - 1  ## we add the difference to x to skip some fights.
                        garden = new_garden

                        print("    -{} fights remaining for {}.".format(garden["fights"], compoName))
                        time.sleep(FIGHT_DELAY)
                    else:
                        break

                print(" == Team fights finished! == ")       
                return True
        else:
            print("No composition named {} found".format(compoName))
        return False
