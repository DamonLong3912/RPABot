from typing import Dict, Any, List, Tuple
from .base_action import BaseAction
import json
import yaml
from pathlib import Path
from datetime import datetime
import mysql.connector
import sqlite3

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
        """导出数据
        
        Args:
            params:
                data: 数据变量名
                format: 导出格式(json)
                filepath: 输出目录路径
                filename: 文件名(支持变量引用)
                mode: 导出模式(append)
        """
        try:
            data_var = params['data']
            format = params.get('format', 'json')
            filepath = params['filepath']
            filename = params['filename']
            
            # 获取要导出的数据
            data = self.bot.get_variable(data_var)
            if not data:
                return True

            # 解析文件名中的变量引用
            if "${" in filename:
                var_name = filename[filename.index("${") + 2:filename.index("}")]
                var_value = self.bot.get_variable(var_name)
                if var_value is None:
                    raise ValueError(f"变量 {var_name} 未定义")
                filename = filename.replace("${" + var_name + "}", str(var_value))
            
            # 确保输出目录存在
            output_dir = Path(filepath)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 处理文件路径
            file_path = output_dir / filename

            if format == 'json':
                existing_data = []
                if file_path.exists():
                    # 读取现有数据
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            existing_data = json.load(f)
                        except json.JSONDecodeError:
                            self.logger.warning(f"文件 {file_path} 内容无效，将重新创建")
                            existing_data = []
                
                # 合并数据
                if isinstance(data, list):
                    existing_data.extend(data)
                else:
                    existing_data.append(data)

                # 写入所有数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"已导出 {len(data) if isinstance(data, list) else 1} 条记录到 {file_path}")
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

class SetTimestampAction(BaseAction):
    """设置时间戳变量"""
    
    def execute(self, params: Dict[str, Any]) -> bool:
        try:
            save_to = params['save_to']
            format = params.get('format', '%Y%m%d_%H%M%S')
            
            # 生成时间戳
            timestamp = datetime.now().strftime(format)
            
            # 保存到变量
            self.bot.set_variable(save_to, timestamp)
            self.logger.info(f"设置时间戳: {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置时间戳失败: {str(e)}")
            return False 

class ExportToDBAction(BaseAction):
    """导出数据到数据库(支持MySQL和SQLite)"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.config = self._load_config()
        self.use_local = self.config.get("use_local", False)
        
    def _load_config(self) -> Dict:
        """加载数据库配置"""
        config_path = Path("config/database.yaml")
        if not config_path.exists():
            raise FileNotFoundError("数据库配置文件不存在")
            
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def _ensure_sqlite_db(self) -> None:
        """确保SQLite数据库和表存在"""
        db_path = Path(self.config["sqlite"]["database"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建时区相关函数
        conn.create_function('LOCAL_TIMESTAMP', 0, lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 创建表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gas_stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_name TEXT NOT NULL,
                station_address TEXT NOT NULL,
                oil_92_gun_price REAL,
                oil_92_platform_price REAL,
                oil_92_guns TEXT,
                oil_95_gun_price REAL,
                oil_95_platform_price REAL,
                oil_95_guns TEXT,
                created_at TIMESTAMP DEFAULT (LOCAL_TIMESTAMP()),
                updated_at TIMESTAMP DEFAULT (LOCAL_TIMESTAMP()),
                UNIQUE(station_name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """获取数据库连接"""
        if self.use_local:
            self._ensure_sqlite_db()
            db_path = Path(self.config["sqlite"]["database"])
            conn = sqlite3.connect(db_path)
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        else:
            return mysql.connector.connect(**self.config["mysql"])
    
    def execute(self, params: Dict[str, Any]) -> bool:
        """执行数据导出"""
        try:
            data_var = params["data"]
            raw_data = self.bot.get_variable(data_var)
            if not raw_data:
                return True
                
            stations = self._transform_data(raw_data)
            conn = self._get_connection()
            
            try:
                if self.use_local:
                    self._execute_sqlite(conn, stations)
                else:
                    self._execute_mysql(conn, stations)
                    
                conn.commit()
                self.logger.info(f"成功处理 {len(stations)} 条记录")
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"导出数据失败: {str(e)}")
            return False
    
    def _prepare_update_fields(self, station: Dict, existing: Dict) -> Tuple[List[str], Dict, bool]:
        """准备更新字段
        
        Args:
            station: 新数据
            existing: 已存在的数据
            
        Returns:
            Tuple[List[str], Dict, bool]: (更新字段列表, 更新值字典, 是否有价格更新)
        """
        update_fields = []
        update_values = {"id": existing["id"]}
        has_price_update = False
        
        # 地址字段
        if station.get("station_address") and station["station_address"] != existing["station_address"]:
            update_fields.append("station_address = %(station_address)s")
            update_values["station_address"] = station["station_address"]
        
        # 92#油价相关字段
        if station.get("oil_92_gun_price") is not None:
            if existing["oil_92_gun_price"] != station["oil_92_gun_price"]:
                update_fields.append("oil_92_gun_price = %(oil_92_gun_price)s")
                update_values["oil_92_gun_price"] = station["oil_92_gun_price"]
                has_price_update = True
        
        if station.get("oil_92_platform_price") is not None:
            if existing["oil_92_platform_price"] != station["oil_92_platform_price"]:
                update_fields.append("oil_92_platform_price = %(oil_92_platform_price)s")
                update_values["oil_92_platform_price"] = station["oil_92_platform_price"]
                has_price_update = True
        
        # 92#油枪
        if station.get("oil_92_guns"):
            guns = json.loads(station["oil_92_guns"])
            if guns and guns != json.loads(existing["oil_92_guns"] or "[]"):
                update_fields.append("oil_92_guns = %(oil_92_guns)s")
                update_values["oil_92_guns"] = station["oil_92_guns"]
        
        # 95#油价相关字段
        if station.get("oil_95_gun_price") is not None:
            if existing["oil_95_gun_price"] != station["oil_95_gun_price"]:
                update_fields.append("oil_95_gun_price = %(oil_95_gun_price)s")
                update_values["oil_95_gun_price"] = station["oil_95_gun_price"]
                has_price_update = True
        
        if station.get("oil_95_platform_price") is not None:
            if existing["oil_95_platform_price"] != station["oil_95_platform_price"]:
                update_fields.append("oil_95_platform_price = %(oil_95_platform_price)s")
                update_values["oil_95_platform_price"] = station["oil_95_platform_price"]
                has_price_update = True
        
        # 95#油枪
        if station.get("oil_95_guns"):
            guns = json.loads(station["oil_95_guns"])
            if guns and guns != json.loads(existing["oil_95_guns"] or "[]"):
                update_fields.append("oil_95_guns = %(oil_95_guns)s")
                update_values["oil_95_guns"] = station["oil_95_guns"]
        
        return update_fields, update_values, has_price_update
    
    def _execute_sqlite(self, conn: sqlite3.Connection, stations: List[Dict]) -> None:
        """执行SQLite数据操作"""
        cursor = conn.cursor()
        
        for station in stations:
            # 验证必要字段
            if not station.get("station_name"):
                self.logger.warning("跳过无效数据: 缺少加油站名称")
                continue
            
            # 检查是否存在该加油站
            cursor.execute(
                "SELECT * FROM gas_stations WHERE station_name = ?",
                (station["station_name"],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 转换为字典格式
                columns = [col[0] for col in cursor.description]
                existing = dict(zip(columns, existing))
                
                # 准备更新字段
                update_fields, update_values, has_price_update = self._prepare_update_fields(station, existing)
                
                # 只有在有字段需要更新时才执行更新
                if update_fields:
                    # 转换MySQL风格的参数占位符为SQLite风格
                    update_fields = [f.replace('%(', ':').replace(')s', '') for f in update_fields]
                    
                    # 只有在价格有更新时才更新时间戳
                    if has_price_update:
                        update_fields.append("updated_at = datetime('now', 'localtime')")
                    
                    update_sql = f"""
                        UPDATE gas_stations SET
                            {', '.join(update_fields)}
                        WHERE id = :id
                    """
                    cursor.execute(update_sql, update_values)
                    self.logger.info(f"更新加油站数据: {station['station_name']}")
                else:
                    self.logger.info(f"加油站数据无变化: {station['station_name']}")
                    
            else:
                # 验证新记录的必要字段
                if not station.get("station_address"):
                    self.logger.warning(f"跳过新增数据: 加油站 {station['station_name']} 缺少地址信息")
                    continue
                    
                # 插入新记录
                insert_sql = """
                    INSERT INTO gas_stations (
                        station_name, station_address,
                        oil_92_gun_price, oil_92_platform_price, oil_92_guns,
                        oil_95_gun_price, oil_95_platform_price, oil_95_guns,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
                """
                cursor.execute(insert_sql, (
                    station["station_name"],
                    station["station_address"],
                    station["oil_92_gun_price"],
                    station["oil_92_platform_price"],
                    station["oil_92_guns"],
                    station["oil_95_gun_price"],
                    station["oil_95_platform_price"],
                    station["oil_95_guns"]
                ))
                self.logger.info(f"插入新加油站: {station['station_name']}")
    
    def _execute_mysql(self, conn: mysql.connector.connection.MySQLConnection, stations: List[Dict]) -> None:
        """执行MySQL数据操作"""
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 首先确保表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gas_stations (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    station_name VARCHAR(100) NOT NULL,
                    station_address VARCHAR(255) NOT NULL,
                    oil_92_gun_price DECIMAL(10,2),
                    oil_92_platform_price DECIMAL(10,2),
                    oil_92_guns JSON,
                    oil_95_gun_price DECIMAL(10,2),
                    oil_95_platform_price DECIMAL(10,2),
                    oil_95_guns JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_name_address (station_name)
                )
            """)
            conn.commit()
            
            for station in stations:
                # 验证必要字段
                if not station.get("station_name"):
                    self.logger.warning("跳过无效数据: 缺少加油站名称")
                    continue
                    
                # 检查是否存在该加油站
                cursor.execute(
                    "SELECT * FROM gas_stations WHERE station_name = %(station_name)s",
                    {"station_name": station["station_name"]}
                )
                existing = cursor.fetchone()
                
                if existing:
                    # 准备更新字段
                    update_fields, update_values, has_price_update = self._prepare_update_fields(station, existing)
                    
                    # 只有在有字段需要更新时才执行更新
                    if update_fields:
                        # 只有在价格有更新时才更新时间戳
                        if has_price_update:
                            update_fields.append("updated_at = CURRENT_TIMESTAMP")
                        
                        update_sql = f"""
                            UPDATE gas_stations SET
                                {', '.join(update_fields)}
                            WHERE id = %(id)s
                        """
                        cursor.execute(update_sql, update_values)
                        self.logger.info(f"更新加油站数据: {station['station_name']}")
                    else:
                        self.logger.info(f"加油站数据无变化: {station['station_name']}")
                    
                else:
                    # 验证新记录的必要字段
                    if not station.get("station_address"):
                        self.logger.warning(f"跳过新增数据: 加油站 {station['station_name']} 缺少地址信息")
                        continue
                    
                    # 插入新记录
                    insert_sql = """
                        INSERT INTO gas_stations (
                            station_name, station_address,
                            oil_92_gun_price, oil_92_platform_price, oil_92_guns,
                            oil_95_gun_price, oil_95_platform_price, oil_95_guns
                        ) VALUES (
                            %(station_name)s, %(station_address)s,
                            %(oil_92_gun_price)s, %(oil_92_platform_price)s, %(oil_92_guns)s,
                            %(oil_95_gun_price)s, %(oil_95_platform_price)s, %(oil_95_guns)s
                        )
                    """
                    cursor.execute(insert_sql, station)
                    self.logger.info(f"插入新加油站: {station['station_name']}")
            
            conn.commit()
            self.logger.info(f"成功处理 {len(stations)} 条记录")
            
        except Exception as e:
            self.logger.error(f"MySQL操作失败: {str(e)}")
            conn.rollback()
            raise
    
    def _transform_data(self, raw_data: List[Dict]) -> List[Dict]:
        """转换数据格式以适应数据库表结构"""
        transformed = []
        for item in raw_data:
            # 检查必要字段
            if not item.get("name") or not item.get("address"):
                self.logger.warning(f"跳过无效数据: 缺少必要字段 name 或 address")
                continue
            
            station = {
                "station_name": item["name"],
                "station_address": item["address"],
                "oil_92_gun_price": self._parse_price(item.get("station_price_92")),
                "oil_92_platform_price": self._parse_price(item.get("didi_price_92")),
                "oil_92_guns": json.dumps(item.get("gun_numbers_92", []), ensure_ascii=False),
                "oil_95_gun_price": self._parse_price(item.get("station_price_95")),
                "oil_95_platform_price": self._parse_price(item.get("didi_price_95")),
                "oil_95_guns": json.dumps(item.get("gun_numbers_95", []), ensure_ascii=False),
            }
            transformed.append(station)
        return transformed
    
    def _parse_price(self, price_str: str) -> float:
        """解析价格字符串"""
        if not price_str:
            return None
        try:
            return float(price_str.replace("油站价¥", "").replace("¥", "").strip())
        except (ValueError, AttributeError):
            return None