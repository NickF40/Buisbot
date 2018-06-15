from postgres import upload_link
from random import choice
from string import ascii_letters, digits
import psycopg2 as sql
from configs import db_configs


conn = sql.connect(**db_configs)
cur = conn.cursor()

def init():
    cur.execute('CREATE TABLE seq_table(id SERIAL PRIMARY KEY, data JSONB, link TEXT )')
    cur.execute('CREATE TABLE users_table(user_id INTEGER, subscribes INTEGER, )')
    cur.execute('CREATE TABLE feedback(id SERIAL PRIMARY KEY, from_user_id INTEGER, stars INTEGER, comment TEXT)')
    conn.commit()

init()

"""
sequences = dict()
def gen_string():
    string = ''.join(choice(ascii_letters + digits) for i in range(5))
    if string in sequences.keys():
        return gen_string()
    return string

upload_link(gen_string(), 63)
upload_link(gen_string(), 64)
"""



