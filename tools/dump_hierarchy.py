#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import json
from datetime import datetime
import xml.dom.minidom
import xml.etree.ElementTree as ET

def get_connected_devices():
    """获取所有已连接的设备"""
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行的"List of devices attached"
    devices = []
    for line in lines:
        if line.strip():
            serial = line.split()[0]
            devices.append(serial)
    return devices

def format_xml(xml_content: str) -> str:
    """格式化XML内容，使其更易读"""
    try:
        # 解析XML
        dom = xml.dom.minidom.parseString(xml_content)
        # 格式化输出，每行缩进2个空格
        formatted_xml = dom.toprettyxml(indent='  ')
        # 移除空行
        formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
        return formatted_xml
    except Exception as e:
        print(f"格式化XML时出错: {str(e)}")
        return xml_content

def dump_hierarchy(device_serial=None):
    """
    导出当前界面的UI层级
    
    Args:
        device_serial: 设备序列号，如果有多个设备时必须指定
    """
    try:
        devices = get_connected_devices()
        
        if not devices:
            print("错误: 未找到已连接的设备")
            return
        
        if len(devices) > 1 and not device_serial:
            print("检测到多个设备:")
            for i, serial in enumerate(devices):
                print(f"{i + 1}. {serial}")
            selection = input("请选择设备序号(1-{}): ".format(len(devices)))
            try:
                device_serial = devices[int(selection) - 1]
            except (ValueError, IndexError):
                print("无效的选择")
                return
        
        # 如果只有一个设备且未指定序列号，使用第一个设备
        if not device_serial:
            device_serial = devices[0]

        print(f"使用设备: {device_serial}")

        # 创建输出目录
        output_dir = "hierarchy_dumps"
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"hierarchy_{timestamp}.xml")
        temp_file = "/sdcard/window_dump.xml"
        
        # 执行dump命令，重定向stderr到/dev/null
        dump_cmd = ['adb', '-s', device_serial, 'shell', 'uiautomator', 'dump', temp_file, '2>/dev/null']
        subprocess.run(' '.join(dump_cmd), shell=True)
        
        # 从设备获取XML内容
        cat_cmd = ['adb', '-s', device_serial, 'shell', 'cat', temp_file]
        result = subprocess.run(cat_cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            # 格式化XML
            formatted_xml = format_xml(result.stdout)
            
            # 保存格式化后的XML
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_xml)
            
            file_size = os.path.getsize(output_file)
            print(f"\n✓ UI层级已成功导出到: {output_file}")
            print(f"  文件大小: {file_size/1024:.1f} KB")
            
            # 清理设备上的临时文件
            subprocess.run(['adb', '-s', device_serial, 'shell', 'rm', temp_file], 
                         capture_output=True)
        else:
            print("\n✗ UI层级导出失败")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"导出UI层级时发生错误: {str(e)}")
    except Exception as e:
        print(f"发生未知错误: {str(e)}")

def main():
    # 支持 -h 或 --help 参数显示帮助信息
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("""
使用方法:
    python dump_hierarchy.py [设备序列号]

参数:
    设备序列号   可选，指定要使用的设备。如果有多个设备连接但未指定，将提示选择。

示例:
    python dump_hierarchy.py                    # 自动选择或提示选择设备
    python dump_hierarchy.py 172.16.1.5:38357  # 使用指定的设备
    python dump_hierarchy.py -h                 # 显示此帮助信息
        """.strip())
        return

    # 如果命令行提供了设备序列号，则使用它
    device_serial = sys.argv[1] if len(sys.argv) > 1 else None
    dump_hierarchy(device_serial)

if __name__ == "__main__":
    main() 