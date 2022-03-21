from asyncio.windows_events import NULL
from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridPublisherClient, EventGridEvent
from datetime import datetime, timedelta
import json
import redis
from textwrap import fill
#import time
from tkinter import *
import tksheet

window = Tk()
window.title("Cache Eventing Demo Rig")

entryFrame = Frame(window)
entryFrame.grid(row=0, column=0, sticky="nswe")
buttonFrame = Frame(window)
buttonFrame.grid(row=0, column=1, sticky="nswe")
imageFrame = Frame(window)
imageFrame.grid(row=0, column=2, sticky="nswe")
textFrame = Frame(window)
textFrame.grid(row=1, column=0, columnspan=3, sticky="nswe")
sheetFrame = Frame(window)
sheetFrame.grid(row=2, column=0, columnspan=3, sticky="nswe")

labelSite = Label(entryFrame, text="Site:")
labelSite.grid(row=0, column=0, sticky='e')
entrySite = Entry(entryFrame)
entrySite.insert(0, "ppc")
entrySite.grid(row=0, column=1)
labelExtruder = Label(entryFrame, text="Extruder:")
labelExtruder.grid(row=1, column=0, sticky='e')
entryExtruder = Entry(entryFrame)
entryExtruder.insert(0, "7-1")
entryExtruder.grid(row=1, column=1)
labelModel = Label(entryFrame, text="Model:")
labelModel.grid(row=2, column=0, sticky='e')
entryModel = Entry(entryFrame)
entryModel.insert(0, "7-1 Model")
entryModel.grid(row=2, column=1)
labelResinName = Label(entryFrame, text="Resin Name:")
labelResinName.grid(row=3, column=0, sticky='e')
entryResinName = Entry(entryFrame)
entryResinName.insert(0, "HHM 5502BN")
entryResinName.grid(row=3, column=1)
labelFromDateTime = Label(entryFrame, text="From:")
labelFromDateTime.grid(row=4, column=0, sticky='e')
entryFromDateTime = Entry(entryFrame)
entryFromDateTime.insert(0, (datetime.utcnow() - timedelta(hours=2)).isoformat(' '))
entryFromDateTime.grid(row=4, column=1)
labelToDateTime = Label(entryFrame, text="To:")
labelToDateTime.grid(row=5, column=0, sticky='e')
entryToDateTime = Entry(entryFrame)
entryToDateTime.insert(0, datetime.utcnow().isoformat(' '))
entryToDateTime.grid(row=5, column=1)

buttonGetKeys = Button(buttonFrame, text="Get Sorted Set Keys")
buttonGetKeys.pack(fill='x')
buttonFetchAll = Button(buttonFrame, text="Fetch All")
buttonFetchAll.pack(fill='x')
buttonFetchCustomDateTimeRange = Button(buttonFrame, text="Fetch From/To")
buttonFetchCustomDateTimeRange.pack(fill='x')
buttonFetchLastTwoHours = Button(buttonFrame, text="Fetch Last Two Hours")
buttonFetchLastTwoHours.pack(fill='x')
buttonFetchLatest = Button(buttonFrame, text="Fetch Latest")
buttonFetchLatest.pack(fill='x')
buttonPublishEvent = Button(buttonFrame, text="Publish Event to Event Grid")
buttonPublishEvent.pack(fill='x')

img = PhotoImage(file='docs/Architecture.png')
Label(
    imageFrame,
    image=img
).pack()

text_box = Text(textFrame, height=10)
text_box.pack(fill='x')

try:
    # Connect to Azure Cache for Redis server.
    redisClient = redis.Redis(host='rcCacheEventing.redis.cache.windows.net', port=6380, db=0, ssl=True, password='cQM2lM2YO5zHSAkdUrJTNzqdzUuMF5TRCAzCaF16CqU=', decode_responses=True)
    text_box.insert(END, "Connected to Azure Cache for Redis.\n")
except:
    text_box.insert(END, "[ERROR] Could not connect to Azure Cache for Redis!\n")

try:
    # Connect to Event Grid Topic.
    key = 'sMtf3ieNHThwCkXJMTcl3Rb/Yo9OaUZalEj4XBLbANY='
    endpoint = 'https://egtcacheeventing.centralus-1.eventgrid.azure.net/api/events'
    credential = AzureKeyCredential(key)
    eventGridClient = EventGridPublisherClient(endpoint, credential)
    text_box.insert(END, "Connected to Azure Event Grid.\n")
except:
    text_box.insert(END, "[ERROR] Could not connect to Azure Event Grid!\n")

def appendRedisStatistics():
    info = redisClient.info()
    text_box.insert(END, "\n--- Redis Info ---\n")
    for metric in [
        'redis_version',
        'used_memory_human',
        'used_memory_peak_human',
        'maxmemory_human']:
        text_box.insert(END, "{metric}: {value}\n".format(metric = metric, value = info[metric]))

sheet = tksheet.Sheet(sheetFrame, width=800, height=200)
sheet.pack()
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

def buttonFetchCallback(fromscore, toscore, reverse : bool = False, top : int = None):
    text_box.delete("1.0", END)
    key = 'site:{site}:extruder:{extruder}'.format(site=entrySite.get(),extruder=entryExtruder.get())
    if reverse is False and top is None:
        text_box.insert(END, "ZRANGEBYSCORE {key} {min} {max} WITHSCORES\n".format(key = key, min = fromscore, max = toscore))
        records = redisClient.zrangebyscore(key,fromscore,toscore,withscores=True)
    elif reverse is False and top is not None:
        text_box.insert(END, "ZRANGEBYSCORE {key} {min} {max} WITHSCORES LIMIT 0 {count}\n".format(key = key, min = fromscore, max = toscore, count = top))
        records = redisClient.zrangebyscore(key,fromscore,toscore,withscores=True,start=0,num=top)
    elif reverse is True and top is None:
        text_box.insert(END, "ZREVRANGEBYSCORE {key} +inf -inf WITHSCORES\n".format(key = key))
        records = redisClient.zrevrangebyscore(key,'+inf','-inf',withscores=True)
    elif reverse is True and top is not None:
        text_box.insert(END, "ZREVRANGEBYSCORE {key} +inf -inf WITHSCORES LIMIT 0 {count}\n".format(key = key, count = top))
        records = redisClient.zrevrangebyscore(key,'+inf','-inf',withscores=True,start=0,num=top)

    text_box.insert(END, "ZCARD {key}\n".format(key = key))
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
    text_box.insert(END, "\nResults: {len_records} (of {cardinality})\n".format(len_records = len(records), cardinality = cardinality))
    appendRedisStatistics()

def buttonPublishEventCallback():
    event = EventGridEvent(subject="PoC",event_type="PoC.Events.NewPrediction",data_version="1.0",data={
        "timestamp": datetime.utcnow().isoformat(' '),
        "site": entrySite.get(), 
        "extruder": entryExtruder.get(), 
        "predicted": 0.5, 
        "lcl": 0.0, 
        "target": 0.5, 
        "ucl": 1.0, 
        "model": entryModel.get(), 
        "resinName": entryResinName.get()})
    eventGridClient.send(event)

def buttonGetKeysCallback():
    text_box.delete("1.0", END)
    text_box.insert(END, 'SCAN 0 MATCH site:*:extruder:*\n')
    sheet_data = []
    sheet_data.append([
        "key",
        "memory",
        "cardinality"])
    for key in redisClient.scan_iter('site:*:extruder:*'):
        text_box.insert(END, "MEMORY USAGE {key}\n".format(key = key))
        text_box.insert(END, "ZCARD {key}\n".format(key = key))
        memory = redisClient.memory_usage(key)
        cardinality = redisClient.zcard(key)
        sheet_data.append([
            key,
            memory,
            cardinality])

    sheet.set_sheet_data(sheet_data)
    sheet.set_all_cell_sizes_to_text()
    appendRedisStatistics()

buttonFetchAll.configure(command=lambda: buttonFetchCallback('-inf', '+inf'))
buttonFetchLatest.configure(command=lambda: buttonFetchCallback('-inf', '+inf', top = 1, reverse = True))
buttonFetchLastTwoHours.configure(command=lambda: buttonFetchCallback((datetime.utcnow() - timedelta(hours=2) - datetime(1,1,1)).total_seconds() * 10**7,'+inf'))
buttonPublishEvent.configure(command=buttonPublishEventCallback)
buttonGetKeys.configure(command=buttonGetKeysCallback)
buttonFetchCustomDateTimeRange.configure(command=lambda: buttonFetchCallback(
    (datetime.strptime(entryFromDateTime.get(), '%Y-%m-%d %H:%M:%S.%f') - datetime(1,1,1)).total_seconds() * 10**7,
    (datetime.strptime(entryToDateTime.get(), '%Y-%m-%d %H:%M:%S.%f') - datetime(1,1,1)).total_seconds() * 10**7))

window.mainloop()