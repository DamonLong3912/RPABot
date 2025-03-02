from typing import Dict, Any, List
import mysql.connector
from mysql.connector import Error
from rpa.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance
    
    def connect(self, config: Dict[str, Any]):
        """连接数据库
        
        Args:
            config: 数据库配置，包含 host, user, password, database 等
        """
        try:
            self.connection = mysql.connector.connect(
                host=config.get('host', 'localhost'),
                user=config.get('user', 'root'),
                password=config.get('password', ''),
                database=config.get('database'),
                port=config.get('port', 3306)
            )
            logger.info("数据库连接成功")
        except Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
            
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")
            
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