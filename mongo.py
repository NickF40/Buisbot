"""
Mongo.py - file with MongoDB interactions funcs
"""

import pymongo as mongo
import time
from configs import mongo_configs

client = mongo.MongoClient(mongo_configs['host'], mongo_configs['port'])
db = client[mongo_configs['name']]


def maketime(time_, diff):
    resulting_time = list(time.gmtime(time.time()))
    if int(diff) > 0:
        resulting_time[2] += int(diff)
    resulting_time[3] = int(time_.split(':')[0])
    resulting_time[4] = int(time_.split(":")[1])
    return time.mktime(time.gmtime(time.mktime(tuple(resulting_time))))


def get_dict(time_, lesson, user_id, seq_id):
    return dict(time=time_, text=lesson['data'], users=[user_id], seq_id=seq_id, _id_=lesson['_id_'])


def add_lesson(lesson,  user_id, diff):
    lesson['time'] = maketime(lesson['time'], diff)
    data = db.lessins_pool.find(dict(time=lesson['time'], _seq_id_=lesson['_seq_id_'], _id_=lesson['_id_']))
    data = [d for d in data]
    print(data)
    if data:
        if user_id in data['users']:
            return
        db.lessons_pool.update(dict(time=lesson['time'], _seq_id_=lesson['_seq_id_'], _id_=lesson['_id_']),
                               dict(users=data['users'].append(user_id)))
    else:
        lesson['users'] = [user_id]
        db.lessons_pool.insert(lesson)
    return lesson['time']


def remove_lessons(lessons):
    for lesson in lessons:
        db.lessons_pool.remove(dict(time=lesson['time'], _seq_id_=lesson['_seq_id_'], _id_=lesson['_id_']))


def upd_lesson(time_, seq_id, lesson_id, users):
    data = db.lessons_pool.find(dict(time=time_, _seq_id_=seq_id, _id_=lesson_id))
    data = [d for d in data][0]
    if not users:
        db.lessons_pool.remove(dict(time=time_, _seq_id_=seq_id, _id_=lesson_id))
    if data:
        db.lessons_pool.update(dict(time=time_, _seq_id_=seq_id, _id_=lesson_id),
                               dict(users=users, time=time_, _seq_id_=seq_id, _id_=lesson_id, link=data['link'], more=data['more'], data=data['data']))
    else:
        raise Exception('Fatal Error occurred\nIncorrect arguments')


def get_lessons():
    return db.lessons_pool.find()


