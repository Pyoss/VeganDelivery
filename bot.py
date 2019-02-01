#!/usr/bin/env python
# -*- coding: utf-8 -*-
import telebot
import main

bot = telebot.TeleBot('525874076:AAHrpOItjryLt_N2-H3aQLXNtopyo5i1W_k', threaded=False)


proxy = 'http://5.189.172.203:3128'
telebot.apihelper.proxy = {
  'http': proxy,
  'https': proxy
}


types = telebot.types
main.load_shops()


@bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
def test_chosen(chosen_inline_result):
    print(chosen_inline_result)
    if chosen_inline_result.result_id[0] == '1':
        order = main.orders[chosen_inline_result.from_user.id]
        order.add_item_from_inline(chosen_inline_result.result_id)


# Инлайн поиска магазина
@bot.inline_handler(func=lambda query: len(query.query) > 4 and ':' in query.query)
def query_text(query):
    main.process_query(query, bot)


@bot.message_handler(commands=['new_order'])
def start(message):
    main.create_order(message.from_user.id)


@bot.message_handler(content_types=['text'])
def text(message):
    if message.from_user.id in main.waiting:
        order = main.waiting[message.from_user.id]
        print('Запрос "{}" к заказу номер {}'.format(message.text, order.id))
        print(order.__waiting_text_func__)
        if order.__waiting_text_func__ is not None:
            print('Запрос выполняется...'.format(message.text, order.id))
            order.complete_waiting(message.text)


@bot.callback_query_handler(func=lambda call: call)
def handle(call):
    call_data = call.data.split('_')
    print(call_data)
    order = main.orders[int(call_data[0])]
    order.handle(call_data)


bot.skip_pending = True

if __name__ == '__main__':
    bot.polling(none_stop=True)