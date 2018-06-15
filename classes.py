"""
Default file with class definitions
Names of functions describes behavior, no need in comments
"""

import time
from math import fabs
import mongo
import postgres


format = "%H:%M"


class Lesson:
    def __init__(self, id_, seq_id, day, time, data, more, link):
        self._id_ = id_
        self._seq_id_ = seq_id
        self.day = day
        self.time = time
        self.data = data
        self.more = more
        self.link = link
        self._update()

    def _update(self):
        postgres.update_lesson(self._seq_id_, self.__dict__)


class Sequence:
    def __init__(self, id_, name, key, lessons, start_message, finish_message, description, more, price, key_id=None):
        if key_id:
            data = postgres.get_sequence(key_id)
            self.id_ = data.get('id')
            self.name = data.get('name')
            self.key = data.get('key')
            self.lessons = data.get('lessons')
            if self.lessons:
                self.lessons.sort(key=lambda x: x['_id_'])
            self.start_message = data.get('start_message')
            self.finish_message = data.get('finish_message')
            self.description = data.get('description')
            self.more = data.get('more')
            self.price = data.get('price')
        else:
            self.id_ = id_
            self.name = name
            self.key = key
            self.lessons = lessons
            if self.lessons:
                self.lessons.sort(key=lambda x: x['_id_'])
            self.start_message = start_message
            self.finish_message = finish_message
            self.description = description
            self.more = more
            self.price = price
            self._update()

    def _update(self):
        postgres.update_sequence(self.__dict__)

    @staticmethod
    def get_links():
        data = postgres.get_links()
        return data

    @staticmethod
    def set_link(link, id_):
        return postgres.upload_link(link, id_)

    @staticmethod
    def create():
        return postgres.create_sequence()

    def check_last(self, lesson_id):
        return len(self.lessons) == lesson_id

    def start(self, user_id):
        time_ = mongo.add_lesson(self.lessons[0], user_id, int(self.lessons[0]['day']))
        return time_

    def next(self, lesson_id, user_id):
        day = int(self.lessons[lesson_id]['day'])
        nday = int(self.lessons[lesson_id + 1]['day'])
        if nday - day < 0:
            raise Exception('Fatal error occurred.\nWrong day identification!')
        mongo.add_lesson(self.lessons[lesson_id + 1], user_id, nday - day)

    def feed_stars(self, user_id, stars):
        postgres.add_feedback(self.id_, user_id, stars=stars)

    def feed_comment(self, user_id, comment):
        postgres.add_feedback(self.id_, user_id, stars=None, comments=comment)

    def get_lessons(self, day):
        return [lesson for lesson in self.lessons if lesson['day'] and (int(lesson['day']) == int(day))]

    def get_times(self, day):
        result = []
        for lesson in self.get_lessons(day):
            if not lesson['time']: continue
            result.append(time.strptime(lesson['time'], format))
        return result

    def is_max_day(self, day):
        for lesson in self.lessons:
            if not lesson['day']: continue
            if int(lesson['day']) > int(day):
                return False
        return True

    def check_time(self, day, time_):
        time_ = time.strptime(time_, format)
        for tm in self.get_times(day):
            if tm > time_:
                return False
        return True


# только как интерфейс для хранения lesson'ов
class LessonsPool:
    def __init__(self):
        # should return dicts!!!
        self.pool = [data for data in mongo.get_lessons()]

    def reload(self):
        self.pool = [data for data in mongo.get_lessons()]

    @staticmethod
    def time_comparator(time_, lesson):
        if fabs(int(time_) - int(lesson['time'])) < 60:
            return True
        return False

    # should return dicts!!!
    def pop_lessons(self):
        current = int(time.time())
        result = []
        if not self.pool:
            return None
        for i in self.pool:
            if self.time_comparator(current, i):
                result.append(i)
        if result:
            mongo.remove_lessons(result)
            self.reload()
        return result

    def push_lesson(self, lesson):
        # convert everything to dict
        if isinstance(lesson, dict):
            self.pool.append(lesson)
            # mongo.set_next_lesson(lesson)
        elif isinstance(lesson, Lesson):
            self.pool.append(lesson.__dict__)
        else:
            raise Exception('Type Error Occured.\nUnsupported type %s in LessonsPool.push_lesson()' % str(type(lesson)))

    def add_user(self):
        self.reload()

    def get_subscribes(self, user_id):
        self.reload()
        result = []
        for lesson in self.pool:
            if user_id in lesson['users']:
                result.append(lesson['_seq_id_'])
        return result

    def delete_from(self, user_id, seq_id):
        for lesson in self.pool:
            if seq_id == lesson['_seq_id_']:
                if user_id in lesson['users']:
                    lesson['users'] = [uid for uid in lesson['users'] if uid != user_id]
                    mongo.upd_lesson(lesson['time'], lesson['_seq_id_'], lesson['_id_'], lesson['users'])
                else:
                    raise Exception('Fatal Error occurred\nIncorrect user_id')
