import urllib.request
import urllib.parse
import http.cookiejar
import json
import csv

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'
}

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

base_url = 'http://data.stats.gov.cn/easyquery.htm'

provinces = []


def init(family_code):
    params = {
        'm': 'getOtherWds',
        'dbcode': 'fsnd',
        'rowcode': 'zb',
        'colcode': 'sj',
        'wds': json.dumps([{
            'wdcode': 'zb',
            'valuecode': family_code
        }])
    }
    data = get(params)
    for node in data['returndata'][0]['nodes']:
        provinces.append({
            'code': node['code'],
            'name': node['name']
        })


def get_data(category_code, province_code):
    params = {
        'm': 'QueryData',
        'dbcode': 'fsnd',
        'rowcode': 'zb',
        'colcode': 'sj',
        'wds': json.dumps([{
            'wdcode': 'reg',
            'valuecode': province_code
        }]),
        'dfwds': json.dumps([{
            'wdcode': 'zb',
            'valuecode': category_code
        }, {
            'wdcode': 'sj',
            'valuecode': 'LAST20'
        }])
    }
    data = get(params)
    name = data['returndata']['wdnodes'][0]['nodes'][0]['name']
    unit = data['returndata']['wdnodes'][0]['nodes'][0]['unit']
    province = data['returndata']['wdnodes'][1]['nodes'][0]['name']
    out = []
    for node in data['returndata']['datanodes']:
        out.append({
            'data': node['data']['data'],
            'year': node['wds'][2]['valuecode'],
            'province': province,
            'unit': unit
        })
    with open(name + '_' + province + '.csv', 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, out[0].keys())
        writer.writeheader()
        writer.writerows(out)
    return out


def get(params):
    url = base_url + '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers=headers)
    with opener.open(url) as f:
        content = f.read().decode('utf-8')
    content = json.loads(content)
    return content

if __name__ == '__main__':
    init('A0604')
    for province in provinces:
        data = get_data('A060402', province['code'])