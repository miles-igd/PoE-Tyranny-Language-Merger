from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkinter import *
from pathlib import Path
from shutil import copytree, copyfile
import os

if os.name == 'nt': BCKGRND = None
else: BCKGRND = 'black'

import xml.etree.ElementTree as ET
import ast

class App:
    def __init__(self, master):
        self.game_files_to_merge = ["interactables.stringtable", "loadingtips.stringtable", "lifepath.stringtable", "missives.stringtable", "notifications.stringtable", "reputationchangereasons.stringtable", "stronghold.stringtable", "subtitles.stringtable" ]
        self.locations = []
        self.languages = []
        self.valid = False
        ##ROW 0__
        self.pathLabel = Label(master, text="Game Folder:")
        self.pathEntry = Entry(master, width=50)
        self.pathEntry.bind("<Key>", self.keypress)
        self.pathButton = Button(master, text="...", width=3, command=self.setRootPath)
        ##ROW 1__
        self.gameName = StringVar()
        self.gameLabel = Label(master, text="Game:")
        self.gameNameLabel = Label(master, textvariable=self.gameName)
        #ROW 2__
        self.primaryLabel = Label(master, text="Primary Language")
        self.statusVar = StringVar()
        self.statusLabel = Label(master, textvariable=self.statusVar)
        self.secondaryLabel = Label(master, text = "<Secondary Language>")
        #ROW 3__
        self.primaryList = ttk.Combobox(master, justify="center", state="readonly", width=25)
        self.mergeButton = Button(master, text="Merge", command=self.mergeText)
        self.secondaryList = ttk.Combobox(master, justify="center", state="readonly", width=25)
        #ROW ___
        self.convVar = IntVar()
        self.convVar.set(1)
        self.conversationsCheck = Checkbutton(master, text="Conversations", bg=BCKGRND, variable = self.convVar)
        self.questsVar = IntVar()
        self.questsVar.set(1)
        self.questsCheck = Checkbutton(master, text="Quests", bg=BCKGRND, variable = self.questsVar)
        self.gameVar = IntVar()
        self.gameVar.set(0)
        self.gameCheck = Checkbutton(master, text= "Game", bg=BCKGRND, variable = self.gameVar)
        #LAYOUT__
        self.pathLabel.grid(row=0, sticky=E)
        self.pathEntry.grid(row=0, column=1)
        self.pathButton.grid(row=0, column=2, sticky=W)

        self.gameLabel.grid(row=1, column=0, sticky=E)
        self.gameNameLabel.grid(row=1, column=1, sticky=W)

        self.primaryLabel.grid(row=2, column=0)
        self.statusLabel.grid(row=2, column=1)
        self.secondaryLabel.grid(row=2, column=2)

        self.primaryList.grid(row=3, column=0)
        self.mergeButton.grid(row=3, column=1)
        self.secondaryList.grid(row=3, column=2)

        self.conversationsCheck.grid(row=4, column=1, sticky=W)
        self.questsCheck.grid(row=5, column=1, sticky=W)
        self.gameCheck.grid(row=6, column=1, sticky=W)

    def keypress(self, key, *args):
        if key.keycode == 13:
            print("Searching...")
            self.gameName.set("Searching...")
            self.validPath(self.pathEntry.get())
        print("Done searching.")

    def recursiveDir(self, filepath, query, locations = []):
        for child in filepath.iterdir():
            if child.is_dir():
                if (child.name==query):
                    locations.append(child)
                self.recursiveDir(child, query, locations)
                #print(child)

        return locations

    def validPath(self, filepath):
        aName = self.findGame(filepath)
        self.gameName.set(aName)
        if aName:
            self.valid = True
            self.locations, self.languages = self.findLanguages(filepath)
            self.updateLists(self.languages, self.locations)
        else:
            self.valid = False
            self.gameName.set("Need valid filepath!")
            messagebox.showerror(title="ERROR", message="No .exe found")

    def setRootPath(self, *args):
        filepath = filedialog.askdirectory(initialdir = "/", title="Select file")
        if (filepath == ""):
            return None
        print("Searching...")
        self.pathEntry.delete(0, END)
        self.pathEntry.insert(0, filepath)
        self.validPath(filepath)
        print("Done searching.")

    def findLanguages(self, filepath):
        locations = []
        languages = []
        rootPath = Path(filepath)
        locations = self.recursiveDir(rootPath, "localized", locations)

        rootPath = locations[0]
        for child in rootPath.iterdir():
            languageName = child / "language.xml"
            try:
                childTree = ET.parse(languageName.absolute())
                childRoot = childTree.getroot()
                childName = childRoot.find('GUIString')
                languages.append({'code': child.name, 'lang': childName.text})
            except FileNotFoundError:
                print("No " + str(languageName) + " file, skipping...")

        return locations, languages

    def findGame(self, filepath):
        name = ""
        rootPath = Path(filepath)
        files = (child for child in rootPath.iterdir() if child.is_file())
        for file in files:
            if file.name == "PillarsOfEternity.exe":
                return "Pillars of Eternity"
            elif file.name == "Tyranny.exe":
                return "Tyranny"
            elif file.name in ["PillarsOfEternity2.exe", "PillarsOfEternityII.exe"]:
                return "Pillars of Eternity II: Deadfire"
            else:
                continue

        return None

    def updateLists(self, languages, locations):
        self.primaryList['values'] = languages
        self.secondaryList['values'] = languages

        self.primaryList.current(0)
        self.secondaryList.current(1)

    def mergeText(self, *args):
        if self.convVar.get() == 0 and self.questsVar.get() == 0 and self.gameVar.get() == 0:
            messagebox.showerror(title="ERROR", message="Please check which files to merge")
            return None

        if self.valid:
            self.statusVar.set("Working...")
            primaryLanguage = ast.literal_eval(self.primaryList.get())
            secondaryLanguage = ast.literal_eval(self.secondaryList.get())

            self.newCode = primaryLanguage['code'] + "_" + secondaryLanguage['code']
            self.newName = primaryLanguage['code'] + "/" + secondaryLanguage['code']
            self.newLang = primaryLanguage['lang'] + "/" + secondaryLanguage['lang']

            for locPath in self.locations:
                rootPath = locPath
                primaryPath = rootPath / primaryLanguage['code'] / 'text'
                secondaryPath = rootPath / secondaryLanguage['code'] / 'text'
                newPath = rootPath / self.newCode / 'text'
                print("Copying...")
                try:
                    copytree(rootPath / primaryLanguage['code'], rootPath / self.newCode)
                except FileExistsError:
                    #messagebox.showerror(title="ERROR", message= self.newCode + " folder already exists" )
                    newPath.mkdir(parents=True, exist_ok=True)
                    self.statusVar.set("Error, directory exists, continuing...")
                print("Done copying.")

                print("Merging...", locPath)
                if self.convVar.get() == 1:
                    self.searchStringtables(primaryPath / 'conversations', secondaryPath / 'conversations', newPath / 'conversations')
                if self.questsVar.get() == 1:
                    self.searchStringtables(primaryPath / 'quests', secondaryPath / 'quests', newPath / 'quests')
                if self.gameVar.get() == 1:
                    self.searchStringtables(primaryPath / 'game', secondaryPath / 'game', newPath / 'game', self.game_files_to_merge)

            rootPath = self.locations[0]
            self.createLanguageXML(rootPath / primaryLanguage['code'] / "language.xml", rootPath / self.newCode / "language.xml")
            self.statusVar.set("Done!")
            print("Done merging.")
        else:
            messagebox.showerror(title="ERROR", message="Game folder not found")
            return None


    def searchStringtables(self, primaryPath, secondaryPath, newPath, specificFiles = None):
        if not primaryPath.exists():
            print(primaryPath, "does not exist")
            return None

        for child in primaryPath.iterdir():
            if child.is_dir():
                newPath.mkdir(parents=True, exist_ok=True)
                self.searchStringtables(child, secondaryPath / child.relative_to(primaryPath), newPath / child.relative_to(primaryPath))

            elif specificFiles is not None:
                print("Special case, checking", child.name)
                if child.name in specificFiles:
                    print("Merging", child.name)
                    newFile = newPath / child.name
                    try:
                        newFile.touch(exist_ok=True)
                    except:
                        print("No parent folder, creating parent folder...")
                        newFile.parent.mkdir(parents=True, exist_ok=True)
                        newFile.touch(exist_ok=True)

                    self.mergeFile(child, secondaryPath / child.name, newFile)

            elif child.suffix == ".stringtable":
                newFile = newPath / child.name
                try:
                    newFile.touch(exist_ok=True)
                except:
                    print("No parent folder, creating parent folder...")
                    newFile.parent.mkdir(parents=True, exist_ok=True)
                    newFile.touch(exist_ok=True)

                if os.path.isfile(secondaryPath / child.name):
                    self.mergeFile(child, secondaryPath / child.name, newFile)
                else:
                    print('Missing secondary file, using source language only')
                    copyfile(child, newFile)

            else:
                continue
        return None
      
    def mergeFile(self, primaryFile, secondaryFile, newFile):
        primaryTree = ET.parse(primaryFile)
        primaryRoot = primaryTree.getroot()
        primaryEntries = primaryRoot.find("Entries")

        secondaryTree = ET.parse(secondaryFile)
        secondaryRoot = secondaryTree.getroot()
        secondaryEntries = secondaryRoot.find("Entries")

        for child in primaryEntries.findall("Entry"):
            primaryID = child.find("ID")
            primaryDefaultText = child.find("DefaultText")
            primaryFemaleText = child.find("FemaleText")

            for child in secondaryEntries.findall("Entry"):
                if child.find("ID").text == primaryID.text:
                    secondaryID = child.find("ID")
                    secondaryDefaultText = child.find("DefaultText")
                    secondaryFemaleText = child.find("FemaleText")

            if primaryFemaleText.text is not None and secondaryFemaleText.text is not None:
                primaryFemaleText.text = primaryFemaleText.text + " «" + secondaryFemaleText.text + "»"
            elif primaryFemaleText.text is None and secondaryFemaleText.text is not None and primaryDefaultText.text is not None:
                primaryFemaleText.text = primaryDefaultText.text + " «" + secondaryFemaleText.text + "»"
            elif primaryFemaleText.text is not None and secondaryFemaleText.text is None and secondaryDefaultText.text is not None:
                primaryFemaleText.text = primaryFemaleText.text + " «" + secondaryDefaultText.text + "»"
            else:
                pass
                #print("NoneType FemaleText at: " + primaryID.text)

            if primaryDefaultText.text is not None and secondaryDefaultText.text is not None:
                primaryDefaultText.text = primaryDefaultText.text + " «" + secondaryDefaultText.text + "»"
            else:
                pass
                #print("NoneType DefaultText at: " + primaryID.text)

        primaryTree.write(newFile, encoding="utf-8", xml_declaration=True, method="xml")

    def createLanguageXML(self, primaryXML, newFile):
        primaryTree = ET.parse(primaryXML)
        primaryRoot = primaryTree.getroot()
        primaryRoot.find("Name").text = self.newName
        primaryRoot.find("GUIString").text = self.newLang

        try:
            newFile.touch(exist_ok=True)
        except:
            print("No parent folder, creating parent folder...")
            newFile.parent.mkdir(parents=True, exist_ok=True)
            newFile.touch(exist_ok=True)

        primaryTree.write(newFile, encoding="utf-8", xml_declaration=True, method="xml")

root = Tk()
root.resizable(False, False)
root.title("PoE/Tyranny Text Merger")

app = App(root)

root.mainloop()
root.destroy()
