import gspread
from oauth2client.service_account import ServiceAccountCredentials
from main import Shop, Item

def get_shops():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('VeganPartnersSheetKey.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("тест таблица").sheet1

    full_list = sheet.get_all_values()
    shop_dict = {}
    i = 0
    current_shop = None
    while i < len(full_list):
        row = full_list[i]
        if row[0] == '':
            shop_dict[current_shop].item_dict[row[2]] = Item(row[2], row[3], int(row[4]), str(i))
        else:
            shop_dict[row[0]] = Shop(row[0], {row[2]: Item(row[2], row[3], int(row[4]), str(i))}, int(row[1])/100)
            current_shop = row[0]
        i += 1
    return shop_dict