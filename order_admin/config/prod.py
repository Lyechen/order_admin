# coding:utf-8
'''
@summary: 全局常量设置
'''

import os

DB_HOST = os.environ.get('DB_HOST', '')
DB_PORT = os.environ.get('DB_PORT', '')
DB_NAME = os.environ.get('DB_NAME', '')
DB_USER = os.environ.get('DB_USER', '')
DB_PWD = os.environ.get('DB_PWD', '')

# APP的url前缀, 不要修改. 如 "/your_app_code/", 在页面中使用
SITE_URL = os.environ.get("SITE_URL", "/")

# logging目录
# LOGGING_DIR_ENV = os.environ.get('LOGGING_DIR', '/project/requisite/logs/')

# 测试环境配置
# if RUN_MODE == 'TEST':
#     # 静态资源目录url
#     REMOTE_STATIC_URL = os.environ.get("REMOTE_STATIC_URL", '/home/apps/static/')
# # 正式环境配置
# elif RUN_MODE == 'PRODUCT':
#     # 静态资源目录url
#     REMOTE_STATIC_URL = os.environ.get("REMOTE_STATIC_URL", '/home/apps/static/')

# ===============================================================================
# 数据库设置
# ===============================================================================
# 测试环境数据库设置
DATABASES_TEST = {
    'default':
        {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': DB_NAME,
            'PASSWORD': DB_PWD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
}

# 正式环境数据库设置
DATABASES_PRODUCT = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PWD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}
