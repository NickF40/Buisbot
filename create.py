"""
Temporary testing file. Need to add it in gitignore
"""

from main import bot, gen_string
from classes import Lesson, Sequence, LessonsPool
import json
from texts import creation_text


lines = ['name', 'description', 'start_message', 'more', 'finish_message', 'price', ]
texts = ['Отличное имя! Теперь введите описание курса(не более 6 предложений), которое пользователи увидят в каталоге.',
         'Хорошее описание, теперь введите приветственное сообщение для только что подписавшегося пользователя.',
         'Теперь, введите дополнительную информацию к приветственному сообщению.',
         'Неплохо! Теперь введите сообщение, которым будет оканчиваться ваш курс!']

valids = [
    '',
    '',
    '',
    '^(?:http|ftp)s?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)$'

]

tree = {
    'Платный?':[False, 'Напишите цену' ]
}


def sequencer(step, seq_id):
    def wrapper(message, step=step, seq_id=seq_id):
        seq = Sequence(*[None for i in range(9)], key_id=seq_id)
        seq.__dict__[lines[step]] = message.text
        seq._update()
        if step == 4:
            pass
        msg = bot.send_message(message.chat.id, texts[step])
        bot.register_next_step_handler(msg, sequencer(step+1, seq_id))

sequences = {item[1]: item[0] for item in Sequence.get_links()}
sequences2 = {item[0]: item[1] for item in Sequence.get_links()}

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
    bot.register_next_step_handler(msg, )