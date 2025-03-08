from typing import Dict, Any, List, Optional
from .base_action import BaseAction
import subprocess
import time

class OCRBaseAction(BaseAction):
    """OCR动作基类"""

    def _click_ocr_result(self, result: Dict[str, Any], screenshot_region: List[int] = None,
                         click_offset: List[int] = None) -> bool:
        """点击OCR识别结果

        Args:
            result: OCR识别结果
            screenshot_region: 截图区域[x1,y1,x2,y2]
            click_offset: 点击偏移量[x_offset, y_offset]

        Returns:
            bool: 点击是否成功
        """
        try:
            box = result['box']
            scale = self.bot.screenshot_helper.get_scale_factor()

            # 计算中心点坐标
            center_x = int((box[0][0] + box[2][0]) / (2 * scale))
            center_y = int((box[0][1] + box[2][1]) / (2 * scale))

            # 添加区域偏移
            if screenshot_region:
                center_x += screenshot_region[0]
                center_y += screenshot_region[1]

            # 添加点击偏移
            if click_offset:
                center_x += click_offset[0]
                center_y += click_offset[1]

            # 使用UIAnimator2执行点击
            self.ui_animator.click(center_x, center_y)

            self.logger.debug(f"点击OCR结果: {result}")
            self.logger.info(f"点击坐标: ({center_x}, {center_y})")
            return True

        except Exception as e:
            self.logger.error(f"点击OCR结果失败: {str(e)}")
            return False

class WaitAndClickOCRTextAction(OCRBaseAction):
    """等待并点击指定文本"""

    def execute(self, params: Dict[str, Any]) -> bool:
        text = params.get('text')
        timeout = params.get('timeout', 30)
        check_interval = params.get('check_interval', 2)
        screenshot_region = params.get('screenshot_region')
        click_offset = params.get('click_offset')
        textContains = params.get('textContains')
        textMatches = params.get('textMatches')

        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                screenshot = self.bot.screenshot_helper.take_screenshot(
                    save_path="temp",
                    filename_prefix="wait_click_text",
                    region=screenshot_region
                )

                # results = self.bot.ocr_helper.extract_text(
                #    screenshot,
                #    keywords=[text]
                # )

                results = self.bot.ocr_helper.find(
                    screenshot,
                    text=text,
                    textContains=textContains,
                    textMatches=textMatches
                )

                if results:
                    self.logger.info(f"找到目标文本: text: {text} , textContains: {textContains} , textMatches: {textMatches} , {results}, screenshot_region: {screenshot_region}, click_offset: {click_offset}")
                    if self._click_ocr_result(results[0], screenshot_region, click_offset):
                        return True

                time.sleep(check_interval)

            self.logger.warning(f"等待超时: {text}")
            return False

        except Exception as e:
            self.logger.error(f"等待点击文本失败: {str(e)}")
            return False

class HandlePopupsUntilTargetAction(OCRBaseAction):
    """处理弹窗直到目标出现"""

    def execute(self, params: Dict[str, Any]) -> bool:
        timeout = params.get('timeout', 60)
        check_interval = params.get('check_interval', 0.5)
        target_text = params['target_text']
        screenshot_region = params.get('screenshot_region')
        popups = params.get('popups', [])

        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                screenshot = self.bot.screenshot_helper.take_screenshot(
                    save_path="temp",
                    filename_prefix="handle_popups",
                    region=screenshot_region
                )

                for popup in popups:
                    patterns = popup['patterns']
                    action = popup.get('action', 'click_first')

                    results = self.bot.ocr_helper.extract_text(screenshot)

                    # 使用包含匹配检查所有 patterns 是否存在
                    pattern_matches = {}
                    for pattern in patterns:
                        matched = [r for r in results if pattern in r['text']]
                        if matched:
                            pattern_matches[pattern] = matched

                    # 只有当所有 pattern 都匹配时才处理弹窗
                    if len(pattern_matches) == len(patterns):
                        self.logger.info(f"检测到弹窗: {popup['name']}")

                        if action == 'click_first':
                            # 对于 click_first，使用精确匹配来查找第一个 pattern
                            first_pattern = patterns[0]
                            exact_match = next((r for r in results if r['text'].strip() == first_pattern.strip()), None)
                            if exact_match and self._click_ocr_result(exact_match, screenshot_region):
                                break
                        elif action == 'click_region':
                            click_region = popup.get('click_region')
                            if click_region:
                                if self._click_region(click_region):
                                    break

                target_results = self.bot.ocr_helper.extract_text(
                    screenshot,
                    keywords=[target_text]
                )

                if target_results:
                    self.logger.info(f"检测到目标文本: {target_text}")
                    return True

                time.sleep(check_interval)

            self.logger.warning(f"超时未检测到目标文本: {target_text}")
            return False

        except Exception as e:
            self.logger.error(f"处理弹窗失败: {str(e)}")
            return False

class GetTextFromRegionAction(BaseAction):
    """获取文本内容"""

    def _get_selector_map(self):
        """获取匹配方式映射"""
        return {
            'text': (lambda pattern: self.ui_animator(text=pattern), "text"),
            'text_contains': (lambda pattern: self.ui_animator(textContains=pattern), "textContains"),
            'description': (lambda pattern: self.ui_animator(description=pattern), "description"),
            'description_contains': (lambda pattern: self.ui_animator(descriptionContains=pattern), "descriptionContains")
        }

    def _get_selectors(self, element_pattern: str, match_type: str, selector_map: dict):
        """获取选择器列表"""
        if match_type:
            if match_type not in selector_map:
                raise ValueError(f"不支持的匹配方式: {match_type}")
            return [(selector_map[match_type][0](element_pattern), match_type)]
        return [(func(element_pattern), type_name)
                for func, type_name in selector_map.values()]

    def _process_text(self, text: str, result_pattern: str) -> str:
        """处理文本，应用result_pattern"""
        if result_pattern and text:
            try:
                import re
                match = re.search(result_pattern, str(text))
                if match:
                    return match.group(1) if match.groups() else match.group(0)
            except Exception as e:
                self.logger.warning(f"应用result_pattern时出错: {str(e)}")
        return text

    def _try_get_text(self, element_pattern: str, match_type: str, result_pattern: str) -> tuple[bool, str]:
        """尝试获取文本"""
        selector_map = self._get_selector_map()
        if not element_pattern:
            return False, ""

        selectors = self._get_selectors(element_pattern, match_type, selector_map)
        for selector, selector_type in selectors:
            if selector.exists:
                element = selector.info
                text = (element.get('contentDescription', '')
                       if 'description' in selector_type
                       else element.get('text', '') or element.get('contentDescription', ''))

                if text:
                    text = self._process_text(text, result_pattern)
                    self.logger.info(f"通过{selector_type}找到文本: {text}")
                    return True, text
        return False, ""

    def execute(self, params: Dict[str, Any]) -> bool:
        save_to = params['save_to']
        element_pattern = params.get('element_pattern')
        match_type = params.get('match_type')
        timeout = params.get('timeout')
        interval = params.get('interval')
        result_pattern = params.get('result_pattern')
        overwrite_on_fail = params.get('overwrite_on_fail', True)

        try:
            self.logger.info(f"开始获取文本 (save_to: {save_to}, match_type: {match_type or 'all'})")

            # 如果没有设置timeout和interval，只执行一次
            if timeout is None or interval is None:
                found, text = self._try_get_text(element_pattern, match_type, result_pattern)
                if found:
                    self.bot.set_variable(save_to, text)
                    return True
                if overwrite_on_fail:
                    self.bot.set_variable(save_to, "")
                return False

            # 如果设置了timeout和interval，使用循环重试逻辑
            start_time = time.time()
            while time.time() - start_time < timeout:
                found, text = self._try_get_text(element_pattern, match_type, result_pattern)
                if found:
                    self.bot.set_variable(save_to, text)
                    return True

                self.logger.debug(f"未找到目标文本,已等待 {time.time() - start_time:.1f} 秒")
                time.sleep(interval)

            self.logger.warning(f"获取文本超时({timeout}秒)")
            if overwrite_on_fail:
                self.bot.set_variable(save_to, "")
            return False

        except Exception as e:
            self.logger.error(f"获取文本失败: {str(e)}")
            if overwrite_on_fail:
                self.bot.set_variable(save_to, "")
            return False

class VerifyTextInRegionAction(BaseAction):
    """验证区域内是否包含指定文字"""

    def execute(self, params: Dict[str, Any]) -> bool:
        region = params.get('region')
        expected_text = params['expected_text']
        save_to = params.get('save_to')
        match_type = params.get('match_type', 'text')  # 匹配方式

        try:
            # 处理region参数
            if isinstance(region, str) and region.startswith('${') and region.endswith('}'):
                var_name = region.strip('${}')
                region = self.bot.get_variable(var_name)
                if region is None:
                    self.logger.error(f"变量 {var_name} 未找到")
                    if save_to:
                        self.bot.set_variable(save_to, False)
                    return False

            # 定义匹配方式映射
            selector_map = {
                'text': (f'new UiSelector().text("{expected_text}")', "text"),
                'text_contains': (f'new UiSelector().textContains("{expected_text}")', "textContains"),
                'description': (f'new UiSelector().description("{expected_text}")', "description"),
                'description_contains': (f'new UiSelector().descriptionContains("{expected_text}")', "descriptionContains")
            }

            if match_type not in selector_map:
                raise ValueError(f"不支持的匹配方式: {match_type}")

            selector_str, selector_type = selector_map[match_type]

            if region:
                # 确保region是列表或元组且包含4个值
                if not isinstance(region, (list, tuple)) or len(region) != 4:
                    raise ValueError("region参数必须是包含4个值的列表或元组: [x1, y1, x2, y2]")

                x1, y1, x2, y2 = map(int, region)

                # 获取所有匹配的元素
                matching_elements = self.ui_animator.xpath(f'//*[@{selector_type}="{expected_text}"]').all()

                for element in matching_elements:
                    bounds = element.info['bounds']
                    if (bounds['left'] >= x1 and bounds['top'] >= y1 and
                        bounds['right'] <= x2 and bounds['bottom'] <= y2):
                        self.logger.info(f"在指定区域内找到文本: {expected_text} (bounds: {bounds})")

                        if save_to:
                            self.bot.set_variable(save_to, True)
                        return True

                self.logger.info(f"在指定区域内未找到文本: {expected_text}")
            else:
                # 不限制区域的查找
                matching_elements = self.ui_animator.xpath(f'//*[@{selector_type}="{expected_text}"]').all()
                if matching_elements:
                    self.logger.info(f"找到文本: {expected_text}")

                    if save_to:
                        self.bot.set_variable(save_to, True)
                    return True

            # 如果没找到
            self.logger.info(f"未找到文本: {expected_text}")
            if save_to:
                self.bot.set_variable(save_to, False)
            return False

        except Exception as e:
            self.logger.error(f"验证文本失败: {str(e)}")
            self.logger.error(f"错误详情: {str(e.__class__.__name__)}: {str(e)}")
            if save_to:
                self.bot.set_variable(save_to, False)
            return False

class WaitForInputReadyAction(BaseAction):
    """等待输入框准备就绪"""

    def execute(self, params: Dict[str, Any]) -> bool:
        timeout = params.get('timeout', 5)
        check_interval = params.get('check_interval', 0.5)

        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 使用UIAutomator2检查当前焦点是否在输入框
                focused = self.ui_animator(focused=True)
                if focused.exists:
                    self.logger.info("输框已激活")
                    return True

                time.sleep(check_interval)

            self.logger.warning("等待输入框激活超时")
            # 如果UIAutomator2检测失败，尝试使用adb命令
            try:
                result = subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'dumpsys', 'input_method'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if "mInputShown=true" in result.stdout:
                    self.logger.info("通过adb命令确认输入框已激活")
                    return True
            except Exception as e:
                self.logger.error(f"使用adb命令检查输入框状态失败: {str(e)}")

            return False

        except Exception as e:
            self.logger.error(f"等待输入框失败: {str(e)}")
            return False

class InputTextAction(BaseAction):
    """输入文本"""

    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            # 获取要输入的文本并解析变量
            text = params['text']
            if isinstance(text, str) and "${" in text:
                var_name = text.replace("${", "").replace("}", "")
                text = self.bot.get_variable(var_name)
                if text is None:
                    self.logger.error(f"变量 {var_name} 未找到")
                    return False

            if not isinstance(text, str):
                text = str(text)

            # 使用UIAutomator2输入文本
            self.ui_animator.send_keys(text)
            self.logger.info(f"输入文本: {text}")
            return True

        except Exception as e:
            self.logger.error(f"输入文本失败: {str(e)}")
            # 如果UIAutomator2失败，尝试使用adb命令作为备选方案
            try:
                text = text.replace(' ', '%s')
                subprocess.run([
                    'adb', '-s', self.device_id, 'shell', 'input', 'text', text
                ], check=True)
                self.logger.info("使用adb命令输入文本成功")
                return True
            except Exception as e2:
                self.logger.error(f"使用adb命令输入文本也失败: {str(e2)}")
                return False

class WaitForKeyElementAction(BaseAction):
    """等待关键元素出现并获取其位置信息"""

    def execute(self, params: Dict[str, Any]) -> bool:
        text_pattern = params['text_pattern']  # 文本模式
        timeout = params.get('timeout', 30)
        interval = params.get('interval', 1)  # 添加等待间隔参数,默认1秒
        save_to = params.get('save_to')  # 保存元素信息到变量
        match_type = params.get('match_type')  # 匹配方式,不指定则尝试所有方式
        contains_only = params.get('contains_only', False)  # 是否只接受包含而不完全匹配的情况

        try:
            self.logger.info(f"开始等待关键元素: {text_pattern} (匹配方式: {match_type or 'all'}, 间隔: {interval}秒, 仅包含匹配: {contains_only})")

            # 定义匹配方式映射
            selector_map = {
                'text': (self.ui_animator(text=text_pattern), "text"),
                'text_contains': (self.ui_animator(textContains=text_pattern), "textContains"),
                'description': (self.ui_animator(description=text_pattern), "description"),
                'description_contains': (self.ui_animator(descriptionContains=text_pattern), "descriptionContains")
            }

            start_time = time.time()
            while time.time() - start_time < timeout:
                # 如果指定了匹配方式
                if match_type:
                    if match_type not in selector_map:
                        raise ValueError(f"不支持的匹配方式: {match_type}")
                    selectors = [selector_map[match_type]]
                else:
                    # 尝试所有匹配方式
                    selectors = list(selector_map.values())

                for selector, selector_type in selectors:
                    if selector.exists:
                        element = selector.info
                        element_text = element.get('text', '') or element.get('contentDescription', '')
                        element_text = element_text.strip()
                        # 如果设置了contains_only，检查是否是包含但不完全一致的情况
                        if contains_only:
                            if text_pattern in element_text and text_pattern != element_text.strip():
                                self.logger.info(f"找到包含但不完全一致的关键元素: {element_text}")
                                if save_to:
                                    element_info = {
                                        'bounds': element['bounds'],
                                        'text': element_text,
                                        'content_desc': element.get('contentDescription', ''),
                                        'resource_id': element.get('resourceId', ''),
                                        'class_name': element['className'],
                                        'package': element.get('package', ''),
                                        'clickable': element.get('clickable', False),
                                        'selected': element.get('selected', False),
                                        'selector_type': selector_type
                                    }
                                    self.bot.set_variable(save_to, element_info)
                                return True
                            else:
                                continue
                        else:
                            # 不需要特殊处理，直接返回找到的元素
                            self.logger.info(f"找到关键元素: {element_text}")
                            if save_to:
                                element_info = {
                                    'bounds': element['bounds'],
                                    'text': element_text,
                                    'content_desc': element.get('contentDescription', ''),
                                    'resource_id': element.get('resourceId', ''),
                                    'class_name': element['className'],
                                    'package': element.get('package', ''),
                                    'clickable': element.get('clickable', False),
                                    'selected': element.get('selected', False),
                                    'selector_type': selector_type
                                }
                                self.bot.set_variable(save_to, element_info)
                            return True

                time.sleep(interval)

            self.logger.warning(f"等待关键元素超时: {text_pattern}")
            return False

        except Exception as e:
            self.logger.error(f"等待关键元素失败: {str(e)}")
            return False