#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telebot

types = telebot.types
bot = telebot.TeleBot('525874076:AAHrpOItjryLt_N2-H3aQLXNtopyo5i1W_k')


# Переопределение метода отправки сообщения (защита от ошибок)
def send_message(chat_id, message, reply_markup=None, parse_mode=None):
    return bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=parse_mode)


def edit_message(chat_id, message_id, message_text, reply_markup=None, parse_mode=None):
    return bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                 text=message_text, reply_markup=reply_markup, parse_mode=parse_mode)


def send_image(image, chat_id, message, reply_markup=None, parse_mode='markdown'):
    return bot.send_photo(chat_id=chat_id, caption=message, photo=image, reply_markup=reply_markup)


def delete_message(chat_id, message_id):
    return bot.delete_message(chat_id, message_id)