#!/usr/bin/env python
#coding:utf-8

import sys

from handler.dbhandler import getODataHandler
from handler.dbhandler import getPlotHandler

url=[
    (r'/getOData', getODataHandler),
    (r'/getPlotData', getPlotHandler),
  
]