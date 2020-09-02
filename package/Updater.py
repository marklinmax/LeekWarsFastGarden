import os
import shutil
import zipfile
from distutils.dir_util import copy_tree

from distutils.version import StrictVersion

import urllib.request


IGNORED = ["__pycache__", ".git", "python", "Temp", "backup", ".", "stats"]

class Updater:

    def __init__(self, version):
        self.version = version

    def checkForUpdates(self, checkURL):
        print("Checking for updates...")
        try:
            raw = urllib.request.urlopen(checkURL).read().decode()
            version = self.findVersion(raw)
            if self.compareVersions(self.version, version):
                print("New version found (v{})!".format(version))
                return True
        except Exception as err:
            print(err)
            print("Couldn't check for updates.\nPlease verify the URL and that you have an internet access.")
            return False
        
        print("Your version is up to date!")
        return False


    def findVersion(self, raw):
        content = raw.split("\n")
        
        for element in content:
            cleaned = element.replace(" ", "")
            if "VERSION" in cleaned:
                return cleaned.split('"')[1::2][0]
        return "0.0"


    ## Compares two version strings (t1 and t2), and return True if t2 is higher than t1, False otherwise.
    def compareVersions(self, v1, v2):
        t1 = v1.replace('"', "")
        t2 = v2.replace('"', "")

        result = False
        try:
           result = StrictVersion(t2) > StrictVersion(t1)
        except Exception:
            return False    ## If version string isn't good, return False to prevent updating.

        return result
    

    def update(self, archiveURL, path):
        print("Starting the update process...")
        error = False
        print("Backing up folder before updating...")
        shutil.copytree(path, "backup", ignore=shutil.ignore_patterns(*IGNORED))

        if "Temp" in os.listdir():
            shutil.rmtree("Temp")
        os.mkdir("Temp")
            
        try:
            print("Downloading the update...")
            urllib.request.urlretrieve(archiveURL, filename="Temp/update.zip")
        except Exception as err:
            error = True
            print(err)
            print("An error occured when trying to retrieve the update...\nPlease verify the URL used.")

        if not error:
            try:
                print("Removing old version...")
                for root, dirs, files in os.walk(path, topdown=True):
                    dirs[:] = [d for d in dirs if d not in IGNORED]
                    if not os.path.abspath(root) == os.path.abspath(path):
                        shutil.rmtree(root)
                    else:
                        for file in files:
                            os.remove(file)
                        
                print("Extracting new files...")
                with zipfile.ZipFile("Temp/update.zip", 'r') as zip_ref:
                    zip_ref.extractall("Temp/update")
                    
                print("Copying new files...")
                copy_tree("Temp/update/" + os.listdir("Temp/update")[0], path)
                    
            except Exception as err:
                error = True
                print(err)
                print('An error occured when updating...\nPrevious version can be found on the "backup" folder.')

            if "Temp" in os.listdir():
                try:
                    print("Removing temporary files...")
                    shutil.rmtree("Temp/")
                except Exception as err:
                    print(err)
            
            if not error:
                try:
                    print("Cleaning the folder...")
                    shutil.rmtree("backup")
                    print("\nUpdating finished!\nPlease restart the script to apply changes!")
                except Exception as err:
                    error = True
                    print(err)
                    print('An error occured while deleting the following folder. Please do it manually.\n-"backup"')

                    
        return not error
        
