import pandas as pd
from pathlib import Path
import glob
from collections import namedtuple
import sys
import datetime
from bs4 import BeautifulSoup
from typing import Any
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter

    
FILE = Path(__file__)
TOP_DIR = Path(__file__).resolve().parent.parent
try:
    sys.path.append(f'{TOP_DIR}')
    from Web import GenerateYJDailyHourlyRankingAbstractList
    from Web import GenerateDailyYJRankingList
    from Web.Structures import DayAndPath
    from Web import GetDigest
    from Web import Base64EncodeDecode
    from Web import Hostname
    from Web import GetBuzzTweet
    from Web import GenerateSignate
except Exception as exc:
    tb_lineno = sys.exc_info()[2].tb_lineno
    raise Exception(f"[{FILE}] import error, exc = {exc}, tb_lineno = {tb_lineno}")


def generate_top(twitter: Any) -> str:
    """
    Args:
        - twitter: flask_danceによる認証情報、認証していないこともある
    Returns:
        - str: htmlをビルドして返却する
    """
    head = '''<html><head><title> Concertion Page </title>
    <style>
    .twitter {
        float: left;
        width: 500px;
        margin-left: 10px;
    }
    .signate {
        float: right;
        width: calc(100% - 500px - 20px);
        margin-left: 10px;
    }
    .yj {
        float: right;
        width: calc(100% - 500px - 20px);
        margin-left: 10px;
    }
    </style>
    </head>'''
    tail = '</html>'
    body = ''
    # titleとか
    body += '<h1>Concertion.Page あなたの特徴の解析とお勧め企業</h1>'
    if not twitter.authorized:
        body += "<h3>ログインして便利に使おう</h3>"
        body += '<p><a href="/login">ログイン</a></p>'
    else:
        token = twitter.token
        screen_name = token['screen_name']
        body += f"<h3>こんにちは、{screen_name}さん</h3>"

    body += f"<div> {GetBuzzTweet.get_buzz_tweet()} </div>"

    return head + body + tail


if __name__ == '__main__':
    # here is single test
    html = get_buzz_tweet()
    print(html)
