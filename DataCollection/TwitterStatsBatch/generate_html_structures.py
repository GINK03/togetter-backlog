import glob
from pathlib import Path
import pandas as pd
import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import pickle
FILE = Path(__file__).name
TOP_DIR = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().name
print(FILE, TOP_DIR)

# 目に見える取得済みのhtmlをciteと紐づけて保存
def process(fn):
    day = Path(fn).name
    cite_html = {}
    output_name = f'var/generate_html_structure/{day}.pkl'
    if Path(output_name).exists():
        return
    for fn0 in glob.glob(f'{fn}/*'):
        digest = Path(fn0).name
        soup = BeautifulSoup(open(fn0).read(), features='lxml')
        if soup.find(attrs={'cite':True}) is None:
            Path(fn0).unlink()
            continue
        # print(day, digest)
        cite = soup.find(attrs={'cite':True}).get('cite')
        # print(soup.find(attrs={'class':'CallToAction-text'}))
        
        div = soup.find('body').find('div')
        if div.find(attrs={'class':'EmbeddedTweet'}):
            div.find(attrs={'class':'EmbeddedTweet'})['style'] = 'margin-top: 10px; margin-left: 10px;'
        imagegrids = soup.find_all('a', {'class': 'ImageGrid-image'})
        for imagegrid in imagegrids:
            src = imagegrid.find('img').get('src')
            imagegrid['href'] = src
        mediaassets = soup.find_all('a', {'class': 'MediaCard-mediaAsset'})
        for mediaasset in mediaassets:
            if mediaasset.find('img') and mediaasset.find('img').get('alt') != 'Embedded video':
                mediaasset['href'] = mediaasset.find('img').get('src')
        buzz_ctx = div.__str__()
        buzz_css = soup.find('body').find('style').__str__()
        html = buzz_ctx + buzz_css
        cite_html[cite] = html
    with open(output_name, 'wb') as fp:
        pickle.dump(cite_html, fp)
        
fns = [fn for fn in tqdm(glob.glob(f'{TOP_DIR}/var/Twitter/tweet/*'))]
with ProcessPoolExecutor(max_workers=16) as exe:
    for ret in tqdm(exe.map(process, fns), total=len(fns)):
        ret

# 別プログラムで作成したtwitter_batch_backlogに対して、取得済みを当てはめていく
for fn in tqdm(glob.glob(f'{TOP_DIR}/var/twitter_batch_backlogs/*/*.csv')):
    path = Path(fn)
    date = path.parent.name
    df = pd.read_csv(fn)
    df['ts'] = df.apply(lambda x: x['date'] + ' ' + x['time'], axis=1)
    df['ts'] = df['ts'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    df['hour'] = df['ts'].dt.hour
   
    # 突合する
    cite_html_name = f'var/generate_html_structure/{date}.pkl'
    with open(cite_html_name, 'rb') as fp:
        cite_html = pickle.load(fp)

    oneday_tweets = ''
    for hour, sub in df.groupby(by=['hour']):
        sub = sub.copy()
        hour_tweets = ''
        hour_tweets += f'<h2>{date} {hour}時</h2>\n'
        sub.sort_values(by=['freq'], ascending=False, inplace=True)
        # print(sub)
        for link, freq in zip(sub.link, sub.freq):
            if link not in cite_html:
                continue
            shot_tweet = ''
            shot_tweet += f'<p>Freq {freq}</p>\n'
            # shot_tweet += f'''<blockquote class="twitter-tweet"><p lang="ja" dir="ltr">context <a href="{link}"> </a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>\n'''
            shot_tweet += cite_html[link]
            hour_tweets += shot_tweet
        oneday_tweets += hour_tweets
    # print(oneday_tweets)
    head = f'<html><head><title>{date}</title></head>'
    body = f'<body>{oneday_tweets}</body>'
    tail = '</html>'
    html = head + body + tail
    with open(f'var/htmls/{date}.html', 'w') as fp:
        fp.write(html)