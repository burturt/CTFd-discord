import hashlib
import ipaddress
import re
import socket
import struct
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from bot.database.tables import CTFdTables

from bot.util import format_date


def get_ctf_name(s: Session, tables: CTFdTables) -> str:
    return s.query(tables.config).filter_by(key='ctf_name').first().value


def get_false_submissions(s: Session, tables: CTFdTables) -> List[Dict]:
    return s.query(tables.users.name, tables.challenges.name, tables.submissions.provided). \
        join(tables.challenges, tables.challenges.id == tables.submissions.challenge_id). \
        join(tables.users, tables.users.id == tables.submissions.user_id). \
        filter(tables.submissions.type == 'incorrect'). \
        group_by(tables.challenges.id). \
        all()


def get_visible_challenges(s: Session, tables: CTFdTables) -> List[int]:
    challenges_id = s.query(tables.challenges.id).filter(tables.challenges.state == 'visible').all()
    return [int(i[0]) for i in challenges_id]


def get_challenge_info(s: Session, tables: CTFdTables, id: int) -> Optional[Tuple[str, str, str]]:
    return s.query(tables.challenges.name, tables.challenges.value, tables.challenges.category). \
        filter(tables.challenges.id == id).first()


def get_scoreboard(s: Session, tables: CTFdTables, user_type: str = 'all') -> List[Dict]:
    scoreboard = s.query(tables.teams.name, func.sum(tables.challenges.value).label('score')). \
        join(tables.solves, tables.teams.id == tables.solves.user_id). \
        join(tables.challenges, tables.challenges.id == tables.solves.challenge_id)

    scoreboard = scoreboard.group_by(tables.teams.id).all()

    score_list = [dict(username=username, score=score_user) for (username, score_user) in scoreboard]
    return sorted(score_list, key=lambda item: item['score'], reverse=True)


def get_users(s: Session, tables: CTFdTables, user_type: str = 'all') -> List[str]:
    users = s.query(tables.users.name).all()
    return [u[0] for u in users]


def get_categories(s: Session, tables: CTFdTables) -> List[str]:
    categories = s.query(tables.challenges.category).distinct().all()
    return sorted([item[0] for item in categories])


def category_exists(s: Session, tables: CTFdTables, category: str) -> bool:
    challenges = s.query(tables.challenges). \
        filter(tables.challenges.category == category).first()
    return challenges is not None


def get_category_info(s: Session, tables: CTFdTables, category_name: str) -> List[Dict]:
    if not category_exists(s, tables, category_name):
        return []
    challenges = s.query(tables.challenges).filter_by(category=category_name). \
        order_by(desc(tables.challenges.value)).all()
    category_info = []
    for challenge in challenges:
        category_info.append(dict(name=challenge.name, value=challenge.value))
    return category_info


def user_exists(s: Session, tables: CTFdTables, user: str, user_type: str = 'all') -> bool:
    query = s.query(tables.users)
    if user_type != 'all':
        query = query.filter(tables.users.type == user_type)
    query = query.filter(tables.users.name == user).first()
    return query is not None


def challenge_exists(s: Session, tables: CTFdTables, challenge: str) -> bool:
    query = s.query(tables.challenges). \
        filter(tables.challenges.name == challenge). \
        first()
    return query is not None


def get_authors_challenge(s: Session, tables: CTFdTables, challenge: str) -> List[Tuple[Any, Any]]:
    if not challenge_exists(s, tables, challenge):
        return []
    description = s.query(tables.challenges.description). \
        filter(tables.challenges.name == challenge). \
        first()
    if description is not None:
        description = description[0]
    result = re.findall(r'@(\w+)#(\d+)', description)
    if result:
        return result
    result = re.findall(r'(.*?)#(\d+)', description)
    if not result:
        return result
    return [(name.split(' ')[-1].replace('@', ''), user_id) for (name, user_id) in result]


def get_users_solved_challenge(s: Session, tables: CTFdTables, challenge: str, user_type: str = 'all'):
    if not challenge_exists(s, tables, challenge):
        return None
    users = get_users(s, tables, user_type=user_type)
    users_solves = s.query(tables.users.name, tables.submissions.date). \
        join(tables.submissions, tables.submissions.user_id == tables.users.id). \
        join(tables.challenges, tables.challenges.id == tables.submissions.challenge_id). \
        filter(tables.submissions.type == 'correct'). \
        filter(tables.challenges.name == challenge). \
        order_by(asc(tables.submissions.date))

    if user_type != 'all':
        users_solves.filter(tables.users.type == user_type)
    users_solves = users_solves.all()

    return [{ 'name': u[0], 'date': format_date(u[1]) } for u in users_solves]


def get_challenges_solved_during(s: Session, tables: CTFdTables, days: int = 1, user_type: str = 'all') -> List[Dict]:
    date_reference = (datetime.now() - timedelta(days=days))  # %y-%m-%d %H:%M:%S
    solved_challenges = s.query(tables.submissions). \
        join(tables.users, tables.users.id == tables.submissions.user_id). \
        join(tables.challenges, tables.challenges.id == tables.submissions.challenge_id). \
        filter(tables.submissions.type == 'correct'). \
        filter(tables.submissions.date > date_reference)

    if user_type != 'all':
        solved_challenges = solved_challenges.filter(tables.users.type == user_type)
    solved_challenges = solved_challenges.order_by(desc(tables.submissions.date)).all()

    return [dict(chall=solve.challenges.name, points=solve.challenges.value, date=format_date(solve.date), user=solve.users.name) for solve in solved_challenges]


def challenges_solved_by_user(s: Session, tables: CTFdTables, user: str, user_type: str = 'all') -> List[Dict]:
    if not user_exists(s, tables, user, user_type=user_type):
        return []
    solved_challenges = s.query(tables.submissions). \
        join(tables.users, tables.users.id == tables.submissions.user_id). \
        join(tables.challenges, tables.challenges.id == tables.submissions.challenge_id). \
        filter(tables.users.name == user). \
        filter(tables.submissions.type == 'correct'). \
        order_by(desc(tables.challenges.value)). \
        all()
    return [dict(name=item.challenges.name, value=item.challenges.value) for item in solved_challenges]


def diff(s: Session, tables: CTFdTables, user1: str, user2: str, user_type: str = 'all') -> Tuple[
    List[Dict], List[Dict]]:
    users = get_users(s, tables, user_type=user_type)
    if user1 not in users or user2 not in users:
        return [], []
    user1, user2 = user1.strip(), user2.strip()
    solved_challenges_1 = challenges_solved_by_user(s, tables, user1, user_type=user_type)
    solved_challenges_2 = challenges_solved_by_user(s, tables, user2, user_type=user_type)
    all_challs = solved_challenges_1 + solved_challenges_2
    diff1 = [item for item in all_challs if item in solved_challenges_1 and item not in solved_challenges_2]
    diff2 = [item for item in all_challs if item in solved_challenges_2 and item not in solved_challenges_1]
    return diff1, diff2


def track_user(s: Session, tables: CTFdTables, user: str, user_type: str = 'all') -> List[str]:
    user = user.strip()
    if not user_exists(s, tables, user, user_type=user_type):
        return []
    ips = s.query(tables.tracking.ip). \
        join(tables.users, tables.users.id == tables.tracking.user_id). \
        filter(tables.users.name == user). \
        distinct().all()
    ips = [item[0] for item in ips]
    ips = [ip for ip in ips if ipaddress.ip_address(ip).__class__.__name__ == 'IPv4Address']
    return sorted(ips, key=lambda ip: struct.unpack("!L", socket.inet_aton(ip))[0])


def get_challenges_solved(s: Session, tables: CTFdTables, user_type: str = 'all') -> List:
    challenges = s.query(tables.submissions). \
        join(tables.challenges, tables.challenges.id == tables.submissions.challenge_id). \
        join(tables.users, tables.users.id == tables.submissions.user_id). \
        filter(tables.submissions.type == 'correct')
    if user_type != 'all':
        challenges = challenges.filter(tables.users.type == user_type)
    return challenges.order_by(desc(tables.submissions.date)).all()


def get_tag(challenge: Any) -> str:
    tag_value = f'{challenge.users.id} | {challenge.challenges.id}'
    return hashlib.sha224(tag_value.encode()).hexdigest()


def select_challenges_by_tags(challenges: List, tag: str) -> List[Any]:
    selected_challenges = []
    for key, challenge in enumerate(challenges):
        if get_tag(challenge) != tag:
            selected_challenges.append(challenge)
        else:
            return selected_challenges[::-1]  # sort from oldest to newest
    return selected_challenges[::-1]  # sort from oldest to newest

def get_solve_count(s: Session, tables: CTFdTables, chall_name: str, user_type: str = 'all') -> int:
    solve_count = s.query(tables.submissions). \
        join(tables.challenges, tables.challenges.id == tables.submissions.challenge_id). \
        filter(tables.challenges.name == chall_name). \
        filter(tables.submissions.type == 'correct')
    if user_type != 'all':
        solve_count = solve_count.filter(tables.users.type == user_type)
    return solve_count.count()


def get_new_challenges(s: Session, tables: CTFdTables, tag: str, user_type: str = 'all') -> Tuple[str, Dict]:
    new_challenge = dict()
    new_tag = None
    challenges = get_challenges_solved(s, tables, user_type=user_type)

    if tag is None:
        if len(challenges) > 0:
            new_tag = get_tag(challenges[0])
        return new_tag, new_challenge

    selected_challenges = select_challenges_by_tags(challenges, tag)
    if len(selected_challenges) > 0:
        item = selected_challenges[0]
        first_blood = get_solve_count(s, tables, item.challenges.name, user_type=user_type) == 1
        new_tag = get_tag(item)
        new_challenge = dict(username=item.users.name, challenge=item.challenges.name, value=item.challenges.value, date=format_date(item.date), first_blood=first_blood)
        #  log.debug(f'New solve', username=item.users.name, challenge=item.challenges.name, date=item.date)
        return new_tag, new_challenge
    else:
        return tag, new_challenge
