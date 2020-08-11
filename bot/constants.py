import os

TIMEZONE = 'Australia/Melbourne'
BOT_CHANNEL = 0
OTHER_CHANNELS = ['bot-spam']
# DB_URI = 'mysql+pymysql://root:ctfd@db/ctfd'
DB_URI = os.environ['DB_URI'] or 'mysql+pymysql://root:ctfd@0.0.0.0:3306/ctfd'
CTFD_MODE = 'teams'  # DO NOT CHANGE: bot will not work in users mode. Keep as `teams`
CATCH_MODE = 'all'  # all or user or admin
LIMIT_SIZE = 1000
MEDALS = [':first_place:', ':second_place:', ':third_place:']
TOKEN = os.environ['TOKEN'] or 'token'
