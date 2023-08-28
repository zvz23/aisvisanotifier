import smtplib

def send_email(subject: str, body: str, email: str, password: str):
    sender_email = email
    receiver_email = email
    password = password
    
    message = f'Subject: {subject}\n\n{body}'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


