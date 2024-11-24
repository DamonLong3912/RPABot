#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import argparse
from lxml import etree
from typing import List, Dict, Tuple

def get_node_path(node: etree._Element, root: etree._Element) -> List[int]:
    """获取节点到根节点的索引路径"""
    path = []
    current = node
    package = node.get('package')
    
    while current != root:
        parent = current.getparent()
        if parent is None:
            break
            
        # 获取当前节点的index
        index = int(current.get('index', 0))
        path.insert(0, index)
        current = parent
    
    # 如果路径不为空,移除第一个index(对应最外层的package匹配节点)
    if path:
        path.pop(0)
        
    return path

def find_nodes_by_text(root: etree._Element, text: str) -> List[Tuple[etree._Element, str, str, str]]:
    """查找包含指定文本的节点
    
    Args:
        root: XML根节点
        text: 要查找的文本
        
    Returns:
        包含匹配节点、匹配属性、匹配值和匹配类型的元组列表
    """
    results = []
    
    # 遍历所有节点
    for node in root.findall(".//node"):
        # 检查text属性
        node_text = node.get("text", "")
        if node_text == text:
            results.append((node, "text", node_text, "exact"))
        elif text in node_text:
            results.append((node, "text", node_text, "contains"))
            
        # 检查content-desc属性    
        content_desc = node.get("content-desc", "")
        if content_desc == text:
            results.append((node, "content-desc", content_desc, "exact"))
        elif text in content_desc:
            results.append((node, "content-desc", content_desc, "contains"))
            
    # 优先返回精确匹配的结果
    exact_matches = [(n, a, v, t) for n, a, v, t in results if t == "exact"]
    contains_matches = [(n, a, v, t) for n, a, v, t in results if t == "contains"]
    
    return exact_matches + contains_matches

def format_node_info(node: etree._Element, attribute: str, value: str, match_type: str, path: List[int], package: str) -> Dict:
    """格式化节点信息为get_node_by_path参数格式"""
    pattern = None
    if match_type == "exact":
        pattern = f"^{re.escape(value)}$"
    elif match_type == "contains":
        pattern = f".*{re.escape(value)}.*"
        
    return {
        "package": package,
        "index_path": path,
        "attributes": [attribute],
        "pattern": pattern,
        "matched_value": value,
        "match_type": match_type
    }

def main():
    parser = argparse.ArgumentParser(description="从UI层级文件中查找指定文本的节点路径")
    parser.add_argument("hierarchy_file", help="UI层级文件路径")
    parser.add_argument("text", help="要查找的文本")
    args = parser.parse_args()
    
    try:
        # 解析XML文件
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(args.hierarchy_file, parser)
        root = tree.getroot()
        
        # 查找匹配节点
        matched_nodes = find_nodes_by_text(root, args.text)
        
        if not matched_nodes:
            print(f"\n未找到匹配文本: {args.text}")
            return
            
        print(f"\n找到 {len(matched_nodes)} 个匹配节点:")
        
        # 按匹配类型分组
        exact_matches = [(n, a, v, t) for n, a, v, t in matched_nodes if t == "exact"]
        contains_matches = [(n, a, v, t) for n, a, v, t in matched_nodes if t == "contains"]
        
        # 输出精确匹配结果
        if exact_matches:
            print("\n=== 精确匹配 ===")
            for node, attribute, value, match_type in exact_matches:
                package = node.get("package", "")
                path = get_node_path(node, root)
                node_info = format_node_info(node, attribute, value, match_type, path, package)
                
                print(f"\n包名: {package}")
                print(f"属性: {attribute}")
                print(f"值: {value}")
                print(f"路径: {path}")
                print("\nget_node_by_path参数格式:")
                print("params:")
                print(f"  package: \"{node_info['package']}\"")
                print("  index_path:")
                print(f"    - {node_info['index_path']}")
                print("  attributes:")
                print(f"    - \"{node_info['attributes'][0]}\"")
                if node_info['pattern']:
                    print(f"  pattern: \"{node_info['pattern']}\"")
                
        # 输出包含匹配结果
        if contains_matches:
            print("\n=== 包含匹配 ===")
            for node, attribute, value, match_type in contains_matches:
                package = node.get("package", "")
                path = get_node_path(node, root)
                node_info = format_node_info(node, attribute, value, match_type, path, package)
                
                print(f"\n包名: {package}")
                print(f"属性: {attribute}")
                print(f"值: {value}")
                print(f"路径: {path}")
                print("\nget_node_by_path参数格式:")
                print("params:")
                print(f"  package: \"{node_info['package']}\"")
                print("  index_path:")
                print(f"    - {node_info['index_path']}")
                print("  attributes:")
                print(f"    - \"{node_info['attributes'][0]}\"")
                if node_info['pattern']:
                    print(f"  pattern: \"{node_info['pattern']}\"")
                
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 