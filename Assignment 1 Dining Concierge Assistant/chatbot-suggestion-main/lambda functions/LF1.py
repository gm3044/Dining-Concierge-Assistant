import json
import boto3
import time
import datetime
import os
import logging
import dateutil.parser

#??
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def close(intent_request, session_attributes, fulfillment_state, message):
    print(intent_request)
    intent_request["sessionState"]["intent"]["state"] = fulfillment_state
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "activeContexts": intent_request["sessionState"]["activeContexts"],
            "dialogAction": {"type": "Close"},
            "intent": intent_request["sessionState"]["intent"],
        },
        "messages": [message],
        "sessionId": intent_request["sessionId"],
        "requestAttributes": intent_request["requestAttributes"]
        if "requestAttributes" in intent_request
        else None,
    }


def validDate(diningDate):
    if datetime.datetime.strptime(diningDate['value']['interpretedValue'], '%Y-%m-%d').date() < datetime.date.today():
        return False
    return True
       
def validTime(diningDate, diningTime):
    if datetime.datetime.strptime(diningDate['value']['interpretedValue'], '%Y-%m-%d').date() == datetime.date.today():
        if datetime.datetime.strptime(diningTime['value']['interpretedValue'], '%H:%M').time() < datetime.datetime.now().time():
            return False
    return True
 
def validCuisine(diningCuisine):
    correctCuisine = ['french', 'chinese', 'japanese', 'indian','greek', 'spanish', 'american', 'mexican', 'turkish', 'thai', 'korean', 'italian']
    if  diningCuisine['value']['interpretedValue'].lower() not in correctCuisine:
        return False
    return True
    
def validPeople(numPeople):
    return True


def validSlots(location, diningCuisine, numPeople, diningDate, diningTime, email):
    
    result = []
    if location is None:
        result = ['Location', 'What city or city area are you looking to dine in?']
        print('Im here')
        print(result)
        return (False, result)
    
    if diningCuisine is None:
        result = ['Cuisine', 'What cuisine would you like to try?']
        return (False, result)
    elif not validCuisine(diningCuisine):
            result = validResult('Cuisine')
            return (False, result)
            
    if numPeople is None:
        result = ['NumberOfPeople', 'Ok, how many people are in your party?']
        return (False, result)
    elif not validPeople(numPeople):
        result = validResult('NumberOfPeople')
        return (False, result)
    
    if diningDate is None:
        result = ['DiningDate', 'A few more to go. What date?']
        return (False, result)
    elif not validDate(diningDate):
        result = validResult('DiningDate')
        return (False, result)
        
        
    if diningTime is None:
        result = ['DiningTime', 'What time?']
        return (False, result)
    elif not validTime(diningDate, diningTime):
        result = validResult('DiningTime')
        return (False, result)
    
    if email is None:
        result = ['Email', 'Great. Lastly, I need your email address so I can send you my findings.']
        return (False, result)
    
    return (True, result)

# helper function to create
def validResult(slot):
    message = 'Please enter valid' + slot
    return [slot, message]

#----------------

def pushSQS(slots):
    #sqs = boto3.client('sqs')
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='ChatQf.fifo')
    #url = 'https://sqs.us-west-2.amazonaws.com/571763095654/ChatQf.fifo'
    
    location = slots['Location']['value']['interpretedValue']
    cuisine = slots['Cuisine']['value']['interpretedValue']
    numP =  slots['NumberOfPeople']['value']['interpretedValue']
    date = slots['DiningDate']['value']['interpretedValue']
    time = slots['DiningTime']['value']['interpretedValue']
    email = slots['Email']['value']['interpretedValue']
    
    response = queue.send_message(
        #QueueUrl=url,
        MessageGroupId='LF1',
        MessageDeduplicationId='LF1',
        MessageBody=json.dumps({
            'Location': location,
            'Cuisine': cuisine,
            'NumberOfPeople': numP,
            'Date': date,
            'Time': time,
            'Email': email
        })
    )
    print(response)



def dining_suggestion(request, invoSource):
    intent_request = request
    request = request['sessionState']
    curIntent = request['intent']['name']
    slots = request['intent']['slots']
    sessionAttributes = request['sessionAttributes']
    
    location = slots['Location']
    cuisine = slots['Cuisine']
    numP =  slots['NumberOfPeople']
    date = slots['DiningDate']
    time = slots['DiningTime']
    email = slots['Email']
    
    print(invoSource)
    if invoSource == 'DialogCodeHook':
        result = validSlots(location,cuisine, numP, date, time, email)
        if not result[0]:
            print(result)
            slots[result[1][0]] = None
            return {
            "sessionState": {
                    "dialogAction": {
                        "slotToElicit": result[1][0],
                        "type": "ElicitSlot"
                    },
                    "intent": {
                        "name": curIntent,
                        "slots": slots,
                        "state": "InProgress"
                }    },
                "messages": [{
                        "contentType": 'PlainText',
                        "content": result[1][1]
                    }]
                
            }
         
    
    print('#######fulfilled invoSource here')
    pushSQS(slots)
    message = {"contentType": 'PlainText',
                "content": 'You all set'}
    fulfillment_state = 'Fulfilled'
    print(close(intent_request, sessionAttributes, fulfillment_state, message))
    return close(intent_request, sessionAttributes, fulfillment_state, message)

def greeting_thankyou(isGreeting, current):
    if isGreeting:
        return  {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent"
            },
            "intent": {
                "state":"Fulfilled"
                
            },
        },
        "messages": [{
                "contentType": 'PlainText',
                "content": 'Hi there, how can I help?'}]
        }
    else:
        return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent"
            },
            "intent": {
                "name": current['name'],
                "slots": current['slots']
            }
        },
        "messages": [{
                "contentType": 'PlainText',
                "content": 'You’re welcome.'}]
      
    }



def lambda_handler(event, context):
    
    #log event
    #logger.debug('event.bot.name={}'.format(event['bot']['name']))

    #distinguish intent event
    if 'sessionState' in event:
        
        currentIntent = event['sessionState']['intent']
        invoSource = event['invocationSource']
        
        #set time envirnment
        os.environ['TZ'] = 'America/New_York'
        time.tzset()
        print(currentIntent)
        if currentIntent['name'] == 'GreetingIntent':
            return greeting_thankyou(0, currentIntent)
        elif currentIntent['name'] == 'DiningSuggestionIntent':
            return dining_suggestion(event, invoSource)
        elif currentIntent['name'] == 'ThankYouIntent':
            return greeting_thankyou(1, currentIntent)
        else:
            raise Exception('Intent not supported')
    





