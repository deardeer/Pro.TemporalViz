#!/usr/bin/env python
#coding:utf-8

import sys

from handler.dbhandler import getODataHandler

url=[
    (r'/getOData', getODataHandler),
  
]