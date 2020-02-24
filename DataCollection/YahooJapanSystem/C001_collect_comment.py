import warnings
import pandas as pd
import random
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
import concurrent
import time
import glob
from pathlib import Path
import pickle
import sys
from urllib.parse import urlparse
import shutil
from bs4 import BeautifulSoup
import datetime
import requests
import glob
from inspect import currentframe, getframeinfo
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from os import environ as E
import multiprocessing

FILE = Path(__file__).name
TOP_FOLDER = Path(__file__).resolve().parent.parent.parent
try:
    sys.path.append(f'{TOP_FOLDER}')
    from Web.Structures import TitleUrlDigestScore
    from Web.Structures import YJComment
    from Web import QueryToDict
except Exception as exc:
    raise Exception(exc)
warnings.simplefilter("ignore")

INPUT_FOLDER = f'{TOP_FOLDER}/var/YJ/frequency_watch/'
OUT_FOLDER = f'{TOP_FOLDER}/var/YJ/comments'
Path(OUT_FOLDER).mkdir(exist_ok=True, parents=True)


def batch_get_iframe_html(arg):
    iframe_url, parent_digest = arg
    if 's.yimg.jp' in iframe_url:
        return None
    try:
        with requests.get(iframe_url, timeout=10) as r:
            if r is None:
                return None
            html = r.text
    except Exception as exc:
        print(f'[{FILE}][{getframeinfo(currentframe()).lineno}] {exc}, arg = {arg}', file=sys.stderr)
        return None
    soup = BeautifulSoup(html, 'html5lib')

    try:
        yj_comments = []
        for article in soup.find_all('article'):
            urls = set()
            for a in article.find_all('a', {'href': True}):
                url = a.get('href')
                urls.add(url)
            try:
                ts = article.find('time').get('datetime')
                comment = article.find('p', {'class': 'comment'}).text.strip()
                username = article.find('h1').text.strip()
                good = article.find(attrs={'class': 'good'}).text.strip()
                bad = article.find(attrs={'class': 'bad'}).text.strip()
                yj_comment = YJComment(
                    username=username,
                    comment=comment,
                    good=good,
                    bad=bad,
                    urls=urls,
                    parent_digest=parent_digest,
                    ts=ts,
                )
                yj_comments.append(yj_comment)
            except AttributeError as exc:
                # print(exc)
                continue
        return yj_comments
    except Exception as exc:
        print(f"[{FILE}][{getframeinfo(currentframe()).lineno}] DeepError {exc}", file=sys.stderr)
        return None


def process(arg):
    key, files = arg['CPU'], arg['files']
    
    # driver = webdriver.PhantomJS()
    # driver.set_window_size(1120, 1550)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("window-size=1024x2024")
    options.add_argument(f"user-data-dir=/tmp/{FILE}_{key:06d}")
    options.binary_location = shutil.which('google-chrome')
    driver = webdriver.Chrome(executable_path=shutil.which("chromedriver"), options=options)
    if key != None:
        iterator = tqdm(files, position=key, desc=f'CPU={key}')
    else:
        iterator = files
    try:
        for file in iterator:
            try:
                title_url_digest_score = pickle.load(open(file, 'rb'))
            except Exception as exc:
                Path(file).unlink()
                continue
            if title_url_digest_score.date <= datetime.datetime.now() - datetime.timedelta(days=1):
                continue
            url = title_url_digest_score.url

            out_dir = f'{TOP_FOLDER}/var/YJ/comments/{title_url_digest_score.digest}'
            Path(out_dir).mkdir(exist_ok=True, parents=True)
            if len(glob.glob(f'{out_dir}/*.pkl')) >= 1:
                continue
            o = urlparse(url)
            d = QueryToDict.query_to_dict(o.query)
            'https://headlines.yahoo.co.jp/cm/main?d=20200214-02140949-nksports-soci&s=lost_points&o=desc&p=1'

            iframe_urls = []
            for p in range(1, 10):
                comment_url = f'https://headlines.yahoo.co.jp/cm/main?d={d["a"]}&s=lost_points&o=desc&p={p}'
                try:
                    driver.get(comment_url)
                except Exception as exc:
                    break
                time.sleep(1.5)
                try:
                    for iframe in driver.find_elements_by_tag_name('iframe'):
                        iframe_url = iframe.get_attribute('src')
                        iframe_urls.append((iframe_url, title_url_digest_score.digest))
                except Exception as exc:
                    continue

            yj_comments = []
            with ThreadPoolExecutor(max_workers=32) as exe:
                for _yj_comments in exe.map(batch_get_iframe_html, iframe_urls):
                    if _yj_comments is None:
                        continue
                    yj_comments.extend(_yj_comments)

            with open(f'{out_dir}/{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.pkl', 'wb') as fp:
                pickle.dump(yj_comments, fp)
                if E.get('DEBUG'):
                    print('finish!', key, len(yj_comments), url)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"[{FILE}] DeepError[Must be fixed.] {exc}, line no. {exc_tb.tb_lineno}")


def process_runner():
    NUM = 64
    args = []
    cur = 0
    for fn0 in glob.glob(f'{INPUT_FOLDER}/*'):
        files1 = sorted(glob.glob(f'{fn0}/*.pkl'))
        random.shuffle(files1)
        for fn1 in files1:
            args.append({'CPU': cur % NUM, 'file': fn1})
            cur += 1
    random.shuffle(args)
    args = pd.DataFrame(args).groupby('CPU').apply(lambda x: x['file'].tolist()).reset_index()
    args.rename(columns={0: 'files'}, inplace=True)

    if E.get('DEBUG_SINGLE'):
        print(args.to_dict('record'))
        for arg in args.to_dict('record'):
            process(arg)
        exit()

    print('run as multithreading...')
    try:
        #  with ProcessPoolExecutor(max_workers=NUM) as exe:
        # exe.map(process, args.to_dict('record'), timeout=300)
        ps = []
        for arg in args.to_dict('record'):
            p = multiprocessing.Process(target=process, args=(arg,))
            p.start()
            ps.append(p)
        [p.join(60) for p in ps]
        for p in ps:
            if p.is_alive():
                p.terminate()
            p.join()
    except concurrent.futures._base.TimeoutError as exc:
        print(f'[{FILE}][{getframeinfo(currentframe()).lineno}] {exc}', file=sys.stderr)
        return
    except Exception as exc:
        print(f'[{FILE}][{getframeinfo(currentframe()).lineno}] {exc}', file=sys.stderr)
        return


def run():
    process_runner()


if __name__ == '__main__':
    run()
