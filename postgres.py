"""
Postgres.py - file with PostgreSQL Database interactions funcs
"""

import psycopg2
from simplejson import loads, dumps
from configs import db_configs
from psycopg2.extras import Json

db = psycopg2.connect(**db_configs)
cur = db.cursor()


def upload_link(link, id_):
    cur.execute("UPDATE seq_table SET link = '%s' WHERE id = %d" % (link, id_))
    db.commit()


def get_links():
    cur.execute('SELECT id, link FROM seq_table')
    return cur.fetchall()


def get_sequences():
    cur.execute("SELECT * FROM seq_table")
    data = cur.fetchall()
    result = []
    if data:
        for d in data:
            d = list(d)
            if not d[1]:
                continue
            d[1] = loads(d[1])
            d[1].update(dict(id_=d[0]))
            d = d[1]
            result.append(d)
    return result


def add_feedback(seq_id, user_id, stars=None, comments=None):
    if (not comments) and stars:
        cur.execute('INSERT INTO feedback(id, from_user_id, stars) VALUES(%d, %d, %d)' % (seq_id, user_id, stars))
        db.commit()
        return
    cur.execute("UPDATE feedback SET comment = '%s' where from_user_id = %d and id = %d" % (comments, user_id, seq_id))
    db.commit()


def get_sequence(id_):
    query = "SELECT * FROM seq_table WHERE id = %d"
    cur.execute(query % id_)
    data = cur.fetchone()
    if not data[1]:
        return dict(id=id_)
    data = loads(data[1])
    data.update(id=id_)
    return data


def get_lesson(lesson_id, seq_id):
    return loads(get_sequence(seq_id)).get('lessons')[lesson_id]


def update_sequence(data):
    data['lessons'] = [lesson.__dict__ if not isinstance(lesson, dict) else lesson for lesson in data['lessons']] if data['lessons'] else None
    cur.execute("UPDATE seq_table SET data = %s WHERE id=%d" % (Json(dumps(data)), data['id_']))
    db.commit()


def update_lesson(seq_id, data):
    seq = get_sequence(seq_id)
    if not seq['lessons']:
        seq['lessons'] = []
    seq['lessons'] = [(lesson if isinstance(lesson, dict) else lesson.__dict__) for lesson in seq['lessons'] if lesson['_id_'] != data['_id_']]
    seq['lessons'].append(data)
    cur.execute("UPDATE seq_table SET data = %s WHERE id=%d" % (Json(dumps(seq)), seq_id))
    db.commit()


def create_sequence():
    cur.execute("INSERT INTO seq_table(data) VALUES(%s)", [Json({})])
    db.commit()
    cur.execute('SELECT MAX(id) FROM seq_table')
    return cur.fetchone()[0]


def get_subscribes(user_id):
    cur.execute('SELECT subscribes FROM users_table WHERE user_id = %d' % user_id)
    return cur.fetchone()


def add_subscribes(user_id, value):
    cur.execute('UPDATE users_table SET subscribes = subscribes + %d where user_id = %d' % (value, user_id))
    db.commit()


def add_user(user_id):
    cur.execute('SELECT * FROM users_table WHERE user_id = %d' % user_id)
    if not cur.fetchone():
        cur.execute('INSERT INTO users_table VALUES (%d, 0)' % user_id)
        db.commit()


def get_users():
    cur.execute('SELECT * FROM users_table')
    return dumps(cur.fetchall())


def get_feedback():
    cur.execute('SELECT * FROM feedback')
    return dumps(cur.fetchall())


def get_seq_table():
    cur.execute('SELECT * FROM seq_table')
    return dumps(cur.fetchall())


def get_columns(table_name):
    cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \'%s\'' % table_name)
    return dumps(cur.fetchall())
