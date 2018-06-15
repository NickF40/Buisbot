"""
markups.py - markup generator funcs definitions

Todo: #
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_markup():
    return InlineKeyboardMarkup(row_width=1).row(InlineKeyboardButton('Мои подписки', callback_data='my')).row(
                                                 InlineKeyboardButton('Новая подписка', callback_data='catalog')).row(
                                                 InlineKeyboardButton('Наши контакты',  callback_data='contacts'))

"""
def lesson_markup(seq_id, lesson_id):
    seq = postgres.get_sequence(seq_id)
    lesson = seq['lessons'][lesson_id-1]
    but1 = InlineKeyboardButton('Подробнее', callback_data='info/lesson/'+str(seq_id)+'/'+str(lesson_id)) if lesson['more'] else None
    but2 = InlineKeyboardButton('Link', url=lesson['link']) if lesson['link'] else None
    markup = InlineKeyboardMarkup(row_width=2)
    if but1:
        markup.add(but1)
    if but2:
        markup.add(but2)
    return markup
"""


def catalog(data, last_=None):
    markup = InlineKeyboardMarkup(row_width=1)
    data_ = []
    last = None
    for seq in data:
        if len(markup.keyboard) > 5:
            markup.add(InlineKeyboardButton('nextpage/' + str(last)))
            break
        if last_:
            if seq['id_'] < last_:
                continue
        markup.add(InlineKeyboardButton('Подписаться на '+seq['name'], callback_data='subscribe/'+str(seq['id_'])))
        data_.extend([seq['name'], '\t - \t'+seq['description'], '\n'])
        last = seq['id_']
    return [data_, markup]


def start_markup(id_):
    return InlineKeyboardMarkup().row(InlineKeyboardButton('Подробнее', callback_data='info/start/'+str(id_)))


def yes_no(seq_id, instance, arg=None):
    call_true = instance+'/1/'+str(seq_id)
    call_false = instance+'/0/' + str(seq_id)
    if arg or (str(arg).isdigit() and int(arg) == 0):
        call_true += '/' + str(arg)
        call_false += '/' + str(arg)

    return InlineKeyboardMarkup(row_width=2).\
        row(
        InlineKeyboardButton('Да', callback_data=call_true),
        InlineKeyboardButton('Нет', callback_data=call_false)
        )


def stars(seq_id):
    markup = InlineKeyboardMarkup(row_width=3)
    markup.row(*[InlineKeyboardButton("⭐"*i, callback_data='stars/'+str(i)+'/'+str(seq_id)) for i in range(1, 3)])
    markup.row(InlineKeyboardButton("⭐⭐⭐⭐", callback_data='stars/'+str(4)+'/'+str(seq_id)))
    markup.row(InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data='stars/'+str(5)+'/'+str(seq_id)))
    markup.add(InlineKeyboardButton('Пропустить', callback_data='skipstars'))
    return markup


def unsub(subscribes):
    markup = InlineKeyboardMarkup()
    for sub in subscribes:
        markup.row(InlineKeyboardButton("Отписаться от %s" % sub.name, callback_data='unsub/'+str(sub.id_)))
    return markup


def les_markup(link, more, lesson_id, seq_id):
    markup = InlineKeyboardMarkup()
    if link:
        markup.add(InlineKeyboardButton('Link', url=link))
    if more:
        markup.add(InlineKeyboardButton('Link', callback_data="info/lesson/"+str(seq_id) + '/' + str(lesson_id)))
    return markup


def choice_marup(step, seq_id):
    return InlineKeyboardMarkup().row(
        InlineKeyboardButton('Да', callback_data='choice/1/%d/%d' % (int(step), int(seq_id))),
        InlineKeyboardButton('Нет', callback_data='choice/0/%d/%d' % (int(step), int(seq_id)))
    )