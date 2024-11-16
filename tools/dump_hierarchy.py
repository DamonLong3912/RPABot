#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uiautomator2 as u2
import argparse
import json
import xml.dom.minidom
import os
from datetime import datetime

def dump_hierarchy(output_dir="dumps", format="xml"):
    """
    导出当前设备的UI层级结构
    
    Args:
        output_dir: 输出目录
        format: 输出格式，支持 "xml" 或 "json"
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 连接设备
        d = u2.connect()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "xml":
            # 获取XML格式的层级结构
            xml_content = d.dump_hierarchy()
            
            # 美化XML输出
            dom = xml.dom.minidom.parseString(xml_content)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            # 保存文件
            filename = f"hierarchy_{timestamp}.xml"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(pretty_xml)
                
        elif format == "json":
            # 获取JSON格式的层级结构
            hierarchy = d.jsonrpc.dumpWindowHierarchy(compressed=False)
            
            # 保存文件
            filename = f"hierarchy_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(hierarchy, f, ensure_ascii=False, indent=2)
                
        print(f"已保存UI层级到: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"导出UI层级时发生错误: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="导出Android设备的UI层级结构")
    parser.add_argument("--output-dir", "-o", default="dumps",
                      help="输出目录 (默认: dumps)")
    parser.add_argument("--format", "-f", choices=["xml", "json"], default="xml",
                      help="输出格式 (默认: xml)")
    
    args = parser.parse_args()
    dump_hierarchy(args.output_dir, args.format)

if __name__ == "__main__":
    main() 