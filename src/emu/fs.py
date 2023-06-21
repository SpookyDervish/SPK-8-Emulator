"""The filesystem module for the SPK-8 emulator. Includes functions for emulating a virtual filesystem and interacting with it.
"""
import json
import os


files = {"": {}}
directory = files[""]


def init():
    """Install the virtual filesystem and create `fs.json`.
    """
    if not os.path.isfile("fs.json"):
        file = open("fs.json", "a")
    else:
        file = open("fs.json", "w")

    file.write("")
    json.dump(files, file)

    file.close()

def ls():
    """Returns a list of all files and folders in the specified directory.
    """
    values = []
    for key in directory:
        value = directory[key]
        values.append(value)
    return values

def cd(dir: str):
    global directory

    if dir == "~":
        directory = files[""]

    directory = directory[dir]

def mkdir(name: str):
    global directory
    directory[name] = {}

def create_file(name: str):
    global directory
    directory[name] = ""

def rm(name: str):
    global directory
    return directory.pop(name)

def writef(name: str, text: str, mode="w"):
    if not directory[name]:
        raise FileNotFoundError
    
    if mode == 'w':
        directory[name] = text
    elif mode == "a":
        directory[name] = directory[name] + text