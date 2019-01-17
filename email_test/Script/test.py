from GiveAnAlarm.email_give_an_alarm import send_func, send_email_api

# msg_list = []
# war_msg = 'haha'
title_format = 'New task Warning! PT: %s'
to_addr = 'BruceX@selmuch.com'
#
# send_func(msg_list, war_msg, title_format, to_addr)

send_api = 'https://sys.selmetrics.com/pyapi/send'
send_dict = dict(ta=to_addr, ts=title_format % (11), ms='xs')
resp = send_email_api(send_api, send_dict)
print(resp.text)