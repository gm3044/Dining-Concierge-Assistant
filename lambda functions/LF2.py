import boto3
from requests_aws4auth import AWS4Auth
import json
import requests
import random

sqsClient = boto3.client('sqs')
queueUrl = 'https://us-west-2.queue.amazonaws.com/571763095654/ChatQf.fifo'

def pullSQS():
    response = sqsClient.receive_message(
        QueueUrl = queueUrl,
        MaxNumberOfMessages=5,
        AttributeNames=['All'],
        VisibilityTimeout=30,
        WaitTimeSeconds=0,
        MessageAttributeNames=['All']
        )
    return response


def findRestaurantsOP(cuisine):
    region = 'us-west-2'
    service = 'es'
    KEY_ID = 'AKIAYKH54PBTLJM776F3' #your ID
    SECRET_KEY = 'OMHw8IahwkBrga6ON8AdhTZ6WLVyMvQCHytLqAHj'
    credentials = boto3.Session(aws_access_key_id=KEY_ID,
                          aws_secret_access_key=SECRET_KEY,
                          region_name=region).get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    host = 'search-restaurants-7pw6cfkb4emr2bps3ryf5etgsi.us-west-2.es.amazonaws.com'
    index = 'restaurants'
    url = 'https://' + host + '/' + index + '/_search'
    
    query = {
        "size": 999,
        "query": {
            "multi_match": {
                "query": cuisine
            }
        }
    }

    headers = { "Content-Type": "application/json" }
    response = requests.get(url,auth=awsauth, headers=headers, data=json.dumps(query))

    res = response.json()
    print(res)
    noOfHits = res['hits']['total']
    hits = res['hits']['hits']
    print(hits)
    buisinessIds = []
    for hit in hits:
        buisinessIds.append(str(hit['_source']['id']))
    return random.sample(buisinessIds, 3)

def getRestaurantFromDb(restaurantIds):
    res = []
    client = boto3.resource('dynamodb')
    table = client.Table('Yelp')
    for id in restaurantIds:
        response = table.get_item(Key={'id': id})
        res.append(response)
    return res

def getMsgToSend(resdetails,message):
    messageBody = json.loads(message['Body'])
    location = messageBody['Location']
    cuisine = messageBody['Cuisine']
    numP = messageBody['NumberOfPeople']
    date = messageBody['Date']
    time = messageBody['Time']
 
    separator = ', '
    name1 = resdetails[0]['Item']['name']
    address1 = separator.join(resdetails[0]['Item']['address'])
    name2 = resdetails[1]['Item']['name']
    address2 = separator.join(resdetails[1]['Item']['address'])
    name3 = resdetails[2]['Item']['name']
    address3 = separator.join(resdetails[2]['Item']['address'])
    msg = 'Hello! Here are my {0} restaurant suggestions for {1} people, for {2} at {3} : 1. {4}, located at {5}, 2. {6}, located at {7},3. {8}, located at {9}. Enjoy your meal!'.format(cuisine,numP,date,time,name1,address1,name1,address2,name3,address3)
    return msg


def sendEmail(message, emailTo):
    ses_client = boto3.client("ses", region_name="us-west-2")
    CHARSET = "UTF-8"

    response = ses_client.send_email(
        Destination={
            "ToAddresses": [
                emailTo,
            ],
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": CHARSET,
                    "Data": message,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "Amazing restaurant suggestions",
            },
        },
        Source="asurashen8@gmail.com",
    )


def lambda_handler(event, context):
    # getting response from sqs queue
    sqsMessages = pullSQS()
    if "Messages" in sqsMessages.keys():
        for message in sqsMessages["Messages"]:
            
            cuisine = json.loads(message['Body'])['Cuisine']
            emailTo = json.loads(message['Body'])['Email']
            restaurantIds = findRestaurantsOP(cuisine)
            restaurantDetails = getRestaurantFromDb(restaurantIds)
            msgToSend = getMsgToSend(restaurantDetails,message)
            sendEmail(msgToSend, emailTo)
            sqsClient.delete_message(QueueUrl=queueUrl,ReceiptHandle=message['ReceiptHandle'])

    return
     


