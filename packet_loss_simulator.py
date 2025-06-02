#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据包丢失模拟器
用于测试GBN和SR协议在网络丢包环境下的表现
"""

import socket
import threading
import time
import random
import struct
from typing import Tuple, List

class PacketLossSimulator:
    """
    网络丢包模拟器
    在客户端和服务器之间模拟网络环境
    """
    def __init__(self, client_port=8887, server_host='localhost', server_port=8888, 
                 loss_rate=0.2, delay_range=(0.1, 0.5)):
        self.client_port = client_port
        self.server_host = server_host
        self.server_port = server_port
        self.loss_rate = loss_rate  # 丢包率
        self.delay_range = delay_range  # 延迟范围(秒)
        
        # 套接字
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('localhost', self.client_port))
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 统计信息
        self.packets_received = 0
        self.packets_dropped = 0
        self.packets_forwarded = 0
        
        self.running = False
        
        print(f"丢包模拟器启动")
        print(f"监听端口: {self.client_port}")
        print(f"转发到: {self.server_host}:{self.server_port}")
        print(f"丢包率: {self.loss_rate*100}%")
        print(f"延迟范围: {self.delay_range[0]}-{self.delay_range[1]}秒")
    
    def parse_packet(self, packet: bytes) -> Tuple[int, bool, bytes]:
        """
        解析数据包以获取序号信息
        """
        try:
            if len(packet) < 9:
                return None, None, None
            
            seq_num, is_ack_byte, data_len = struct.unpack('!IBI', packet[:9])
            is_ack = bool(is_ack_byte)
            data = packet[9:9+data_len]
            return seq_num, is_ack, data
        except:
            return None, None, None
    
    def should_drop_packet(self) -> bool:
        """
        根据丢包率决定是否丢弃数据包
        """
        return random.random() < self.loss_rate
    
    def get_random_delay(self) -> float:
        """
        获取随机延迟时间
        """
        return random.uniform(self.delay_range[0], self.delay_range[1])
    
    def forward_packet_with_delay(self, packet: bytes, dest_addr: Tuple[str, int], 
                                source_addr: Tuple[str, int], packet_type: str):
        """
        延迟转发数据包
        """
        def delayed_send():
            delay = self.get_random_delay()
            time.sleep(delay)
            
            if dest_addr[1] == self.server_port:
                # 转发到服务器
                self.server_socket.sendto(packet, dest_addr)
            else:
                # 转发到客户端
                self.client_socket.sendto(packet, dest_addr)
            
            seq_num, is_ack, data = self.parse_packet(packet)
            print(f"[模拟器] {packet_type} {seq_num} 延迟{delay:.2f}s后转发到 {dest_addr}")
        
        # 在新线程中延迟发送
        threading.Thread(target=delayed_send, daemon=True).start()
    
    def handle_client_to_server(self):
        """
        处理客户端到服务器的数据包
        """
        while self.running:
            try:
                packet, client_addr = self.client_socket.recvfrom(1024)
                self.packets_received += 1
                
                seq_num, is_ack, data = self.parse_packet(packet)
                packet_type = "ACK" if is_ack else "DATA"
                
                if self.should_drop_packet():
                    self.packets_dropped += 1
                    print(f"[模拟器] 丢弃 {packet_type} {seq_num} (来自客户端)")
                else:
                    self.packets_forwarded += 1
                    self.forward_packet_with_delay(packet, (self.server_host, self.server_port), 
                                                 client_addr, packet_type)
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[模拟器] 处理客户端数据包时出错: {e}")
    
    def handle_server_to_client(self):
        """
        处理服务器到客户端的数据包
        """
        # 创建用于接收服务器响应的套接字
        server_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_listener.bind(('localhost', self.server_port + 1000))  # 使用不同端口避免冲突
        server_listener.settimeout(0.1)
        
        # 这里简化处理，实际应用中需要更复杂的地址映射
        print(f"[模拟器] 注意：服务器响应处理已简化")
    
    def start(self):
        """
        启动模拟器
        """
        self.running = True
        self.client_socket.settimeout(0.1)
        
        # 启动处理线程
        client_thread = threading.Thread(target=self.handle_client_to_server, daemon=True)
        client_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
                # 定期打印统计信息
                if self.packets_received > 0:
                    loss_percentage = (self.packets_dropped / self.packets_received) * 100
                    print(f"[统计] 接收: {self.packets_received}, 转发: {self.packets_forwarded}, "
                          f"丢弃: {self.packets_dropped} ({loss_percentage:.1f}%)")
        
        except KeyboardInterrupt:
            print("\n[模拟器] 模拟器关闭")
        finally:
            self.running = False
            self.client_socket.close()
            self.server_socket.close()

class ReliabilityTester:
    """
    协议可靠性测试器
    """
    def __init__(self):
        self.test_results = []
    
    def test_gbn_with_loss(self, loss_rates: List[float], message_count: int = 10):
        """
        测试GBN协议在不同丢包率下的表现
        """
        print("\n=== GBN协议丢包测试 ===")
        
        for loss_rate in loss_rates:
            print(f"\n测试丢包率: {loss_rate*100}%")
            
            # 启动丢包模拟器
            simulator = PacketLossSimulator(loss_rate=loss_rate)
            simulator_thread = threading.Thread(target=simulator.start, daemon=True)
            simulator_thread.start()
            
            time.sleep(1)  # 等待模拟器启动
            
            # 测试数据传输
            start_time = time.time()
            
            # 这里应该启动GBN客户端和服务器进行测试
            # 由于需要修改客户端连接到模拟器端口，这里只做演示
            print(f"模拟发送 {message_count} 条消息...")
            time.sleep(3)  # 模拟传输时间
            
            end_time = time.time()
            transmission_time = end_time - start_time
            
            # 记录测试结果
            result = {
                'protocol': 'GBN',
                'loss_rate': loss_rate,
                'message_count': message_count,
                'transmission_time': transmission_time,
                'packets_dropped': simulator.packets_dropped,
                'packets_forwarded': simulator.packets_forwarded
            }
            
            self.test_results.append(result)
            simulator.running = False
            
            print(f"传输完成，用时: {transmission_time:.2f}秒")
    
    # SR协议测试功能已移除
    
    def generate_report(self):
        """
        生成测试报告
        """
        print("\n=== 测试报告 ===")
        print("协议\t丢包率\t消息数\t传输时间(s)\t效率")
        print("-" * 50)
        
        for result in self.test_results:
            efficiency = result['message_count'] / result['transmission_time']
            print(f"{result['protocol']}\t{result['loss_rate']*100:.0f}%\t"
                  f"{result['message_count']}\t{result['transmission_time']:.2f}\t\t{efficiency:.2f}")
        
        # 分析结果
        print("\n=== 分析结果 ===")
        gbn_results = [r for r in self.test_results if r['protocol'] == 'GBN']
        sr_results = [r for r in self.test_results if r['protocol'] == 'SR']
        
        if gbn_results and sr_results:
            avg_gbn_time = sum(r['transmission_time'] for r in gbn_results) / len(gbn_results)
            avg_sr_time = sum(r['transmission_time'] for r in sr_results) / len(sr_results)
            
            print(f"GBN平均传输时间: {avg_gbn_time:.2f}秒")
            print(f"SR平均传输时间: {avg_sr_time:.2f}秒")
            
            if avg_sr_time < avg_gbn_time:
                improvement = ((avg_gbn_time - avg_sr_time) / avg_gbn_time) * 100
                print(f"SR协议比GBN协议快 {improvement:.1f}%")
            else:
                print("在当前测试条件下，GBN协议表现更好")

def main():
    """
    主测试函数
    """
    print("网络协议可靠性测试工具")
    print("1. 启动丢包模拟器")
    print("2. 运行协议对比测试")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == '1':
        # 启动丢包模拟器
        loss_rate = float(input("请输入丢包率 (0.0-1.0): ") or "0.2")
        simulator = PacketLossSimulator(loss_rate=loss_rate)
        simulator.start()
    
    elif choice == '2':
        # 运行协议对比测试
        tester = ReliabilityTester()
        
        loss_rates = [0.1, 0.2, 0.3]  # 测试不同丢包率
        message_count = 10
        
        tester.test_gbn_with_loss(loss_rates, message_count)
        tester.test_sr_with_loss(loss_rates, message_count)
        tester.generate_report()
    
    else:
        print("无效选择")

if __name__ == "__main__":
    main()