from datetime import datetime
from random import randint
from libs.youtube_parser import YouTubeParser
from libs.db import YoutubeSaver
from libs.common import try_to_execute
import time
import os
import logging

logging.basicConfig(filename='/app/logs/logs.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


@try_to_execute(4, 5)
def create_db_connection():
    host = os.environ['MYSQLHOST']
    user = os.environ['MYSQLUSER']
    passw = os.environ['MYSQLPASS']
    db = os.environ['MYSQLDB']
    youtube_saver = YoutubeSaver(host, user, passw, db)
    return youtube_saver


@try_to_execute(1, 0)
def save_video_info(db_driver, resource_info, video_info):
    video_info['owner_id'] = resource_info['owner_id']
    video_info['res_id'] = resource_info['res_id']
    video_info['add_date'] = video_info['end_date'] = datetime.utcnow()
    db_driver.save_video_info(**video_info)
    info_string = f'video with id {video_info["item_id"]} is successfully saved'
    print(info_string)
    logging.info(info_string)


@try_to_execute(4, 1)
def parse_channel(youtube_parser, link):
    return youtube_parser.get_channel_videos_ids(link)


@try_to_execute(4, 1)
def parse_video_data(youtube_parser, video_id):
    return youtube_parser.get_video_total_data(video_id)


def main():
    print('parser starts')
    parser = YouTubeParser()
    saver = create_db_connection()
    resources = saver.get_youtube_resources()
    for r in resources:
        videos_ids = parse_channel(parser, f'{r["link"]}/videos')
        for vid_id in videos_ids:
            video_info = parse_video_data(parser, vid_id)
            save_video_info(saver, r, video_info)

    time.sleep(randint(60, 600))


if __name__ == '__main__':
    main()
