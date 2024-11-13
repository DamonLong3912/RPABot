from typing import Dict, Any, List
from .base_action import BaseAction
import subprocess
import time

class GetTextFromRegionAction(BaseAction):
    """从指定区域获取文本"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        region = params.get('region')
        save_to = params['save_to']
        
        try:
            # 获取截图
            screenshot = self.bot.screenshot_helper.take_screenshot(
                save_path="temp",
                filename_prefix="text_region",
                region=region
            )
            
            # 执行OCR识别
            results = self.bot.ocr_helper.extract_text(screenshot)
            
            # 合并所有文本
            text = ' '.join([r['text'] for r in results])
            
            # 保存结果
            self.bot.set_variable(save_to, text)
            
            self.logger.info(f"从区域 {region} 获取文本: {text}")
            return True
            
        except Exception as e:
            self.logger.error(f"获取区域文本失败: {str(e)}")
            return False

class CheckTextExistsAction(BaseAction):
    """检查文本是否存在"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        region = params['region']
        text = params['text']
        save_to = params.get('save_to')
        
        try:
            # 获取截图
            screenshot = self.bot.screenshot_helper.take_screenshot(
                save_path="temp",
                filename_prefix="check_text",
                region=region
            )
            
            # 执行OCR识别
            results = self.bot.ocr_helper.extract_text(
                screenshot,
                keywords=[text]
            )
            
            exists = len(results) > 0
            
            if save_to:
                self.bot.set_variable(save_to, exists)
            
            self.logger.info(f"检查文本 '{text}' 是否存在: {exists}")
            return exists
            
        except Exception as e:
            self.logger.error(f"检查文本存在失败: {str(e)}")
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
                annotations = []
                for result in results:
                    box = result['box']
                    
                    # 计算文本位置（使用框的左上角）
                    text_x = int(box[0][0])
                    text_y = int(box[0][1]) - 10
                    
                    # 添加文本标注
                    annotations.append({
                        'type': 'text',
                        'data': [
                            f"{result['text']} ({result.get('confidence', 0):.2f})",
                            text_x,
                            text_y
                        ],
                        'color': (0, 0, 255),  # 红色
                        'thickness': 2
                    })
                    
                    # 添加边框
                    points = [[int(x), int(y)] for x, y in box]
                    annotations.append({
                        'type': 'polygon',
                        'data': points,
                        'color': (0, 255, 0) if expected_text in result['text'] else (0, 0, 255),  # 匹配绿色，不匹配红色
                        'thickness': 2
                    })
                
                # 保存调试截图
                self.save_debug_screenshot(
                    step_name=step_name,
                    region=region,
                    annotations=annotations,
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

class WaitAndClickOCRTextAction(BaseAction):
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
                # 获取截图
                screenshot = self.bot.screenshot_helper.take_screenshot(
                    save_path="temp",
                    filename_prefix="wait_click_text",
                    region=screenshot_region
                )
                
                # OCR识别
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

class HandlePopupsUntilTargetAction(BaseAction):
    """处理弹窗直到目标出现"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        timeout = params.get('timeout', 60)
        check_interval = params.get('check_interval', 1)
        target_text = params['target_text']
        screenshot_region = params.get('screenshot_region')
        popups = params.get('popups', [])
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 获取截图
                screenshot = self.bot.screenshot_helper.take_screenshot(
                    save_path="temp",
                    filename_prefix="handle_popups",
                    region=screenshot_region
                )
                
                # 检查目标文本
                target_results = self.bot.ocr_helper.extract_text(
                    screenshot,
                    keywords=[target_text]
                )
                
                if target_results:
                    self.logger.info(f"检测到目标文本: {target_text}")
                    return True
                
                # 检查并处理弹窗
                for popup in popups:
                    patterns = popup['patterns']
                    action = popup.get('action', 'click_first')
                    
                    results = self.bot.ocr_helper.extract_text(screenshot)
                    matched_results = [r for r in results if any(p in r['text'] for p in patterns)]
                    
                    if matched_results:
                        self.logger.info(f"检测到弹窗: {popup['name']}")
                        
                        if action == 'click_first':
                            if self._click_ocr_result(matched_results[0], screenshot_region):
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