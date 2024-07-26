#[] declare host site
#[] declare port (587), user address and password
#[] declare content - sender, receiver, subject, body (message)
#[] create the message 'message = MIMEMultipart()


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

type_of_order = ''

mail_host = 'gmail.com'
port = 587
mail_user = 'cjpallari@gmail.com'
mail_pass = 'Archie2525!'

sender = 'cjpallari@gmail.com'
receiver = 'cjpallari@gmail.com'
subject = 'Order Notification'

def createMessage(type_of_order, symbol, latest_trade):
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = subject
    body = f'{type_of_order} {symbol} at {latest_trade}'
    message.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(mail_host, port)
        server.starttls()  # Secure the connection
        server.login(mail_user, mail_pass)
        text = message.as_string()
        server.sendmail(sender, receiver, text)
        print('Email notification sent successfully!')
    except Exception as e:
        print(f'Error sending email: {str(e)}')
    finally:
        server.quit()  # Disconnect from the server
    return body