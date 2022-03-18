from asyncio.windows_events import NULL
from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridPublisherClient, EventGridEvent
from datetime import datetime, timedelta
import json
import redis
from textwrap import fill
import time
from tkinter import *
import tksheet

# Connect to Azure Cache for Redis server.
redisClient = redis.Redis(host='rcCacheEventing.redis.cache.windows.net', port=6380, db=0, ssl=True, password='cQM2lM2YO5zHSAkdUrJTNzqdzUuMF5TRCAzCaF16CqU=', decode_responses=True)

# Connect to Event Grid Topic.
key = 'sMtf3ieNHThwCkXJMTcl3Rb/Yo9OaUZalEj4XBLbANY='
endpoint = 'https://egtcacheeventing.centralus-1.eventgrid.azure.net/api/events'
credential = AzureKeyCredential(key)
eventGridClient = EventGridPublisherClient(endpoint, credential)

window = Tk()
window.title("Cache Eventing Demo Rig")
window.geometry('800x600+200+200')

labelSite = Label(text="Site:")
labelSite.grid(row=0, column=0, sticky="e")
entrySite = Entry()
entrySite.grid(row=0, column=1, sticky="w")
entrySite.insert(0, "ppc")
labelExtruder = Label(text="Extruder:")
labelExtruder.grid(row=1, column=0, sticky="e")
entryExtruder = Entry()
entryExtruder.grid(row=1, column=1, sticky="w")
entryExtruder.insert(0, "7-1")
labelModel = Label(text="Model:")
labelModel.grid(row=2, column=0, sticky="e")
entryModel = Entry()
entryModel.grid(row=2, column=1, sticky="w")
entryModel.insert(0, "7-1 Model")
labelResinName = Label(text="Resin Name:")
labelResinName.grid(row=3, column=0, sticky="e")
entryResinName = Entry()
entryResinName.grid(row=3, column=1, sticky="w")
entryResinName.insert(0, "HHM 5502BN")

text_box = Text(height=10, width=40)
text_box.grid(row=4, column=0, columnspan=2, sticky="we")

buttomFrame = Frame(window)
buttomFrame.grid(row=0, column=2, rowspan=5, sticky="nswe")
buttonFetchAll = Button(buttomFrame, text="Fetch All")
buttonFetchAll.pack(fill='x')
buttonFetchLastTwoHours = Button(buttomFrame, text="Fetch Last Two Hours")
buttonFetchLastTwoHours.pack(fill='x')
buttonFetchLatest = Button(buttomFrame, text="Fetch Latest")
buttonFetchLatest.pack(fill='x')
buttonPublishEvent = Button(buttomFrame, text="Publish Event to Event Grid")
buttonPublishEvent.pack(fill='x')

sheet = tksheet.Sheet(window, width=700, height=400)
sheet.grid(row=5, column=0, columnspan=3, sticky="nswe")
sheet.enable_bindings((
    "single_select",
    "row_select",
    "column_width_resize",
    "arrowkeys",
    "right_click_popup_menu",
    "rc_select",
    "rc_insert_row",
    "rc_delete_row",
    "copy",
    "cut",
    "paste",
    "delete",
    "undo",
    "edit_cell"))

def buttonFetchCallback(fromscore, toscore, top : int = None):
    text_box.delete("1.0", END)
    key = 'site:{site}:extruder:{extruder}'.format(site = entrySite.get(), extruder = entryExtruder.get())
    if top is None:
        text_box.insert(END, "ZRANGEBYSCORE\n")
        records = redisClient.zrangebyscore(key,fromscore,toscore,withscores=True)
    else:
        text_box.insert(END, "ZREVRANGEBYSCORE\n")
        records = redisClient.zrevrangebyscore(key,'+inf','-inf',start=0,num=top,withscores=True)

    sheet_data = []
    sheet_data.append([
        "score",
        "timestamp",
        "site",
        "extruder",
        "predicted",
        "lcl",
        "target",
        "ucl",
        "model",
        "resinName"])
    for record in records:
        #score = record[1]
        #dt = datetime(1,1,1) + timedelta(microseconds=score/10)
        memberJSON = json.loads(record[0])
        sheet_data.append([
            record[1],
            memberJSON["timestamp"],
            memberJSON["site"],
            memberJSON["extruder"],
            memberJSON["predicted"],
            memberJSON["lcl"],
            memberJSON["target"],
            memberJSON["ucl"],
            memberJSON["model"],
            memberJSON["resinName"]])

    sheet.set_sheet_data(sheet_data)
    sheet.set_all_cell_sizes_to_text()

    cardinality = redisClient.zcard('site:{site}:extruder:{extruder}'.format(site = entrySite.get(), extruder = entryExtruder.get()))
    text_box.insert(END, "Sorted Set Cardinality: {cardinality}\n".format(cardinality = cardinality))

def buttonPublishEventCallback():
    event = EventGridEvent(subject="PoC",data={
        "timestamp": datetime.utcnow().isoformat(' '),
        "site": entrySite.get(), 
        "extruder": entryExtruder.get(), 
        "predicted": 0.5, 
        "lcl": 0.0, 
        "target": 0.5, 
        "ucl": 1.0, 
        "model": "7-1 Model", 
        "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0")
    eventGridClient.send(event)

buttonFetchAll.configure(command=lambda: buttonFetchCallback('-inf', '+inf'))
buttonFetchLatest.configure(command=lambda: buttonFetchCallback('-inf', '+inf', top = 1))
buttonFetchLastTwoHours.configure(command=lambda: buttonFetchCallback((datetime.utcnow() - timedelta(hours=2) - datetime(1,1,1)).total_seconds() * 10**7,'+inf'))
buttonPublishEvent.configure(command=buttonPublishEventCallback)

window.mainloop()