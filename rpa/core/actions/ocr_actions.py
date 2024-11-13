from typing import Dict, Any, List
from .base_action import BaseAction
from ...utils.ocr_helper import OCRHelper
from ...utils.screenshot import ScreenshotHelper
from ...utils.logger import get_logger
from ..base_bot import BaseBot
import time
import yaml
import subprocess
import numpy as np

class OCRActions(BaseAction):
    """OCR相关动作处理类"""
    
    def __init__(self, bot: BaseBot):
        super().__init__(bot)
        self.ocr_helper = OCRHelper()
        self.screenshot_helper = ScreenshotHelper(bot.device_id)
        self.logger = get_logger(__name__)
        
    def _save_debug_info(self, step_name: str, screenshot_path: str, 
                        ocr_results: List[Dict], region: List[int] = None,
                        debug_dir: str = None):
        """保存调试信息"""
        if not self.bot.debug:
            return
            
        step_index = self.bot.current_step_index
        
        # 使用step_index创建调试目录
        if debug_dir is None:
            # 确保step_name包含编号前缀
            if not str(step_name).startswith(f"{step_index:03d}_"):
                step_name = f"{step_index:03d}_{step_name}"
            debug_dir = self.bot.debug_dir / step_name
        else:
            # 如果传入了debug_dir，确保其父目录包含编号前缀
            parent_dir = debug_dir.parent
            if parent_dir.name == self.bot.debug_dir.name:  # 如果父目录是debug根目录
                if not str(debug_dir.name).startswith(f"{step_index:03d}_"):
                    debug_dir = self.bot.debug_dir / f"{step_index:03d}_{debug_dir.name}"
            else:  # 如果是子目录
                if not str(parent_dir.name).startswith(f"{step_index:03d}_"):
                    new_parent = self.bot.debug_dir / f"{step_index:03d}_{parent_dir.name}"
                    debug_dir = new_parent / debug_dir.name
        
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制截图
        import shutil
        shutil.copy2(screenshot_path, debug_dir / "screenshot.png")
        
        # 在截图上标注识别结果
        import cv2
        import numpy as np
        img = cv2.imread(screenshot_path)
        
        # 如果有区域设置，画出区域框
        if region:
            x1, y1, x2, y2 = region
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # 标注识别到的文字位置
        for result in ocr_results:
            box = result['box']
            text = result['text']
            confidence = result['confidence']
            
            # 画框
            points = np.array(box).astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(img, [points], True, (0, 0, 255), 2)
            
            # 显示文字和置信度
            cv2.putText(img, f"{text} ({confidence:.2f})", 
                       (int(box[0][0]), int(box[0][1])-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # 保存标注后的图片
        cv2.imwrite(str(debug_dir / "annotated.png"), img)
        
        # 保存OCR结果
        with open(debug_dir / "ocr_results.yaml", "w", encoding="utf-8") as f:
            yaml.dump(ocr_results, f, allow_unicode=True)

    def _click_ocr_result(self, result: Dict[str, Any], screenshot_region: List[int] = None, 
                         click_offset: List[int] = None) -> bool:
        """点击OCR识别结果的中心位置"""
        # 计算相对于裁剪区域的中心点（在缩放图片上的坐标）
        box = result['box']
        center_x = (box[0][0] + box[2][0]) // 2
        center_y = (box[0][1] + box[2][1]) // 2
        
        # 应用偏移量
        if click_offset:
            center_x += click_offset[0]
            center_y += click_offset[1]
        
        # 转换为实际坐标（考虑缩放因子）
        real_x, real_y = self.screenshot_helper.get_real_coordinates(center_x, center_y)
        
        self.logger.debug(f"坐标计算过程:")
        self.logger.debug(f"OCR原始坐标: ({center_x}, {center_y})")
        if click_offset:
            self.logger.debug(f"点击偏移量: ({click_offset[0]}, {click_offset[1]})")
        self.logger.debug(f"缩放因子: {self.screenshot_helper.get_scale_factor()}")
        
        # 使用基类的点击方法
        return self._click_at_point(real_x, real_y, screenshot_region)

    def wait_and_click_ocr_text(self, params: Dict[str, Any]) -> bool:
        """等待指定文字出现并点击"""
        text = params['text']
        timeout = params.get('timeout', 30)
        check_interval = params.get('check_interval', 2)
        screenshot_region = params.get('screenshot_region')
        click_offset = params.get('click_offset', None)
        
        self.logger.info(f"等待文字出现: {text}, 检查间隔: {check_interval}秒")
        start_time = time.time()
        
        # 创建步骤专属的调试目录
        if self.bot.debug:
            step_index = self.bot.current_step_index
            step_debug_dir = self.bot.debug_dir / f"{step_index:03d}_等待点击_{text}"
            step_debug_dir.mkdir(exist_ok=True)
            attempt = 1
            
            # 创建screenshots子目录
            screenshots_dir = step_debug_dir / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
        
        while time.time() - start_time < timeout:
            # 获取截图
            screenshot = self.screenshot_helper.take_screenshot(
                save_path=str(screenshots_dir) if self.bot.debug else "temp",
                region=screenshot_region,
                filename_prefix=f"attempt_{attempt:03d}"
            )
            
            # OCR识别
            results = self.ocr_helper.extract_text(
                screenshot,
                keywords=[text]
            )
            
            # 保存调试信息
            if self.bot.debug:
                self._save_debug_info(
                    f"attempt_{attempt:03d}",
                    screenshot,
                    results,
                    screenshot_region,
                    debug_dir=step_debug_dir / f"attempt_{attempt:03d}"
                )
                attempt += 1
            
            if results:
                self.logger.info(f"找到目标文字: {text}")
                # 使用公共点击方法，传入click_offset参数
                if self._click_ocr_result(results[0], screenshot_region, click_offset):
                    return True
                self.logger.debug(f"点击失败，将重试")
            
            self.logger.debug(f"未找到文字: {text}, {check_interval}秒后重试")
            time.sleep(check_interval)
        
        self.logger.warning(f"等待超时: {text}")
        return False

    def handle_popups_until_target(self, params: Dict[str, Any]) -> bool:
        """处理弹窗直到出现目标文本
        
        Args:
            params:
                timeout: 超时时间(秒)
                check_interval: 检查间隔(秒)
                target_text: 目标文本
                screenshot_region: 截图区域[x1,y1,x2,y2]，默认全屏
                popups: 弹窗配置列表，每个弹窗支持：
                    - name: 弹窗名称
                    - patterns: 匹配文本列表
                    - action: 动作类型(click_first/click_region)
                    - click_region: 当action为click_region时的点击区域[x1,y1,x2,y2]
                    - priority: 优先级(数字越小优先级越高)
        """
        timeout = params.get('timeout', 60)
        check_interval = params.get('check_interval', 1)
        target_text = params.get('target_text')
        target_clickable = params.get('target_clickable', True)
        screenshot_region = params.get('screenshot_region')
        popups = params.get('popups', [])
        
        # 按优先级排序弹窗配置
        popups.sort(key=lambda x: x.get('priority', 999))
        
        start_time = time.time()
        attempt = 1
        
        while time.time() - start_time < timeout:
            # 获取截图
            if self.bot.debug:
                step_index = self.bot.current_step_index
                debug_dir = self.bot.debug_dir / f"{step_index:03d}_处理弹窗_{target_text}/attempt_{attempt:03d}"
                debug_dir.mkdir(parents=True, exist_ok=True)
                screenshot = self.screenshot_helper.take_screenshot(
                    save_path=str(debug_dir),
                    filename_prefix="screenshot",
                    region=screenshot_region
                )
            else:
                screenshot = self.screenshot_helper.take_screenshot(
                    save_path="temp",
                    filename_prefix="popup_check",
                    region=screenshot_region
                )
            
            # 检查目标文本
            target_results = self.ocr_helper.extract_text(
                screenshot,
                keywords=[target_text]
            )
            
            # 保存调试信息
            if self.bot.debug:
                self._save_debug_info(
                    f"attempt_{attempt}",
                    screenshot,
                    target_results,
                    screenshot_region,
                    debug_dir=debug_dir
                )
            
            if target_results:
                self.logger.info(f"检测到目标文本: {target_text}")
                # 检查是否需要验证可点击性
                if not target_clickable or self._is_element_clickable(target_results[0], screenshot):
                    return True
                else:
                    self.logger.debug(f"目标文本当前不可点击，继续处理弹窗")
            
            # 检查并处理弹窗
            popup_handled = False
            
            for popup in popups:
                patterns = popup['patterns']
                action = popup.get('action', 'click_first')
                
                # 获取所有文本并匹配
                all_results = self.ocr_helper.extract_text(screenshot)
                matched_results = [r for r in all_results if r['text'] in patterns]
                
                # 保存调试信息
                if self.bot.debug:
                    with open(debug_dir / f"popup_{popup['name']}.yaml", "w", encoding="utf-8") as f:
                        yaml.dump({
                            'popup_name': popup['name'],
                            'patterns': patterns,
                            'matched_results': matched_results,
                            'all_results': all_results,
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                        }, f, allow_unicode=True)
                
                if matched_results:
                    self.logger.info(f"检测到弹窗: {popup['name']}")
                    
                    if action == 'click_first':
                        # 原有的点击文本逻辑
                        target_result = None
                        for pattern in patterns:
                            for result in matched_results:
                                if result['text'] == pattern:
                                    target_result = result
                                    break
                            if target_result:
                                break
                        
                        if target_result:
                            self.logger.debug(f"将点击文本: {target_result['text']}")
                            if self._click_ocr_result(target_result, screenshot_region):
                                popup_handled = True
                    
                    elif action == 'click_region':
                        # 点击指定区域
                        click_region = popup.get('click_region')
                        if click_region:
                            # 保存调试信息
                            if self.bot.debug:
                                x1, y1, x2, y2 = map(int, click_region)
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                
                                annotations = [
                                    # 添加点击区域框
                                    {
                                        'type': 'rectangle',
                                        'data': [x1, y1, x2, y2],
                                        'color': (0, 255, 0),  # 绿色
                                        'thickness': 2
                                    },
                                    # 添加点击点
                                    {
                                        'type': 'circle',
                                        'data': [center_x, center_y, 10],
                                        'color': (0, 0, 255),  # 红色
                                        'thickness': -1  # 实心圆
                                    },
                                    # 添加坐标文本
                                    {
                                        'type': 'text',
                                        'data': [
                                            f"Click: ({center_x}, {center_y})",
                                            center_x + 10,
                                            center_y - 10
                                        ],
                                        'color': (0, 0, 255),
                                        'thickness': 2
                                    }
                                ]
                                
                                self.save_debug_screenshot(
                                    step_name=f"popup_{popup['name']}_click",
                                    region=screenshot_region,
                                    annotations=annotations,
                                    extra_info={
                                        'popup_name': popup['name'],
                                        'click_region': click_region,
                                        'click_point': [center_x, center_y],
                                        'matched_text': [r['text'] for r in matched_results]
                                    }
                                )
                            
                            popup_handled = self._click_region(click_region)
                            if popup_handled:
                                self.logger.info(f"点击区域成功: {click_region}")
                    
                    if popup_handled:
                        self.logger.info(f"成功处理弹窗: {popup['name']}")
                        break
            
            if not popup_handled:
                self.logger.debug(f"当前未检测到任何弹窗，继续等待目标文本: {target_text}")
                time.sleep(check_interval)
            
            attempt += 1
        
        self.logger.warning(f"超时未检测到目标文本: {target_text}")
        return False

    def wait_for_input_ready(self, params: Dict[str, Any]) -> bool:
        """等待输入框准备就绪
        
        Args:
            params:
                timeout: 超时时间(秒)
                check_interval: 检查间隔(秒)
        
        Returns:
            bool: 输入框是否就绪
        """
        timeout = params.get('timeout', 5)
        check_interval = params.get('check_interval', 0.5)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查输入框状态
            try:
                result = subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'dumpsys', 'input_method'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if "mInputShown=true" in result.stdout:
                    self.logger.info("输入框已激活")
                    return True
            except subprocess.CalledProcessError as e:
                self.logger.error(f"检查输入框状态失败: {e}")
            
            time.sleep(check_interval)
        
        self.logger.warning("等待输入框激活超时")
        return False

    def input_text(self, params: Dict[str, Any]) -> bool:
        """输入文本
        
        Args:
            params:
                text: 要输入的文本
                input_type: 输入型(text/number)
                clear_first: 是否先清空输入框
                timeout: 超时时间(秒)
        
        Returns:
            bool: 是否输入成功
        """
        text = params['text']
        input_type = params.get('input_type', 'text')
        clear_first = params.get('clear_first', True)
        timeout = params.get('timeout', 5)
        
        try:
            # 如果需要先清空输入框
            if clear_first:
                # 模拟长按选择全部文本
                subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'input', 'keyevent', 'KEYCODE_MOVE_END'],
                    check=True
                )
                time.sleep(0.5)
                subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'input', 'keyevent', 'KEYCODE_DEL'],
                    check=True
                )
            
            # 根据输入类型选择不同的输入方式
            if input_type == 'number':
                # 对于数字，使用keyevent模拟按键
                for digit in text:
                    keycode = f'KEYCODE_{digit}'
                    subprocess.run(
                        ['adb', '-s', self.bot.device_id, 'shell', 'input', 'keyevent', keycode],
                        check=True
                    )
                    time.sleep(0.1)  # 短暂延迟确保输入稳定
            else:
                # 对于普通文本，使用text输入
                subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'input', 'text', text],
                    check=True
                )
            
            self.logger.info(f"成功输入文本: {text}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"输入文本失败: {e}")
            return False

class GetTextFromRegionAction(BaseAction):
    """从指定区域获取文本"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        region = params.get('region')
        screenshot_region = params.get('screenshot_region')
        save_to = params['save_to']
        step_name = params.get('name', 'get_text_from_region')
        
        # 优先使用region，如果没有则使用screenshot_region
        capture_region = region if region is not None else screenshot_region
        
        if capture_region is None:
            self.logger.error("必须提供region或screenshot_region参数")
            return False
        
        try:
            # 获取截图
            screenshot = self.bot.screenshot_helper.take_screenshot(
                save_path="temp",
                filename_prefix="text_region",
                region=capture_region
            )
            
            # 执行OCR识别
            results = self.bot.ocr_helper.extract_text(screenshot)
            
            # 合并所有文本
            text = ' '.join([r['text'] for r in results])
            
            # 保存结果
            self.bot.set_variable(save_to, text)
            
            self.logger.info(f"从区域 {capture_region} 获取文本: {text}")

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
                        'color': (0, 0, 255),
                        'thickness': 2
                    })
                
                # 保存调试截图
                self.save_debug_screenshot(
                    step_name=step_name,
                    region=capture_region,
                    annotations=annotations,
                    extra_info={
                        'ocr_results': results,
                        'extracted_text': text,
                        'save_to_variable': save_to
                    }
                )
            
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
            screenshot = self.screenshot_helper.take_screenshot(
                save_path="temp",
                filename_prefix="check_text",
                region=region
            )
            
            # 执行OCR识别
            results = self.ocr_helper.extract_text(
                screenshot,
                keywords=[text]
            )
            
            exists = len(results) > 0
            
            # 如果需要保存结果
            if save_to:
                self.bot.set_variable(save_to, exists)
            
            self.logger.info(f"检查文本 '{text}' 是否存在: {exists}")
            return exists
            
        except Exception as e:
            self.logger.error(f"检查文本存在失败: {str(e)}")
            return False