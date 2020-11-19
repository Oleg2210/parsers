import pymysql


class YoutubeSaver:
    def __init__(self, host, user, password, db):
        self.connection = pymysql.connect(host, user, password, db)

    def _make_select_query(self, query, **kwargs):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, tuple(kwargs.values()))
            return cursor.fetchall()

    def _make_insert_query(self, query, **kwargs):
        with self.connection.cursor() as cursor:
            cursor.execute(query, tuple(kwargs.values()))
            self.connection.commit()

    @classmethod
    def _create_fields_and_values_texts(cls, **kwargs):
        fields_text = ','.join(kwargs.keys())
        values_text = '%s,' * len(kwargs.keys())
        return fields_text, values_text[:-1]

    def get_youtube_resources(self):
        query = 'SELECT id, owner_id, res_id, link FROM youtube_resources;'
        return self._make_select_query(query)

    def save_video_info(self, **kwargs):
        fields_text, values_text = self._create_fields_and_values_texts(**kwargs)
        query = f'''REPLACE INTO youtube_videos({fields_text}) VALUES({values_text});'''
        self._make_insert_query(query, **kwargs)
