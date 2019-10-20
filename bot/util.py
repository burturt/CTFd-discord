from datetime import datetime
import pytz

from bot.constants import TIMEZONE

def format_date(d):
    fmt = '%d/%m/%Y %I:%M:%S%p'
    D = datetime(d.year, d.month, d.day, d.hour, d.minute, d.second, tzinfo=pytz.utc)
    config_timezone = pytz.timezone(TIMEZONE)
    return D.astimezone(config_timezone).strftime(fmt)
