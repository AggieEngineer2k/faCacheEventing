import azure.functions as func
import json
import logging
import redis
import datetime

def main(event: func.EventGridEvent):
    jsonevent = event.get_json()

    #result = json.dumps({
    #    'id': event.id,
    #    'data': jsonevent,
    #    'topic': event.topic,
    #    'subject': event.subject,
    #    'event_type': event.event_type,
    #})

    #logging.info('Python EventGrid trigger processed an event.')
    #logging.info('%s', result)

    try:
        # Connect to Azure Cache for Redis.
        r = redis.Redis(host='rcCacheEventing.redis.cache.windows.net', port=6380, db=0, ssl=True, password='cQM2lM2YO5zHSAkdUrJTNzqdzUuMF5TRCAzCaF16CqU=', decode_responses=True)
        
        # Construct the sorted set element's name using the site and extruder from the JSON payload.
        name = "site:{site}:extruder:{extruder}".format(site = jsonevent['site'], extruder = jsonevent['extruder'])
        
        # Construct the sorted set element, using the JSON payload as the data and the timestamp's seconds as the score.
        # Extract the timestamp from the JSON payload as a datetime.
        # Calculate the timestamp's ticks since 0001-01-01 00:00:00.
        date = datetime.datetime.strptime(jsonevent['timestamp'], "%Y-%m-%d %H:%M:%S.%f")        
        ticks = (date - datetime.datetime(1,1,1)).total_seconds() * 10**7
        mapping = {json.dumps(jsonevent): ticks}
        
        logging.info('Adding name "%s" with mapping "%s" to Redis.', name, mapping)
        
        # Add the element to the sorted set. Since the JSON payload contains fields to uniquely identify a prediction, there should never be duplicates.
        r.zadd(name, mapping)
    except:
        logging.error('Python EventGrid trigger failed to update Azure Cache for Redis.')