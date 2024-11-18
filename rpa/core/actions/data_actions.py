from typing import Dict, Any, List
from .base_action import BaseAction
import json
import yaml
from pathlib import Path

class AppendToListAction(BaseAction):
    """向列表追加数据"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            list_name = params['list']
            data = params['data']
            max_length = params.get('max_length')
            
            # 获取当前列表
            current_list = self.bot.get_variable(list_name, [])
            if not isinstance(current_list, list):
                current_list = []
                
            # 解析数据
            resolved_data = self._resolve_data(data)
            
            # 添加新数据
            current_list.append(resolved_data)
            # 记录日志
            self.logger.debug(f"向列表 {list_name} 追加数据: {resolved_data}")
            
            # 如果设置了max_length，保持列表长度
            if max_length and len(current_list) > max_length:
                current_list = current_list[-max_length:]
            
            # 更新变量
            self.bot.set_variable(list_name, current_list)
            return True
            
        except Exception as e:
            self.logger.error(f"追加数据到列表失败: {str(e)}")
            return False
            
    def _resolve_data(self, data: Any) -> Any:
        """解析数据中的变量引用
        
        处理两种情况:
        1. 简单变量引用: "${variable_name}"
        2. 复杂数据结构: {"key": "${variable_name}", ...}
        """
        if isinstance(data, str):
            # 情况1: 简单变量引用
            if data.startswith("${") and data.endswith("}"):
                var_name = data[2:-1]
                return self.bot.get_variable(var_name)
            return data
            
        elif isinstance(data, dict):
            # 情况2: 复杂数据结构
            resolved_dict = {}
            for key, value in data.items():
                if isinstance(value, str) and "${" in value:
                    # 解析变量引用
                    var_name = value[2:-1]
                    resolved_dict[key] = self.bot.get_variable(var_name)
                else:
                    resolved_dict[key] = value
            return resolved_dict
            
        elif isinstance(data, list):
            # 处理列表中的变量引用
            return [self._resolve_data(item) for item in data]
            
        return data

class ExportDataAction(BaseAction):
    """导出数据到文件"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        # 获取变量名并解析变量引用
        data_var = params['data']
        if isinstance(data_var, str) and "${" in data_var:
            data = self.bot._resolve_variable(data_var)
        else:
            data = self.bot.get_variable(data_var)
            
        format_type = params.get('format', 'json')
        filename = params['filename']
        
        try:
            # 确保输出目录存在
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 记录导出的数据内容
            self.logger.debug(f"准备导出数据: {data}")
            
            # 根据格式类型导出数据
            if format_type == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
            elif format_type == 'yaml':
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True)
                    
            elif format_type == 'csv':
                import csv
                if not isinstance(data, list):
                    raise ValueError("CSV格式只支持列表数据")
                    
                # 获取所有可能的字段
                fields = set()
                for item in data:
                    if isinstance(item, dict):
                        fields.update(item.keys())
                fields = sorted(list(fields))
                
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(data)
                    
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
                
            self.logger.info(f"已导出 {len(data) if isinstance(data, list) else 1} 条记录到: {filename}")
            
            # 如果是调试模式,同时保存一份到调试目录
            if self.bot.debug:
                debug_path = self.bot.debug_dir / f"{self.bot.current_step_index:03d}_导出数据" / output_path.name
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                
                if format_type == 'json':
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                elif format_type == 'yaml':
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f, allow_unicode=True)
                elif format_type == 'csv':
                    with open(debug_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fields)
                        writer.writeheader()
                        writer.writerows(data)
                        
                self.logger.debug(f"调试数据已保存到: {debug_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {str(e)}")
            return False

class SetVariableAction(BaseAction):
    """设置变量值"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            # 支持单个变量设置
            if "name" in params and "value" in params:
                name = params["name"]
                value = self._resolve_value(params["value"])
                self.set_variable(name, value)
                return True
                
            # 支持批量设置变量
            elif "variables" in params:
                variables = params["variables"]
                for name, value in variables.items():
                    resolved_value = self._resolve_value(value)
                    self.set_variable(name, resolved_value)
                return True
                
            else:
                raise ValueError("必须提供 name/value 或 variables 参数")
                
        except Exception as e:
            self.logger.error(f"设置变量失败: {str(e)}")
            return False

    def _resolve_value(self, value: Any) -> Any:
        """解析变量值中的变量引用
        
        Args:
            value: 要解析的值
            
        Returns:
            解析后的值
        """
        # 处理字符串类型的变量引用
        if isinstance(value, str) and "${" in value:
            var_name = value[2:-1]  # 去掉 ${ 和 }
            return self.get_variable(var_name)
            
        # 处理字典类型
        elif isinstance(value, dict):
            return {k: self._resolve_value(v) for k, v in value.items()}
            
        # 处理列表类型
        elif isinstance(value, list):
            return [self._resolve_value(item) for item in value]
            
        return value

class GetVariableAction(BaseAction):
    """获取变量值"""
    
    def execute(self, params: Dict[str, Any]) -> Any:
        try:
            name = params['name']
            default = params.get('default')
            
            # 获取变量值
            value = self.bot.get_variable(name, default)
            
            self.logger.debug(f"获取变量 {name} = {value}")
            return value
            
        except Exception as e:
            self.logger.error(f"获取变量失败: {str(e)}")
            return None

class GetListItemAction(BaseAction):
    """从列表中获取指定索引的项目"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        list_var = params['list']  # 列表变量名
        index = params.get('index', 0)  # 默认取第一项
        save_to = params['save_to']  # 保存结果的变量名
        
        try:
            # 获取列表
            source_list = self.bot.get_variable(list_var)
            if not source_list or not isinstance(source_list, list):
                self.logger.warning(f"列表为空或不是列表类型: {list_var}")
                return False
                
            if index >= len(source_list):
                self.logger.warning(f"索引超出列表范围: {index} >= {len(source_list)}")
                return False
                
            # 获取指定项并保存
            value = source_list[index]
            self.bot.set_variable(save_to, value)
            self.logger.info(f"获取列表项成功: {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"获取列表项失败: {str(e)}")
            return False 