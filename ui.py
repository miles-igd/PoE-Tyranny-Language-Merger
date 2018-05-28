from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkinter import *
from pathlib import Path
from shutil import copytree

import xml.etree.ElementTree as ET
import ast

class App:
    def __init__(self, master):
        self.locations = []
        self.languages = []
        self.valid = False

        self.pathLabel = Label(master, text="Game Folder:")
        self.pathEntry = Entry(master, width=50)
        self.pathButton = Button(master, text="...", width=3, command=self.setRootPath)

        self.gameName = StringVar()
        self.gameLabel = Label(master, text="Game:")
        self.gameNameLabel = Label(master, textvariable=self.gameName)

        self.primaryLabel = Label(master, text="Primary Language")
        self.statusVar = StringVar()
        self.statusLabel = Label(master, textvariable=self.statusVar)
        self.secondaryLabel = Label(master, text = "<Secondary Language>")

        self.primaryList = ttk.Combobox(master, justify="center", state="readonly", width=25)
        self.mergeButton = Button(master, text="Merge", command=self.mergeText)
        self.secondaryList = ttk.Combobox(master, justify="center", state="readonly", width=25)

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

    def recursiveDir(self, filepath, query, locations = []):
        for child in filepath.iterdir():
            if child.is_dir():
                if (child.name==query):
                    locations.append(child)
                self.recursiveDir(child, query, locations)
                #print(child)

        return locations

    def setRootPath(self, *args):
        filepath = filedialog.askdirectory(initialdir = "/", title="Select file")
        if (filepath == ""):
            return None
        self.pathEntry.delete(0, END)
        self.pathEntry.insert(0, filepath)
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
        for child in rootPath.iterdir():
            if child.name == "PillarsOfEternity.exe":
                return "Pillars of Eternity"
            elif child.name == "Tyranny.exe":
                return "Tyranny"
            elif child.name == "PillarsOfEternity2.exe":
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
        if self.valid:
            self.statusVar.set("Working...")
            primaryLanguage = ast.literal_eval(self.primaryList.get())
            secondaryLanguage = ast.literal_eval(self.secondaryList.get())

            self.newCode = primaryLanguage['code'] + "_" + secondaryLanguage['code']
            self.newName = primaryLanguage['code'] + "/" + secondaryLanguage['code']
            self.newLang = primaryLanguage['lang'] + "/" + secondaryLanguage['lang']

            for locPath in self.locations:
                rootPath = locPath
                primaryPath = rootPath / primaryLanguage['code'] / 'text' / 'conversations'
                secondaryPath = rootPath / secondaryLanguage['code'] / 'text' / 'conversations'
                newPath = rootPath / self.newCode / 'text' / 'conversations'
                copytree(rootPath / primaryLanguage['code'], rootPath / self.newCode)
                #newPath.mkdir(parents=True, exist_ok=True)

                self.searchStringtables(primaryPath, secondaryPath, newPath)

            rootPath = self.locations[0]
            self.createLanguageXML(rootPath / primaryLanguage['code'] / "language.xml", rootPath / self.newCode / "language.xml")
            self.statusVar.set("Done!")
        else:
            messagebox.showerror(title="ERROR", message="Game folder not found")

    #def mergeAction(self, primaryPath, secondaryPath):
    def searchStringtables(self, primaryPath, secondaryPath, newPath):
        for child in primaryPath.iterdir():
            if child.is_dir():
                newPath.mkdir(parents=True, exist_ok=True)
                self.searchStringtables(child, secondaryPath / child.relative_to(primaryPath), newPath / child.relative_to(primaryPath))

            elif child.suffix == ".stringtable":
                newFile = newPath / child.name
                try:
                    newFile.touch(exist_ok=True)
                except:
                    print("No parent folder, creating parent folder...")
                    newFile.parent.mkdir(parents=True, exist_ok=True)
                    newFile.touch(exist_ok=True)

                self.mergeFile(child, secondaryPath / child.name, newFile)

            else:
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

            try:
                primaryDefaultText.text = primaryDefaultText.text + " «" + secondaryDefaultText.text + "»"
            except:
                print("NoneType at: " + primaryID.text)
                pass

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

app = App(root)

root.mainloop()
root.destroy()
