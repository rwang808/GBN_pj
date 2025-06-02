#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GBN (Go-Back-N) 协议服务器端实现
基于UDP实现可靠数据传输
"""

import socket
import threading
import time
import struct
import os
from typing import Dict, List, Tuple

class GBNServer:
    def __init__(self, host='localhost', port=8888, window_size=4, timeout=2.0):
        self.host = host
        self.port = port
        self.window_size = window_size
        self.timeout = timeout
        
        # 套接字
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        
        # 客户端状态管理
        self.clients: Dict[Tuple[str, int], dict] = {}
        
        print(f"GBN服务器启动在 {self.host}:{self.port}")
        print(f"窗口大小: {self.window_size}, 超时时间: {self.timeout}s")
    
    def create_packet(self, seq_num: int, data: bytes, is_ack: bool = False) -> bytes:
        """
        创建数据包
        格式: [seq_num(4字节)] [is_ack(1字节)] [data_len(4字节)] [data]
        """
        is_ack_byte = 1 if is_ack else 0
        data_len = len(data)
        header = struct.pack('!IBI', seq_num, is_ack_byte, data_len)
        return header + data
    
    def parse_packet(self, packet: bytes) -> Tuple[int, bool, bytes]:
        """
        解析数据包
        返回: (seq_num, is_ack, data)
        """
        if len(packet) < 9:  # 最小包头大小
            return None, None, None
        
        seq_num, is_ack_byte, data_len = struct.unpack('!IBI', packet[:9])
        is_ack = bool(is_ack_byte)
        data = packet[9:9+data_len]
        return seq_num, is_ack, data
    
    def send_ack(self, client_addr: Tuple[str, int], seq_num: int):
        """
        发送ACK确认
        """
        ack_packet = self.create_packet(seq_num, b'', is_ack=True)
        self.socket.sendto(ack_packet, client_addr)
        print(f"发送ACK {seq_num} 到 {client_addr}")
    
    def handle_client_data(self, client_addr: Tuple[str, int], seq_num: int, data: bytes):
        """
        处理客户端数据
        """
        if client_addr not in self.clients:
            self.clients[client_addr] = {
                'expected_seq': 0,
                'received_data': {},
                'last_activity': time.time()
            }
        
        client_state = self.clients[client_addr]
        client_state['last_activity'] = time.time()
        
        print(f"收到来自 {client_addr} 的数据包，序号: {seq_num}, 期望序号: {client_state['expected_seq']}")
        
        if seq_num == client_state['expected_seq']:
            # 按序到达的数据包
            print(f"数据包 {seq_num} 按序到达: {data.decode('utf-8', errors='ignore')}")
            client_state['received_data'][seq_num] = data
            
            # 发送ACK
            self.send_ack(client_addr, seq_num)
            
            # 更新期望序号
            client_state['expected_seq'] += 1
            
            # 检查是否有连续的数据包可以处理
            while client_state['expected_seq'] in client_state['received_data']:
                next_seq = client_state['expected_seq']
                next_data = client_state['received_data'][next_seq]
                print(f"处理缓存的数据包 {next_seq}: {next_data.decode('utf-8', errors='ignore')}")
                client_state['expected_seq'] += 1
        
        elif seq_num < client_state['expected_seq']:
            # 重复的数据包，发送ACK但不处理数据
            print(f"收到重复数据包 {seq_num}，发送ACK")
            self.send_ack(client_addr, seq_num)
        
        else:
            # 乱序数据包，缓存但不发送ACK
            print(f"数据包 {seq_num} 乱序到达，缓存等待")
            client_state['received_data'][seq_num] = data
            # 发送最后一个按序收到的ACK
            if client_state['expected_seq'] > 0:
                self.send_ack(client_addr, client_state['expected_seq'] - 1)
    
    def cleanup_inactive_clients(self):
        """
        清理不活跃的客户端
        """
        current_time = time.time()
        inactive_clients = []
        
        for client_addr, state in self.clients.items():
            if current_time - state['last_activity'] > 60:  # 60秒超时
                inactive_clients.append(client_addr)
        
        for client_addr in inactive_clients:
            print(f"清理不活跃客户端: {client_addr}")
            del self.clients[client_addr]
    
    def start(self):
        """
        启动服务器
        """
        # 启动清理线程
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()
        
        try:
            while True:
                try:
                    packet, client_addr = self.socket.recvfrom(1024)
                    seq_num, is_ack, data = self.parse_packet(packet)
                    
                    if seq_num is not None and not is_ack:
                        # 处理数据包
                        self.handle_client_data(client_addr, seq_num, data)
                    
                except socket.error as e:
                    print(f"套接字错误: {e}")
                except Exception as e:
                    print(f"处理数据包时出错: {e}")
        
        except KeyboardInterrupt:
            print("\n服务器关闭")
        finally:
            self.socket.close()
    
    def _cleanup_loop(self):
        """
        清理循环
        """
        while True:
            time.sleep(30)  # 每30秒清理一次
            self.cleanup_inactive_clients()

if __name__ == "__main__":
    server = GBNServer()
    server.start()