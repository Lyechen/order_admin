# coding:utf-8
import os

'''
@summary: 用户自定义全局常量设置
'''

# ===============================================================================
# 静态资源
# ===============================================================================
# 静态资源文件(js,css等）在APP上线更新后, 由于浏览器有缓存, 可能会造成没更新的情况.
# 所以在引用静态资源的地方，都把这个加上，如：<script src="/a.js?v=${STATIC_VERSION}"></script>；
# 如果静态资源修改了以后，上线前改这个版本号即可
STATIC_VERSION = 1.0

# ===============================================================================
# SSO 配置
# ===============================================================================
SSO_HOST = os.environ.get('SSO_HOST', 'http://127.0.0.1:8011')
SSO_VERIFY = SSO_HOST + '/server/verify'
SSO_EXPIRE_TIME = 24 * 60 * 60

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'omD4PtIjczXouDCqaiHgh2yhSQMcUwdPZyPXUClJ5ig2H2blaWyW4X0GoMeKxSPf')

# ===============================================================================
# debug toolbar 配置
# ===============================================================================
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {
    'JQUERY_URL': "http://code.jquery.com/jquery-2.1.1.min.js"
}

# ID生成器主机地址
ORDER_API_HOST = 'http://127.0.0.1:8000'

# 商品信息查询主机
GOODS_API_HOST = 'http://139.199.96.235:9007'
# 供应商查询主机
SUPPLIER_API_HOST = 'http://139.199.96.235:9006'

# CDN域名前缀
CDN_HOST = 'http://imgcdn.robo2025.com'

# ===============================================================================
# session、cookie配置
# ===============================================================================
# SESSION_ENGINE = 'redis_sessions.session'
# SESSION_REDIS = {
#     'host': os.environ.get('SESSION_REDIS_HOST','localhost'),
#     'port': os.environ.get('SESSION_REDIS_PORT',6379),
#     'db': os.environ.get('SESSION_REDIS_DB',0),
#     'password': os.environ.get('SESSION_REDIS_PWD',''),
#     'prefix': 'session',
#     'socket_timeout': 1
# }
# SESSION_COOKIE_NAME=''
# SESSION_COOKIE_AGE

# 内网ip列表
INTERNAL_IPS = ['127.0.0.1']

# ==============================================================================
# 中间件和应用
# ==============================================================================
# 自定义中间件
MIDDLEWARE_CLASSES_CUSTOM = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware'
]

# 自定义APP
INSTALLED_APPS_CUSTOM = [
    # add your app here...
    # Note: 请注意在第一次syncdb时不加自己的app
    # 'debug_toolbar',
    # 'crispy_forms',
    # 'reversion',
    # 'xadmin',
    'orders',
    # 'django_filters',
]

# ===============================================================================
# 日志级别
# ===============================================================================
# 本地开发环境日志级别
LOG_LEVEL_DEVELOP = 'DEBUG'
# 测试环境日志级别
LOG_LEVEL_TEST = os.environ.get('LOG_LEVEL_TEST', 'INFO')
# 正式环境日志级别
LOG_LEVEL_PRODUCT = os.environ.get('LOG_LEVEL_PRODUCT', 'ERROR')
