from twilio.rest import TwilioRestClient

accountSID = 'AC8e87f7e3dfec4552532dcae2480fa021'
authToken = 'a576d5aac28efc503b50b5958e9276f0'
twilioCli = TwilioRestClient(accountSID, authToken)
myTwilioNumber = '+441725762055'
myCellPhone = '+447932553111'
message = twilioCli.messages.create(
    body='Experiment Finished',
    from_=myTwilioNumber,
    to=myCellPhone
)
