from .base import Base as BaseBot
import uiautomator2 as u2
import hashlib
import time
import base64
from lib.ocr import OCR
from lib.rapidocr import Ocr as RapidOcr
import pdb
import os
import logging
import random
import json
import threading
import traceback
import re
import pydash

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class TakeScreenshotContext:
    def __init__(self, bot):
        self.bot = bot

    def __enter__(self):
        self.screenshot_file = self.bot.take_screenshot()
        self.bot.screenshot_context = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(self.screenshot_file)
        self.bot.screenshot_context = None



class Base(BaseBot):
    d = None
    activity = None
    app_name = None
    app_version = None
    package_name = None
    screenshot_context = None

    def is_app_installed(self):
        return self.package_name in self.d.app_list()

    def get_app_version(self):
        info = self.d.app_info(self.package_name)
        return info['versionName']

    def uninstall_app(self):
        serial = self.adb_address
        cmd = f"adb -s {serial} uninstall {self.package_name}"
        log.info(f"cmd {cmd}")
        result = os.system(cmd)
        log.info(f"uninstall app result: {result}")
        return True

    def install_apk(self):
        serial = self.adb_address
        local_file = f"apk/{self.__class__.__name__}.apk"
        if os.path.exists(local_file):
            cmd = f"adb -s {serial} install -d -r {local_file}"
            log.info(f"cmd {cmd}")
            result = os.system(cmd)
            if result == 0:
                return True
            else:
                log.error(f"install apk failed, result: {result}")
                return False
        else:
            log.error(f"apk file {local_file} not found")
            return False

    def clear_data(self):
        cmd = f"pm clear {self.package_name}"
        log.info(f"clear data {cmd}")
        result = self.d.shell(cmd)
        log.info(f"clear data result: {result}")
        return result


    def current_activity(self):
        app_current = self.d.app_current()
        return app_current.get('activity')

    def export_apk(self):
        """
        (backend) ➜  backend git:(dev) adb shell pm path com.ss.android.ugc.aweme.lite
        package:/data/app/~~skSSa11DT7Hv_k2LYsaCJg==/com.ss.android.ugc.aweme.lite-Sk8AxWy41_IphYOj7hJlrw==/base.apk
        """
        local_file = f"apk/{self.__class__.__name__}.apk"
        local_dir = os.path.dirname(local_file)
        path = self.apk_path()
        if path:
            # 创建目录
            os.makedirs(local_dir, exist_ok=True)
            self.d.pull(path, local_file)
            log.info(f"export apk {path} -> {local_file}")
            return local_file
        else:
            return None

    def apk_path(self):
        cmd = f"pm path {self.package_name}"
        result = self.d.shell(cmd)
        output = result.output
        if output:
            path = output.split(":")[1].strip()
            return path
        else:
            return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.info(f"init uiautomator base {args} {kwargs}")
        adb_address = kwargs.get("adb_address", pydash.get(args,'0') or os.environ.get("ADB_ADDRESS"))
        self.adb_address = adb_address
        self.d = u2.connect(adb_address)
        if adb_address is None:
            device_info = self.d.device_info
            self.adb_address = device_info['serial']


    def login(self):
        pass


    def logout(self):
        pass

    def switch_account(self):
        pass

    def start_watch_daemon(self):
        run_interval = 1
        log.info(f"start watch daemon, interval={run_interval}")
        run_times = 0
        while True:
            run_times += 1
            log.debug(f"run watch, times={run_times}")
            self.watch()
            time.sleep(run_interval)

    def start_watch(self):
        self.watch_thread = threading.Thread(target=self.start_watch_daemon)
        self.watch_thread.start()

    def stop_watch(self):
        try:
            self.watch_thread = None
        except Exception as e:
            log.error(f"error: {e}")

    def __del__(self):
        self.stop_watch()

    def screen_on(self):
        log.info("turn screen on")
        self.d.screen_on()


    def watch(self):
        d = self.d
        if d(text="传输文件").exists(timeout=0):
            d(text="取消").click_exists(timeout=0)
        if d(text="USB文件传输提示").exists(timeout=0):
            d(text="我知道了").click_exists(timeout=0)

    def screen_unlock(self):
        log.info("unlock screen")
        self.screen_on()
        q = self.d(text='上滑解锁')
        if q.exists(timeout=1):
            self.d.swipe_ext('up', scale=1)

    def click(self, *args, **kwargs):
        return self.click_screen_text(*args, **kwargs)

    def exists(self, *args, **kwargs):
        return self.screen_text_exists(*args, **kwargs)

    def text(self, *args, **kwargs):
        return self.get_screen_text(*args, **kwargs)

    def rect(self, *args, **kwargs):
        return self.ocr_find(*args, **kwargs)

    def find_task(self, textContains = None, text = None, textMatches = None, message = None, click=False):
        method_name = 'click' if click else 'exists'
        method = getattr(self, method_name)
        if message is None:
            message = f"find task {textContains} {text} {textMatches}"
        return self.scroll_up_until(
            lambda: method(text=text, textMatches=textMatches, textContains=textContains),
            message=message,
            max_times=20
        )

    def click_screen_text_by_ocr(
        self,
        textContains = None,
        index=0,
        delay=None,
        text=None,
        textMatches=None,
        offset=None,
        position='center'
    ):
        log.info(f"click screen text by ocr, textContains={textContains}, index={index}, text={text}, textMatches={textMatches}")
        ocr_info = self.rapid_ocr.info(text=text, textMatches=textMatches, textContains=textContains)
        log.info(f'ocr_info {ocr_info}')
        if ocr_info:
            rect = ocr_info['rect']

            if offset is True:
                # 计算出一个随机的偏移量， 但是都是限制在rect的范围内
                offset = (random.randint(0, int(ocr_info['width'])), random.randint(0, int(ocr_info['height'])))
                log.info(f"computed offset: {offset}")

            x, y = ocr_info['x'], ocr_info['y']
            width, height = ocr_info['width'], ocr_info['height']
            if delay:
                if callable(delay):
                    delay = delay()
                self.sleep(delay, '延迟点击')
            if offset:
                new_x, new_y = (x + offset[0], y + offset[1])
                x = new_x
                y = new_y
            elif position == 'top_left':
                x = x - width / 3
                y = y - height / 3
            elif position == 'top_right':
                x = x + width / 3
                y = y - height / 3
            elif position == 'bottom_left':
                x = x - width / 3
                y = y + height / 3
            elif position == 'bottom_right':
                x = x + width / 3
                y = y + height / 3
            elif position == 'top_center' or position == 'top':
                x = x
                y = y - height / 3
            elif position == 'bottom_center' or position == 'bottom':
                x = x
                y = y + height / 3
            elif position == 'left_center' or position == 'left':
                x = x - width / 3
                y = y
            elif position == 'right_center' or position == 'right':
                x = x + width / 3
                y = y

            log.info(f"click {x} {y}")
            self.d.click(x, y)
            return True
        else:
            log.info(f"text {textContains} not found")
            return False


    def screen_text_exists(self, textContains = None, text=None, textMatches=None):
        log.info(f"screen_text_exists text={text}, textMatches={textMatches}, textContains={textContains}")
        kwargs = {}
        if textContains is not None:
            kwargs['textContains'] = textContains
        if text is not None:
            kwargs['text'] = text
        if textMatches is not None:
            kwargs['textMatches'] = textMatches
        log.info("check text exists by uiautomator")
        if self.d(**kwargs).exists(timeout=1):
            log.debug('Exists.')
            return True
        else:
            log.debug('Not exists.')
        log.info(f"check text exists by ocr text={text}, textMatches={textMatches}, textContains={textContains}")
        if self.rapid_ocr.text_position(text=text, textMatches=textMatches, textContains=textContains):
            log.debug('Exists.')
            return True
        else:
            log.debug('Not exists.')
        return False

    def ocr_find(self, text=None, textMatches=None, textContains=None):
        return self.rapid_ocr.text_rect_and_text(text=text, textMatches=textMatches, textContains=textContains)

    def ele_fingerprint(self, ele):
        image = ele.screenshot()
        # md5
        return hashlib.md5(image.tobytes()).hexdigest()

    # 获取屏幕上匹配的元素
    # 比如 find_match(r"金币(\d+)")会返回一个列表，列表中每个元素是一个元组，元组中第一个元素是元素的文本，第二个元素是元素的坐标
    def find_match(self, regexp, convert=None):
        result = self.ocr_find(textMatches=regexp)
        if result:
            log.info(f"ocr find result: {result}")
            rect, text = result
            match = re.match(regexp, text)
            if match:
                result = match.groups()[0]
                if convert:
                    result = convert(result)
                return result
        return None

    def click_screen_text_by_uiautomator(
        self,
        textContains = None,
        index=0,
        delay=None,
        text=None,
        textMatches=None,
        position='center',
        offset=None
    ):
        if offset is True:
            offset = (random.randint(3, 7) / 10, random.randint(3, 7) / 10)
        log.info(f"click screen text by uiautomator, textContains={textContains}, index={index}, text={text}, textMatches={textMatches}, offset={offset}")

        kwargs = {}
        if textContains is not None:
            kwargs['textContains'] = textContains
        if text is not None:
            kwargs['text'] = text
        if textMatches is not None:
            kwargs['textMatches'] = textMatches

        ele = self.d(**kwargs)
        if ele.exists(timeout=1):
            if delay:
                if callable(delay):
                    delay = delay()
                self.sleep(delay, '延迟点击')
            try:
                ele.click(timeout=0, offset=offset)
                return True
            except Exception as e:
                log.error(f"click error: {e}")
                return False
        else:
            log.info(f"textContains {textContains}, text={text}, textMatches={textMatches} not found")
            return False

    def get_screen_text(self, text=None, textMatches=None, textContains=None):
        return self.rapid_ocr.text(text=text, textMatches=textMatches, textContains=textContains)

    def click_screen_text(
        self,
        textContains = None,
        index=0,
        by="both",
        after=None,
        delay=None,
        text=None,
        textMatches=None,
        offset=None,
        position='center',
    ):
        if by == "ocr":
            return self.click_screen_text_by_ocr(index=index, delay=delay, text=text, textMatches=textMatches, textContains=textContains, offset=offset, position=position)
        elif by == "uiautomator":
            return self.click_screen_text_by_uiautomator(index=index, delay=delay, text=text, textMatches=textMatches, textContains=textContains, position=position)
        elif by == "both":
            result = self.click_screen_text_by_uiautomator(index=index, delay=delay, text=text, textMatches=textMatches, textContains=textContains, position=position) or self.click_screen_text_by_ocr(index=index, delay=delay, text=text, textMatches=textMatches, textContains=textContains, offset=offset, position=position)
            if callable(after):
                after()
            return result
        else:
            raise Exception(f"invalid click screen text method: {by}")

    def screen_contains_text(self, textContains = None, text=None, textMatches=None):
        rect = self.rapid_ocr.text_position(text=text, textMatches=textMatches, textContains=textContains)
        return rect is not None

    def scroll_until(
        self,
        func=lambda: False,
        interval=1,
        max_times=None,
        direction="up",
        message='',
        timeout=None,
        after=None,
        before=None,
        checker = None,
        scale=1,
    ):

        if max_times is None and timeout is not None:
            log.warning('--------------------------------')
            log.warning(f"max_times is None, timeout is not None, this will cause infinite loop if func always return False")
            log.warning('--------------------------------')

        if timeout is not None:
            checker = self.timeout_checker(timeout)
        d = self.d
        current = 1
        while True:
            try:
                if callable(interval):
                    computed_interval = interval()
                    log.info(f"computed interval: {computed_interval}")
                else:
                    computed_interval = interval
                if checker is not None:
                    if checker.check():
                        log.info("checker check true, exiting...")
                        return False
                if callable(before):
                    log.info("call before")
                    try:
                        if not before():
                            log.info("before return false, continue...")
                            self.sleep(computed_interval)
                            continue
                        else:
                            log.info("before return true")
                    except Exception as e:
                        log.error(f"error: {e}")
                        log.info("before raise exception, exiting...")
                        return False
                result = func()
                if result:
                    return True
            except Exception as e:
                # 打印错误堆栈
                traceback.print_exc()
                log.error(f"error: {e}")
                result = False
            if not result:
                if max_times is not None:
                    log.info(f"({current}/{max_times}): scroll {direction} {message}")
                d.swipe_ext(direction, scale=scale)
                if callable(after):
                    log.info("call after")
                    try:
                        if not after():
                            log.info("after return false, continue...")
                            continue
                    except Exception as e:
                        log.error(f"error: {e}")
                        log.info("after raise exception, exiting...")
                        return False
                self.sleep(computed_interval)
                current += 1
                if max_times is not None:
                    if current > max_times:
                        log.info(f"reach max times {max_times}, {message} exiting...")
                        return False
            else:
                log.info("func success")
                return True

    def scroll_up_until(self, *args, **kwargs):
        d = self.d
        return self.scroll_until(*args, direction="up", **kwargs)

    def scroll_down_until(self, *args, **kwargs):
        return self.scroll_until(*args, direction="down", **kwargs)

    def scroll_left_until(self, *args, **kwargs):
        kwargs['direction'] = "left"
        if 'scale' not in kwargs:
            kwargs['scale'] = 0.5
        return self.scroll_until(*args,  **kwargs)

    def scroll_right_until(self, *args, **kwargs):
        kwargs['direction'] = "right"
        if 'scale' not in kwargs:
            kwargs['scale'] = 0.5
        return self.scroll_until(*args,  **kwargs)

    @property
    def ocr(self):
        image_path = self.take_screenshot()
        ocr = OCR(image_path)
        return ocr

    @property
    def rapid_ocr(self):
        image = self.take_screenshot_as_image()
        ocr = RapidOcr(image)
        return ocr

    def print_ocr_info(self):
        ocr = self.rapid_ocr
        result, elapse = ocr.result()
        log.info(f"ocr result: {result}, elapse: {elapse}")
        for el in result:
            rect, text, score = el
            # log.info(f"{text}, {score}, {rect}")
            log.info({
                'text': text,
                'score': score,
                'rect': rect
            })

    def before_app_start(self):
        pass

    def after_app_start(self):
        pass

    def is_app_running(self):
        current_package_name = self.d.info.get('currentPackageName')
        return current_package_name == self.package_name

    def search_text(self, regexp):
        ele = self.d(textMatches=regexp)
        try:
            text = ele.get_text(timeout=0)
            match = re.search(regexp, text)
            return match
        except Exception as e:
            log.error(f"error: {e}")
            return False

    def app_start(self, package_name = None, activity=None, hard=True, wait=0):
        self.screen_unlock()
        if package_name is None:
            package_name = self.package_name
        if activity is None:
            activity = self.activity
        log.info(f"start app {package_name} {activity}")
        self.before_app_start()
        if hard:
            self.app_stop()
            self.sleep(1, "等待 app 停止")
            self.d.app_start(package_name, activity)
            if wait:
                self.sleep(wait, "等待 app 启动")
        else:
            if self.is_app_running():
                log.info("app is running, skip start")
            else:
                self.d.app_start(package_name, activity)
                if wait:
                    self.sleep(wait, "等待 app 启动")
        self.after_app_start()

    def take_screenshot(self, context=False):
        if context:
            return TakeScreenshotContext(self)
        file = f"screenshots/{time.strftime('%Y-%m-%d_%H-%M-%S')}.png"
        self.d.screenshot(file)
        log.info(f"screenshot saved to {file}")
        return file

    def take_screenshot_as_base64(self):
        d = self.d
        image = d.screenshot(format="raw")
        data = base64.b64encode(image).decode("utf-8")
        data = "data:image/png;base64," + data
        log.info(f"screenshot as base64, {len(data)} bytes")
        return data

    def take_screenshot_as_image(self):
        image = self.d.screenshot()
        return image

    def app_stop(self):
        log.info(f"stop app {self.package_name}")
        d = self.d
        d.app_stop(self.package_name)

    def app_clear(self):
        d = self.d
        log.info(f"clear app {self.appid}")
        d.app_clear(self.appid)

    def reset(self, clear=False):
        log.info(f"reset app {self.appid}")
        self.app_stop()
        if clear:
            self.app_clear()
        self.app_start()

    def back_home(self, text="首页", after=None, before=None, func=None):
        log.info(f"back to home, text={text}")
        if func is None:
            func = lambda: self.d(text=text).exists(timeout=1)
        self.back_until(
            func,
            after=after,
            before=before
        )

    def back_until(self, func, interval=1, max_times=10, before=None, after=None):
        d = self.d
        current = 1
        while True:
            if not func():
                if callable(before):
                    log.info("call before")
                    before()
                log.info("press back")
                d.press("back")
                if callable(after):
                    log.info("call after")
                    after()
                self.sleep(interval)
                current += 1
                if current > max_times:
                    log.info("reach max times")
                    break
            else:
                break

    def random_swipe(self, direction="up", scale=1, min=1, max=20):
        log.info(f"random swipe {direction} {scale} {min} {max}")
        d = self.d
        sleep_time = random.randint(min, max)
        log.info(f"sleep {sleep_time} seconds before swipe")
        self.sleep(sleep_time)
        d.swipe_ext(direction, scale=scale)

    def scroll_times(self, times=10, direction="up", min=10, max=40, message=''):
        log.info(f"scroll {times} times {direction} {min} {max} {message}")
        d = self.d
        for i in range(times):
            self.random_swipe(direction=direction, min=min, max=max, message=message)


    def update_android_id(self, android_id):
        self.android_id = android_id
        cmd = f"settings put secure android_id {android_id}"
        return self.d.shell(cmd)

    def get_android_id(self):
        cmd = "settings get secure android_id"
        return self.d.shell(cmd)

if __name__ == "__main__":
    bot = Base()
    file = bot.take_screenshot()
    log.info(file)
