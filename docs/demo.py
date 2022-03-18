from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridPublisherClient, EventGridEvent
import redis
import time

# Declare time constants.
ticks_00_00 = 6.30822816e+17 # 2000-01-01 00:00:00
ticks_00_05 = 6.30822819e+17 # 2000-01-01 00:05:00
ticks_00_10 = 6.30822822e+17 # 2000-01-01 00:10:00
ticks_00_15 = 6.30822825e+17 # 2000-01-01 00:15:00
ticks_00_20 = 6.30822828e+17 # 2000-01-01 00:20:00
ticks_00_25 = 6.30822831e+17 # 2000-01-01 00:25:00
ticks_00_30 = 6.30822834e+17 # 2000-01-01 00:30:00
ticks_00_35 = 6.30822837e+17 # 2000-01-01 00:35:00
ticks_00_40 = 6.30822840e+17 # 2000-01-01 00:40:00
ticks_00_45 = 6.30822843e+17 # 2000-01-01 00:45:00
ticks_1_second = 10e6

# Connect to Azure Cache for Redis server.
redisClient = redis.Redis(host='rcCacheEventing.redis.cache.windows.net', port=6380, db=0, ssl=True, password='cQM2lM2YO5zHSAkdUrJTNzqdzUuMF5TRCAzCaF16CqU=', decode_responses=True)

# Connect to Event Grid Topic.
key = 'sMtf3ieNHThwCkXJMTcl3Rb/Yo9OaUZalEj4XBLbANY='
endpoint = 'https://egtcacheeventing.centralus-1.eventgrid.azure.net/api/events'
credential = AzureKeyCredential(key)
eventGridClient = EventGridPublisherClient(endpoint, credential)

# Purge the Redis Cache.
redisClient.delete('site:ppc:extruder:7-1',1)
redisClient.zcard('site:ppc:extruder:7-1')

# ============================================================================#

# Initialize the Redis Cache using Event Grid.
events = []
events.append(EventGridEvent(subject="PoC",data={
    "timestamp": "2000-01-01 00:00:00.000", 
    "site": "ppc", 
    "extruder": "7-1", 
    "predicted": 0.5, 
    "lcl": 0.0, 
    "target": 0.5, 
    "ucl": 1.0, 
    "model": "7-1 Model", 
    "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:05:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.2, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:10:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.3, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:15:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.4, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:20:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.5, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:25:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.6, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:30:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.7, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
eventGridClient.send(events)
events.clear()

# Give the function app a second to catch up.
time.sleep(2)

# Get the cardinality of the sorted set.
redisClient.zcard('site:ppc:extruder:7-1')

# ============================================================================#

# Get the first 7 elements with their scores.
redisClient.zrange('site:ppc:extruder:7-1',0,7,withscores=True)

# Get the elements with scores between 00:05 and 00:25
redisClient.zrangebyscore('site:ppc:extruder:7-1',ticks_00_05,ticks_00_25, withscores=True)

# Get last element by score.
redisClient.zrevrangebyscore('site:ppc:extruder:7-1','+inf','-inf',start=0,num=1)

# Get latest element since 00:30 (exclusive by adding 1 second offset)
redisClient.zrevrangebyscore('site:ppc:extruder:7-1','+inf',ticks_00_30 + ticks_1_second,start=0,num=1)

# Remove all elements with scores up to 00:00
redisClient.zremrangebyscore('site:ppc:extruder:7-1',0,ticks_00_00)
redisClient.zcard('site:ppc:extruder:7-1')

# ============================================================================#

# Add additional elements directly
# Note: This is NOT advised due to the ease of creating even a *slightly* different member, which would create two entries for the same score/timestamp.
#       Best left to EventGrid/Function App for single-responsibility principle.
#redisClient.zadd('site:ppc:extruder:7-1', {json.dumps({"timestamp": "2000-01-01 00:35:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.8, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"}): ticks_00_35})
#redisClient.zadd('site:ppc:extruder:7-1', {json.dumps({"timestamp": "2000-01-01 00:40:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.9, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"}): ticks_00_40})
#redisClient.zadd('site:ppc:extruder:7-1', {json.dumps({"timestamp": "2000-01-01 00:45:00.000", "site": "ppc", "extruder": "7-1", "predicted": 1.0, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"}): ticks_00_45})

# Add elements through eventing (preferred)
events.clear()
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:35:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.8, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:40:00.000", "site": "ppc", "extruder": "7-1", "predicted": 0.9, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
events.append(EventGridEvent(subject="PoC",data={"timestamp": "2000-01-01 00:45:00.000", "site": "ppc", "extruder": "7-1", "predicted": 1.0, "lcl": 0.0, "target": 0.5, "ucl": 1.0, "model": "7-1 Model", "resinName": "HHM 5502BN"},event_type="Azure.Sdk.Demo",data_version="2.0"))
eventGridClient.send(events)
# Give the function app a second to catch up.
time.sleep(2)
# Get NEW last element by score.
redisClient.zrevrangebyscore('site:ppc:extruder:7-1','+inf','-inf',start=0,num=1)

# ============================================================================#

# Remove elements from all sorted sets matching the site/extruder pattern with scores up through 00:30
running_results = []
cursor, results = redisClient.scan(0,match='site:*:extruder:*',count=1000)
running_results += results
while cursor != 0:
    cursor, results = redisClient.scan(cursor,match='site:*:extruder:*',count=1000)
    running_results += results

for key in set(running_results):
    redisClient.zremrangebyscore(key,0,ticks_00_30)

# Get the remaining elements with their scores.
redisClient.zrange('site:ppc:extruder:7-1',0,7,withscores=True)

# ============================================================================#

# Remove the entire set.
redisClient.delete('site:ppc:extruder:7-1',1)