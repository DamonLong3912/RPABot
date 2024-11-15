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
        text = params['text']
        timeout = params.get('timeout', 30)
        check_interval = params.get('check_interval', 2)
        screenshot_region = params.get('screenshot_region')
        click_offset = params.get('click_offset')
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                screenshot = self.bot.screenshot_helper.take_screenshot(
                    save_path="temp",
                    filename_prefix="wait_click_text",
                    region=screenshot_region
                )
                
                results = self.bot.ocr_helper.extract_text(
                    screenshot,
                    keywords=[text]
                )
                
                if results:
                    self.logger.info(f"找到目标文本: {text}")
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
                
                target_results = self.bot.ocr_helper.extract_text(
                    screenshot,
                    keywords=[target_text]
                )
                
                if target_results:
                    self.logger.info(f"检测到目标文本: {target_text}")
                    return True
                
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
                                # 添加调试信息
                                self.logger.debug(f"准备点击区域: {click_region}")
                                if self.bot.debug:
                                    self.save_debug_screenshot(
                                        step_name=f"click_region_{popup['name']}",
                                        region=click_region,
                                        extra_info={
                                            'action': 'click_region',
                                            'popup_name': popup['name'],
                                            'click_region': click_region
                                        }
                                    )
                                if self._click_region(click_region):
                                    break
                
                time.sleep(check_interval)
            
            self.logger.warning(f"超时未检测到目标文本: {target_text}")
            return False
            
        except Exception as e:
            self.logger.error(f"处理弹窗失败: {str(e)}")
            return False

class GetTextFromRegionAction(BaseAction):
    """获取文本内容"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        save_to = params['save_to']
        relative_to = params.get('relative_to')  # 相对于某个元素的位置
        element_pattern = params.get('element_pattern')  # 元素文本模式
        match_type = params.get('match_type')  # 匹配方式,不指定则尝试所有方式
        timeout = params.get('timeout', 5)  # 默认10秒超时
        interval = params.get('interval', 0.5)  # 默认0.5秒检查间隔
        
        try:
            self.logger.info(f"开始获取文本 (save_to: {save_to}, match_type: {match_type or 'all'})")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 定义匹配方式映射
                selector_map = {
                    'text': (lambda pattern: self.ui_animator(text=pattern), "text"),
                    'text_contains': (lambda pattern: self.ui_animator(textContains=pattern), "textContains"),
                    'description': (lambda pattern: self.ui_animator(description=pattern), "description"),
                    'description_contains': (lambda pattern: self.ui_animator(descriptionContains=pattern), "descriptionContains")
                }
                
                if element_pattern:
                    # 如果指定了匹配方式
                    if match_type:
                        if match_type not in selector_map:
                            raise ValueError(f"不支持的匹配方式: {match_type}")
                        selectors = [(selector_map[match_type][0](element_pattern), match_type)]
                    else:
                        # 尝试所有匹配方式
                        selectors = [(func(element_pattern), type_name) 
                                   for func, type_name in selector_map.values()]
                    
                    for selector, selector_type in selectors:
                        if selector.exists:
                            element = selector.info
                            # 根据匹配方式获取文本
                            if 'description' in selector_type:
                                text = element.get('contentDescription', '')
                            else:
                                text = element.get('text', '') or element.get('contentDescription', '')
                            
                            if text:  # 只在找到非空文本时返回
                                self.logger.info(f"通过{selector_type}找到文本: {text}")
                                self.bot.set_variable(save_to, text)
                                return True

                elif relative_to:
                    # 获取参考元素的位置
                    ref_element = self.bot.get_variable(relative_to)
                    if not ref_element:
                        self.logger.error(f"未找到参考元素变量: {relative_to}")
                        time.sleep(interval)
                        continue
                    
                    ref_bounds = ref_element['bounds']
                    
                    # 计算目标区域边界
                    # 垂直方向优先使用绝对位置,没有则使用offset
                    expected_top = params.get('top', ref_bounds['top'] + params.get('offset_top', 0))
                    expected_bottom = params.get('bottom', ref_bounds['bottom'] + params.get('offset_bottom', 0))
                    
                    # 水平方向优先使用绝对位置,没有则使用offset
                    expected_left = params.get('left', ref_bounds['left'] + params.get('offset_left', 0))
                    expected_right = params.get('right', ref_bounds['right'] + params.get('offset_right', 0))
                    self.logger.debug(f"参考元素边界: top={ref_bounds['top']}, bottom={ref_bounds['bottom']}, left={ref_bounds['left']}, right={ref_bounds['right']}")
                    self.logger.debug(f"目标区域边界: top={expected_top}, bottom={expected_bottom}, left={expected_left}, right={expected_right}")
                    
                    # 获取所有可能的文本元素
                    elements = []
                    
                    # 根据匹配方式获取元素
                    if match_type:
                        if 'description' in match_type:
                            elements = self.ui_animator.xpath('//*//*[@content-desc]').all()
                        else:
                            elements = self.ui_animator.xpath('//*//*[@text]').all()
                    else:
                        # 获取所有可能的文本元素，包括嵌套元素
                        elements = []
                        elements.extend(self.ui_animator.xpath('//*//*[@text]').all())
                        elements.extend(self.ui_animator.xpath('//*//*[@content-desc]').all())

                    # 去重逻辑优化
                    unique_elements = []
                    seen_bounds = set()
                    for element in elements:
                        element_info = element.info
                        bounds_str = str(element_info['bounds'])
                        text = element_info.get('text', '') or element_info.get('contentDescription', '')
                        # 使用边界和文本组合作为唯一标识
                        unique_key = f"{bounds_str}_{text}"
                        if unique_key not in seen_bounds:
                            seen_bounds.add(unique_key)
                            unique_elements.append(element)
                    
                    # 检查每个元素是否在目标区域内
                    for element in unique_elements:
                        element_info = element.info
                        bounds = element_info['bounds']
                        
                        # 根据匹配方式获取文本
                        if match_type and 'description' in match_type:
                            text = element_info.get('contentDescription', '')
                        else:
                            text = element_info.get('text', '') or element_info.get('contentDescription', '')
                        
                        # 检查元素是否在目标区域内
                        if (bounds['left'] >= expected_left and
                            bounds['right'] <= expected_right and
                            bounds['top'] >= expected_top and
                            bounds['bottom'] <= expected_bottom):
                            if text:  # 只处理有文本内容的元素
                                self.logger.info(f"找到相对位置的文本: {text}")
                                self.bot.set_variable(save_to, text)
                                return True

                self.logger.debug(f"未找到目标文本,已等待 {time.time() - start_time:.1f} 秒")
                time.sleep(interval)

            self.logger.warning(f"获取文本超时({timeout}秒)")
            # 记录当前UI层级结构以便调试
            try:
                hierarchy = self.ui_animator.dump_hierarchy()
                self.logger.debug(f"当前UI层级结构:\n{hierarchy}")
            except Exception as e:
                self.logger.error(f"获取UI层级结构失败: {str(e)}")
            # 设置空字符串作为默认值
            self.bot.set_variable(save_to, "")
            return False
            
        except Exception as e:
            self.logger.error(f"获取文本失败: {str(e)}")
            # 发生异常时也设置空字符串
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
            # 定义匹配方式映射
            selector_map = {
                'text': (self.ui_animator(text=expected_text), "text"),
                'text_contains': (self.ui_animator(textContains=expected_text), "textContains"),
                'description': (self.ui_animator(description=expected_text), "description"),
                'description_contains': (self.ui_animator(descriptionContains=expected_text), "descriptionContains")
            }
            
            if match_type not in selector_map:
                raise ValueError(f"不支持的匹配方式: {match_type}")
                
            selector, selector_type = selector_map[match_type]
            
            if region:
                x1, y1, x2, y2 = map(int, region)
                
                if selector.exists:
                    element = selector.info
                    bounds = element['bounds']
                    if (bounds['left'] >= x1 and bounds['top'] >= y1 and 
                        bounds['right'] <= x2 and bounds['bottom'] <= y2):
                        self.logger.info(f"找到文本: {expected_text} (bounds: {bounds})")
                        
                        if save_to:
                            self.bot.set_variable(save_to, True)
                        return True
            else:
                # 不限制区域的查找
                if selector.exists:
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