# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class NewstubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?newstube\.ru/media/(?P<id>.+)'
    _TEST = {
        'url': 'http://newstube.ru/media/na-korable-progress-prodolzhaetsya-testirovanie-sistemy-kurs',
        'info_dict': {
            'id': 'd156a237-a6e9-4111-a682-039995f721f1',
            'ext': 'flv',
            'title': 'На корабле «Прогресс» продолжается тестирование системы «Курс»',
            'description': 'md5:d0cbe7b4a6f600552617e48548d5dc77',
            'duration': 20.04,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, 'Downloading page')

        video_guid = self._html_search_regex(
            r'<meta property="og:video" content="https?://(?:www\.)?newstube\.ru/freshplayer\.swf\?guid=(?P<guid>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})',
            page, 'video GUID')

        player = self._download_xml(
            'http://p.newstube.ru/v2/player.asmx/GetAutoPlayInfo6?state=&url=%s&sessionId=&id=%s&placement=profile&location=n2' % (url, video_guid),
            video_guid, 'Downloading player XML')

        def ns(s):
            return s.replace('/', '/%(ns)s') % {'ns': '{http://app1.newstube.ru/N2SiteWS/player.asmx}'}

        session_id = player.find(ns('./SessionId')).text
        media_info = player.find(ns('./Medias/MediaInfo'))
        title = media_info.find(ns('./Name')).text
        description = self._og_search_description(page)
        thumbnail = media_info.find(ns('./KeyFrame')).text
        duration = int(media_info.find(ns('./Duration')).text) / 1000.0

        formats = []

        for stream_info in media_info.findall(ns('./Streams/StreamInfo')):
            media_location = stream_info.find(ns('./MediaLocation'))
            if media_location is None:
                continue

            server = media_location.find(ns('./Server')).text
            app = media_location.find(ns('./App')).text
            media_id = stream_info.find(ns('./Id')).text
            quality_id = stream_info.find(ns('./QualityId')).text
            name = stream_info.find(ns('./Name')).text
            width = int(stream_info.find(ns('./Width')).text)
            height = int(stream_info.find(ns('./Height')).text)

            formats.append({
                'url': 'rtmp://%s/%s' % (server, app),
                'app': app,
                'play_path': '01/%s' % video_guid.upper(),
                'rtmp_conn': ['S:%s' % session_id, 'S:%s' % media_id, 'S:n2'],
                'page_url': url,
                'ext': 'flv',
                'format_id': quality_id,
                'format_note': name,
                'width': width,
                'height': height,
            })

        self._sort_formats(formats)

        return {
            'id': video_guid,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }