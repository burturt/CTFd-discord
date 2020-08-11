# CTFd-discord
Discord bot to display events and information about a CTFd instance (https://ctfd.io/) 

```
>>categories                      - lists all challenge categories
>>category <category>             - lists challenges in the specified category
>>diff <user1> <user2>            - displays the difference of solved challenges between two users
>>help                            - displays this message
>>scoreboard                      - displays the top 20 teams
>>scoreboard_complete             - displays the entire scoreboard
>>recent (<num>) (<user>)         - displays recent solves (up to <num> days for a specific <user>)
>>who_solved <chall_name>         - displays the solves for the specified challenge
```

An improvement in interface and design over https://github.com/zteeed/CTFd-discord and edited https://github.com/josephsurin/CTFd-discord to fix the scoreboard command when in teams mode.

Setup:
`pip3 install pipenv`
`pipenv --python 3.8`
`pipenv shell`
`pip3 install -r requirements.txt`
`nano bot/constants.py`:
 - BOT_CHANNEL = live feed
 - OTHER_CHANNELS = places you can run bot commands
 - time zone: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
`python3 main.py`
