from pytz import timezone
from datetime import datetime

def get_formatted_input_message(self, msg):
    input_msg = msg.lower()
    return input_msg.replace(input_msg[0:input_msg.find(' ') + 1], '')

def get_current_eastern_time():
    eastern = timezone('US/Eastern')
    time = datetime.now(eastern)
    return time