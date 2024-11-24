from typing import Dict, List, Optional, Union, Any
from .base_action import BaseAction
import time
import re
import xml.etree.ElementTree as ET
import os
from datetime import datetime

class GetNodeDescendantsContentAction(BaseAction):
    """获取指定区域内的节点内容"""
    
    def execute(self, params: Dict) -> List[str]:
        """执行动作
        
        Args:
            params: 动作参数
                bounds: 目标区域范围 [left, top, right, bottom]
                content_desc_pattern: 内容匹配模式(正则表达式)
                save_to: 保存结果的变量名
        """
        try:
            bounds = params.get("bounds")
            if not bounds or len(bounds) != 4:
                raise ValueError("必须提供有效的bounds参数: [left, top, right, bottom]")
            
            pattern = params.get("content_desc_pattern")
            
            # 获取区域内的所有节点内容
            results = self._collect_nodes_in_bounds(bounds, pattern)
            
            # 保存结果
            if "save_to" in params:
                self.logger.info(f"获取到节点内容: {results}")
                self.set_variable(params["save_to"], results)
                
            return results
            
        except Exception as e:
            self.logger.error(f"获取节点内容失败: {str(e)}")
            return []

    def _check_node_in_bounds(self, node_bounds: Dict, target_bounds: List[int]) -> bool:
        """检查节点是否在指定区域内"""
        try:
            return (node_bounds.get('left', 0) >= target_bounds[0] and
                    node_bounds.get('top', 0) >= target_bounds[1] and 
                    node_bounds.get('right', 0) <= target_bounds[2] and
                    node_bounds.get('bottom', 0) <= target_bounds[3])
        except:
            return False

    def _collect_nodes_in_bounds(self, bounds: List[int], pattern: Optional[str] = None) -> List[str]:
        """收集指定区域内符合条件的节点内容"""
        # 用字典按drawing_order分组存储节点内容
        order_groups = {}
        
        try:
            # 获取所有节点
            nodes = self.ui_animator.xpath('//*//*[@content-desc]').all()
            
            # 遍历所有节点
            for node in nodes:
                attrs = node.attrib
                
                # 解析bounds
                bounds_str = attrs.get('bounds', '')
                if not bounds_str:
                    continue
                    
                try:
                    bounds_parts = bounds_str.strip('[]').split('][')
                    x1, y1 = map(int, bounds_parts[0].split(','))
                    x2, y2 = map(int, bounds_parts[1].split(','))
                    node_bounds = {
                        'left': x1,
                        'top': y1,
                        'right': x2,
                        'bottom': y2
                    }
                except:
                    continue
                
                # 检查bounds
                if not self._check_node_in_bounds(node_bounds, bounds):
                    continue
                    
                # 获取content-desc
                content = attrs.get('content-desc', '')
                if not content:
                    continue
                    
                # 检查pattern
                if pattern and not re.match(pattern, str(content)):
                    continue
                
                # 获取drawing-order并分组
                drawing_order = int(attrs.get('drawing-order', '0'))
                if drawing_order not in order_groups:
                    order_groups[drawing_order] = []
                order_groups[drawing_order].append(content)
            
            # 如果有分组,返回drawing_order最小的那组内容
            if order_groups:
                min_order = min(order_groups.keys())
                return order_groups[min_order]
            
            return []
            
        except Exception as e:
            self.logger.error(f"收集节点时出错: {str(e)}")
            return []

class WaitAndClickNodeAction(BaseAction):
    """等待并点击指定节点"""
    
    def execute(self, params: Dict) -> bool:
        """
        等待并点击符合条件的节点

        Args:
            params: 动作参数
                locate_by (str): 定位方式
                    - "text": 通过文本定位
                    - "description": 通过content-description定位
                    - "resourceId": 通过resource-id定位
                    - "className": 通过class name定位
                text (str): 要匹配的文本
                match_type (str): 匹配方式
                    - "exact": 精确匹配
                    - "contains": 包含匹配
                timeout (int): 超时时间(秒)
                interval (float): 检查间隔(秒)
                bounds (List[int], optional): 优先区域范围 [left, top, right, bottom]
                save_to (str): 可选,保存执行结果到变量
        """
        locate_by = params.get("locate_by", "text")
        text = params.get("text", "")
        match_type = params.get("match_type", "exact")
        timeout = params.get("timeout", 10)
        interval = params.get("interval", 0.5)
        bounds = params.get("bounds")
        save_to = params.get("save_to")
        
        # 解析text中的变量引用
        if isinstance(text, str) and "${" in text:
            var_name = text[2:-1]  # 去掉 ${ 和 }
            text = self.get_variable(var_name)
            
        # 检查text是否为None或空
        if not text:
            self.logger.error("text参数不能为空")
            if save_to:
                self.set_variable(save_to, False)
            return False
            
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                # 构建选择器
                selector = self._build_selector(locate_by, text, match_type)
                
                # 检查元素是否存在
                if selector.exists:
                    # 获取元素信息
                    element_info = selector.info
                    if not element_info or 'bounds' not in element_info:
                        self.logger.warning("无法获取元素bounds信息")
                        time.sleep(interval)
                        continue
                        
                    element_bounds = element_info['bounds']
                    
                    # 如果指定了bounds，检查元素是否在bounds内
                    if bounds:
                        if not self._check_node_in_bounds(element_bounds, bounds):
                            # 如果不在指定区域内，尝试查找下一个匹配元素
                            xml_content = self.ui_animator.dump_hierarchy()
                            root = ET.fromstring(xml_content)
                            
                            # 根据定位方式构建xpath
                            if locate_by == "text":
                                xpath = f".//*[@text='{text}']" if match_type == "exact" else f".//*[contains(@text,'{text}')]"
                            elif locate_by == "description":
                                xpath = f".//*[@content-desc='{text}']" if match_type == "exact" else f".//*[contains(@content-desc,'{text}')]"
                            else:
                                raise ValueError(f"不支持的定位方式: {locate_by}")
                            
                            # 查找所有匹配的元素
                            matching_elements = root.findall(xpath)
                            
                            # 遍历找到第一个在bounds内的元素
                            for element in matching_elements:
                                bounds_str = element.get('bounds', '')
                                if not bounds_str:
                                    continue
                                    
                                try:
                                    bounds_parts = bounds_str.strip('[]').split('][')
                                    x1, y1 = map(int, bounds_parts[0].split(','))
                                    x2, y2 = map(int, bounds_parts[1].split(','))
                                    node_bounds = {
                                        'left': x1,
                                        'top': y1,
                                        'right': x2,
                                        'bottom': y2
                                    }
                                    
                                    if self._check_node_in_bounds(node_bounds, bounds):
                                        element_bounds = node_bounds
                                        break
                                except:
                                    continue
                            else:
                                # 没找到在bounds内的元素，继续等待
                                time.sleep(interval)
                                continue
                    
                    # 计算点击坐标
                    center_x = (element_bounds['left'] + element_bounds['right']) // 2
                    center_y = (element_bounds['top'] + element_bounds['bottom']) // 2
                    
                    self.ui_animator.click(center_x, center_y)
                    if save_to:
                        self.set_variable(save_to, True)
                    return True
                    
            except Exception as e:
                self.logger.warning(f"点击元素时出错: {str(e)}")
                
            time.sleep(interval)

        self.logger.error(f"未能在 {timeout} 秒内找到并点击符合条件的元素: {text}")
        if save_to:
            self.set_variable(save_to, False)
        return False

    def _check_node_in_bounds(self, node_bounds: Dict, target_bounds: List[int]) -> bool:
        """检查节点是否在指定区域内"""
        try:
            return (node_bounds['left'] >= target_bounds[0] and
                    node_bounds['top'] >= target_bounds[1] and 
                    node_bounds['right'] <= target_bounds[2] and
                    node_bounds['bottom'] <= target_bounds[3])
        except:
            return False

    def _build_selector(self, locate_by: str, text: str, match_type: str) -> object:
        """构建元素选择器"""
        if locate_by == "text":
            if match_type == "exact":
                return self.ui_animator(text=text)
            else:
                return self.ui_animator(textContains=text)
                
        elif locate_by == "description":
            if match_type == "exact":
                return self.ui_animator(description=text)
            else:
                return self.ui_animator(descriptionContains=text)
            
        else:
            raise ValueError(f"不支持的定位方式: {locate_by}")

class GetNodeByPathAction(BaseAction):
    """通过路径获取节点值"""
    
    def execute(self, params: Dict) -> Dict:
        try:
            # 获取并验证参数
            package = params.get("package")
            if not package:
                raise ValueError("必须提供package参数")
                
            index_paths = params.get("index_path", [])
            if not index_paths:
                raise ValueError("必须提供index_path参数")
            
            # 确保index_paths是二维数组
            if not isinstance(index_paths[0], list):
                index_paths = [index_paths]
                
            attributes = params.get("attributes", ["text", "content-desc"])
            pattern = params.get("pattern")  # 可选的匹配模式
            
            # 获取当前UI树
            xml_content = self.ui_animator.dump_hierarchy()
            root = ET.fromstring(xml_content)
            
            # 首先找到package对应的根节点
            package_nodes = root.findall(f".//*[@package='{package}']")
            
            if not package_nodes:
                self.logger.warning(f"未找到package为{package}的节点")
                return {}
            
            # 遍历所有可能的路径
            for path_index, index_path in enumerate(index_paths):
                
                try:
                    # 获取第一个package节点作为起点
                    current_node = package_nodes[0]
                    
                    # 按照index path逐层查找
                    for i, target_index in enumerate(index_path):
                        children = list(current_node)
                        if not children:
                            break
                        
                        # 查找index属性匹配的子节点
                        found = False
                        for child in children:
                            if child.get("index") == str(target_index):
                                current_node = child
                                found = True
                                break
                        if not found:
                            break
                    
                    # 如果成功找到节点
                    if found:
                        # 如果只请求了一个属性
                        if len(attributes) == 1:
                            value = current_node.get(attributes[0], "")
                            # 如果有pattern，检查是否匹配
                            if pattern:
                                import re
                                if not re.match(pattern, str(value)):
                                    continue
                            
                            if "save_to" in params:
                                self.logger.info(f"将值 {value} 保存到变量 {params['save_to']}")
                                self.set_variable(params["save_to"], value)
                                
                            return value
                        
                        # 如果请求了多个属性
                        else:
                            result = {}
                            for attr in attributes:
                                result[attr] = current_node.get(attr, "")
                            
                            # 如果有pattern，检查第一个属性是否匹配
                            if pattern and attributes:
                                first_value = result[attributes[0]]
                                if not re.match(pattern, str(first_value)):
                                    continue
                            
                            if "save_to" in params:
                                self.set_variable(params["save_to"], result)
                            return result
                            
                except Exception as e:
                    continue
            
            self.logger.error("所有路径都未找到匹配的节点")
            
            # 保存UI层级结构到dumps目录
            try:
                dumps_dir = "dumps"
                os.makedirs(dumps_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dump_file = os.path.join(dumps_dir, f"hierarchy_dump_{timestamp}.xml")
                
                with open(dump_file, "w", encoding="utf-8") as f:
                    f.write(xml_content)
                    
                self.logger.info(f"UI层级结构已保存到: {dump_file}")
            except Exception as dump_err:
                self.logger.error(f"保存UI层级结构失败: {str(dump_err)}")
            
            return {} if len(attributes) > 1 else ""
            
        except Exception as e:
            self.logger.error(f"通过路径获取节点值失败: {str(e)}")
            return {} if len(attributes) > 1 else ""

class GetListItemBoundsAction(BaseAction):
    """获取列表项的bounds"""
    def execute(self, params: Dict[str, Any]) -> bool:
        list_id = params['list_id']
        save_to = params['save_to']
        
        try:
            # 获取当前UI树
            xml_content = self.ui_animator.dump_hierarchy()
            root = ET.fromstring(xml_content)
            
            # 找到列表容器节点
            list_nodes = root.findall(f".//*[@resource-id='{list_id}']")
            if not list_nodes:
                self.logger.error(f"未找到列表节点: {list_id}")
                return False
            
            list_node = list_nodes[0]
            
            # 获取直接子节点
            bounds_list = []
            for child in list_node:
                bounds = child.get('bounds')
                if bounds:
                    # 解析bounds字符串 "[x1,y1][x2,y2]"
                    bounds_parts = bounds.strip('[]').split('][')
                    x1, y1 = map(int, bounds_parts[0].split(','))
                    x2, y2 = map(int, bounds_parts[1].split(','))
                    bounds_list.append([x1, y1, x2, y2])
            
            # 保存结果
            self.bot.set_variable(save_to, bounds_list)
            self.logger.info(f"获取到 {len(bounds_list)} 个列表项bounds")
            return True
            
        except Exception as e:
            self.logger.error(f"获取列表项bounds失败: {str(e)}")
            return False
