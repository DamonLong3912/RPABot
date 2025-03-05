from .base import Base
import time
import re
import pandas as pd
import sys
import pdb
from .uiautomator_base import Base
import pdb
import random
import argparse
import logging
import os
import argparse
import retry
from lib.cli import cli

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Taobao(Base):

  package_name = "com.taobao.taobao"
  app_name = "淘宝"
  app_version = "10.10.0"

if __name__ == "__main__":
  bot = Taobao()
  cli(bot)
