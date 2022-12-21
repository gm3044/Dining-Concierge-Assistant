import boto3
import datetime
import json
import requests
from decimal import *
from time import sleep


KEY_ID = 'AKIAYKH54PBTLJM776F3' #your ID
SECRET_KEY = 'OMHw8IahwkBrga6ON8AdhTZ6WLVyMvQCHytLqAHj' #your Secret key
dynamodb = boto3.resource(service_name='dynamodb',
                              aws_access_key_id=KEY_ID,
                              aws_secret_access_key=SECRET_KEY,
                              region_name="us-west-2",
                             )
table = dynamodb.Table('Yelp')
    
API_KEY = 'dVQdT3yzHA-rXtb8e4XNU7meJg88VC-youv-WRgt0NZ5ngoJCgdcKO9i54GHxH9ctfWMEul8kBqaT6o7qa1euh2kvj2ttewsJA3kc5meornF2Xdyg_xuvnxMqBk3Y3Yx'
PATH = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization': 'bearer %s' % API_KEY}
cuisines = ['chinese', 'korean', 'japanese', 'vietnamese', 'thai', 'indian', 'italian', 'american']
restaurants = {}

def addItems(data, cuisine):
    global restaurants
    with table.batch_writer() as batch:
      for i in data:
              if i["alias"] not in restaurants:
                i['cuisine'] = cuisine
                i["rating"] = Decimal(str(i["rating"]))
                i['insertedAtTimestamp'] = str(datetime.datetime.now())
                i["coordinates"]["latitude"] = Decimal(str(i["coordinates"]["latitude"]))
                i["coordinates"]["longitude"] = Decimal(str(i["coordinates"]["longitude"]))
                i['address'] = i['location']['display_address']
                i.pop("distance", None)
                i.pop("location", None)
                batch.put_item(Item=i)
                # print(i)

def batch_offset(cuisine,offset):
  params = {'location': 'Manhattan',
            'offset': offset,
            'limit': 50,
            'term': cuisine + " restaurants"}
  response = requests.get(PATH, headers = HEADERS, params=params)
  return response.json()

def lambda_handler(event, context):
    for keyword in cuisines:
        for i in range(0,999,50):
            data = batch_offset(keyword,i)
            addItems(data["businesses"], keyword)


