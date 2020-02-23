import pandas as pd
from pathlib import Path
import glob
from collections import namedtuple
import sys
import datetime

try:
    FILE = Path(__file__)
    TOP_FOLDER = Path(__file__).resolve().parent.parent
    sys.path.append(f'{TOP_FOLDER}')
    from Web import GenerateYJDailyHourlyRankingAbstractList
    from Web import GenerateDailyYJRankingList
    from Web.Structures import DayAndPath
    from Web import GetDigest
    from Web import Base64EncodeDecode
    from Web import Hostname
except Exception as exc:
    print(exc)
    raise Exception(exc)

def generate_top() -> str:
    head = '<html><head><title> Concertion Page </title></head>'
    tail = '</html>'
    body = ''
    # yahoo
    body += '<div class="yj">'
    body += GenerateYJDailyHourlyRankingAbstractList.generate_yj_daily_houry_ranking_abstract_list()
    body += '</div>'

    body += '<div class="yj_daily_ranking">'
    body += '<h2>過去のYahoo Newsのログ</h2>'
    body += GenerateDailyYJRankingList.generate_daily_ranking_list()
    body += '</div>'
    """
    # togetter
    day_and_paths: List[DayAndPath] = generate_daily_rankin_list()
    body += '<div class="togetter">'
    body += '<p>togetter backlog</p>'
    for day_and_path in day_and_paths:
        tmp = f'<a href="https://{Hostname.hostname()}/get_day/{day_and_path.day}?serialized={day_and_path.path}">{day_and_path.day}</a><br>'
        body += tmp
    body += "</div>"
    """
    return head + body + tail