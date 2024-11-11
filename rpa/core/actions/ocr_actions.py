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
            
        debug_dir = debug_dir or self.bot.debug_dir / step_name
        debug_dir.mkdir(exist_ok=True)
        
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

    def wait_for_ocr_text(self, params: Dict[str, Any]) -> bool:
        """等待指定文字出现
        
        Args:
            params:
                text: 要等待的文字
                timeout: 超时时间(秒)
                check_interval: 检查间隔(秒)
                screenshot_region: 截图区域[x1,y1,x2,y2]
        """
        text = params['text']
        timeout = params.get('timeout', 10)
        check_interval = params.get('check_interval', 2)
        region = params.get('screenshot_region')
        
        self.logger.info(f"等待文字出现: {text}, 检查间隔: {check_interval}秒")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 获取截图
            screenshot = self.screenshot_helper.take_screenshot(
                save_path="temp",
                region=region
            )
            
            # OCR识别
            results = self.ocr_helper.extract_text(
                screenshot,
                keywords=[text]
            )
            
            # 保存调试信息
            self._save_debug_info(
                f"wait_for_ocr_text_{int(time.time())}", 
                screenshot, 
                results,
                region
            )
            
            if results:
                self.logger.info(f"找到目标文字: {text}")
                return True
            
            self.logger.debug(f"未找到文字: {text}, 等待 {check_interval} 秒后重试")
            time.sleep(check_interval)
        
        self.logger.warning(f"等待超时: {text}")
        return False
        
    def click_by_ocr(self, params: Dict[str, Any]) -> bool:
        """通过OCR识别文字并点击
        
        Args:
            params:
                text: 要点击的文字
                timeout: 等待超时(秒)
                retry_times: 重试次数
                check_interval: 检查间隔(秒)
                screenshot_region: 截图区域[x1,y1,x2,y2]
        """
        text = params['text']
        timeout = params.get('timeout', 5)
        retry_times = params.get('retry_times', 3)
        check_interval = params.get('check_interval', 2)
        region = params.get('screenshot_region')
        
        for attempt in range(retry_times):
            # 获取截图
            screenshot = self.screenshot_helper.take_screenshot(
                save_path="temp",
                region=region
            )
            
            # OCR识别
            results = self.ocr_helper.extract_text(
                screenshot,
                keywords=[text]
            )
            
            if results:
                # 获取文字中心点坐标
                box = results[0]['box']
                center_x = (box[0][0] + box[2][0]) // 2
                center_y = (box[0][1] + box[2][1]) // 2
                
                # 点击
                self.bot.device.click(center_x, center_y)
                return True
            
            if attempt < retry_times - 1:  # 不是最后一次尝试
                self.logger.debug(f"未找到文字: {text}, 等待 {check_interval} 秒后重试")
                time.sleep(check_interval)
        
        return False

    def wait_and_click_ocr_text(self, params: Dict[str, Any]) -> bool:
        """等待指定文字出现并点击"""
        text = params['text']
        timeout = params.get('timeout', 30)
        check_interval = params.get('check_interval', 2)
        region = params.get('screenshot_region')
        
        self.logger.info(f"等待文字出现: {text}, 检查间隔: {check_interval}秒")
        start_time = time.time()
        
        # 创建步骤专属的调试目录
        if self.bot.debug:
            step_debug_dir = self.bot.debug_dir / f"等待并点击{text}"
            step_debug_dir.mkdir(exist_ok=True)
            attempt = 1
        
        while time.time() - start_time < timeout:
            # 获取截图
            self.logger.debug(f"正在截图...")
            screenshot = self.screenshot_helper.take_screenshot(
                save_path=str(step_debug_dir / "screenshots") if self.bot.debug else "temp",
                region=region,
                filename_prefix=f"attempt_{attempt}"
            )
            self.logger.debug(f"截图已保存: {screenshot}")
            
            # OCR识别
            self.logger.debug(f"开始OCR识别...")
            results = self.ocr_helper.extract_text(
                screenshot,
                keywords=[text]
            )
            self.logger.debug(f"OCR识别结果: {results}")
            
            # 保存调试信息到步骤目录下
            if self.bot.debug:
                self._save_debug_info(
                    f"attempt_{attempt}", 
                    screenshot, 
                    results,
                    region,
                    debug_dir=step_debug_dir
                )
                attempt += 1
            
            if results:
                self.logger.info(f"找到目标文字: {text}")
                # 找到文字，执行点击
                box = results[0]['box']
                
                # 计算相对于裁剪区域的中心点（在缩放图片上的坐标）
                center_x = (box[0][0] + box[2][0]) // 2
                center_y = (box[0][1] + box[2][1]) // 2
                
                # 转换为实际坐标
                real_x, real_y = self.screenshot_helper.get_real_coordinates(center_x, center_y)
                
                # 如果有区域设置，加上偏移量得到实际屏幕坐标
                if region:
                    x_offset, y_offset = region[0], region[1]
                    screen_x = real_x + x_offset
                    screen_y = real_y + y_offset
                    self.logger.debug(f"区域偏移: ({x_offset}, {y_offset})")
                    self.logger.debug(f"缩放坐标: ({center_x}, {center_y})")
                    self.logger.debug(f"实际坐标: ({screen_x}, {screen_y})")
                else:
                    screen_x, screen_y = real_x, real_y
                
                # 点击
                subprocess.run(
                    ['adb', '-s', self.bot.device_id, 'shell', 'input', 'tap', 
                     str(int(screen_x)), str(int(screen_y))],
                    check=True
                )
                self.logger.info(f"点击坐标: ({screen_x}, {screen_y})")
                return True
            
            self.logger.debug(f"未找到文字: {text}, {check_interval}秒后重试")
            time.sleep(check_interval)
        
        self.logger.warning(f"等待超时: {text}")
        return False