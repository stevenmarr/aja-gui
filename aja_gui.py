#BASIC AJA Control GUI
#BASIC UNTESTED Application for use
#Steven Marr stevenmarr@ceavco.com written: 20130402

from Tkinter import *
import tkMessageBox
from aja.embedded.rest.kipro import Client

import time
import argparse
import re
TIMECODE_RE = re.compile(r"^[0-9]+:+[0-9]+:+[0-9]+:+[0-9]")

client_list=[]
try:
    client1 = Client('http://192.168.1.2')
except:
    print "Can't Connect to Client 1"
    quit()
client2 = Client('http://192.168.1.2')
try:
    client2 = Client('http://192.168.1.3')
except:
    print "Can't Connect to Client 2"
    quit()
client_list.append(client1)
client_list.append(client2)

#def getClient():
#    client_ip = client_entry.get()
#    try:
#        client = Client(client_ip)
#    except:
#        return None
#    client_list.append(client)

def playClip():
    for client in client_list:
        client.cueToTimecode(getTC())
        #print getTC()
        time.sleep(.3)
    for client in client_list:
        client.play()

def stopClip():
    for client in client_list:
        client.stop()
    time.sleep(.3)
def prevClip():
    for client in client_list:
        client.previousClip()
    time.sleep(1)
    clip_name.itemconfigure(t, text=client_list[0].getCurrentClipName())
    time.sleep(.3)
def nextClip():
    for client in client_list:
        client.nextClip()
    time.sleep(1)
    clip_name.itemconfigure(t, text=client_list[0].getCurrentClipName())
    time.sleep(.3)
def getTC():
    timecode = timecode_entry.get()

    if TIMECODE_RE.match(timecode) == None:

        timecode_entry.delete(0, END)
        timecode_entry.insert(INSERT,'00:00:00:00')
        return '00:00:00:00'
    else:
        return timecode

top = Tk()
# Title
t = Label(top, text = "CEAVCO AV AJA Kipro Controller")
t.pack()
#Current Clip
clip_name = Canvas(top , height = 20, width = 300)
t = clip_name.create_text(150,10, text = client_list[0].getCurrentClipName() )
clip_name.pack()
#Connected Clients
for client in client_list:
    client_name = Label(top, fg="#f00", text = "Kipro's Controlled %s" %client.url)
    client_name.pack()
#Timecode
timecode_entry = Entry(top, justify = 'center',bd =2)
timecode_entry.insert(INSERT,'00:00:00:00')
timecode_entry.pack()
tc_butt = Button(top, text ="Use Timecode", width = '20',
                command = getTC)
tc_butt.pack()
#PLAY/STOP Buttons
PlayButt = Button(top, text ="Play", width = '20', command =           playClip)
PlayButt.pack()
StopButt = Button(top, text ="Stop", width = '20', command = stopClip)
StopButt.pack()
PrevButt = Button(top, text ="Prev Clip", width = '20', command = prevClip)
PrevButt.pack()
NextButt = Button(top, text ="Next Clip", width = '20', command = nextClip)
NextButt.pack()

top.mainloop()
