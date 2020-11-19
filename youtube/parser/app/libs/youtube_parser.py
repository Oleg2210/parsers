import requests
import re
import json
import langdetect
from fake_headers import Headers
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeParser:
    CLIENT_DATA = {'X-YouTube-Client-Name': '1', 'X-YouTube-Client-Version': '2.20201031.02.00', 'Accept-Language': 'en-US,en;q=0.5'}

    def __init__(self, proxies=None):
        self.proxies = proxies
        self.fake_headers = Headers(os='lin', browser='firefox')
        self.title_and_descripition_delimeter = '*#-'*20 + '\n'

    @staticmethod
    def _lang_detect(text):
        lang = langdetect.detect(text)
        if lang == 'ru':
            kazakh_letters = 'ӘәҒғҚқҢңӨөҰұҮү'
            for letter in kazakh_letters:
                if letter in text:
                    lang = 'kz'
                    break
        return lang

    def _find_field(self, field_name, search_text):
        regexp = f'"{field_name}":".*?"'
        field = re.search(regexp, search_text)
        field_text = field.group(0)
        return field_text.replace(f'"{field_name}":"', '')[:-1]

    def _find_cookie(self, cookie_name, cookies_header):
        cookies = cookies_header.split(';')
        found_cookies = [c for c in cookies if cookie_name in c][0].split(',')
        cookie = [c for c in found_cookies if cookie_name in c][0]
        return cookie

    def _get_initial_variable(self, response, var_name):
        regexp = r'window\[\"' + re.escape(var_name) + '\"\] = \{.*?\};'
        initial_data = re.search(regexp, response.text).group(0)
        initial_data = initial_data.replace(f'window["{var_name}"] = ', '')[:-1]
        return json.loads(initial_data)

    def _prepare_headers_for_video_comments(self, youtube_response, fake_headers):
        visitor = self._find_cookie('VISITOR_INFO1_LIVE', youtube_response.headers['Set-Cookie'])
        ysc = self._find_cookie('YSC', youtube_response.headers['Set-Cookie'])
        cookies = ';'.join((visitor, ysc)).strip()
        additional_headers = {
            'X-YouTube-Client-Name': '1',
            'X-YouTube-Client-Version': '2.20201031.02.00',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.youtube.com',
            'Cookie': cookies,
        }
        fake_headers.update(additional_headers)
        return fake_headers

    def _get_tokens(self, youtube_response):
        tokens = re.search(
            r'"continuations"\:\[\{"nextContinuationData"\:\{"continuation"\:".*?","clickTrackingParams"\:".*?"',
            youtube_response.text)

        if tokens is None:
            return None, None

        tokens = tokens.group(0)
        tokens = tokens.split(',')
        token = tokens[0].replace('"continuations":[{"nextContinuationData":{"continuation":"', '')[:-1]
        itct = tokens[1].replace('"clickTrackingParams":"', '')[:-1]
        return token, itct

    def _prepare_query_for_video_comments(self, youtube_response):
        token, itct = self._get_tokens(youtube_response)
        return f'https://www.youtube.com/comment_service_ajax?action_get_comments=1&pbj=1&ctoken={token}&continuation={token}&itct={itct}'

    def _prepare_query_for_channels_videos(self, youtube_response=None, token=None, itct=None):
        if (not token) and (not itct):
            token, itct = self._get_tokens(youtube_response)
            if token is None:
                return None
        return f'https://www.youtube.com/browse_ajax?ctoken={token}&continuation={token}&itct={itct}'

    def _get_video_comments_number(self, youtube_response, fake_headers):
        fake_headers = self._prepare_headers_for_video_comments(youtube_response, fake_headers)
        payload = {'session_token': self._find_field('XSRF_TOKEN', youtube_response.text)}
        query = self._prepare_query_for_video_comments(youtube_response)

        comments_data = requests.post(query, data=payload, headers=fake_headers).json()
        comments_number_text = comments_data['response']['continuationContents']['itemSectionContinuation']['header']['commentsHeaderRenderer']['countText']['runs'][0]['text']
        return int(''.join(re.findall(r'[0-9]+', comments_number_text)))

    def _make_right_subtitles_format(self, sub_entity, video_id):
        zerofy = lambda number: f'0{number}' if number < 10 else f'{number}'
        start = int(sub_entity['start'])
        minutes = zerofy(start // 60)
        seconds = zerofy(start % 60)
        sub_string = f'''<a href="https://youtu.be/{video_id}?t={start}" target="_blanc">{minutes}:{seconds}</a>'''
        sub_string += sub_entity['text']
        return sub_string

    def get_video_subtitles(self, video_id, subtitles_langs):
        subtitles = {}
        for lang in subtitles_langs:
            try:
                subs = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                formatted_subs = []
                for s in subs:
                    formatted_subs.append(self._make_right_subtitles_format(s, video_id))
                subtitles['lang'] = formatted_subs
            except Exception:
                pass

        return subtitles

    def _get_channel_last_videos_ids(self, response):
        initial_data = self._get_initial_variable(response, 'ytInitialData')
        items = initial_data['contents']['twoColumnBrowseResultsRenderer']['tabs'][1]['tabRenderer']['content']
        items = items['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['gridRenderer']['items']
        return [item['gridVideoRenderer']['videoId'] for item in items]

    def _get_video_initial_data(self, response):
        video = {}
        initial_data = self._get_initial_variable(response, 'ytInitialData')
        video_info = initial_data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']
        title = video_info['title']['runs'][0]['text']
        description = self._get_initial_variable(response, 'ytInitialPlayerResponse')['videoDetails']['shortDescription']

        video['lang'] = self._lang_detect(title)
        video['count_views'] = int(''.join(re.findall(r'[0-9]+', video_info['viewCount']['videoViewCountRenderer']['viewCount']['simpleText'])))
        video['date'] = int(datetime.strptime(video_info['dateText']['simpleText'], '%b %d, %Y').strftime('%s'))
        video['text'] = title + self.title_and_descripition_delimeter + description
        return video

    def get_video_total_data(self, video_id, subtitles_langs=['ru', 'eng']):
        video_link = f'https://www.youtube.com/watch?v={video_id}'
        fake_h = self.fake_headers.generate()
        fake_h.update({'accept-language': 'en-US,en;q=0.9'})
        response = requests.get(video_link, headers=fake_h, proxies=self.proxies)
        video = self._get_video_initial_data(response)
        video['item_id'] = video_id
        video['link'] = video_link
        video['count_comments'] = self._get_video_comments_number(response, fake_h)
        video['subtitles'] = str(self.get_video_subtitles(video_id, subtitles_langs))
        return video

    def get_channel_videos_ids(self, channel_videos_link):
        fake_h = self.fake_headers.generate()
        fake_h.update(self.CLIENT_DATA)
        response = requests.get(channel_videos_link, headers=fake_h, proxies=self.proxies)

        videos_ids = self._get_channel_last_videos_ids(response)
        query = self._prepare_query_for_channels_videos(youtube_response=response)
        if query is not None:
            while True:
                videos_resp = requests.get(query, headers=fake_h, proxies=self.proxies).json()
                videos_data = videos_resp[1]['response']['continuationContents']['gridContinuation']
                items = videos_data['items']
                for item in items:
                    videos_ids.append(item['gridVideoRenderer']['videoId'])

                if not videos_data.get('continuations'):
                    break

                ctoken = videos_data['continuations'][0]['nextContinuationData']['continuation']
                itct = videos_data['continuations'][0]['nextContinuationData']['clickTrackingParams']
                query = self._prepare_query_for_channels_videos(token=ctoken, itct=itct)

        return videos_ids


