# coding:utf-8

class PagedResult:
    def __init__(self):
        self.records = 50,  # 总记录数
        self.rows = '',  # 页数据
        self.page = 1  # 页码
        self.pagesize = 5  # 页容量
        self.total = 10  # 页总数

    def set(self, page, pagesize, recodes, rows=None):
        self.page = page
        self.pagesize = pagesize
        self.records = recodes
        self.rows = rows
        self.total = (self.records + self.pagesize - 1) // self.pagesize  # 向上整除

    def to_dict(self):
        return {
            'records': self.records,
            'rows': self.rows,
            'page': self.page,
            'pagesize': self.pagesize,
            'total': self.total
        }


paged_result = PagedResult()


class ResCode(tuple):
    Success = '10000'
    Error = '10001'
    # 验证
    Token_Missing = '20001'
    Token_Timed_Out = '20002'
    Token_Invalid = '20003'
    Login_Timed_Out = '20004'
    # 授权
    Access_Denied = '30001'


res_code = {
    'success': '10000',
    'error': '10001'
}

res = {
    'msg': '',
    'data': '',
    'rescode': res_code['success'],
}


class JsonResult:
    def __call__(self, rescode=res_code['success'], data=None, msg=''):
        res['rescode'] = rescode
        res['data'] = data
        res['msg'] = msg
        return res
