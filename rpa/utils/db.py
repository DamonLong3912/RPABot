from typing import Dict, Any, List
import mysql.connector
from mysql.connector import Error
from rpa.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance
    
    def __init__(self):
        self.connection = None
        self.connected = False
    
    def connect(self, config: Dict[str, Any]):
        """连接数据库
        
        Args:
            config: 数据库配置，包含 host, user, password, database 等
        """
        if self.connected:
            return
        try:
            self.connection = mysql.connector.connect(
                host=config.get('host', 'localhost'),
                user=config.get('user', 'root'),
                password=config.get('password', ''),
                database=config.get('database'),
                port=config.get('port', 3306)
            )
            logger.info("数据库连接成功")
            self.connected = True
        except Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
            
    def disconnect(self):
        """断开数据库连接"""
        if not self.connected:
            return
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")
            self.connected = False
            
    def execute(self, query: str, params: tuple = None) -> Any:
        """执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.lower().startswith('select'):
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = cursor.rowcount
                
            cursor.close()
            return result
            
        except Error as e:
            logger.error(f"执行SQL失败: {str(e)}")
            raise
            
    def insert_flow_result(self, flow_name: str, status: str, message: str = None):
        """记录流程执行结果
        
        Args:
            flow_name: 流程名称
            status: 执行状态 (success/failed)
            message: 执行消息
        """
        query = """
        INSERT INTO flow_results (flow_name, status, message, create_time) 
        VALUES (%s, %s, %s, NOW())
        """
        self.execute(query, (flow_name, status, message))

    @classmethod
    def init_from_config(cls, config_path='config.yaml'):
        """从配置文件初始化数据库连接
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            DatabaseManager: 数据库管理器实例
        """
        try:
            # 导入这里避免循环导入
            from run import load_config
            
            config = load_config(config_path)
            db_config = config.get('database')
            
            if db_config:
                db = cls.get_instance()
                db.connect(db_config)
                logger.info("数据库连接已初始化")
                
                # 注册应用退出时的清理函数
                import atexit
                
                @atexit.register
                def cleanup_db():
                    try:
                        db.disconnect()
                        logger.info("数据库连接已关闭")
                    except Exception as e:
                        logger.error(f"关闭数据库连接失败: {str(e)}")
                
                return db
            else:
                logger.warning("配置文件中未找到数据库配置")
                return None
        except Exception as e:
            logger.error(f"初始化数据库连接失败: {str(e)}")
            return None 