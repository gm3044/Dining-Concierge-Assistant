import boto3

client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):

    msg_from_usr = event['messages'][0]
    msg_from_usr = msg_from_usr['unstructured']['text']

    print(f"Message from frontend: {msg_from_usr}")
    
    response = client.recognize_text(botId='XWLGJEDACY',botAliasId='3UAWZECO1H',localeId='en_US',sessionId='testuser',text=msg_from_usr)
    
    msg_from_lex = response.get('messages',[])
    if msg_from_lex:
        print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
        print(response)
        
        if response['messages'][0] is not None or len(response['messages'][0]) > 0:
            botMessage = response['messages'][0]
        
        print("Bot message", botMessage)
        
        botResponse =  [{
            'type': 'unstructured',
            'unstructured': {
              'text': botMessage['content']
            }
          }]
        
          
        return {
            'statusCode': 200,
            'messages': botResponse
        }
        return resp
    
