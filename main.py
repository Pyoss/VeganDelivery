import random
import bot_methods
import materials
from telebot import types

orders = {}
waiting = {}


class Item:
    def __init__(self, name, desc, price, id):
        self.name = name
        self.price = price
        self.desc = desc
        self.id = id

    def to_order(self, shop, value=1):
        return OrderItem(self.name, self.price, shop, value=value)


class OrderItem(Item):
    def __init__(self, name, price, shop, value=1):
        Item.__init__(self, name, None, price, id=None)
        self.value = value
        self.shop = shop


class Shop:
    def __init__(self, name, item_dict, discount):
        self.name = name
        self.item_dict = item_dict
        self.discount = discount


class Client:
    def __init__(self, number=None, name=None, address=None):
        self.number = number
        self.name = name
        self.address = address


class Order:
    def __init__(self, manager_chat_id):
        self.client = Client()
        self.shop = None
        self.items = []
        self.weight = None
        self.urgent = False
        self.id = manager_chat_id
        self.manager_chat_id = manager_chat_id
        self.message_id = None

        self.courier_price = 300
        self.weight_dict = {5: '<5кг', 7: '5-10кг', 10: '>10кг', 0: 'Такси'}
        self.weight = 5
        self.urgent = False

        self.__waiting_text_func__ = None
        print('Order {} created...'.format(self.id))

    def get_client(self):
        string = 'Создание нового заказа... Введите телефон клиента.'
        self.add_waiting(self.get_client_number)
        self.new_message(string)

    def get_client_number(self, text):
        string = 'Введите имя клиента...'
        self.new_message(string)
        self.add_waiting(self.create_client, text)

    def create_client(self, name, number):
        print('{}{}'.format(name, number))
        self.client.name = name
        print(number)
        number = ''.join([letter for letter in number if letter.isdigit()])
        print(number)
        if number[0] == '8' or number[0] == '7':
            number = '+7' + number[1:]
        else:
            number = '+7' + number
        self.client.number = number
        self.generate_main_menu()

    def message(self, text, reply_markup=None, new=False):
        if not isinstance(reply_markup, types.InlineKeyboardMarkup):
            reply_markup = self.keyboard(reply_markup)
        if new:
            self.delete_message()
        if self.message_id is None:
            self.message_id = bot_methods.send_message(self.manager_chat_id, text, reply_markup=reply_markup).message_id
        else:
            bot_methods.edit_message(self.manager_chat_id, self.message_id, text, reply_markup=reply_markup)

    def new_message(self, text):
        self.delete_message()
        bot_methods.send_message(self.manager_chat_id, text)

    def delete_message(self):
        if self.message_id is not None:
            bot_methods.delete_message(self.manager_chat_id, self.message_id)
            self.message_id = None

    @staticmethod
    def keyboard(buttons):
        if buttons is None:
            return None
        button_list = []
        for button in buttons:
            button_list.append(types.InlineKeyboardButton(button[0], callback_data=button[1]))
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*button_list)
        return keyboard

    def add_waiting(self, func, *args):
        self.__waiting_text_func__ = (func, args)
        waiting[self.manager_chat_id] = self

    def complete_waiting(self, text):
        del waiting[self.manager_chat_id]
        func, self.__waiting_text_func__ = self.__waiting_text_func__, None
        func[0](text, *func[1])

    def handle(self, call_data):
        data_type = call_data[1]
        if data_type == 'shop':
            shop_name = call_data[2]
            self.shop = shop_name
            self.shop_add_menu(shop_name)
        elif data_type == 'ready':
            self.check_out()
        elif data_type == 'client':
            self.client_handler(call_data)
        elif data_type == 'delivery':
            self.delivery_handler(call_data)
        elif data_type == 'items':
            self.items_handler(call_data)
        elif data_type == 'item':
            item_name = call_data[2]
            shop_name = call_data[3]
            self.generate_item_menu(item_name, shop_name)
        elif data_type == 'menu':
            self.generate_main_menu()
        elif data_type == 'add':
            self.add_item(call_data[2], call_data[3], int(call_data[4]))
        elif data_type == 'chooseadd':
            self.add_waiting(self.manual_value_add, call_data[2], call_data[3])
            self.message('Введите количество товара...')

# ------------------------------------МЕТОДЫ КЛИЕНТА----------------------------------------- #

    def client_handler(self, call_data):
        if len(call_data) == 2:
            self.get_client_menu()
            return True
        data_type = call_data[-1]
        if data_type == 'name':
            self.get_new_name()
        elif data_type == 'address':
            self.get_new_address()
        elif data_type == 'number':
            self.get_new_number()

    def get_client_menu(self):
        string = 'Подробности клиента:\n'
        string += 'Адрес: {}\n'.format(self.client.address if self.client.address is not None else '-')
        string += 'Имя: {}\n'.format(self.client.name)
        string += 'Телефон: {}\n'.format(self.client.number)
        keyboard = (('Имя', self.create_callback('client', 'name')),
                    ('Адрес', self.create_callback('client', 'address')),
                    ('Телефон', self.create_callback('client', 'number')),
                    ('Назад', self.create_callback('menu')))
        self.message(string, reply_markup=keyboard)

    def get_new_address(self):
        self.add_waiting(self.set_new_address)
        self.new_message('Введите новый адрес.')

    def set_new_address(self, text):
        self.client.address = text
        self.new_message('Адрес успешно изменен.')
        self.generate_main_menu()

    def get_new_number(self):
        self.add_waiting(self.set_new_number)
        self.new_message('Введите новый номер.')

    def set_new_number(self, text):
        self.client.number = text
        self.new_message('Номер успешно изменен.')
        self.generate_main_menu()

    def get_new_name(self):
        self.add_waiting(self.set_new_name)
        self.new_message('Введите новое имя.')

    def set_new_name(self, text):
        self.client.name = text
        self.new_message('Имя успешно изменено.')
        self.generate_main_menu()

######
# --------------------------------------------- МЕТОДЫ ТОВАРОВ -------------------------------------------- #
######

    def get_items_menu(self):
        string = self.to_string()
        keyboard = (
            ('Добавить', self.create_callback('items', 'new')),
            ('Удалить', self.create_callback('items', 'choosedelete')),
            #('+ Магазин', self.create_callback('items', 'new-shop')),
            ('Назад', self.create_callback('menu')),
            ('Свой товар', self.create_callback('items', 'manual')),
                    )
        self.message(string, reply_markup=keyboard)

    def items_handler(self, call_data):
        if len(call_data) == 2:
            self.get_items_menu()
            return True
        data_type = call_data[2]
        if data_type == 'choosedelete':
            self.get_items_to_delete()
        elif data_type == 'new':
            if self.shop is not None:
                self.shop_add_menu(self.shop)
            else:
                self.shop_choice_menu()
        elif data_type == 'new-shop':
            self.get_new_shops()
        elif data_type == 'manual':
            self.start_manual_item_creation()
        elif data_type == 'delete':
            item_name = call_data[-1]
            self.delete_item(item_name)

    def get_items_to_delete(self):
        string = 'Выберите удаляемый предмет'
        keyboard = [(item.name, self.create_callback('items', 'delete', item.name)) for item in self.items]
        keyboard.append(('Отмена', self.create_callback('menu')))
        self.message(string, reply_markup=keyboard)

    def delete_item(self, item_name):
        self.items = [item for item in self.items if item.name != item_name]
        self.new_message('Товар {} успешно удален из списка.'.format(item_name))
        self.generate_main_menu()

    def get_new_shops(self):
        if not self.shop.additional_shops:
            self.new_message('К данному магазину нельзя добавить новые.')

    def start_manual_item_creation(self):
        self.new_message('Введите название нового товара')
        self.add_waiting(self.set_manual_item_name)

    def set_manual_item_name(self, text):
        self.new_message('Создание товара {}: Введите его цену'.format(text))
        self.add_waiting(self.set_manual_price, text)

    def set_manual_price(self, text, name):
        self.new_message('{}:{}; Сколько товара добавить?'.format(name, text))
        self.add_waiting(self.set_manual_value, text, name)

    def set_manual_value(self, text, price, name):
        self.items.append((OrderItem(name, int(price), shop=self.shop, value=int(text))))
        self.new_message('Товар {} успешно добавлен.'.format(name))
        self.generate_main_menu()

    def generate_item_menu(self, shop_name, item_name):
        item = materials.shops[shop_name].item_dict[item_name]
        print(shop_name)
        print(item_name)
        text = '{} - {}\n\n{}'.format(item.name, str(item.price), item.desc)
        keyboard = (('Добавить 1', self.create_callback('add', shop_name, item.id, '1')),
                    ('Добавить', self.create_callback('chooseadd', shop_name, item.id)),
                    ('Отмена', self.create_callback('menu')))
        self.message(text, reply_markup=keyboard, new=True)

    def add_item_from_inline(self, result_id):
        item_id = result_id[1:]
        item = find_item_from_id(self.shop, item_id)
        self.generate_item_menu(self.shop, item.name)

    def manual_value_add(self, text, shop_name, item_id):
        #try:
        item = find_item_from_id(shop_name, item_id)
        value = int(text)
        self.new_message('{} {} успешно добавлен.'.format(value, get_item(shop_name, item.name).name))
        self.add_item(shop_name, item_id, value)
        #except:
        #    self.message('Это же не число!')
        #    self.generate_item_menu(shop_name, item_name)

    def add_item(self, shop_name, item_id, value):
        item = find_item_from_id(shop_name, item_id)
        order_item = item.to_order(shop_name, value=value)
        if any(ord_item.name == order_item.name for ord_item in self.items):
            ord_item = next(ord_item for ord_item in self.items if ord_item.name == order_item.name)
            ord_item.value += value
        else:
            self.items.append(order_item)
        self.generate_main_menu()


######
# --------------------------------------------- МЕТОДЫ ДОСТАВКИ -------------------------------------------- #
######

    def delivery_handler(self, call_data):
        if len(call_data) == 2:
            self.get_delivery_menu()
            return True
        data_type = call_data[2]
        if data_type == 'weight':
            if len(call_data) == 3:
                self.get_weight_menu()
            else:
                self.weight = int(call_data[-1])
                self.get_delivery_menu()
        elif data_type == 'distance':
            if len(call_data) == 3:
                self.get_distance_menu()
            else:
                self.courier_price = int(call_data[-1])
                self.get_delivery_menu()
        elif data_type == 'manual':
            self.wait_manual_delivery_price()
        elif data_type == 'urgent':
            self.change_urgency()

    def get_delivery_menu(self):
        string = 'Подробности доставки\n'
        string += 'Срочный заказ: {}\n'.format("Да" if self.urgent else "Нет")
        string += 'Вес: {}\n'.format(self.weight_dict[self.weight])
        string += 'Цена за расстояние: {}\n'.format(self.courier_price)
        string += 'Итоговая цена доставки: {}'.format(self.get_courier_income())
        keyboard = (
            ('Вес', self.create_callback('delivery', 'weight')),
            ('Расстояние', self.create_callback('delivery', 'distance')),
            ('Срочность', self.create_callback('delivery', 'urgent')),
            ('Назад', self.create_callback('menu')),
            ('Вручную', self.create_callback('delivery', 'manual')),
                    )
        self.message(string, reply_markup=keyboard)

    def change_urgency(self):
        self.urgent = False if self.urgent else True
        self.get_delivery_menu()

    def get_weight_menu(self):
        string = 'Выберите новый вес.'
        keyboard = [(value, self.create_callback('delivery', 'weight', str(key))) for key, value in self.weight_dict.items()]
        keyboard.append(('Назад', self.create_callback('delivery')))
        self.message(string, reply_markup=keyboard)

    def get_distance_menu(self):
        string = 'Выберите новую цену доставки.'
        keyboard = [(item, self.create_callback('delivery', 'distance', item)) for item in ('250', '300', '350')]
        keyboard.append(('Назад', self.create_callback('delivery')))
        self.message(string, reply_markup=keyboard)

    def wait_manual_delivery_price(self):
        self.add_waiting(self.set_manual_delivery_price)
        self.new_message('Введите новую общую стоимость доставки.')

    def set_manual_delivery_price(self, text):
        self.courier_price = int(text)
        self.urgent = False
        self.weight = 5
        self.new_message('Новая стоимость доставки установлена.')
        self.get_delivery_menu()


# --------------------------------------------- МЕТОДЫ МАГАЗИНА -------------------------------------------- #
    def shop_choice_menu(self):
        buttons = [(value.name, self.create_callback('shop', key)) for key, value in materials.shops.items()]
        buttons.append(('Отмена', self.create_callback('menu')))
        string = 'Выберите магазин'
        self.message(string, reply_markup=buttons)

    def shop_add_menu(self, shop_name):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Поиск', switch_inline_query_current_chat=shop_name + ': '))
        keyboard.add(types.InlineKeyboardButton('Отмена', callback_data=self.create_callback('menu')))
        self.message(text='Выберите товар:',
                     reply_markup=keyboard)

    def generate_main_menu(self):
        text = self.to_string()
        keyboard = [
            ('Товары +\-', self.create_callback('items')),
            ('Подробности', self.create_callback('delivery')),
            ('Клиент', self.create_callback('client'))
        ]
        if self.client.address is not None and self.items:
            keyboard.append(('Готово', self.create_callback('ready')))
        elif self.client.address is None:
            keyboard.append(('Введите адрес!', self.create_callback('client', 'address')))
        self.message(text, reply_markup=keyboard)

    def create_callback(self, *args):
        return '_'.join((str(self.id), *args))

    def get_price(self):
        price = sum(order_item.price*order_item.value for order_item in self.items)
        price += self.get_courier_income()
        return price

    def get_manager_income(self):
        return sum(self.shop.item_list[key.lower()].price * self.items[key]
                   for key in self.items) * self.shop.discount - self.get_owner_income()

    def get_courier_income(self):
        courier_income = self.courier_price
        if self.urgent:
            courier_income += 50
        if self.weight == 7:
            courier_income += 50
        elif self.weight == 10:
            courier_income += 100
        return courier_income

    def get_owner_income(self):
        return sum(
            self.shop.item_list[key.lower()].price * self.items[key] for key in self.items) * self.shop.discount * 0.2

    def to_string(self):
        string = '{} {}\n'.format(self.client.name, self.client.number)
        string += '{}\n'.format(self.client.address if self.client.address is not None else 'Укажите адрес!')
        for order_item in self.items:
            string += '--------  {} * {}: {}р\n'.format(order_item.name, order_item.value,
                                                        order_item.price*order_item.value)
        string += '___________________________\n'
        string += 'Доставка: {}р\n'.format(self.get_courier_income())
        string += 'Итого: {}р'.format(self.get_price())
        return string

    def check_out(self):
        self.new_message('Генерируется заказ...')
        checkout_string = ''
        checkout_string += '{} {}\n'.format(self.client.name, self.client.number)
        checkout_string += '{}\n'.format(self.client.address if self.client.address is not None else 'Без адреса')
        checkout_string += '\n'
        for item in self.items:
            checkout_string += '{} {}*{}\n'.format(item.name, item.price, item.value)
        checkout_string += '\n'
        client_price = self.get_price()
        all_items = sum(order_item.price*order_item.value for order_item in self.items)
        my_cut = all_items * materials.shops[self.shop].discount
        cafe_price = all_items - my_cut
        checkout_string += '{} клиент, {} кафе, {} тебе, {} мне'.format(client_price,
                                                                        int(cafe_price),
                                                                        self.get_courier_income(),
                                                                        int(my_cut))
        self.new_message(checkout_string)


def create_order(manager_chat_id):
    new_order = Order(manager_chat_id)
    orders[new_order.id] = new_order
    new_order.get_client()


def create_test_order(manager_chat_id):
    new_order = Order(manager_chat_id)
    orders[new_order.id] = new_order
    new_order.client.name = 'Тестовое имя'
    new_order.client.number = '555 55 55'
    new_order.generate_main_menu()


def get_item(shop_name, item_name):
    return materials.shops[shop_name].item_dict[item_name]


def load_shops():
    import spreadsheet_sync
    materials.shops = spreadsheet_sync.get_shops()
    print('Список магазинов загружен...')


def find_item_from_id(shop_name, item_id):
    item_list = [value for key, value in materials.shops[shop_name].item_dict.items() if value.id == item_id]
    return item_list[0]


def process_query(query, bot):
        query_data = query.query.split(':')
        shop_name = query_data[0]
        search_word = query_data[1]
        item_dict = materials.shops[shop_name].item_dict
        suitable_items = [value for key, value in item_dict.items() if search_word.lower().replace(' ', '') in key.lower()]
        if len(suitable_items) > 30:
            suitable_items = suitable_items[:30]
        bot.answer_inline_query(query.id, list([types.InlineQueryResultArticle(
            id='1' + str(item.id), title=item.name,
            # Описание отображается в подсказке,
            # message_text - то, что будет отправлено в виде сообщения
            description=item.desc,
            input_message_content=types.InputTextMessageContent(message_text=item.name)
        ) for item in suitable_items]))

