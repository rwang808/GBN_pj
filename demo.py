#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目演示脚本
展示GBN的基本使用方法
"""

import threading
import time
import os
from gbn_server import GBNServer
from gbn_client import GBNClient

def demo_gbn_protocol():
    """
    演示GBN协议的基本使用
    """
    print("\n" + "="*50)
    print("GBN协议演示")
    print("="*50)
    
    # 启动GBN服务器
    print("1. 启动GBN服务器...")
    server = GBNServer(port=8888, window_size=3, timeout=2.0)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(1)
    print("   服务器已启动")
    
    # 创建GBN客户端
    print("\n2. 创建GBN客户端...")
    client = GBNClient(server_port=8888, window_size=3, timeout=2.0)
    
    # 准备测试数据
    test_messages = [
        "Hello from GBN client!",
        "This is message 2",
        "Testing reliable transmission",
        "Message 4 with GBN protocol",
        "Final test message"
    ]
    
    try:
        print("\n3. 发送测试消息...")
        print(f"   准备发送 {len(test_messages)} 条消息")
        
        start_time = time.time()
        client.send_text_messages(test_messages)
        end_time = time.time()
        
        print(f"\n4. 传输完成！")
        print(f"   传输时间: {end_time - start_time:.2f}秒")
        print(f"   平均每条消息: {(end_time - start_time)/len(test_messages):.2f}秒")
        
    except Exception as e:
        print(f"   发送过程中出错: {e}")
    finally:
        client.close()
        print("   客户端已关闭")


def demo_file_transfer():
    """
    演示文件传输功能
    """
    print("\n" + "="*50)
    print("文件传输演示")
    print("="*50)
    
    # 创建演示文件
    demo_file = "demo_file.txt"
    print("1. 创建演示文件...")
    
    with open(demo_file, 'w', encoding='utf-8') as f:
        f.write("这是一个演示文件\n")
        f.write("用于测试GBN协议的文件传输功能\n")
        f.write("\n")
        for i in range(1, 11):
            f.write(f"第 {i} 行：这是文件传输测试的内容\n")
        f.write("\n文件传输演示结束\n")
    
    file_size = os.path.getsize(demo_file)
    print(f"   文件已创建: {demo_file} ({file_size} 字节)")
    
    # 启动GBN服务器用于文件传输
    print("\n2. 启动文件传输服务器...")
    server = GBNServer(port=8890, window_size=4, timeout=3.0)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    
    time.sleep(1)
    print("   服务器已启动")
    
    # 创建客户端进行文件传输
    print("\n3. 开始文件传输...")
    client = GBNClient(server_port=8890, window_size=4, timeout=3.0)
    
    try:
        start_time = time.time()
        client.send_file(demo_file, chunk_size=64)  # 64字节块大小
        end_time = time.time()
        
        transmission_time = end_time - start_time
        transfer_rate = file_size / transmission_time if transmission_time > 0 else 0
        
        print(f"\n4. 文件传输完成！")
        print(f"   文件大小: {file_size} 字节")
        print(f"   传输时间: {transmission_time:.2f}秒")
        print(f"   传输速率: {transfer_rate:.2f} 字节/秒")
        
    except Exception as e:
        print(f"   文件传输过程中出错: {e}")
    finally:
        client.close()
        # 清理演示文件
        if os.path.exists(demo_file):
            os.remove(demo_file)
            print(f"   演示文件已删除: {demo_file}")

def demo_protocol_comparison():
    """
    演示协议性能对比
    """
    print("\n" + "="*50)
    print("协议性能对比演示")
    print("="*50)
    
    # 测试数据
    test_messages = [f"Performance test message {i+1}" for i in range(8)]
    
    print("\n测试场景: 发送8条消息")
    print("窗口大小: 4")
    print("超时时间: 2.0秒")
    
    # 测试GBN协议性能
    print("\n1. 测试GBN协议性能...")
    
    # 启动GBN服务器
    gbn_server = GBNServer(port=8891, window_size=4, timeout=2.0)
    gbn_server_thread = threading.Thread(target=gbn_server.start, daemon=True)
    gbn_server_thread.start()
    time.sleep(1)
    
    # GBN客户端测试
    gbn_client = GBNClient(server_port=8891, window_size=4, timeout=2.0)
    
    try:
        gbn_start = time.time()
        gbn_client.send_text_messages(test_messages)
        gbn_end = time.time()
        gbn_time = gbn_end - gbn_start
        print(f"   GBN传输时间: {gbn_time:.2f}秒")
    except Exception as e:
        print(f"   GBN测试出错: {e}")
        gbn_time = float('inf')
    finally:
        gbn_client.close()
    
    time.sleep(1)
    
    # SR协议性能测试已移除
    print("\n2. 性能测试结果:")
    print(f"   GBN协议: {gbn_time:.2f}秒")
    print("   (SR协议功能已移除)")

def main():
    """
    主演示函数
    """
    print("GBN协议项目演示")
    print("="*40)
    
    options = [
        ("GBN协议基本使用", demo_gbn_protocol),
        ("文件传输功能", demo_file_transfer),
        ("协议性能测试", demo_protocol_comparison),
        ("退出", None)
    ]
    
    try:
        while True:
            print("\n请选择要演示的功能:")
            for i, (name, _) in enumerate(options, 1):
                print(f"{i}. {name}")
            
            try:
                choice = int(input("\n请输入选项编号: "))
                if choice < 1 or choice > len(options):
                    print("无效选项，请重新选择")
                    continue
                
                name, demo_func = options[choice - 1]
                if demo_func is None:
                    break
                
                print(f"\n{'='*60}")
                print(f"演示: {name}")
                print(f"{'='*60}")
                
                demo_func()
                print("\n演示完成！")
                
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n演示被用户中断")
                break
            except Exception as e:
                print(f"\n演示过程中出错: {e}")
        
        print("\n" + "="*60)
        print("所有演示完成！")
        print("="*60)
        print("\n项目功能演示结束。")
        print("更多功能请运行 test_protocols.py 进行详细测试。")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n\n演示过程中出现错误: {e}")

if __name__ == "__main__":
    main()