import smtplib
from email.mime.text import MIMEText

msg = MIMEText('The body of the email is here')  # 这里是你的信件中的内容
msg['From'] = 'm15555081413@163.com'  # 这里是发送人的邮箱.
msg['To'] = '1104963431@qq.com'  # 这里是接收信件人的邮箱
msg['Subject'] = 'an email'  # 这里是信件的标题

server = smtplib.SMTP('smtp.163.com') # 163 SMTP 服务器地址
server.login(user='m15555081413@163.com', password='xs1104963601')
# user 是发送人的邮箱, password 是你的授权码!授权码!授权码!(这不是我生日.)
server.send_message(msg=msg)

server.close()
