import urllib.request
import urllib.parse
import json
import re
import pprint
import sqlite3

sqlite3.register_adapter(bool,int)
sqlite3.register_converter("BOOL",lambda v:bool(int(v)))

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
        self.wds=None
        self.trees=[]
    def init(self,data_type):
        root_tree_params = national_data.get_root_tree_params(data_type)
        draw_chart_param = national_data.get_draw_chart_param(data_type)
        draw_chart_param['dbcode'] = root_tree_params[0]['dbcode']
        draw_chart_param['rowcode'] = root_tree_params[0]['wdcode']
        self.wds=national_data.get_wds(draw_chart_param)['returndata']
        self.write_wds_to_db(self.wds)
        #pp.pprint(self.wds)
        for root_tree_param in root_tree_params:
            #print('root tree param', root_tree_param)
            root_tree = national_data.build_tree(root_tree_param)
            self.trees.append(root_tree)
            #pp.pprint(root_tree)
            self.write_tree_to_db(root_tree)
    def get_root_tree_params(self, data_type):
        content = http_get(parse_url(self.base_url, {'cn': data_type}))
        reg_results = re.findall(r"var\srootTree\s=\s'(.*?)';", content)
        if reg_results:
            return json.loads(reg_results[0])
    def get_draw_chart_param(self,data_type):
        content = http_get(parse_url(self.base_url, {'cn': data_type}))
        db_code=re.findall(r'drawChart\.DbCode\("(.*?)"\)',content)
        if db_code:
            db_code=db_code[0]
        row_code = re.findall(r'drawChart\.RowCode\("(.*?)"\)', content)
        if row_code:
            row_code = row_code[0]
        col_code = re.findall(r'drawChart\.ColCode\("(.*?)"\)', content)
        if col_code:
            col_code = col_code[0]
        return {
            'dbcode':db_code,
            'rowcode':row_code,
            'colcode':col_code
        }
    def get_tree(self, tree_param):
        data = {
            'id': tree_param['id'],
            'dbcode': tree_param['dbcode'],
            'wdcode': tree_param['wdcode'],
            'm': 'getTree'
        }
        content = http_get(parse_url(self.base_url,data))
        content = json.loads(content)
        # print(json.dumps(content,indent=4))
        return content

    def build_tree(self, root):
        if root['isParent']:
            root['children'] = self.get_tree(root)
            for item in root['children']:
                self.build_tree(item)
        return root
    def get_wds(self,draw_chart_param):
        data={
            'm':'getOtherWds',
            'dbcode':draw_chart_param['dbcode'],
            'rowcode':draw_chart_param['rowcode'],
            'colcode':draw_chart_param['colcode'],
            'wds':json.dumps([])
        }
        content = http_get(parse_url(self.base_url,data))
        content = json.loads(content)
        return content
    def init_db(self):
        conn=sqlite3.connect('data.db')
        c=conn.cursor()
        c.execute('DROP TABLE IF EXISTS tree')
        c.execute('CREATE TABLE tree (dbcode text,id text,name text,pid text,wdcode text,isparent BOOL,PRIMARY KEY (id))')
        c.execute('DROP TABLE IF EXISTS wds')
        c.execute('CREATE TABLE wds (code text,name text,sort text,issj BOOL,wdcode text,wdname text,PRIMARY KEY (code))')
        conn.commit()
        conn.close()
    def write_tree_to_db(self,tree):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        self.write_tree_to_db_recur(tree,c)
        conn.commit()
        conn.close()
    def write_tree_to_db_recur(self, tree,cursor):
        cursor.execute("INSERT INTO tree (dbcode,id,name,pid,wdcode,isparent) VALUES (?,?,?,?,?,?)",(tree['dbcode'],tree['id'],tree['name'],tree['pid'],tree['wdcode'],tree['isParent']))
        if tree['isParent']:
            for child in tree['children']:
                self.write_tree_to_db_recur(child,cursor)
    def write_wds_to_db(self,wds):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        for wd in wds:
            for node in wd['nodes']:
                c.execute("INSERT INTO wds (code,name,sort,issj,wdcode,wdname) VALUES (?,?,?,?,?,?)",(node['code'],node['name'],node['sort'],wd['issj'],wd['wdcode'],wd['wdname']))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    national_data = NationalData()
    national_data.init_db()
    national_data.init('E0103')

