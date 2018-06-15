"""
Wrappers.py - set of functions, that wrap the process of sending request, handling response and saving data from user
Helps to shorten lines of code, but get more complex syntax instead

Consists of:
    Steps sequences for requesting:
        - Sequence(Course) data
        - Lesson's data (each one)

    Sequence(course) request wrapper

    Bridge(transition between course and lesson's part) wrapper

    Lessons wrapper

    Feedback wrapper


Each one of wrappers returns function, that will handle new data from "steps",
which than passes to the next_step_handler() func. as parameter

Todo: Need to rewrite with Builders (classes_new.py)
"""

from texts import *
from markups import *
from classes import Lesson, Sequence
import re
from time import strftime
import uuid
import os

# Sequence of lines
seq_steps = dict(
    name=[1, 'description'],
    description=[2, 'more'],
    more=[3, 'start_message'],
    start_message=[4, 'finish_message'],
    finish_message=[5, 'more', True]

)

les_steps = dict(
    data=[1, 'day'],
    day=[2, 'time'],
    time=[3, 'photo'],
    photo=[4, 'document'],
    document=[1, 'link'],
    link=[2, 'more'],
    more=[2, 'next'],
)


def validate_link(link):
    regex = re.compile(
        r'^(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if re.match(regex, link):
        return True
    return False


def validate_time(time, day):
    hour, mins = map(int, time.split(':'))
    if day <= 0:
        raise Exception('Error occurred : invalid day')
    if hour < 3 and day == 1:
        return None, None
    else:
        if hour >= 3:
            return ':'.join([str(hour - 3).rjust(2, '0'), str(mins).rjust(2, '0')]), day
        else:
            day -= 1
            hour = str(24 + hour - 3)
            return ':'.join([hour.rjust(2, '0'), str(mins).rjust(2, '0')]), day


# return func with passed default parameters
def wrap_seq(id_, datatype_, steps, bot):
    def updater(message, id_=id_, datatype_=datatype_):
        # print('id_= ', id_)
        data = message.text
        seq = Sequence(*[None for i in range(9)], key_id=id_)
        if datatype_ == 'description':
            data += '\n\nПодписаться на этот курс?'
        seq.__dict__[datatype_] = data
        print(datatype_, data)
        seq._update()
        if datatype_ != 'finish_message':
            msg = bot.send_message(message.chat.id, create_text[steps.get(datatype_)[0]])
            bot.register_next_step_handler(msg, wrap_seq(id_, steps.get(datatype_)[1], seq_steps, bot))
        else:
            bot.send_message(message.chat.id, create_text[steps.get(datatype_)[0]],
                             reply_markup=yes_no(id_, 'price'))

    return updater


def wrap_bridge(id_, bot):
    def wrapper(message, id_=id_):
        data = message.text
        seq = Sequence(*[None for i in range(9)], key_id=id_)
        if not data.isdigit():
            msg = bot.send_message(message.chat.id, 'Неверный формат денег!\nВведите сумму одним числом в рублях')
            bot.register_next_step_handler(msg, wrap_bridge(id_, bot))
            return
        elif int(data) > 100000:
            msg = bot.send_message(message.chat.id, 'Неверный формат денег!\nСумма должны быть меньше 100 000 рублей.')
            bot.register_next_step_handler(msg, wrap_bridge(id_, bot))
            return
        seq.__dict__['price'] = data
        seq._update()
        bot.send_message(message.chat.id, 'Вы хотите создать урок номер 1?',
                         reply_markup=yes_no(seq.id_, 'newlesson', 0))

    return wrapper


def wrap_lesson(seq_id, lesson_id, step, steps, bot):
    def updater(message, seq_id=seq_id, lesson_id=lesson_id, step=step, steps=steps):
        seq = Sequence(*[None for i in range(9)], key_id=seq_id)

        # handles start
        if step == 'data':
            seq.lessons = [] if not seq.lessons else seq.lessons
            seq.lessons.append(Lesson(len(seq.lessons), seq.id_, None, None, message.text, None, None))
            msg = bot.send_message(message.chat.id,
                                   'Теперь, введите номер дня, начиная с дня подписки, на который придется ваш %d урок!' %
                                   int(lesson_id + 1))
            bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'day', steps, bot))
            seq._update()
            return

        # Окончание создания урока и запрос на создание следующего
        elif step == 'more':
            seq.lessons[lesson_id][step] = message.text
            bot.send_message(message.chat.id, 'Отлично! Вы только что успешно создали новый урок!\n Создать ещё один?',
                             reply_markup=yes_no(seq_id, 'newlesson', lesson_id + 1))
            seq._update()
            return

        # handles photo
        # error handling included
        # Handles document entity, gets it's file id, downloads it from telegram server, saves.
        elif step == 'photo':
            # error handle
            if not message.photo:
                msg = bot.send_message(message.chat.id, 'Photo expected, please, try again and send photo...')
                bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'photo', steps, bot))

            id_ = uuid.uuid4()
            ph_file = open('photos/%s.jpeg' % id_, 'wb')
            ph_file.write(bot.download_file(bot.get_file(message.photo[-1].file_id).file_path))
            ph_file.close()
            seq.lessons[lesson_id][step] = '%s.jpeg' % id_
            seq._update()

        # handles document
        # error handling included
        elif step == 'document':
            if not message.document:
                msg = bot.send_message(message.chat.id, 'Document expected, please, try again and send photo...')
                bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'document', steps, bot))

            id_ = uuid.uuid4()
            filetype = message.document.file_name.split('.')[1]
            doc_file = open('documents/%s.%s' % (id_, filetype), 'wb')
            doc_file.write(bot.download_file(bot.get_file(message.document.file_id).file_path))
            doc_file.close()
            seq.lessons[lesson_id][step] = '%s.%s' % (id_, filetype)
            seq._update()

        # --------------ERROR HANDLING BLOCK--------------
        else:

            reg_expr = '^(([0,1][0-9])|(2[0-3])):[0-5][0-9]$'
            if step == 'time':
                # Checks for matching regular expression
                if not re.match(reg_expr, message.text):
                    msg = bot.send_message(message.chat.id, 'Неверный формат времени!\n'
                                                            'Введите время урока согласно примеру: 18:00')
                    bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'time', steps, bot))
                    return
                # Checks time for being <= previous days
                time, day = validate_time(message.text, int(seq.lessons[lesson_id]['day']))
                if time is None and day is None:
                    msg = bot.send_message(
                        message.chat.id,
                        'Неверный формат времени!'
                        '\nВремя исполнения первого урока должно быть больше или равно 03:00 во избежание ошибок!\n'
                        'Введите время ещё раз...')
                    bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'time', steps, bot))
                    return
                else:
                    seq.lessons[lesson_id]['day'] = day
                    message.text = time
                if not seq.check_time(seq.lessons[lesson_id]['day'], message.text):
                    msg = bot.send_message(
                        message.chat.id,
                        'Неверный формат времени!'
                        '\nВремя исполнения каждого нового урока должно быть больше предыдущего или равен ему!'
                        '\nВремя отправки вашего последнего урока - %s, отправьте следующий урок позже.'
                        % strftime('%H:%M', max(seq.get_times(seq.lessons[lesson_id]['day']))))
                    bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'time', steps, bot))
                    return
            elif step == 'day':
                # checks day format
                if not message.text.isdigit():
                    msg = bot.send_message(message.chat.id, 'Неверный формат дня!\nВведенное число 2 будет означать,'
                                                            ' что этот урок отправится пользователю на вторые'
                                                            ' сутки после подписки.'
                                                            '\nВведите день согласно примеру: 1')
                    bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'day', steps, bot))
                    return
                # checks day for being <= previous days
                elif not seq.is_max_day(int(message.text)):
                    msg = bot.send_message(message.chat.id,
                                           "Неверный формат дня!"
                                           "\nДень исполнения каждого нового урока должен быть больше предыдущего или "
                                           "равен ему!\nДень отправки вашего последнего урока - %d, например,"
                                           "вы можете отправить этот урок на %d-й день" %
                                           max(*[lesson['day'] for lesson in seq.lessons if lesson['day']]),
                                           max(*[lesson['day'] for lesson in seq.lessons if lesson['day']]) + 1)
                    bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'day', steps, bot))
                    return
            if step == 'link':
                # checks link for being equal
                # https://www.google.com
                if not validate_link(message.text):
                    msg = bot.send_message(message.chat.id,
                                           'Unvalid URL!\nPlease, check the url spelling and write it again')
                    bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'link', steps, bot))
                    return
            # default
            seq.lessons[lesson_id][step] = message.text
            seq._update()

        # needs special because there's no usage of yes/no
        if step == 'day':
            msg = bot.send_message(message.chat.id, 'Теперь, напиши время формата 18:00,'
                                                    'на которое придется ваш %d урок!\nВнимание, используется '
                                                    'московское время!' % (
                                       lesson_id + 1))
            bot.register_next_step_handler(msg, wrap_lesson(seq_id, lesson_id, 'time', steps, bot))
            return

        # default
        bot.send_message(message.chat.id, lessons_texts[steps.get(step)[0]],
                         reply_markup=yes_no(seq_id, steps.get(step)[1], lesson_id))

    return updater


def wrap_feedback(bot, id_=None):
    def wrapper(message, id_=id_):
        data = message.text
        seq = Sequence(*[None for i in range(9)], key_id=id_)
        seq.feed_comment(message.chat.id, data)
        bot.send_message(message.chat.id, 'Спасибо вам за то, что помогаете сделать наш сервис лучше!\n%s' % start_text,
                         reply_markup=main_markup())

    return wrapper
