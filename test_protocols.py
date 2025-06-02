#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协议测试脚本
用于测试GBN和SR协议的功能和性能
"""

import threading
import time
import os
import sys
from gbn_server import GBNServer
from gbn_client import GBNClient
# SR协议相关代码已移除
from packet_loss_simulator import PacketLossSimulator, ReliabilityTester

class ProtocolTester:
    """
    协议测试类
    """
    def __init__(self):
        self.test_data = [
            "Hello, this is test message 1",
            "Testing GBN protocol with message 2",
            "Third message for reliability testing",
            "Message 4 - checking order preservation",
            "Final test message 5",
            "Additional message 6 for window testing",
            "Message 7 - testing timeout handling",
            "Last message 8 for comprehensive test"
        ]
    
    def test_gbn_protocol(self):
        """
        测试GBN协议
        """
        print("\n" + "="*50)
        print("测试GBN (Go-Back-N) 协议")
        print("="*50)
        
        # 启动GBN服务器
        server = GBNServer(port=8888, window_size=4, timeout=2.0)
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        
        print("等待服务器启动...")
        time.sleep(2)
        
        # 创建GBN客户端并发送数据
        client = GBNClient(server_port=8888, window_size=4, timeout=2.0)
        
        try:
            print("\n开始发送测试数据...")
            start_time = time.time()
            
            client.send_text_messages(self.test_data)
            
            end_time = time.time()
            transmission_time = end_time - start_time
            
            print(f"\nGBN协议测试完成")
            print(f"发送消息数: {len(self.test_data)}")
            print(f"传输时间: {transmission_time:.2f}秒")
            print(f"平均每条消息: {transmission_time/len(self.test_data):.2f}秒")
            
        except Exception as e:
            print(f"GBN测试出错: {e}")
        finally:
            client.close()
            time.sleep(1)
    
    
    def test_with_packet_loss(self):
        """
        测试协议在丢包环境下的表现
        """
        print("\n" + "="*50)
        print("测试协议在网络丢包环境下的表现")
        print("="*50)
        
        tester = ReliabilityTester()
        
        # 测试不同丢包率
        loss_rates = [0.1, 0.2, 0.3]
        message_count = len(self.test_data)
        
        print("\n开始丢包环境测试...")
        tester.test_gbn_with_loss(loss_rates, message_count)
        tester.test_sr_with_loss(loss_rates, message_count)
        tester.generate_report()
    
    def create_test_file(self):
        """
        创建测试文件
        """
        test_file_path = "test_data.txt"
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文件\n")
            f.write("用于测试文件传输功能\n")
            for i, msg in enumerate(self.test_data, 1):
                f.write(f"{i}. {msg}\n")
            f.write("\n文件传输测试结束\n")
        
        print(f"测试文件已创建: {test_file_path}")
        return test_file_path
    
    def test_file_transfer(self):
        """
        测试文件传输功能
        """
        print("\n" + "="*50)
        print("测试文件传输功能")
        print("="*50)
        
        # 创建测试文件
        test_file = self.create_test_file()
        
        # 启动GBN服务器
        server = GBNServer(port=8890, window_size=6, timeout=3.0)
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        
        time.sleep(2)
        
        # 使用GBN客户端传输文件
        client = GBNClient(server_port=8890, window_size=6, timeout=3.0)
        
        try:
            print(f"\n开始传输文件: {test_file}")
            start_time = time.time()
            
            client.send_file(test_file, chunk_size=50)  # 小块传输测试
            
            end_time = time.time()
            transmission_time = end_time - start_time
            
            file_size = os.path.getsize(test_file)
            print(f"\n文件传输完成")
            print(f"文件大小: {file_size} 字节")
            print(f"传输时间: {transmission_time:.2f}秒")
            print(f"传输速率: {file_size/transmission_time:.2f} 字节/秒")
            
        except Exception as e:
            print(f"文件传输测试出错: {e}")
        finally:
            client.close()
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"测试文件已删除: {test_file}")
    
    def run_comprehensive_test(self):
        """
        运行综合测试
        """
        print("\n" + "="*60)
        print("GBN协议综合测试")
        print("="*60)
        
        print("\n测试包括:")
        print("1. GBN协议基本功能测试")
        print("2. 文件传输功能测试")
        print("3. 网络丢包环境测试")
        
        try:
            # 1. 测试GBN协议
            self.test_gbn_protocol()
            time.sleep(2)
            
            # 2. 测试文件传输
            self.test_file_transfer()
            time.sleep(2)
            
            # 3. 测试丢包环境
            self.test_with_packet_loss()
            
            print("\n" + "="*60)
            print("所有测试完成！")
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n测试被用户中断")
        except Exception as e:
            print(f"\n测试过程中出错: {e}")

def print_menu():
    """
    打印菜单
    """
    print("\n" + "="*40)
    print("GBN协议测试程序")
    print("="*40)
    print("1. 测试GBN协议")
    print("2. 测试文件传输")
    print("3. 测试网络丢包环境")
    print("4. 运行综合测试")
    print("5. 启动丢包模拟器")
    print("0. 退出")
    print("-" * 40)

def main():
    """
    主函数
    """
    tester = ProtocolTester()
    
    while True:
        print_menu()
        choice = input("请选择测试项目 (0-5): ").strip()
        
        try:
            if choice == '1':
                tester.test_gbn_protocol()
            elif choice == '2':
                tester.test_file_transfer()
            elif choice == '3':
                tester.test_with_packet_loss()
            elif choice == '4':
                tester.run_comprehensive_test()
            elif choice == '5':
                print("\n启动丢包模拟器...")
                loss_rate = float(input("请输入丢包率 (0.0-1.0, 默认0.2): ") or "0.2")
                simulator = PacketLossSimulator(loss_rate=loss_rate)
                simulator.start()
            elif choice == '0':
                print("\n程序退出")
                break
            else:
                print("\n无效选择，请重新输入")
        
        except KeyboardInterrupt:
            print("\n操作被中断")
        except Exception as e:
            print(f"\n执行出错: {e}")
        
        if choice != '0':
            input("\n按回车键继续...")

if __name__ == "__main__":
    main()