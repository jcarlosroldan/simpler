from smtplib import SMTP
from threading import Thread
from email.message import EmailMessage
from email.headerregistry import Address
from email.policy import default

# --- general methods ---------------------------------------------------------

def compose(from_mail: str, dest_mail: object, from_name: str = None, dest_name: object = None, text: str = '', text_type: str = 'plain', subject: str = '', blocking: bool = False):
	message = EmailMessage(policy=default)
	message['From'] = Address(from_name, from_mail)
	message['To'] = Address(dest_name, dest_mail)
	message['Subject'] = subject
	if text_type == 'plain':
		message.set_content(text)
	else:
		message.set_content(text, subtype='html')
	return message

def send(smtp_server: str, password: str, mail: str, message: EmailMessage) -> None:
	''' Sends a message. '''
	server = SMTP(smtp_server)
	server.starttls()
	server.login(mail, password)
	server.send_message(message)
	server.quit()