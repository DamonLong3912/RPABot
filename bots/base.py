import argparse
import time
import sys
import os
import base64
import re, uuid
from argparse import ArgumentParser
from lib.timeit import timeit
import logging
import pydash
from lib.cli import cli
from functools import wraps
from enum import Enum
import traceback
from datetime import datetime

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TaskCompleted(Exception):
    pass

class TaskFailed(Exception):
    pass

class TaskTimeout(Exception):
    pass

class MaxTimesReached(Exception):
    pass

class TimeoutReached(Exception):
    pass

class TimeOutChecker:
    def __init__(self, timeout=10):
        log.info(f"init timeout checker, timeout={timeout}")
        if callable(timeout):
            timeout = timeout()
        self.timeout = timeout
        self.start_time = time.time()

    def check(self, raise_exception=False):
        elapsed = time.time() - self.start_time
        # log.info(f"check timeout, elapsed: {elapsed} / {self.timeout}")
        eta = int(self.timeout - elapsed)
        log.info(f"check timeout, eta: {eta} / {self.timeout}")
        if eta < 0:
            if raise_exception:
                raise TimeoutReached("timeout")
            return True
        return False

class Base():
    def __init__(self, device=None, *args, **kwargs):
        self.device = device
        self.args = args
        self.kwargs = kwargs

    def timeout_checker(self, timeout=10):
        return TimeOutChecker(timeout)


    def is_logged_in(self):
        return False

    def take_screenshot_as_text(self, trim=False):
        filename = self.take_screenshot()
        text = ocr_image_to_string(filename)
        if trim:
            text = re.sub(r"\s", "", text)
        return text

    def sleep(self, seconds, message=''):
        log.info(f"sleep {seconds} seconds")
        for i in range(seconds):
            eta = seconds - i
            log.info(f"eta: {eta} / {seconds} seconds {message}")
            time.sleep(1)

    def wait_until(
        self,
        func=lambda: False,
        timeout=360,
        interval=1,
        message='',
        raise_exception=False,
        on_success=None,
        on_fail=None,
        max_times=None
    ):
        d = self.d
        current = 1
        checker = self.timeout_checker(timeout)
        while True:
            if checker.check(raise_exception):
                return False
            if not func():
                if callable(on_fail):
                    log.info("call on_fail")
                    if not on_fail():
                        log.info("on_fail return false, exiting...")
                        return False
                if max_times and current >= max_times:
                    log.info("max times reached, exiting...")
                    if raise_exception:
                        raise Exception("max times reached")
                    return False
                if max_times:
                    log.info(f"func return false, wait until {current}/{max_times} {message}")
                if callable(interval):
                    interval = interval()
                    log.info(f"computed interval: {interval}")
                time.sleep(interval)
                current += 1
            else:
                log.info("wait success")
                if callable(on_success):
                    on_success()
                return True

    def run_times(self, func, times=100, before=None, after=None):
        for i in range(times):
            try:
                log.info(f"run {i}/{times} times")
                if callable(before):
                    log.info("call before")
                    if not before():
                        break
                func()
                if callable(after):
                    log.info("call after")
                    if not after():
                        break
            except Exception as e:
                log.error(f"error: {e}")
                break

    def run_until_timeout(self, func, interval=1, timeout=10, raise_exception=False):
        checker = self.timeout_checker(timeout)
        while True:
            if checker.check(raise_exception):
                break
            func()
            self.sleep(interval)

    def run_task(self, task, *args, **kwargs):
        self.before_run_task()
        task_method = getattr(self, "task_" + task)
        meta = getattr(task_method, "meta", None)
        if callable(task_method):
            if meta:
                log.info(f"run task {meta['name']}")
            task_method(*args, **kwargs)
        else:
            log.error(f"task {task} not found")
        self.after_run_task()

    def before_run_task(self):
        pass

    def after_run_task(self):
        pass

    def random_do(self, func, min=1, max=100):
        num = random.randint(min, max)
        return func(num)

    @classmethod
    def full_class_name(cls):
        return f"{cls.__module__}.{cls.__name__}"

    def cli(self):
        cli(self)