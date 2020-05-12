from orcsome import get_wm
from orcsome.actions import *

#################################################################################
# Some from: https://github.com/BlaineEXE/window-layout
#################################################################################
import argparse
import os
import os.path as path
import pickle
import re
import statistics as stat
import subprocess

def RunCommand(command):
    res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise Exception("could not run command: " + command + "\nresult: " + res)
    return(res.stdout.decode("utf8"))

class Window:
    def __init__(self):
        return

    def NewFromWmctrlListLine(self, line):
        fields = line.split()
        self.id = fields[0]
        self.desktop = int(fields[1])
        self.x, self.y, self.w, self.h= getWindowXYWH(self.id)

def GetWindows():
    rawWins = RunCommand(["wmctrl", "-pl"])
    wins = []
    for line in rawWins.splitlines(0):
        w = Window()
        w.NewFromWmctrlListLine(line)
        if w.desktop < 0:
            continue
        wins += [w]
    return(wins)

def getWindowXYWH(windowID):
    rawInfo = RunCommand(["xwininfo", "-id", windowID])
    x = extractValueFromXwininfoLine("Absolute upper-left X", rawInfo)
    y = extractValueFromXwininfoLine("Absolute upper-left Y", rawInfo)
    w = extractValueFromXwininfoLine("Width", rawInfo)
    h = extractValueFromXwininfoLine("Height", rawInfo)
    return int(x), int(y), int(w), int(h)

def extractValueFromXwininfoLine(fullFieldText, multilineText):
    matcher = re.compile(r"{}\:\s+(-?\d+)".format(fullFieldText))
    match = matcher.search(multilineText)
    return match.group(1)

# saved 总是0 current 总是1
def Matches(savedWins, currentWins):
    winMatches = []
    for i in savedWins:
        for j in currentWins:
            if i.id == j.id:
                if i.x==j.x and i.y==j.y and i.w==j.w and i.h==j.h:
                    continue
                winMatches += [[i, j]]
    return winMatches

def IsDiff(savedWins, currentWins):
    for i in currentWins:
        _diff = True
        for j in savedWins:
            if i.id == j.id:
                if i.x==j.x and i.y==j.y and i.w==j.w and i.h==j.h:
                    _diff = False
        if _diff is True:
            return True
    return False

def UnExist(savedWins, currentWins):
    unExist = []
    for i in currentWins:
        _unexist = True
        for j in savedWins:
            if i.id == j.id:
                _unexist = False
        if _unexist is True:
            unExist += [i]
    return unExist

def SetGeometry(windowMatch):
    saved = windowMatch[0]
    currID  = windowMatch[1].id
    RunCommand(["wmctrl",  "-i", "-r", currID,
        "-e", "0,{},{},{},{}".format(saved.x , saved.y , saved.w, saved.h)])

def HideWindow(window):
    currID = window.id
    print(currID)
    RunCommand(["xdotool",  "windowminimize", currID])
#################################################################################

wm = get_wm()

_back = []
_forward = []

@wm.on_property_change('_NET_WM_STATE')
def property():
    append_wins()

@wm.on_create
def create():
    append_wins()

def append_wins():
    global _forward, _back
    wins = GetWindows()
    if len(_back)==0 or IsDiff(_back[-1], wins):
        _back.append(wins)
        _forward.clear()

@wm.on_key('Mod+u')
def forward_wins():
    global _forward, _back
    savedWins = _forward.pop()
    _back.append(savedWins)
    change_wins(savedWins)

@wm.on_key('Mod+d')
def back_wins():
    global _forward, _back
    savedWins = _back.pop()
    _forward.append(savedWins)
    change_wins(savedWins)

def change_wins(savedWins):
    currentWins = GetWindows()
    matches = Matches(savedWins, currentWins)
    unexists = UnExist(savedWins, currentWins)

    for m in matches:
        SetGeometry(m)
    for u in unexists:
        HideWindow(u)
        
