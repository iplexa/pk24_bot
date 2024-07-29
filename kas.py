import time
import json
import requests


headers = {
    'Host': 'kas.ranepa.ru',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Accept': 'application/json',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://kas.ranepa.ru/pk24/ru_RU/',
    'Content-Type': 'application/json; charset=utf-8',
    'vrs-session': '262c527e-492e-409b-989b-c425547ea3e0',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=4',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'TE': 'trailers'
}

cookies = {
    "_ym_d": "1719518049",
    "_ym_isad": "2",
    "_ym_uid": "1653260795268512349",
    "BITRIX_CONVERSION_CONTEXT_s1": "{\"ID\":9,\"EXPIRE\":1720904340,\"UNIQUE\":[\"conversion_visit_day\"]}",
    "BITRIX_SM_GUEST_ID": "2449407",
    "BITRIX_SM_LAST_ADV": "5",
    "BITRIX_SM_LAST_VISIT": "13.07.2024 13:45:37",
    "BITRIX_SM_SALE_UID": "28449994",
    "conftitle": "2024 / 2025 / ÐÑÐ¸ÐµÐ¼Ð½Ð°Ñ ÐºÐ¾Ð¼Ð¸ÑÑÐ¸Ñ. ",
    "PHPSESSID": "05ads10tuB2uQbpeQ2uYpWwPcRwFY2q7",
    "tmr_lvid": "69b0c8f0dbaf173f4f695c1a92c4bdc3",
    "tmr_lvidTS": "1698251360411"
}


response = requests.post(
    url='https://kas.ranepa.ru/pk24/ru_RU/e1cib/login?version=8.3.21.1622&sid=262c527e-492e-409b-989b-c425547ea3e0&nooida&vl=ru_RU&clnId=d268ebd8-d87a-445c-958f-6635bf08649c',
    data={"cred":"DyJwVJogSZ1I3mTxLDM2/Su3OEqX6op/3ZhB48Lwb7Dcu7ZesAMNFZH6MAUSrkgMSTjN8p1wTupGqLRzMwia6eX9tOT8s6jcmOyaKQzjUtjd6vkOFIf2EZXbOdw5rVK6+0CrMr0UOJ9sSITMa5Yh/A=="},
    headers=headers
)
response.encoding = 'utf-8-sig'

time.sleep(1)

response2 = requests.get(
    url='https://kas.ranepa.ru/pk24/ru_RU/e1cib/about',
    cookies=response.cookies,
    headers=headers
)
response2.encoding = 'utf-8-sig'

time.sleep(1)

# response3 = requests.post(
#     url='https://kas.ranepa.ru/pk24/ru_RU/e1cib/dlist?cmd=query',
#     data=json.dumps({
#         "root": {
#             "remoteKey": "FE492F50-F4E0-44D8-B638-73A2B6103F52",
#             "dataPath": {
#             "id": [
#                 "4"
#             ]
#             },
#             "tableId": 13,
#             "list": {
#                 "ChangeState": 0,
#                 "SettingsComposer": {},
#                 "ChangesVersion": 128
#             },
#             "choiceMode": False,
#             "formUUID": "fe492f50-f4e0-44d8-b638-73a2b6103f52",
#             "forward": False,
#             "autopos": False,
#             "page": 22,
#             "source": 0,
#             "showTree": False,
#             "#filter": [],
#             "filter": [],
#             "autoParent": True,
#             "level": -1,
#             "autoLevel": True,
#             "period": {
#                 "startDate": "0001-01-01T00:00:00",
#                 "endDate": "0001-01-01T00:00:00",
#                 "#variant": "64918FA8-6F26-4DC3-90E6-B6D3F5B0087F",
#                 "variant": "Custom"
#             },
#             "presents": True,
#             "ftext": "СПО001932",
#             "allowAsync": True,
#             "backgroundSearchInfo": "e1cib/tempstorage/92aadcdf-f7dd-47d4-bdf5-950037a3cbf2?seanceId=N2EyNDk1NjgtYWVlMi00YjU1LThkYTEtYTM1NDYwZWI0NDY1K2IMvhpebkWS3ff_dpkgQgAAAAA",
#             "waitTime": 200,
#             "needDataDescr": True
#         }
#     }, ensure_ascii=False),
#     headers=headers,
# )
# response3.encoding = 'utf-8-sig'

# time.sleep(1)

# response4 = requests.post(
#     url='https://kas.ranepa.ru/pk24/ru_RU/e1cib/logForm?cmd=query',
#     data=json.dumps(
#         {
#             "root": {
#                 "key": "Документ.ПроверкаЗаявленийПоВидамПК.Форма.ФормаОбработки",
#                 "prms": {
#                 "prm": [
#                     {
#                     "name": "Ссылка",
#                     "#val": "429FF5A0-8CB5-4353-90BF-FDCE3BD69D38",
#                     "val": "a86536e1-37c4-11ef-aa03-00620b9300d1"
#                     }
#                 ]
#                 },
#                 "mw": 0,
#                 "mh": 0,
#                 "cw": 0,
#                 "ch": 0,
#                 "pres": False,
#                 "trdata": False,
#                 "cf": False
#             }
#         },
#         ensure_ascii=False
#     ),
#     headers=headers
# )
# response4.encoding = 'utf-8-sig'

response4 = requests.post(
    url='https://kas.ranepa.ru/pk24/ru_RU/e1cib/misc/trdata',
    cookies=cookies,
    headers=headers,
    data=json.dumps({
        "root": {
            "item": [
                {
                    "path": "0:94121666-05E2-43CB-B7C4-96F0ABA42AA4",
                    "type": "D79E5036-6B75-4B37-8E26-0EC44092F0CC",
                    "ref": "bda86c7a-3dff-11ef-aa03-00620b9300d1"
                },
                {
                    "path": "0:98942DE3-CC43-4859-8DA8-904EB8DEAE3E",
                    "type": "D79E5036-6B75-4B37-8E26-0EC44092F0CC",
                    "ref": "bda86c7a-3dff-11ef-aa03-00620b9300d1"
                },
                {
                    "path": "0:F2CFC71A-5A13-4E88-8B12-337B8E7AACA9",
                    "type": "D79E5036-6B75-4B37-8E26-0EC44092F0CC",
                    "ref": "bda86c7a-3dff-11ef-aa03-00620b9300d1"
                },
            ]
        }
    }, ensure_ascii=False)
)
response4.encoding = 'utf-8-sig'

with open('response.json', 'w', encoding='utf-8-sig') as response_file:
    # response_file.write(response4.text)
    json.dump(response4.json(), response_file, ensure_ascii=False, indent=4)