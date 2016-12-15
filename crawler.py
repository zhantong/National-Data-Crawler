import urllib.request
import urllib.parse
import json
import re
import pprint

pp = pprint.PrettyPrinter(indent=4)


def parse_url(base_url, params):
    if params:
        return base_url + '?' + urllib.parse.urlencode(params)
    return base_url


def http_get(url):
    with urllib.request.urlopen(url) as f:
        return f.read().decode('utf-8')


class NationalData:
    def __init__(self):
        self.base_url = 'http://data.stats.gov.cn/easyquery.htm'

    def get_root_tree_params(self, data_type):
        content = http_get(parse_url(self.base_url, {'cn': data_type}))
        reg_results = re.findall(r"var\srootTree\s=\s'(.*?)';", content)
        if reg_results:
            return json.loads(reg_results[0])

    def get_tree(self, tree_param):
        data = {
            'id': tree_param['id'],
            'dbcode': tree_param['dbcode'],
            'wdcode': tree_param['wdcode'],
            'm': 'getTree'
        }
        request = urllib.request.Request(self.base_url, data=urllib.parse.urlencode(data).encode('utf-8'))
        with urllib.request.urlopen(request) as f:
            content = f.read().decode('utf-8')
            content = json.loads(content)
            # print(json.dumps(content,indent=4))
            return content

    def build_tree(self, root):
        if root['isParent']:
            root['children'] = self.get_tree(root)
            for item in root['children']:
                self.build_tree(item)
        return root


if __name__ == '__main__':
    national_data = NationalData()
    root_tree_params = national_data.get_root_tree_params('A01')
    for root_tree_param in root_tree_params:
        print('root tree param', root_tree_param)
        root_tree = national_data.build_tree(root_tree_param)
        pp.pprint(root_tree)
