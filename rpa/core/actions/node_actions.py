from typing import Dict, List, Optional, Union
from .base_action import BaseAction
import time
import re
import xml.etree.ElementTree as ET

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
                save_to (str): 可选,保存执行结果到变量
        """
        locate_by = params.get("locate_by", "text")
        text = params.get("text", "")
        match_type = params.get("match_type", "exact")
        timeout = params.get("timeout", 10)
        interval = params.get("interval", 0.5)
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
                    # 获取元素中心点坐标并点击
                    bounds = selector.info.get('bounds', {})
                    center_x = (bounds.get('left', 0) + bounds.get('right', 0)) // 2
                    center_y = (bounds.get('top', 0) + bounds.get('bottom', 0)) // 2
                    
                    # 使用坐标点击而不是元素点击
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
            return {} if len(attributes) > 1 else ""
            
        except Exception as e:
            self.logger.error(f"通过路径获取节点值失败: {str(e)}")
            return {} if len(attributes) > 1 else ""
