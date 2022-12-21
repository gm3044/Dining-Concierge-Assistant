import json
import boto3
import requests
from boto3.dynamodb.conditions import Key


#config
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('Yelp')
username = 'asura'
password = 'Ciel862423!'
headers = {"Content-Type": "application/json"}
url = 'https://search-restaurants-7pw6cfkb4emr2bps3ryf5etgsi.us-west-2.es.amazonaws.com/restaurants/Restaurants'

def postRequests():
    resp = table.scan()
    print('scan done')

    for item in resp['Items']:
        body = {"id": item['id'], "Cuisine": item['cuisine']}
        r = requests.post(url, data=json.dumps(body), auth=(username,password), headers=headers)

def lambda_handler(event, context):

    postRequests()
    # scrape()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

