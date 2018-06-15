"""
Copy of main.py with some Telegram Payments handlers added
"""

import telebot
from telebot.types import LabeledPrice, ShippingOption
from configs import *   # should've been configs2 here!
from texts import *
from markups import *
from random import choice
from string import ascii_letters, digits
from classes import Sequence, LessonsPool
import postgres
import cherrypy
from telegram.ext import Updater, Job
from time import time, ctime
import json
from wrappers import wrap_bridge, wrap_lesson, wrap_seq, wrap_feedback, seq_steps, les_steps

bot = telebot.TeleBot(TOKEN)
sequences = {item[1]: item[0] for item in Sequence.get_links()}
sequences2 = {item[0]: item[1] for item in Sequence.get_links()}

# working with pool
pool = LessonsPool()

upd = Updater(TOKEN)
queue = upd.job_queue

shipping_options = [
    ShippingOption(id='instant', title='WorldWide Teleporter').add_price(LabeledPrice('Teleporter', 1000)),
    ShippingOption(id='pickup', title='Local pickup').add_price(LabeledPrice('Pickup', 300))]


def process(upd, job):
    # should return dicts!!!
    print('checking...', ctime(time()))
    lessons = pool.pop_lessons()
    if lessons:
        for lesson in lessons:
            seq = Sequence(*[None for i in range(9)], key_id=lesson['_seq_id_'])
            for user_id in lesson['users']:
                bot.send_message(user_id, lesson['data'],
                                 reply_markup=les_markup(lesson['link'], lesson['more'], lesson['_id_'],
                                                         lesson['_seq_id_']))
                if lesson['photo']:
                    with open('photos/%s' % lesson['photo'], 'rb') as photo:
                        bot.send_photo(user_id, photo)
                if lesson['document']:
                    with open('documents/%s' % lesson['document'], 'rb') as document:
                        bot.send_document(user_id, document)
                if len(seq.lessons) == lesson['_id_'] + 1:
                    bot.send_message(user_id, seq.finish_message)
                else:
                    seq.next(lesson['_id_'], user_id)


queue.put(Job(process, interval=60), 0)

queue.start()


def find_key(d, value):
    return [k for k, v in d.items() if v == value]


def gen_string():
    string = ''.join(choice(ascii_letters + digits) for i in range(5))
    if string in sequences.keys():
        return gen_string()
    return string


def get_unique_seq(user_id):
    global pool
    return [seq for seq in postgres.get_sequences() if seq['id_'] not in pool.get_subscribes(user_id)]


# Cherrypy calls handler
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

    @cherrypy.expose
    def stop(self):
        print('!!!!')
        return '<h1>Here<h1>'

    @cherrypy.expose
    def get_tables(self):
        return 'seq_table,users_table,feedback'

    @cherrypy.expose
    def get_columns(self, table_name):
        print(postgres.get_columns(table_name))
        return postgres.get_columns(table_name)

    @cherrypy.expose
    def get_rows(self, table_name):
        if table_name == 'users_table':
            return postgres.get_users()
        elif table_name == 'feedback':
            return postgres.get_feedback()
        elif table_name == 'seq_table':
            return postgres.get_seq_table()



@bot.message_handler(commands=['start'])
def handle_start(message):
    print(message.text)
    if len(message.text) > 6:
        key = message.text[7:]
        if key not in sequences.keys():
            bot.send_message(message.chat.id, 'Вы прошли по неработающей ссылке.\n%s' % start_text)
            return
        seq = Sequence(*[None for i in range(9)], key_id=sequences.get(key))
        if not seq.price:
            prices = [LabeledPrice('Комиссия', 10000)]
        else:
            prices = [LabeledPrice(label=seq.name, amount=int(seq.price) * 100), LabeledPrice('Комиссия', 10000)]

        bot.send_invoice(message.chat.id, title=seq.name,
                         description=seq.description,
                         provider_token=PROVIDER_TOKEN,
                         currency='rub',
                         photo_url='http://hsct.co.uk/wp-content/uploads/2016/04/course2.png',
                         photo_height=448,  # !=0/None or picture won't be shown
                         photo_width=1024,
                         photo_size=512,
                         is_flexible=False,  # True If you need to set up Shipping Fee
                         prices=prices,
                         start_parameter='test-query',
                         invoice_payload='%d/%d' % (seq.id_, message.chat.id))
        # bot.send_message(message.chat.id, seq.start_message, reply_markup=start_markup(seq.id_))
        # seq.start(message.from_user.id)
        # pool.reload()
    else:
        bot.send_message(message.chat.id, menu_text, reply_markup=main_markup())


@bot.message_handler(func=lambda message: message.text == 'Меню')
def handle_menu_(message):
    bot.send_message(message.chat.id, menu_text, reply_markup=main_markup())


@bot.message_handler(commands=['create'])
def handle_new(message):
    id_ = Sequence.create()
    str_ = gen_string()
    Sequence.set_link(str_, id_)
    sequences.update({str_: id_})
    sequences2.update({id_: str_})
    # print(sequences)
    with open('sequences.txt', 'w', encoding='utf-8') as file:
        file.write(json.dumps(sequences))
    msg = bot.send_message(message.chat.id, creation_text)
    bot.register_next_step_handler(msg, wrap_seq(id_, 'name', seq_steps, bot))


@bot.message_handler(commands=['copyright'])
def handle_copyright(message):
    bot.send_message(message.chat.id, 'Designed and developed by LampusIT(www.lampus-it.com)\n©LampusIT, 2017')


@bot.message_handler(commands=['menu'])
def handle_menu(message):
    bot.send_photo(message.chat.id, open('course2.png', 'rb'))
    bot.send_message(message.chat.id, menu_text, reply_markup=main_markup())


@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['link'])
def handle_help(message):
    bot.send_message(message.chat.id, LINK + '\nСпасибо, что помогаете привлечь новых пользователей!'
                                             'Больше людей - больше действительно стоящих курсов')


@bot.callback_query_handler(func=lambda call: call.data == 'my')
def handle_my(call):
    subscribes = pool.get_subscribes(call.message.chat.id)
    subscribes = [Sequence(*[None for i in range(9)], key_id=int(sub)) for sub in subscribes]
    if not subscribes:
        bot.edit_message_text('Вы ещё не подписаны ни на один курс!\n\n' + menu_text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              reply_markup=main_markup())
        return
    bot.edit_message_text('Cписок ваших подписок - нажмите на соовтетствующие кнопки чтобы отписаться',
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=unsub(subscribes))


@bot.callback_query_handler(func=lambda call: call.data == 'catalog')
def handle_catalog(call):
    data = get_unique_seq(call.message.chat.id)
    if not data:
        bot.send_photo(call.message.chat.id, open('404.png', 'rb'))
        bot.send_message(call.message.chat.id, 'Нет доступных курсов..')
        return
    for seq in data:
        if not seq['price']:
            prices = [LabeledPrice('Комиссия', 10000)]
        else:
            prices = [LabeledPrice(label=seq['name'], amount=int(seq['price']) * 100), LabeledPrice('Комиссия', 10000)]
        bot.send_invoice(call.message.chat.id, title=seq['name'],
                         description=seq['description'],
                         provider_token=PROVIDER_TOKEN,
                         currency='rub',
                         photo_url='http://hsct.co.uk/wp-content/uploads/2016/04/course2.png',
                         photo_height=448,  # !=0/None or picture won't be shown
                         photo_width=1024,
                         photo_size=512,
                         is_flexible=False,  # True If you need to set up Shipping Fee
                         prices=prices,
                         start_parameter='test-query',
                         invoice_payload='%d/%d' % (seq['id_'], call.message.chat.id))


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    print(shipping_query)
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options,
                              error_message='Oh, seems like our system administrators are having a lunch now. Try again later!')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Hackers tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id, "Спасибо за покупку, теперь вам доступен этот курс!")

    seq = Sequence(*[None for i in range(9)], key_id=int(message.successful_payment.invoice_payload.split('/')[0]))
    bot.send_message(message.chat.id, 'Поздравляем! Вы подписались на курс \"%s\"\n' % seq.name)
    bot.send_message(message.chat.id,  seq.start_message, reply_markup=start_markup(seq.id_))
    seq.start(int(message.successful_payment.invoice_payload.split('/')[1]))


@bot.callback_query_handler(func=lambda call: call.data == 'contacts')
def handle_contacts(call):
    bot.send_message(call.message.chat.id, 'Наши контакты \n\nКоманда разработчиков:'
                                           '\n\t - \tНикита @lampus_it (баг-репорты сюда)'
                                           '\n\n\tВладелец бота, автор идеи и админ проекта:'
                                           '\n\t - \tАлексей @AfkParty (отзывы и пожелания)')


@bot.callback_query_handler(func=lambda call: call.data.startswith('nextpage'))
def handle_next_page(call):
    data = get_unique_seq(call.message.chat.id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                  reply_markup=catalog(data, int(call.data.split('/')[1]))[1])


@bot.callback_query_handler(func=lambda call: call.data.startswith('newlesson'))
def handle_lesson_request(call):
    splitted = call.data.split('/')
    if splitted[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Хорошо, приступим! Введите мне текст урока ниже..')
        bot.register_next_step_handler(msg, wrap_lesson(int(splitted[2]), int(splitted[3]), 'data', les_steps, bot))
    else:
        bot.send_message(call.message.chat.id,
                         'Отлично, курс создан! Вы можете пройти его по ссылке '
                         + URL + str(sequences2[int(splitted[2])]),
                         reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                         .row(telebot.types.KeyboardButton('Меню')))


@bot.callback_query_handler(func=lambda call: call.data.startswith('price'))
def handle_ask_price(call):
    splitted = call.data.split('/')
    if splitted[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Тогда, напишите ниже его цену в рублях')
        bot.register_next_step_handler(msg, wrap_bridge(int(splitted[2]), bot))
    else:
        bot.send_message(call.message.chat.id, 'Хорошо!')
        seq = Sequence(*[None for i in range(9)], key_id=int(splitted[2]))
        bot.send_message(call.message.chat.id,
                         'Вы хотите создать урок номер 1?',
                         reply_markup=yes_no(seq.id_, 'newlesson', 0))


#
# TODO(Nick)
# Write bridges for photo and document handling
#


@bot.callback_query_handler(func=lambda call: call.data.startswith('photo'))
def handle_request2(call):
    splitted = call.data.split('/')
    if splitted[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Теперь отправьте фотографию,'
                                                     ' которая должна быть прикреплена к вашему уроку')
        bot.register_next_step_handler(msg, wrap_lesson(int(splitted[2]), int(splitted[3]), 'photo', les_steps, bot))
    else:
        bot.send_message(call.message.chat.id, "Хорошо! Хотите прикрепить документ?",
                         reply_markup=yes_no(int(splitted[2]), 'document', int(splitted[3]))
                         )


@bot.callback_query_handler(func=lambda call: call.data.startswith('document'))
def handle_request2(call):
    splitted = call.data.split('/')
    if splitted[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Теперь, отправьте документа,'
                                                     ' который должен быть прикреплена к вашему уроку')
        bot.register_next_step_handler(msg, wrap_lesson(int(splitted[2]), int(splitted[3]), 'document', les_steps, bot))
    else:
        bot.send_message(call.message.chat.id, "Хорошо! Прикрепить ссылку к вашему уроку?",
                         reply_markup=yes_no(int(splitted[2]), 'link', int(splitted[3]))
                         )


@bot.callback_query_handler(func=lambda call: call.data.startswith('unsub'))
def handle_unsub(call):
    pool.delete_from(call.message.chat.id, int(call.data.split('/')[1]))
    subscribes = [Sequence(*[None for i in range(9)], key_id=int(sub)) for sub in
                  pool.get_subscribes(call.message.chat.id)]
    bot.edit_message_text(chat_id=call.message.chat.id,
                          text='Вы успешно отписались! Как бы вы смогли оценить этот курс?',
                          message_id=call.message.message_id, reply_markup=stars(int(call.data.split('/')[1])))


@bot.callback_query_handler(func=lambda call: call.data.startswith('link'))
def handle_request2(call):
    splitted = call.data.split('/')
    if splitted[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Теперь напишите мне ссылку,'
                                                     ' которая должна быть прикреплена к вашему уроку')
        bot.register_next_step_handler(msg, wrap_lesson(int(splitted[2]), int(splitted[3]), 'link', les_steps, bot))
    else:
        bot.send_message(call.message.chat.id, "Хорошо! Добавить кнопку \"Подробнее\"?",
                         reply_markup=yes_no(int(splitted[2]), 'more', int(splitted[3]))
                         )


@bot.callback_query_handler(func=lambda call: call.data.startswith('day'))
def handle_request3(call):
    splitted = call.data.split('/')
    if splitted[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Теперь, напишите мне ссылку,'
                                                     ' которая долна быть прикреплена к вашему уроку')
        bot.register_next_step_handler(msg, wrap_lesson(int(splitted[2]), int(splitted[3]), 'link', les_steps))


@bot.callback_query_handler(func=lambda call: call.data.startswith('more'))
def handle_request4(call):
    splitted = call.data.split('/')
    if splitted[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Напишите дополнительную информацию об уроке,'
                                                     ' которую смогут увидеть пользователи,'
                                                     ' нажавшие на кнопку \"Подробнее\"')
        bot.register_next_step_handler(msg, wrap_lesson(int(splitted[2]), int(splitted[3]), 'more', les_steps, bot))
    else:
        seq = Sequence(*[None for i in range(9)], key_id=int(splitted[2]))
        bot.send_message(call.message.chat.id, 'Отлично! Вы только что успешно создали новый урок!\n Создать ещё один?',
                         reply_markup=yes_no(int(splitted[2]), 'newlesson', len(seq.lessons) if seq.lessons else 0))


@bot.callback_query_handler(func=lambda call: call.data.startswith('stars'))
def handle_stars(call):
    data = call.data.split('/')
    seq = Sequence(*[None for i in range(9)], key_id=int(data[2]))
    seq.feed_stars(call.message.chat.id, int(data[1]))
    bot.send_message(call.message.chat.id, 'Cпасибо за оценку!\nНаписать комментарий?\n'
                                           'Обратная связь очень важна для нас, '
                                           'ваши отзывы помогут нам сделать ресурс лучше.',
                     reply_markup=yes_no(seq.id_, 'commentary'))


@bot.callback_query_handler(func=lambda call: call.data.startswith('commentary'))
def handle_is_comment(call):
    data = call.data.split('/')
    if data[1] == '1':
        msg = bot.send_message(call.message.chat.id, 'Хорошо! Введите комментарий ниже')
        bot.register_next_step_handler(msg, wrap_feedback(bot, int(data[2])))
    else:
        bot.send_message(call.message.chat.id, 'Спасибо за оценку!\n' + menu_text, reply_markup=main_markup())


@bot.callback_query_handler(func=lambda call: call.data.startswith('skipstars'))
def skip_stars(call):
    bot.edit_message_text('Вы успешно завершили курс!\n%s' % start_text, chat_id=call.message.chat.id,
                          message_id=call.message.message_id, reply_markup=main_markup())


@bot.callback_query_handler(func=lambda call: call.data.startswith('subscribe'))
def subscribe(call):
    global pool
    if '/' in call.data:
        id_ = int(call.data.split('/')[1])
        seq = Sequence(*[None for i in range(9)], key_id=id_)
        bot.send_message(call.message.chat.id,
                         ('Поздравляем! Вы подписались на курс %s\n' % seq.name) + seq.start_message,
                         reply_markup=start_markup(id_))
        seq.start(call.message.chat.id)
        pool.reload()
        return
    key = call.data[9:]
    if len(key) > 5:
        raise Exception('Sequence key error: expected key 5 character long, got %d' % len(key))
    seq = Sequence(*[None for i in range(9)], key_id=sequences.get(key))
    bot.send_message(call.message.chat.id, seq.start_message, reply_markup=start_markup(seq))
    seq.start(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('info'))
def handle_infos(call):
    data = call.data.split('/')
    if data[1] == 'start':
        seq = Sequence(*[None for i in range(9)], key_id=int(data[2]))
        bot.edit_message_text(seq.more, chat_id=call.message.chat.id, message_id=call.message.message_id)
    if data[1] == 'lesson':
        seq = Sequence(*[None for i in range(9)], key_id=int(data[2]))
        bot.edit_message_text(seq.lessons[int(data[2])]['more'], chat_id=call.message.chat.id,
                              message_id=call.message.id)


try:
    bot.remove_webhook()

    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                    certificate=open(WEBHOOK_SSL_CERTIFICATE, 'r'))

    # Disable requests log
    access_log = cherrypy.log.access_log
    for handler in tuple(access_log.handlers):
        access_log.removeHandler(handler)

    # Configure and start server
    cherrypy.config.update({
        'server.socket_host': WEBHOOK_LISTEN,
        'server.socket_port': WEBHOOK_PORT,
        'server.ssl_module': 'builtin',
        'server.ssl_certificate': WEBHOOK_SSL_CERTIFICATE,
        'server.ssl_private_key': WEBHOOK_SSL_PRIVATE_KEY
    })

    cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})

    cherrypy.config.update({
        'server.socket_host': WEBHOOK_LISTEN,
        'server.socket_port': WEBHOOK_PORT2,
        'server.ssl_module': 'builtin'
    })
    cherrypy.quickstart(WebhookServer2(), WEBHOOK_URL_BASE2)


except Exception as e:
    raise Exception('Webhook initializing error')
