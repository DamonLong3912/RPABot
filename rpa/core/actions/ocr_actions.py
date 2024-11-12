from typing import Dict, Any, List
from ..base_bot import BaseBot
from ...utils.ocr_helper import OCRHelper
from ...utils.screenshot import ScreenshotHelper
from ...utils.logger import get_logger
import time
import yaml
import subprocess

class OCRActions:
    """OCR相关动作处理类"""
    
    def __init__(self, bot: BaseBot):
        self.bot = bot
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
        """点击OCR识别结果的中心位置
        
        Args:
            result: OCR识别结果
            screenshot_region: 截图区域[x1,y1,x2,y2]
            click_offset: 点击位置的偏移量[offset_x, offset_y]
        
        Returns:
            bool: 点击是否成功
        """
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
        
        # 如果有截图区域，加上区域偏移
        if screenshot_region:
            real_x += screenshot_region[0]
            real_y += screenshot_region[1]
        
        self.logger.debug(f"坐标计算过程:")
        self.logger.debug(f"OCR原始坐标: ({center_x}, {center_y})")
        if click_offset:
            self.logger.debug(f"点击偏移量: ({click_offset[0]}, {click_offset[1]})")
        self.logger.debug(f"缩放因子: {self.screenshot_helper.get_scale_factor()}")
        if screenshot_region:
            self.logger.debug(f"截图区域偏移: ({screenshot_region[0]}, {screenshot_region[1]})")
        self.logger.debug(f"最终点击坐标: ({real_x}, {real_y})")
        # 执行点击
        try:
            subprocess.run(
                ['adb', '-s', self.bot.device_id, 'shell', 'input', 'tap',
                 str(int(real_x)), str(int(real_y))],
                check=True
            )
            self.logger.info(f"点击坐标: ({real_x}, {real_y})")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"点击操作失败: {e}")
            return False

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
                popups: 弹窗配置列表
        """
        timeout = params.get('timeout', 60)
        check_interval = params.get('check_interval', 1)
        target_text = params.get('target_text')
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
                return True
            
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
                    
                    # 根据action类型选择要点击的目标
                    if action == 'click_first':
                        # 按照patterns的顺序找到第一个匹配的结果
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
                            # 使用公共点击方法
                            if self._click_ocr_result(target_result, screenshot_region):
                                self.logger.info(f"点击弹窗 {popup['name']} 的 {target_result['text']}")
                                popup_handled = True
                                time.sleep(1)  # 等待动画完成
                            else:
                                self.logger.warning(f"点击弹窗 {popup['name']} 失败")
                    else:
                        self.logger.warning(f"未支持的action类型: {action}")
            
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