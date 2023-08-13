#coding: UTF-8

import os
import sys
import time
from dotenv import load_dotenv
import requests
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth1Session as session
import datetime
import numpy as np
from pprint import pprint

#「.env」で定義した環境変数を使えるようにする
load_dotenv()

# 動画を読み込み
movie01 = "./movie/01_グー_ゆに.mp4"
movie02 = "./movie/02_グー_すう.mp4"
movie03 = "./movie/03_チョキ_ゆに.mp4"
movie04 = "./movie/04_チョキ_ぺこ.mp4"
movie05 = "./movie/05_パー_ゆに.mp4"
movie06 = "./movie/06_パー_みゅー.mp4"
movie07 = "./movie/07_みゅーちあ_グー.mp4"
movie08 = "./movie/08_みゅーちあ_チョキ.mp4"
movie09 = "./movie/09_みゅーちあ_パー.mp4"
movie10 = "./movie/10_ぺこすう_グー.mp4"
movie11 = "./movie/11_ぺこすう_チョキ.mp4"
movie12 = "./movie/12_ぺこすう_パー.mp4"
movie13 = "./movie/13_ねねれい_グー.mp4"
movie14 = "./movie/14_ねねれい_チョキ.mp4"
movie15 = "./movie/15_ねねれい_パー.mp4"
movie16 = "./movie/16_ゆにつぎはぎ_グー.mp4"
movie17 = "./movie/17_ゆにつぎはぎ_チョキ.mp4"
movie18 = "./movie/18_ゆにつぎはぎ_パー.mp4"


# 動画を抽選
items = [movie01, movie02, movie03, movie04, movie05, movie06, movie07, movie08, movie09, movie10, movie11, movie12, movie13, movie14, movie15, movie16, movie17, movie18]  # 内容
prob = [0.05, 0.11, 0.05, 0.1, 0.06, 0.11, 0.05, 0.05, 0.04, 0.04, 0.04, 0.03, 0.05, 0.05, 0.04, 0.05, 0.04, 0.04]  # 確率
N = 1  # 回数

result = np.random.choice(items, N, p=prob)


# アップロードする動画ファイルのパス
VIDEO_FILENAME =  result[0]

MEDIA_ENDPOINT_URL = 'https://upload.twitter.com/1.1/media/upload.json'
POST_TWEET_URL = 'https://api.twitter.com/2/tweets'


# Twitter APIの認証情報を設定
# APP_ENVがPRDなら本番の認証情報、DEVなら開発の認証情報を使う
APP_ENV = os.environ.get('APP_ENV')
if APP_ENV == "PRD":
    CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
    CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
    ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
    ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
else:
    CONSUMER_KEY = os.environ.get("CONSUMER_KEY_DEV")
    CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET_DEV")
    ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN_DEV")
    ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET_DEV")


# API認証
oauth = OAuth1(CONSUMER_KEY,
  client_secret=CONSUMER_SECRET,
  resource_owner_key=ACCESS_TOKEN,
  resource_owner_secret=ACCESS_TOKEN_SECRET)


# 動画ツイートのclass
class VideoTweet(object):

  def __init__(self, file_name):
    '''
    Defines video tweet properties
    '''
    self.video_filename = file_name
    self.total_bytes = os.path.getsize(self.video_filename)
    self.media_id = None
    self.processing_info = None

    self.req = session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)


  def upload_init(self):
    '''
    Initializes Upload
    '''
    print('INIT')

    request_data = {
      'command': 'INIT',
      'media_type': 'video/mp4',
      'total_bytes': self.total_bytes,
      'media_category': 'tweet_video'
    }

    req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, auth=oauth)
    media_id = req.json()['media_id']

    self.media_id = media_id

    print('Media ID: %s' % str(media_id))


  def upload_append(self):
    '''
    Uploads media in chunks and appends to chunks uploaded
    '''
    segment_id = 0
    bytes_sent = 0
    file = open(self.video_filename, 'rb')

    while bytes_sent < self.total_bytes:
      chunk = file.read(4*1024*1024)
      
      print('APPEND')

      request_data = {
        'command': 'APPEND',
        'media_id': self.media_id,
        'segment_index': segment_id
      }

      files = {
        'media':chunk
      }

      req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, files=files, auth=oauth)

      if req.status_code < 200 or req.status_code > 299:
        print(req.status_code)
        print(req.text)
        sys.exit(0)

      segment_id = segment_id + 1
      bytes_sent = file.tell()

      print('%s of %s bytes uploaded' % (str(bytes_sent), str(self.total_bytes)))

    print('Upload chunks complete.')


  def upload_finalize(self):
    '''
    Finalizes uploads and starts video processing
    '''
    print('FINALIZE')

    request_data = {
      'command': 'FINALIZE',
      'media_id': self.media_id
    }

    req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, auth=oauth)
    print(req.json())

    self.processing_info = req.json().get('processing_info', None)
    self.check_status()


  def check_status(self):
    '''
    Checks video processing status
    '''
    if self.processing_info is None:
      return

    state = self.processing_info['state']

    print('Media processing status is %s ' % state)

    if state == u'succeeded':
      return

    if state == u'failed':
      sys.exit(0)

    check_after_secs = self.processing_info['check_after_secs']
    
    print('Checking after %s seconds' % str(check_after_secs))
    time.sleep(check_after_secs)

    print('STATUS')

    request_params = {
      'command': 'STATUS',
      'media_id': self.media_id
    }

    req = requests.get(url=MEDIA_ENDPOINT_URL, params=request_params, auth=oauth)
    
    self.processing_info = req.json().get('processing_info', None)
    self.check_status()


  def tweet(self):
    '''
    Publishes Tweet with attached video
    '''
    # ツイート部分のみAPI v2を使用
    media_ids = [str(self.media_id)]
    d_today = datetime.date.today()
    format_date = d_today.strftime('%-m/%-d')
    msg = f'''🌈#ミュークルじゃんけん 🌈

今日({format_date})の運試し✨'''

    body = {
        "text": msg,
        "media": {
          "media_ids": media_ids
        }
    }

    res = self.req.post(POST_TWEET_URL, json=body)

    if not (res.status_code >= 200 and res.status_code <= 299):
        print(f"something went wrong...status:{res.status_code}")

    pprint(res.json())

# ツイートを実行
if __name__ == '__main__':
    
    # 本番環境の場合、時刻外ツイートを避ける処理を念の為入れている
    if APP_ENV == "PRD":
        dt_now = datetime.datetime.now()
        if datetime.time(6,50,00) < dt_now.time() < datetime.time(7,15,00):
            videoTweet = VideoTweet(VIDEO_FILENAME)
            videoTweet.upload_init()
            videoTweet.upload_append()
            videoTweet.upload_finalize()
            videoTweet.tweet()
        else:
            print("時間外に実行されました")

    # 開発環境の場合そのまま実行
    else:
        videoTweet = VideoTweet(VIDEO_FILENAME)
        videoTweet.upload_init()
        videoTweet.upload_append()
        videoTweet.upload_finalize()
        videoTweet.tweet()
    
