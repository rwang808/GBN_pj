#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GBN (Go-Back-N) 协议客户端实现
基于UDP实现可靠数据传输
"""

import socket
import threading
import time
import struct
import queue
from typing import List, Tuple, Optional

class GBNClient:
    def __init__(self, server_host='localhost', server_port=8888, window_size=4, timeout=2.0):
        self.server_host = server_host
        self.server_port = server_port
        self.window_size = window_size
        self.timeout = timeout
        
        # 套接字
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # GBN协议状态
        self.base = 0  # 窗口基序号
        self.next_seq_num = 0  # 下一个要发送的序号
        self.send_buffer = {}  # 发送缓冲区 {seq_num: (data, timestamp)}
        self.ack_received = {}  # 收到的ACK {seq_num: timestamp}
        
        # 线程控制
        self.running = False
        self.send_lock = threading.Lock()
        
        print(f"GBN客户端初始化，服务器: {self.server_host}:{self.server_port}")
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
    
    def send_packet(self, seq_num: int, data: bytes):
        """
        发送数据包
        """
        packet = self.create_packet(seq_num, data)
        self.socket.sendto(packet, (self.server_host, self.server_port))
        print(f"发送数据包 {seq_num}: {data.decode('utf-8', errors='ignore')}")
    
    def send_data(self, data_list: List[bytes]):
        """
        发送数据列表
        """
        self.running = True
        
        # 启动ACK接收线程
        ack_thread = threading.Thread(target=self._receive_acks, daemon=True)
        ack_thread.start()
        
        # 启动超时检查线程
        timeout_thread = threading.Thread(target=self._timeout_handler, daemon=True)
        timeout_thread.start()
        
        data_index = 0
        
        try:
            while data_index < len(data_list) or self.base < len(data_list):
                with self.send_lock:
                    # 发送窗口内的数据包
                    while (self.next_seq_num < self.base + self.window_size and 
                           data_index < len(data_list)):
                        
                        data = data_list[data_index]
                        self.send_packet(self.next_seq_num, data)
                        
                        # 记录发送时间
                        self.send_buffer[self.next_seq_num] = (data, time.time())
                        
                        self.next_seq_num += 1
                        data_index += 1
                
                # 等待ACK或超时
                time.sleep(0.1)
                
                # 检查是否所有数据都已确认
                if self.base >= len(data_list):
                    break
            
            print("所有数据发送完成")
        
        except KeyboardInterrupt:
            print("\n发送被中断")
        finally:
            self.running = False
            time.sleep(0.5)  # 等待线程结束
    
    def _receive_acks(self):
        """
        接收ACK的线程
        """
        self.socket.settimeout(0.1)  # 设置接收超时
        
        while self.running:
            try:
                packet, addr = self.socket.recvfrom(1024)
                seq_num, is_ack, data = self.parse_packet(packet)
                
                if is_ack and seq_num is not None:
                    self._handle_ack(seq_num)
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"接收ACK时出错: {e}")
    
    def _handle_ack(self, ack_seq: int):
        """
        处理收到的ACK
        """
        with self.send_lock:
            print(f"收到ACK {ack_seq}")
            
            # 累积确认：确认所有小于等于ack_seq的数据包
            if ack_seq >= self.base:
                # 移动窗口基序号
                old_base = self.base
                self.base = ack_seq + 1
                
                # 清理已确认的数据包
                for seq in range(old_base, self.base):
                    if seq in self.send_buffer:
                        del self.send_buffer[seq]
                
                print(f"窗口滑动: base从 {old_base} 移动到 {self.base}")
    
    def _timeout_handler(self):
        """
        超时处理线程
        """
        while self.running:
            current_time = time.time()
            
            with self.send_lock:
                # 检查是否有超时的数据包
                timeout_packets = []
                for seq_num, (data, send_time) in self.send_buffer.items():
                    if current_time - send_time > self.timeout:
                        timeout_packets.append((seq_num, data))
                
                if timeout_packets:
                    print(f"检测到超时，重传从序号 {self.base} 开始的所有数据包")
                    
                    # Go-Back-N: 重传从base开始的所有未确认数据包
                    for seq_num in sorted(self.send_buffer.keys()):
                        if seq_num >= self.base:
                            data, _ = self.send_buffer[seq_num]
                            self.send_packet(seq_num, data)
                            # 更新发送时间
                            self.send_buffer[seq_num] = (data, current_time)
            
            time.sleep(0.1)
    
    def send_file(self, file_path: str, chunk_size: int = 100):
        """
        发送文件
        """
        try:
            with open(file_path, 'rb') as f:
                data_list = []
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    data_list.append(chunk)
                
                print(f"准备发送文件 {file_path}，共 {len(data_list)} 个数据包")
                self.send_data(data_list)
        
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在")
        except Exception as e:
            print(f"发送文件时出错: {e}")
    
    def send_text_messages(self, messages: List[str]):
        """
        发送文本消息列表
        """
        data_list = [msg.encode('utf-8') for msg in messages]
        print(f"准备发送 {len(messages)} 条消息")
        self.send_data(data_list)
    
    def close(self):
        """
        关闭客户端
        """
        self.running = False
        self.socket.close()
        print("客户端已关闭")

def main():
    client = GBNClient()
    
    try:
        # 测试发送文本消息
        messages = [
            "Hello, this is message 1",
            "This is message 2",
            "Message 3 for testing",
            "Fourth message",
            "Final message 5"
        ]
        
        print("开始发送测试消息...")
        client.send_text_messages(messages)
        
        # 等待一段时间确保所有数据传输完成
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("\n程序被中断")
    finally:
        client.close()

if __name__ == "__main__":
    main()