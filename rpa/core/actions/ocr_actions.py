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
            
            # 计算中心点坐标，考虑缩放因子
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
            
            # 使用 adb 命令执行点击
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'input', 'tap', str(center_x), str(center_y)],
                check=True,
                capture_output=True
            )
            # 记录点击结果
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
                            if click_region and self._click_region(click_region):
                                break
                
                time.sleep(check_interval)
            
            self.logger.warning(f"超时未检测到目标文本: {target_text}")
            return False
            
        except Exception as e:
            self.logger.error(f"处理弹窗失败: {str(e)}")
            return False

class GetTextFromRegionAction(BaseAction):
    """从指定区域获取文本"""
    
    def _parse_region(self, region: List) -> List[int]:
        """解析区域参数，处理变量和计算"""
        parsed_region = []
        for value in region:
            if isinstance(value, str) and '${' in value:
                # 提取变量名和运算表达式
                expr = value.replace('${', '').replace('}', '')
                try:
                    # 分离变量名和运算
                    parts = expr.split(' ')
                    var_name = parts[0]
                    
                    # 如果是嵌套字典访问（如 detail_position.y1）
                    if '.' in var_name:
                        obj_name, attr_name = var_name.split('.')
                        var_value = self.bot.get_variable(obj_name)[attr_name]
                    else:
                        var_value = self.bot.get_variable(var_name)
                    
                    # 执行运算
                    if len(parts) > 1:
                        operation = ' '.join(parts[1:])
                        result = eval(f"{var_value} {operation}")
                        parsed_region.append(int(result))
                    else:
                        parsed_region.append(int(var_value))
                except Exception as e:
                    self.logger.error(f"解析区域参数失败: {str(e)}")
                    raise
            else:
                parsed_region.append(int(value))
        return parsed_region
    
    def execute(self, params: Dict[str, Any]) -> bool:
        region = params.get('region')
        save_to = params['save_to']
        step_name = params.get('name', 'get_text_from_region')
        
        try:
            # 解析区域参数
            if region:
                region = self._parse_region(region)
                        
            # 获取截图
            screenshot = self.bot.screenshot_helper.take_screenshot(
                save_path="temp",
                filename_prefix="text_region",
                region=region
            )
            
            # OCR识别
            results = self.bot.ocr_helper.extract_text(screenshot)
            
            # 合并所有文本
            text = ' '.join([r['text'] for r in results])
            
            # 保存结果
            self.bot.set_variable(save_to, text)
            
            # 如果是调试模式，保存调试信息
            if self.bot.debug:
                self.save_debug_screenshot(
                    step_name=step_name,
                    region=region,
                    extra_info={
                        'ocr_results': results,
                        'extracted_text': text,
                        'save_to_variable': save_to
                    }
                )
            
            self.logger.info(f"从区域 {region} 获取文本: {text}")
            return True
            
        except Exception as e:
            self.logger.error(f"获取区域文本失败: {str(e)}")
            return False

class VerifyTextInRegionAction(BaseAction):
    """验证指定区域内是否包含预期文本"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        region = params['region']
        expected_text = params['expected_text']
        save_to = params.get('save_to')
        step_name = params.get('name', 'verify_text_in_region')
        
        try:
            # 获取截图
            screenshot = self.bot.screenshot_helper.take_screenshot(
                save_path="temp",
                filename_prefix="verify_text",
                region=region
            )
            
            # 执行OCR识别
            results = self.bot.ocr_helper.extract_text(screenshot)
            
            # 合并所有文本
            text = ' '.join([r['text'] for r in results])
            
            # 检查是否包含预期文本
            result = expected_text in text
            
            if save_to:
                self.bot.set_variable(save_to, result)
                
            self.logger.info(f"验证文本 '{expected_text}' 是否存在: {result}")

            # 如果是调试模式，保存调试信息
            if self.bot.debug:
                
                # 保存调试截图
                self.save_debug_screenshot(
                    step_name=step_name,
                    region=region,
                    extra_info={
                        'ocr_results': results,
                        'expected_text': expected_text,
                        'extracted_text': text,
                        'verification_result': result,
                        'save_to_variable': save_to
                    }
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"验证文本失败: {str(e)}")
            return False

class WaitForInputReadyAction(BaseAction):
    """等待输入框准备就绪"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        timeout = params.get('timeout', 5)
        check_interval = params.get('check_interval', 0.5)
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                result = subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'dumpsys', 'input_method'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if "mInputShown=true" in result.stdout:
                    self.logger.info("输入框已激活")
                    return True
                    
                time.sleep(check_interval)
            
            self.logger.warning("等待输入框激活超时")
            return False
            
        except Exception as e:
            self.logger.error(f"等待输入框失败: {str(e)}")
            return False

class InputTextAction(BaseAction):
    """输入文本"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        text = params['text']
        input_type = params.get('input_type', 'text')
        clear_first = params.get('clear_first', True)
        
        try:
            if clear_first:
                subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'input', 'keyevent', 'KEYCODE_MOVE_END'],
                    check=True
                )
                time.sleep(0.5)
                subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'input', 'keyevent', 'KEYCODE_DEL'],
                    check=True
                )
            
            if input_type == 'number':
                for digit in text:
                    keycode = f'KEYCODE_{digit}'
                    subprocess.run(
                        ['adb', '-s', self.bot.device_id, 'shell', 'input', 'keyevent', keycode],
                        check=True
                    )
                    time.sleep(0.1)
            else:
                subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'input', 'text', text],
                    check=True
                )
            
            self.logger.info(f"成功输入文本: {text}")
            return True
            
        except Exception as e:
            self.logger.error(f"输入文本失败: {str(e)}")
            return False

class GetElementPositionAction(BaseAction):
    """获取指定文本的位置"""
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, int]:
        text = params['text']
        region = params.get('region')
        save_to = params.get('save_to')
        step_name = params.get('name', 'get_element_position')
        
        try:
            # 获取截图
            screenshot = self.bot.screenshot_helper.take_screenshot(
                save_path="temp",
                filename_prefix="element_position",
                region=region
            )
            
            # OCR识别
            results = self.bot.ocr_helper.extract_text(screenshot)
            
            # 获取截图缩放比例
            scale = self.bot.screenshot_helper.get_scale_factor()
            
            # 查找目标文本
            for item in results:
                if text in item['text']:
                    box = item['box']  # box 格式: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                    
                    # 调整OCR坐标以考虑缩放
                    adjusted_box = []
                    for point in box:
                        x = int(point[0] / scale)  # 将缩放后的坐标转换回原始坐标
                        y = int(point[1] / scale)
                        
                        if region:
                            # 如果指定了区域，加上区域偏移
                            x += region[0]
                            y += region[1]
                            
                        adjusted_box.append([x, y])
                        
                    # 计算边界框的位置
                    position = {
                        'x1': adjusted_box[0][0],  # 左上角x
                        'y1': adjusted_box[0][1],  # 左上角y
                        'x2': adjusted_box[2][0],  # 右下角x
                        'y2': adjusted_box[2][1]   # 右下角y
                    }
                    
                    if save_to:
                        self.bot.set_variable(save_to, position)
                    self.logger.info(f"找到文本 '{text}' 的位置: {position}")
                    return position
                    
            self.logger.error(f"未找到文本: {text}")
            return {}
            
        except Exception as e:
            self.logger.error(f"获取元素位置失败: {str(e)}")
            return {}