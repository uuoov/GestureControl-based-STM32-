#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手势控制音乐播放器 - PC端控制器
功能：
1. 通过串口接收STM32发送的xyz手势数据
2. 分析手势并控制音乐播放器
3. 通过Modbus协议发送控制指令和歌曲名给STM32
"""

# ========== 在最开始设置异常处理和日志 ==========
import sys
import os
import traceback
from datetime import datetime

# 全局日志文件变量
_global_log_file = None
_global_log_path = None

def _init_crash_log():
    """初始化崩溃日志文件（在程序最开始调用）"""
    global _global_log_file, _global_log_path
    try:
        # 尝试多种方法获取脚本目录
        script_dir = None
        
        # 方法1: 使用 __file__
        try:
            if '__file__' in globals():
                script_dir = os.path.dirname(os.path.abspath(__file__))
        except:
            pass
        
        # 方法2: 使用当前工作目录
        if script_dir is None:
            try:
                script_dir = os.getcwd()
            except:
                pass
        
        # 方法3: 使用当前工作目录（作为最后手段）
        if script_dir is None:
            script_dir = os.getcwd()
        
        _global_log_path = os.path.join(script_dir, 'crash_log.txt')
        
        # 打印路径信息（用于调试）
        print(f"[Debug] 尝试创建日志文件: {_global_log_path}")
        print(f"[Debug] 脚本目录: {script_dir}")
        print(f"[Debug] 目录是否存在: {os.path.exists(script_dir) if script_dir else 'N/A'}")
        
        # 确保目录存在
        try:
            os.makedirs(script_dir, exist_ok=True)
        except:
            pass
        
        # 创建日志文件
        _global_log_file = open(_global_log_path, 'a', encoding='utf-8')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _global_log_file.write(f"\n{'='*60}\n")
        _global_log_file.write(f"[{timestamp}] 程序启动\n")
        _global_log_file.write(f"{'='*60}\n")
        _global_log_file.flush()
        
        print(f"[System] ✓ 崩溃日志文件已创建: {_global_log_path}")
        print(f"[System] ✓ 日志文件路径（完整）: {os.path.abspath(_global_log_path)}")
        return True
    except Exception as e:
        print(f"[CRITICAL ERROR] 无法创建日志文件: {e}")
        print(f"[CRITICAL ERROR] 错误类型: {type(e).__name__}")
        try:
            import traceback
            print("[CRITICAL ERROR] 堆栈跟踪:")
            traceback.print_exc()
        except:
            pass
        _global_log_file = None
        _global_log_path = None
        return False

def _log_crash(message):
    """记录崩溃信息"""
    global _global_log_file
    try:
        print(message)
        if _global_log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            _global_log_file.write(f"\n[{timestamp}] {message}\n")
            _global_log_file.flush()
    except:
        pass

def _global_excepthook(exc_type, exc_value, exc_traceback):
    """全局异常处理钩子（在程序最开始设置）"""
    if exc_type == KeyboardInterrupt:
        if sys.__excepthook__:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = "\n" + "=" * 60 + "\n"
    error_msg += "[CRITICAL ERROR] 程序发生未捕获的异常！\n"
    error_msg += "=" * 60 + "\n"
    error_msg += f"异常类型: {exc_type.__name__}\n"
    error_msg += f"异常信息: {exc_value}\n"
    error_msg += "\n堆栈跟踪:\n"
    error_msg += "-" * 60 + "\n"
    
    try:
        traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        error_msg += traceback_str
    except:
        error_msg += "无法获取堆栈跟踪\n"
    
    error_msg += "-" * 60 + "\n"
    
    _log_crash(error_msg)
    
    # 尝试写入文件
    try:
        if _global_log_file:
            _global_log_file.close()
    except:
        pass
    
    # 尝试直接写入文件（如果日志文件对象失败）
    try:
        if _global_log_path:
            with open(_global_log_path, 'a', encoding='utf-8') as f:
                f.write(error_msg)
                f.write("\n按Enter键退出...\n")
    except:
        pass
    
    try:
        input("\n按Enter键退出...")
    except:
        import time
        time.sleep(3)
    
    sys.exit(1)

# 立即初始化日志和异常处理
try:
    _init_crash_log()
    sys.excepthook = _global_excepthook
    # 记录初始化成功
    if _global_log_file:
        _log_crash("[System] 异常处理和日志系统初始化成功")
except Exception as init_error:
    # 如果初始化失败，至少尝试打印错误
    try:
        print(f"[CRITICAL] 初始化失败: {init_error}")
        import traceback
        traceback.print_exc()
    except:
        pass

# ========== 现在开始导入其他模块 ==========
try:
    import serial
except Exception as e:
    _log_crash(f"[CRITICAL] 无法导入 serial 模块: {e}")
    raise

try:
    import time
    import struct
    import threading
    import math
    import glob
    from enum import Enum
    from typing import Optional, List
except Exception as e:
    _log_crash(f"[CRITICAL] 导入标准库失败: {e}")
    raise

# Windows音量控制
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False
    print("[Warning] pycaw not installed, system volume control disabled")
except Exception as e:
    HAS_PYCAW = False
    print(f"[Warning] pycaw import error: {e}")

# 音乐播放
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    print("[Warning] pygame not installed, music playback disabled")

# Modbus协议相关定义
MODBUS_SLAVE_ADDR = 0x01  # STM32从机地址
MODBUS_FC_READ_HOLDING_REGS = 0x03
MODBUS_FC_WRITE_SINGLE_REG = 0x06
MODBUS_FC_WRITE_MULTIPLE_REGS = 0x10

# Modbus寄存器地址
REG_GESTURE_CMD = 0x0000
REG_VOLUME = 0x0001
REG_CURRENT_SONG = 0x0002
REG_SONG_NAME_LEN = 0x0003
REG_SONG_NAME = 0x0004

# 手势类型定义（与STM32一致）
GESTURE_NONE = 0x00
GESTURE_LEFT = 0x01      # 向左滑动：上一首
GESTURE_RIGHT = 0x02     # 向右滑动：下一首
GESTURE_UP = 0x03         # 向上滑动：音量加
GESTURE_DOWN = 0x04       # 向下滑动：音量减
GESTURE_CLOCKWISE = 0x05  # 顺时针转圈：暂停/播放
GESTURE_COUNTERCLOCKWISE = 0x06  # 逆时针转圈：暂停/播放（与顺时针相同）

# 支持的音频格式
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']

def scan_music_files(music_dir: str = 'Music') -> List[tuple]:
    """
    扫描音乐文件夹，返回音乐文件列表
    :param music_dir: 音乐文件夹路径
    :return: [(文件路径, 文件名), ...] 列表
    """
    music_files = []
    
    # 获取脚本所在目录的父目录（项目根目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) if os.path.basename(script_dir) == 'pc_controller' else script_dir
    music_path = os.path.join(project_root, music_dir)
    
    if not os.path.exists(music_path):
        print(f"[Warning] Music directory not found: {music_path}")
        return music_files
    
    # 扫描所有支持的音频文件
    for ext in AUDIO_EXTENSIONS:
        pattern = os.path.join(music_path, f'*{ext}')
        files = glob.glob(pattern)
        for file_path in files:
            # 获取文件名（不含扩展名）作为显示名称
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            music_files.append((file_path, file_name))
    
    # 按文件名排序
    music_files.sort(key=lambda x: x[1])
    
    return music_files


class MusicPlayerController:
    """音乐播放器控制器"""
    
    def __init__(self, port: str = 'COM11', baudrate: int = 115200, music_dir: str = 'Music'):
        """
        初始化控制器
        :param port: 串口端口号
        :param baudrate: 波特率
        :param music_dir: 音乐文件夹路径
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.running = False
        
        # 扫描音乐文件
        self.music_files = scan_music_files(music_dir)
        if len(self.music_files) == 0:
            print("[Warning] No music files found! Using empty list.")
            self.music_files = []
        else:
            # 打印完整的歌曲列表用于调试
            print(f"[System] 扫描到 {len(self.music_files)} 首音乐文件:")
            for i, (file_path, song_name) in enumerate(self.music_files):
                print(f"[System]   索引 {i}: {song_name} (文件: {os.path.basename(file_path)})")
        
        # 音乐播放器状态
        self.current_song_index = 0
        self.volume = 50  # 0-100
        self.play_mode = "list"  # "list" 或 "single"
        self.is_playing = False
        self.is_paused = False  # 暂停状态
        
        # 初始化Windows系统音量控制
        self.system_volume_interface = None
        if HAS_PYCAW:
            try:
                # 方法1：尝试使用pycaw的标准方法
                devices = AudioUtilities.GetSpeakers()
                interface = None
                
                # 检查是否有Activate方法
                if hasattr(devices, 'Activate'):
                    try:
                        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    except Exception as e:
                        print(f"[Debug] Activate方法调用失败: {e}")
                
                # 方法2：使用pycaw的EndpointVolume属性（这是正确的方法！）
                if interface is None:
                    try:
                        # EndpointVolume属性已经是POINTER(IAudioEndpointVolume)类型，可以直接使用
                        if hasattr(devices, 'EndpointVolume') and devices.EndpointVolume is not None:
                            interface = devices.EndpointVolume
                        # 备用：检查_volume属性
                        elif hasattr(devices, '_volume') and devices._volume is not None:
                            interface = devices._volume
                        # 备用：检查是否有内部COM对象
                        elif hasattr(devices, '_dev') and devices._dev is not None:
                            interface = devices._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    except Exception as e:
                        print(f"[Debug] 内部属性方法失败: {e}")
                
                if interface is None:
                    raise Exception("无法通过任何方法获取音量控制接口")
                
                # EndpointVolume已经是正确的类型（POINTER(IAudioEndpointVolume)），可以直接使用
                # 检查是否有GetMasterVolumeLevelScalar方法，如果有则直接使用，否则尝试转换
                if hasattr(interface, 'GetMasterVolumeLevelScalar'):
                    self.system_volume_interface = interface
                else:
                    self.system_volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                
                # 测试是否能读取音量
                try:
                    current_volume = self.system_volume_interface.GetMasterVolumeLevelScalar()
                    self.volume = int(current_volume * 100)
                    print(f"[System] Windows音量控制已启用，当前音量: {self.volume}%")
                except Exception as vol_err:
                    print(f"[System] Windows音量控制已启用（无法读取当前音量，使用默认: {self.volume}%）")
            except Exception as e:
                print(f"[Warning] 无法初始化Windows音量控制: {e}")
                print(f"[Info] 音量控制功能将不可用，但其他功能正常")
                self.system_volume_interface = None
        
        # 初始化pygame音乐播放
        self.pygame_available = False
        if HAS_PYGAME:
            try:
                pygame.mixer.init()
                self.pygame_available = True
                print("[System] 音乐播放器已启用")
            except Exception as e:
                print(f"[Warning] 无法初始化音乐播放器: {e}")
                self.pygame_available = False
        
        # 手势数据缓存
        self.last_gesture = GESTURE_NONE
        self.gesture_data_buffer = []  # 存储最近的xyz数据用于分析
        self.debug_count = 0  # 调试计数器
        self.last_gesture_time = 0  # 上次识别手势的时间戳
        self.gesture_cooldown = 1.0  # 手势冷却期：1秒，每两个手势之间最少间隔1秒
        self.last_volume_time = 0  # 上次调整音量的时间戳
        self.volume_cooldown = 1.0  # 音量调整冷却期：1秒，1秒内不允许再次调整音量
        self.last_song_change_time = 0  # 上次切换歌曲的时间戳
        self.song_change_cooldown = 1.0  # 歌曲切换冷却期：1秒，1秒内不允许再次切换歌曲
        self.velocity_buffer = []  # 速度缓冲区，用于检测手势趋势
        self.last_gesture_ignore_time = 0  # 上次识别手势后的忽略时间戳
        self.gesture_ignore_period = 0.8  # 手势识别后的忽略期：0.8秒，避免识别到返回动作
        
        # 数据卡住检测
        self.last_data_point = None  # 上一个数据点
        self.stuck_data_count = 0  # 连续相同数据的计数
        self.max_stuck_count = 50  # 最大允许的连续相同数据次数（约0.2秒，假设4ms采样）
        self.last_stuck_warning_time = 0.0  # 上次卡住警告的时间（初始化为浮点数）
        
        # 自适应校准相关
        self.calibration_mode = True  # 是否处于校准模式
        self.calibration_data = []  # 校准数据收集
        self.calibration_samples = 100  # 校准所需样本数（必须达到此数量才能完成校准）
        self.calibration_min_samples = 50  # 最少需要的样本数（用于提示，但不用于完成校准）
        self.calibration_complete = False  # 校准是否完成
        
        # 校准后的参数
        self.x_min = 0
        self.x_max = 65535
        self.y_min = 0
        self.y_max = 65535
        self.z_min = 0
        self.z_max = 65535
        self.x_center = 32767  # 中心值
        self.y_center = 32767
        self.z_center = 32767
        self.x_range = 65535  # 范围
        self.y_range = 65535
        self.z_range = 65535
        
        # 自适应阈值（根据校准结果调整）
        self.adaptive_min_distance = 2000  # 自适应最小距离
        self.adaptive_min_circle_distance = 8000  # 自适应圆形手势最小距离
        
    def send_command(self, cmd: str, flush=True):
        """发送文本命令给STM32（优化版：参考流畅项目，立即发送，无延时）"""
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                return
            
            cmd_str = f"CMD:{cmd}\r\n"
            self.serial_conn.write(cmd_str.encode('utf-8'))
            
            # 立即刷新缓冲区（参考流畅项目：直接操作，不等待）
            if flush:
                self.serial_conn.flush()
            
            # 移除延时，提高响应速度（参考流畅项目：不等待）
        except Exception as e:
            pass  # 静默失败，减少日志
    
    def send_song_name(self, song_name: str, silent=False):
        """通过文本协议发送歌曲名给STM32（改进版：立即同步，支持静默模式）"""
        try:
            name_len = len(song_name)
            
            # 限制长度
            if name_len > 30:
                song_name = song_name[:30]
                name_len = 30
            
            # 发送命令：CMD:NAME,长度,歌曲名（立即发送）
            cmd = f"NAME,{name_len},{song_name}"
            self.send_command(cmd, flush=True)
            
            if not silent:
                print(f"[Command] Sent song name: {song_name} (length: {name_len})")
        except Exception as e:
            if not silent:
                print(f"[Error] 发送歌曲名失败: {e}")
    
    def send_current_song_info(self, song_index=None, silent=False):
        """发送当前歌曲信息给STM32（改进版：确保同步，支持指定索引）"""
        if len(self.music_files) == 0:
            if not silent:
                print("[Warning] No music files available")
            return
        
        try:
            # 使用指定的索引或当前索引
            if song_index is None:
                song_index = self.current_song_index
            
            # 验证索引有效性
            if song_index < 0 or song_index >= len(self.music_files):
                if not silent:
                    print(f"[Warning] 无效的歌曲索引: {song_index}")
                return
            
            # 获取歌曲信息（使用局部变量确保一致性，在发送前就获取）
            file_path, song_name = self.music_files[song_index]
            
            # 确保串口连接正常
            if not self.serial_conn or not self.serial_conn.is_open:
                if not silent:
                    print("[Warning] 串口未打开，无法发送歌曲信息")
                return
            
            # 验证文件路径（用于调试，仅在非静默模式下）
            if not silent:
                file_name = os.path.basename(file_path)
                print(f"[Debug] 准备发送到OLED: 索引={song_index}, 名称={song_name}, 文件={file_name}")
            
            # 第一步：发送歌曲编号：CMD:SONG,编号
            cmd = f"SONG,{song_index}"
            self.send_command(cmd, flush=True)
            
            # 等待STM32处理（增加延时确保命令被处理）
            time.sleep(0.01)  # 增加到10ms，确保STM32有时间处理
            
            # 第二步：发送歌曲名（使用静默模式如果silent=True）
            self.send_song_name(song_name, silent=silent)
            
            # 再次等待，确保歌曲名也被处理
            time.sleep(0.01)
            
            # 确保所有命令已发送完成
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.flush()
            
            # 调试信息：确认发送的内容（仅在非静默模式下）
            if not silent:
                print(f"[Debug] ✓ 已发送歌曲信息到OLED: 索引={song_index}, 名称={song_name}")
        except Exception as e:
            if not silent:
                print(f"[Error] 发送歌曲信息失败: {e}")
                import traceback
                traceback.print_exc()
    
    def send_volume(self, volume_value=None, silent=False):
        """发送音量值给STM32（改进版：确保同步，支持指定音量值）"""
        try:
            # 使用指定的音量值或当前音量
            if volume_value is None:
                volume_value = self.volume
            
            # 确保音量值在有效范围内
            volume_value = max(0, min(100, int(volume_value)))
            
            # 确保串口连接正常
            if not self.serial_conn or not self.serial_conn.is_open:
                if not silent:
                    print("[Warning] 串口未打开，无法发送音量")
                return
            
            # 发送音量命令
            cmd = f"VOLUME,{volume_value}"
            self.send_command(cmd, flush=True)
            
            # 等待STM32处理
            time.sleep(0.01)
            
            # 确保命令已发送完成
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.flush()
            
            if not silent:
                print(f"[Debug] ✓ 已发送音量到OLED: {volume_value}%")
        except Exception as e:
            if not silent:
                print(f"[Error] 发送音量失败: {e}")
                import traceback
                traceback.print_exc()
    
    def send_all_info_to_oled(self):
        """发送所有信息到OLED（歌名、音量、序号、播放状态等）- 静默模式，避免刷屏"""
        try:
            # 确保串口连接正常
            if not self.serial_conn or not self.serial_conn.is_open:
                return
            
            # 发送歌曲信息（序号和歌名）- 使用静默模式
            if len(self.music_files) > 0:
                self.send_current_song_info(song_index=self.current_song_index, silent=True)
                time.sleep(0.01)
            
            # 发送音量 - 使用静默模式
            self.send_volume(volume_value=self.volume, silent=True)
            time.sleep(0.01)
            
            # 发送播放状态（暂停/播放）
            try:
                if hasattr(self, 'is_paused') and self.is_paused:
                    cmd = "PAUSE,1"  # 1表示暂停
                else:
                    cmd = "PAUSE,0"  # 0表示播放
                self.send_command(cmd, flush=True)
                time.sleep(0.01)
            except Exception as e:
                pass  # 静默失败
            
            # 确保所有命令已发送完成
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.flush()
            
        except Exception as e:
            # 静默失败，避免刷屏
            pass
    
    def process_gesture(self, gesture_type: int, x: int, y: int, z: int, reason: str = ""):
        """处理手势命令（优化版：参考流畅项目，简化流程，提高响应速度，增强异常处理）"""
        try:
            current_time = time.time()
            
            # 检查冷却期：确保每两个手势之间至少间隔1秒
            if hasattr(self, 'last_gesture_time') and current_time - self.last_gesture_time < self.gesture_cooldown:
                return  # 在1秒冷却期内，静默忽略
            
            # 移除相同手势检查：允许相同动作，但需间隔1秒（通过冷却期控制）
            # 如果从非NONE手势变为NONE，重置last_gesture
            if gesture_type == GESTURE_NONE:
                if hasattr(self, 'last_gesture') and self.last_gesture != GESTURE_NONE:
                    self.last_gesture = GESTURE_NONE
                return
            
            # 更新状态
            self.last_gesture = gesture_type
            self.last_gesture_time = current_time
            
            gesture_name = self.get_gesture_name(gesture_type)
            print(f"[Gesture] {gesture_name}")
            if reason:
                print(f"[Reason] {reason}")
            
            # 立即发送手势命令给STM32（参考流畅项目：直接调用，不等待）
            try:
                cmd = f"GESTURE,{gesture_type}"
                self.send_command(cmd, flush=True)
            except Exception as send_error:
                print(f"[Error] 发送手势命令失败: {send_error}")
            
            # 立即执行操作，并在操作后立即更新OLED（确保实时同步）
            try:
                if gesture_type == GESTURE_LEFT:
                    self.prev_song()
                    # prev_song内部已经发送了歌曲信息，不需要重复发送
                elif gesture_type == GESTURE_RIGHT:
                    self.next_song()
                    # next_song内部已经发送了歌曲信息，不需要重复发送
                elif gesture_type == GESTURE_UP:
                    self.volume_up()
                    # volume_up内部已经发送了音量，不需要重复发送
                elif gesture_type == GESTURE_DOWN:
                    self.volume_down()
                    # volume_down内部已经发送了音量，不需要重复发送
                elif gesture_type == GESTURE_CLOCKWISE:
                    self.toggle_pause()
                elif gesture_type == GESTURE_COUNTERCLOCKWISE:
                    self.toggle_pause()  # 逆时针也执行暂停/播放切换
            except Exception as action_error:
                print(f"[Error] 执行手势操作失败: {action_error}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"[Error] 处理手势时发生未预期错误: {e}")
            import traceback
            traceback.print_exc()
    
    def get_gesture_name(self, gesture_type: int) -> str:
        """获取手势名称"""
        names = {
            GESTURE_NONE: "None",
            GESTURE_LEFT: "Left (Prev Song)",
            GESTURE_RIGHT: "Right (Next Song)",
            GESTURE_UP: "Up (Volume +)",
            GESTURE_DOWN: "Down (Volume -)",
            GESTURE_CLOCKWISE: "Clockwise (Pause/Play)",
            GESTURE_COUNTERCLOCKWISE: "Counterclockwise (Pause/Play)"
        }
        return names.get(gesture_type, "Unknown")
    
    def play_music(self, file_path: str = None, song_index: int = None):
        """播放音乐文件（改进版：支持通过索引播放，确保同步）"""
        if not HAS_PYGAME or not getattr(self, 'pygame_available', False):
            return
        
        # 优先使用索引，确保和OLED显示一致
        if song_index is not None:
            if song_index < 0 or song_index >= len(self.music_files):
                print(f"[Error] 无效的歌曲索引: {song_index}")
                return
            file_path, song_name = self.music_files[song_index]
            print(f"[Debug] 通过索引播放: 索引={song_index}, 名称={song_name}")
        elif file_path is None:
            # 如果没有提供文件路径，使用当前索引
            if hasattr(self, 'current_song_index') and len(self.music_files) > 0:
                song_index = self.current_song_index
                file_path, song_name = self.music_files[song_index]
                print(f"[Debug] 使用当前索引播放: 索引={song_index}, 名称={song_name}")
            else:
                print("[Error] 没有提供文件路径或索引")
                return
        
        if not file_path or not isinstance(file_path, str):
            self.is_playing = False
            return
        
        if not os.path.exists(file_path):
            self.is_playing = False
            print(f"[Warning] 音乐文件不存在: {file_path}")
            return
        
        try:
            # 获取文件名用于调试
            file_name = os.path.basename(file_path)
            song_name_from_path = os.path.splitext(file_name)[0]
            
            # 验证当前索引对应的文件名是否匹配
            if len(self.music_files) > 0 and hasattr(self, 'current_song_index'):
                try:
                    expected_file_path, expected_song_name = self.music_files[self.current_song_index]
                    if expected_file_path != file_path:
                        print(f"[Error] 文件路径不匹配！")
                        print(f"  当前索引: {self.current_song_index}")
                        print(f"  期望文件: {expected_file_path} ({expected_song_name})")
                        print(f"  实际播放: {file_path} ({song_name_from_path})")
                        # 使用期望的文件路径
                        file_path = expected_file_path
                        song_name_from_path = expected_song_name
                        print(f"[Debug] 已修正为: {file_path} ({song_name_from_path})")
                except (IndexError, AttributeError):
                    pass
            
            # 直接停止并加载（参考流畅项目：不检查状态，直接操作）
            try:
                pygame.mixer.music.stop()
            except Exception as stop_error:
                # 停止失败不影响加载新文件
                pass
            
            try:
                pygame.mixer.music.load(file_path)
            except Exception as load_error:
                print(f"[Error] 加载音乐文件失败: {load_error}")
                self.is_playing = False
                return
            
            try:
                pygame.mixer.music.play()
                self.is_playing = True
                self.is_paused = False  # 重置暂停状态
                print(f"[Music] 正在播放: {song_name_from_path} (文件: {file_name})")
            except Exception as play_error:
                print(f"[Error] 播放音乐失败: {play_error}")
                self.is_playing = False
                self.is_paused = False
        except Exception as e:
            print(f"[Error] 播放音乐时发生错误: {e}")
            import traceback
            traceback.print_exc()
            self.is_playing = False
    
    def stop_music(self):
        """停止播放"""
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
                self.is_playing = False
                self.is_paused = False
                print("[Music] 已停止播放")
            except Exception as e:
                print(f"[Error] 停止播放失败: {e}")
    
    def pause_music(self):
        """暂停播放"""
        if not HAS_PYGAME or not getattr(self, 'pygame_available', False):
            return
        
        if not self.is_playing:
            print("[Music] 当前没有播放音乐")
            return
        
        if self.is_paused:
            print("[Music] 音乐已经暂停")
            return
        
        try:
            pygame.mixer.music.pause()
            self.is_paused = True
            print("[Music] 已暂停播放")
            
            # 发送暂停状态到STM32
            try:
                cmd = "PAUSE,1"  # 1表示暂停
                self.send_command(cmd, flush=True)
            except Exception as e:
                print(f"[Error] 发送暂停状态失败: {e}")
        except Exception as e:
            print(f"[Error] 暂停播放失败: {e}")
    
    def resume_music(self):
        """恢复播放"""
        if not HAS_PYGAME or not getattr(self, 'pygame_available', False):
            return
        
        if not self.is_paused:
            print("[Music] 音乐没有暂停")
            return
        
        try:
            pygame.mixer.music.unpause()
            self.is_paused = False
            print("[Music] 已恢复播放")
            
            # 发送播放状态到STM32
            try:
                cmd = "PAUSE,0"  # 0表示播放
                self.send_command(cmd, flush=True)
            except Exception as e:
                print(f"[Error] 发送播放状态失败: {e}")
        except Exception as e:
            print(f"[Error] 恢复播放失败: {e}")
    
    def toggle_pause(self):
        """切换暂停/播放状态"""
        if self.is_paused:
            self.resume_music()
        else:
            self.pause_music()
    
    def prev_song(self):
        """上一首（优化版：简化流程，提高响应速度，1秒内不允许再次切换）"""
        current_time = time.time()
        
        # 检查歌曲切换冷却期：1秒内不允许再次切换歌曲
        if current_time - self.last_song_change_time < self.song_change_cooldown:
            return  # 在1秒冷却期内，忽略切换请求
        
        if len(self.music_files) == 0:
            return
            
        if self.play_mode == "single":
            return  # 单曲循环模式下不切换
        
        # 更新歌曲切换时间戳
        self.last_song_change_time = current_time
        
        # 计算新索引
        new_index = (self.current_song_index - 1) % len(self.music_files)
        
        # 更新索引（先更新，确保后续操作使用正确的索引）
        self.current_song_index = new_index
        
        # 获取新歌曲信息（使用更新后的索引）
        file_path, song_name = self.music_files[new_index]
        
        print(f"[Debug] 切换歌曲 - 上一首: 索引={new_index}, 名称={song_name}, 文件={os.path.basename(file_path)}")
        
        # 先发送歌曲信息到OLED（使用当前索引确保同步）
        self.send_current_song_info(song_index=new_index)
        
        # 等待OLED更新完成（给STM32时间处理命令）
        time.sleep(0.02)  # 20ms延时，确保OLED已更新
        
        # 然后播放音乐（使用索引确保和OLED显示一致）
        self.play_music(song_index=new_index)
        
        print(f"[Music] ✓ 上一首完成: {song_name} (索引: {new_index})")
    
    def next_song(self):
        """下一首（优化版：简化流程，提高响应速度，1秒内不允许再次切换）"""
        current_time = time.time()
        
        # 检查歌曲切换冷却期：1秒内不允许再次切换歌曲
        if current_time - self.last_song_change_time < self.song_change_cooldown:
            return  # 在1秒冷却期内，忽略切换请求
        
        if len(self.music_files) == 0:
            return
            
        if self.play_mode == "single":
            return  # 单曲循环模式下不切换
        
        # 更新歌曲切换时间戳
        self.last_song_change_time = current_time
        
        # 计算新索引
        new_index = (self.current_song_index + 1) % len(self.music_files)
        
        # 更新索引（先更新，确保后续操作使用正确的索引）
        self.current_song_index = new_index
        
        # 获取新歌曲信息（使用更新后的索引）
        file_path, song_name = self.music_files[new_index]
        
        print(f"[Debug] 切换歌曲 - 下一首: 索引={new_index}, 名称={song_name}, 文件={os.path.basename(file_path)}")
        
        # 先发送歌曲信息到OLED（使用当前索引确保同步）
        self.send_current_song_info(song_index=new_index)
        
        # 等待OLED更新完成（给STM32时间处理命令）
        time.sleep(0.02)  # 20ms延时，确保OLED已更新
        
        # 然后播放音乐（使用索引确保和OLED显示一致）
        self.play_music(song_index=new_index)
        
        print(f"[Music] ✓ 下一首完成: {song_name} (索引: {new_index})")
    
    def set_system_volume(self, volume: int):
        """设置Windows系统音量（改进版：确保同步）"""
        if self.system_volume_interface is None:
            return
        
        try:
            # 确保音量值在有效范围内
            volume = max(0, min(100, int(volume)))
            
            # 音量范围：0.0 到 1.0
            volume_scalar = max(0.0, min(1.0, volume / 100.0))
            self.system_volume_interface.SetMasterVolumeLevelScalar(volume_scalar, None)
            
            # 更新内部音量值，确保一致性
            self.volume = volume
            
            print(f"[Debug] ✓ 已设置系统音量: {volume}%")
        except Exception as e:
            print(f"[Error] 设置系统音量失败: {e}")
            import traceback
            traceback.print_exc()
    
    def volume_up(self):
        """音量加（改进版：确保OLED和系统音量同步）"""
        current_time = time.time()
        
        # 检查音量调整冷却期：1秒内不允许再次调整音量
        if current_time - self.last_volume_time < self.volume_cooldown:
            return  # 在1秒冷却期内，忽略音量调整请求
        
        # 更新音量调整时间戳
        self.last_volume_time = current_time
        
        # 计算新音量值
        new_volume = min(100, self.volume + 5)
        
        print(f"[Debug] 音量调整 - 增加: 从 {self.volume}% 到 {new_volume}%")
        
        # 先更新内部音量值
        self.volume = new_volume
        
        # 先发送到OLED（使用新音量值）
        self.send_volume(volume_value=new_volume)
        
        # 等待OLED更新完成
        time.sleep(0.01)
        
        # 然后设置系统音量（确保和OLED一致）
        self.set_system_volume(new_volume)
        
        print(f"[Volume] ✓ 音量已增加: {new_volume}%")
    
    def volume_down(self):
        """音量减（改进版：确保OLED和系统音量同步）"""
        current_time = time.time()
        
        # 检查音量调整冷却期：1秒内不允许再次调整音量
        if current_time - self.last_volume_time < self.volume_cooldown:
            return  # 在1秒冷却期内，忽略音量调整请求
        
        # 更新音量调整时间戳
        self.last_volume_time = current_time
        
        # 计算新音量值
        new_volume = max(0, self.volume - 5)
        
        print(f"[Debug] 音量调整 - 减少: 从 {self.volume}% 到 {new_volume}%")
        
        # 先更新内部音量值
        self.volume = new_volume
        
        # 先发送到OLED（使用新音量值）
        self.send_volume(volume_value=new_volume)
        
        # 等待OLED更新完成
        time.sleep(0.01)
        
        # 然后设置系统音量（确保和OLED一致）
        self.set_system_volume(new_volume)
        
        print(f"[Volume] ✓ 音量已减少: {new_volume}%")
    
    def set_single_loop(self):
        """设置单曲循环"""
        self.play_mode = "single"
        print(f"[Music] Play mode: Single loop")
        # 手势命令已在process_gesture中发送
    
    def set_list_loop(self):
        """设置列表循环"""
        self.play_mode = "list"
        print(f"[Music] Play mode: List loop")
        # 手势命令已在process_gesture中发送
    
    def parse_gesture_data(self, line: str):
        """解析STM32发送的手势数据"""
        # 格式：X,Y,Z\r\n
        try:
            line = line.strip()
            parts = line.split(',')
            if len(parts) == 3:
                x = int(parts[0])
                y = int(parts[1])
                z = int(parts[2])
                return (x, y, z)
        except ValueError as e:
            # 不是数字格式，可能是其他数据，不打印错误
            pass
        
        return None
    
    def calculate_velocity(self, buffer: List[tuple]) -> tuple:
        """计算速度向量（使用最近几个点的平均速度，改进版：使用更多点）"""
        if len(buffer) < 2:
            return (0, 0)
        
        # 使用最近5个点计算速度（从3增加到5，更平滑）
        recent_points = buffer[-5:] if len(buffer) >= 5 else buffer
        vx_list = []
        vy_list = []
        
        for i in range(1, len(recent_points)):
            dx = recent_points[i][0] - recent_points[i-1][0]
            dy = recent_points[i][1] - recent_points[i-1][1]
            vx_list.append(dx)
            vy_list.append(dy)
        
        if len(vx_list) == 0:
            return (0, 0)
        
        # 使用中位数而不是平均值，减少异常值影响
        vx_sorted = sorted(vx_list)
        vy_sorted = sorted(vy_list)
        mid = len(vx_sorted) // 2
        avg_vx = vx_sorted[mid] if len(vx_sorted) % 2 == 1 else (vx_sorted[mid-1] + vx_sorted[mid]) / 2
        avg_vy = vy_sorted[mid] if len(vy_sorted) % 2 == 1 else (vy_sorted[mid-1] + vy_sorted[mid]) / 2
        
        return (avg_vx, avg_vy)
    
    def check_direction_consistency(self, buffer: List[tuple], direction: str) -> float:
        """检查方向一致性（返回一致性分数 0-1）- 改进版：使用角度判断"""
        if len(buffer) < 3:  # 从5降到3
            return 0.0
        
        # 将缓冲区分成多个段，检查每段的方向是否一致
        segments = min(3, len(buffer) // 2)  # 根据缓冲区大小调整段数
        if segments < 2:
            segments = 2
        segment_size = len(buffer) // segments
        if segment_size < 2:
            segment_size = 2
        
        consistent_count = 0
        total_segments = 0
        
        for i in range(segments):
            start_idx = i * segment_size
            end_idx = start_idx + segment_size
            if end_idx > len(buffer):
                end_idx = len(buffer)
            
            segment = buffer[start_idx:end_idx]
            if len(segment) < 2:
                continue
            
            # 计算该段的方向和角度
            x_start = segment[0][0]
            x_end = segment[-1][0]
            y_start = segment[0][1]
            y_end = segment[-1][1]
            
            x_diff = x_end - x_start
            y_diff = y_end - y_start
            angle = math.atan2(y_diff, x_diff) * 180 / math.pi
            
            total_segments += 1
            
            # 使用角度范围和方向占比检查方向是否一致（改进版）
            angle_normalized = angle
            if angle < 0:
                angle_normalized += 360
            
            # 计算方向占比
            total_abs = abs(x_diff) + abs(y_diff)
            if total_abs == 0:
                continue
            
            x_ratio_seg = abs(x_diff) / total_abs
            y_ratio_seg = abs(y_diff) / total_abs
            
            # 使用更严格的角度范围和方向占比判断
            if direction == "right":
                # 右：0° 到 60° 或 300° 到 360°
                if ((0 <= angle_normalized <= 60) or (300 <= angle_normalized <= 360)) and x_ratio_seg >= 0.6 and x_diff > 0:
                    consistent_count += 1
            elif direction == "left":
                # 左：120° 到 240°
                if (120 <= angle_normalized <= 240) and x_ratio_seg >= 0.6 and x_diff < 0:
                    consistent_count += 1
            elif direction == "up":
                # 上：30° 到 150°
                if (30 <= angle_normalized <= 150) and y_ratio_seg >= 0.6 and y_diff > 0:
                    consistent_count += 1
            elif direction == "down":
                # 下：210° 到 330°
                if (210 <= angle_normalized <= 330) and y_ratio_seg >= 0.6 and y_diff < 0:
                    consistent_count += 1
        
        if total_segments == 0:
            return 0.0
        
        return consistent_count / total_segments
    
    def perform_calibration(self, x: int, y: int, z: int):
        """执行校准：收集数据并计算范围"""
        if not self.calibration_mode:
            return
        
        # 记录最后接收数据的时间
        self._last_calibration_data_time = time.time()
        
        # 过滤无效数据点
        if not self.is_valid_data_point(x, y, z):
            return
        
        # 收集校准数据
        self.calibration_data.append((x, y, z))
        
        # 显示校准进度（每10个样本显示一次）
        if len(self.calibration_data) % 10 == 0:
            progress = min(100, len(self.calibration_data) / self.calibration_samples * 100)
            print(f"[Calibration] 进度: {progress:.0f}% ({len(self.calibration_data)}/{self.calibration_samples})")
        
        # 收集足够的数据后，进行校准计算
        # 严格要求：必须达到目标样本数才能完成校准
        if len(self.calibration_data) >= self.calibration_samples:
            print(f"[Calibration] 已收集足够的样本点 ({len(self.calibration_data)}/{self.calibration_samples})，开始计算校准参数...")
            self.calculate_calibration_parameters()
            self.calibration_mode = False
            self.calibration_complete = True
        elif len(self.calibration_data) >= self.calibration_min_samples:
            # 如果达到最少样本数但未达到目标样本数，继续等待收集更多数据
            # 不完成校准，必须达到目标样本数
            if len(self.calibration_data) % 20 == 0:  # 每20个样本提示一次
                print(f"[Calibration] 已收集 {len(self.calibration_data)}/{self.calibration_samples} 个样本，继续收集中...")
    
    def calculate_calibration_parameters(self):
        """根据校准数据计算参数（改进版：使用统计方法和异常值检测）"""
        if len(self.calibration_data) == 0:
            return
        
        # 提取各轴数据（过滤异常值）
        x_values = [p[0] for p in self.calibration_data if p[0] != 0 and p[0] < 65535]
        y_values = [p[1] for p in self.calibration_data if p[1] != 0 and p[1] < 65535]
        z_values = [p[2] for p in self.calibration_data if p[2] != 0 and p[2] < 65535]
        
        def calculate_robust_range(values, axis_name):
            """使用鲁棒统计方法计算范围（对异常值不敏感）"""
            if len(values) < 3:
                return None, None, None, None
            
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            
            # 使用中位数作为中心（比均值更鲁棒）
            median = sorted_vals[n // 2]
            
            # 使用IQR（四分位距）方法去除异常值
            q1_idx = n // 4
            q3_idx = 3 * n // 4
            q1 = sorted_vals[q1_idx]
            q3 = sorted_vals[q3_idx]
            iqr = q3 - q1
            
            # 使用更严格的分位数（2%和98%）去除极端值
            lower_percentile = max(0.02, 2.0 / n)
            upper_percentile = min(0.98, 1.0 - 2.0 / n)
            
            min_val = sorted_vals[int(n * lower_percentile)]
            max_val = sorted_vals[int(n * upper_percentile)]
            
            # 如果IQR太小，使用分位数范围
            if iqr < 100:
                iqr = max_val - min_val
            
            # 计算动态范围（考虑噪声）
            range_size = max(max_val - min_val, iqr * 1.5)
            
            # 如果范围太小，使用默认值
            if range_size < 500:
                min_val = 0
                max_val = 65535
                range_size = 65535
                median = 32767
            
            return min_val, max_val, median, range_size
        
        # 计算X轴参数
        if len(x_values) > 0:
            self.x_min, self.x_max, self.x_center, self.x_range = calculate_robust_range(x_values, "X")
            if self.x_min is None:
                self.x_min, self.x_max, self.x_center, self.x_range = 0, 65535, 32767, 65535
        else:
            self.x_min, self.x_max, self.x_center, self.x_range = 0, 65535, 32767, 65535
        
        # 计算Y轴参数
        if len(y_values) > 0:
            self.y_min, self.y_max, self.y_center, self.y_range = calculate_robust_range(y_values, "Y")
            if self.y_min is None:
                self.y_min, self.y_max, self.y_center, self.y_range = 0, 65535, 32767, 65535
        else:
            self.y_min, self.y_max, self.y_center, self.y_range = 0, 65535, 32767, 65535
        
        # 计算Z轴参数
        if len(z_values) > 0:
            self.z_min, self.z_max, self.z_center, self.z_range = calculate_robust_range(z_values, "Z")
            if self.z_min is None:
                self.z_min, self.z_max, self.z_center, self.z_range = 0, 65535, 32767, 65535
        else:
            self.z_min, self.z_max, self.z_center, self.z_range = 0, 65535, 32767, 65535
        
        # 根据校准结果计算自适应阈值（改进版：基于统计特性）
        avg_range = (self.x_range + self.y_range) / 2
        
        if avg_range > 1000:
            # 使用标准差估算噪声水平
            if len(x_values) > 10 and len(y_values) > 10:
                x_std = (sum((x - self.x_center) ** 2 for x in x_values) / len(x_values)) ** 0.5
                y_std = (sum((y - self.y_center) ** 2 for y in y_values) / len(y_values)) ** 0.5
                avg_std = (x_std + y_std) / 2
                
                # 最小距离阈值：降低到2.5-4倍标准差，提高灵敏度
                self.adaptive_min_distance = max(800, min(4000, avg_std * 2.5))  # 从4倍降到2.5倍
                # 圆形手势阈值：降低到6-10倍标准差
                self.adaptive_min_circle_distance = max(4000, min(12000, avg_std * 7))  # 从10倍降到7倍
            else:
                # 使用范围百分比作为后备（降低百分比）
                self.adaptive_min_distance = max(800, min(4000, avg_range * 0.025))  # 从3%降到2.5%
                self.adaptive_min_circle_distance = max(4000, min(12000, avg_range * 0.08))  # 从10%降到8%
        else:
            # 使用默认值（降低默认阈值）
            self.adaptive_min_distance = 1500  # 从2000降到1500
            self.adaptive_min_circle_distance = 6000  # 从8000降到6000
    
    def normalize_coordinate(self, value: int, min_val: int, max_val: int, center: float) -> float:
        """归一化坐标值（改进版：使用动态范围和软限制）"""
        if max_val == min_val:
            return 0.0
        
        # 计算动态范围（使用95%置信区间，去除极端值）
        range_size = max_val - min_val
        if range_size < 1000:
            range_size = 65535  # 使用全范围作为后备
        
        # 归一化到 -1 到 1 的范围（相对于中心）
        normalized = (value - center) / (range_size / 2)
        
        # 软限制：使用tanh函数平滑处理超出范围的值
        if abs(normalized) > 1.0:
            normalized = math.tanh(normalized) * 1.0
        
        return normalized
    
    def is_valid_data_point(self, x: int, y: int, z: int) -> bool:
        """检查数据点是否有效（过滤异常值）"""
        # 过滤掉全0的数据点
        if x == 0 and y == 0 and z == 0:
            return False
        # 过滤掉饱和值（65535）过多的数据点（如果两个轴都饱和，可能是异常）
        saturated_count = 0
        if x >= 65535:
            saturated_count += 1
        if y >= 65535:
            saturated_count += 1
        if z >= 65535:
            saturated_count += 1
        if saturated_count >= 2:  # 如果两个或更多轴饱和，可能是异常
            return False
        return True
    
    def check_data_stuck(self, x: int, y: int, z: int) -> bool:
        """检查数据是否卡住（长时间不变）"""
        try:
            current_time = time.time()
            
            # 检查是否与上一个数据点完全相同
            if self.last_data_point is not None:
                last_x, last_y, last_z = self.last_data_point
                # 允许很小的变化（噪声范围内）
                if abs(x - last_x) <= 1 and abs(y - last_y) <= 1 and abs(z - last_z) <= 1:
                    self.stuck_data_count += 1
                    
                    # 如果连续相同数据超过阈值，认为数据卡住
                    if self.stuck_data_count >= self.max_stuck_count:
                        # 每5秒警告一次，避免刷屏
                        if current_time - self.last_stuck_warning_time >= 5.0:
                            print(f"[Warning] 传感器数据卡住（连续{self.stuck_data_count}次相同值: {x},{y},{z}）")
                            print(f"[Warning] 请检查传感器连接或重新校准")
                            self.last_stuck_warning_time = current_time
                            # 清空缓冲区，避免使用卡住的数据
                            self.gesture_data_buffer.clear()
                        return True
                else:
                    # 数据有变化，重置计数
                    self.stuck_data_count = 0
                    self.last_data_point = (x, y, z)
                    return False
            else:
                # 第一次接收数据，初始化
                self.last_data_point = (x, y, z)
                self.stuck_data_count = 0
                return False
        except Exception as e:
            # 如果检测过程中出错，记录错误但不影响主流程
            print(f"[Error] 数据卡住检测出错: {e}")
            return False
    
    def analyze_gesture_from_xyz(self, x: int, y: int, z: int) -> tuple:
        """
        分析手势类型
        返回: (gesture_type, reason) 元组，reason是识别原因的字符串
        """
        """根据xyz数据分析手势类型（全新算法：基于特征提取和模式识别，增强异常处理）"""
        try:
            # 验证输入参数
            if not isinstance(x, int) or not isinstance(y, int) or not isinstance(z, int):
                return (GESTURE_NONE, "无效数据类型")
            
            # 如果还在校准模式，先进行校准
            if hasattr(self, 'calibration_mode') and self.calibration_mode:
                try:
                    self.perform_calibration(x, y, z)
                except Exception as calib_error:
                    print(f"[Error] 校准过程错误: {calib_error}")
                return (GESTURE_NONE, "校准模式中")
            
            # 过滤无效数据点
            try:
                if not self.is_valid_data_point(x, y, z):
                    return (GESTURE_NONE, "无效数据点")
            except Exception as valid_error:
                print(f"[Error] 数据有效性检查失败: {valid_error}")
                return (GESTURE_NONE, "数据检查失败")
            
            # 检查数据是否卡住（长时间不变）
            try:
                if self.check_data_stuck(x, y, z):
                    return (GESTURE_NONE, "数据卡住")  # 数据卡住，不进行手势识别
            except Exception as stuck_error:
                print(f"[Error] 数据卡住检查失败: {stuck_error}")
                # 继续处理，不因为检查失败而中断
            
            # 确保缓冲区存在
            if not hasattr(self, 'gesture_data_buffer'):
                self.gesture_data_buffer = []
            
            # 处理饱和值：使用数据平滑和插值
            try:
                if len(self.gesture_data_buffer) > 0:
                    last_x, last_y, last_z = self.gesture_data_buffer[-1]
                    # 使用线性插值处理饱和值
                    if x >= 65535:
                        x = min(65534, int(last_x * 0.9 + 60000 * 0.1)) if last_x < 60000 else 60000
                    if y >= 65535:
                        y = min(65534, int(last_y * 0.9 + 60000 * 0.1)) if last_y < 60000 else 60000
                    if z >= 65535:
                        z = min(65534, int(last_z * 0.9 + 60000 * 0.1)) if last_z < 60000 else 60000
            except Exception as sat_error:
                print(f"[Error] 处理饱和值失败: {sat_error}")
            
            # 归一化坐标（相对于校准的中心和范围）
            try:
                if hasattr(self, 'calibration_complete') and self.calibration_complete:
                    x_norm = self.normalize_coordinate(x, self.x_min, self.x_max, self.x_center)
                    y_norm = self.normalize_coordinate(y, self.y_min, self.y_max, self.y_center)
                    # 将归一化值转换回0-65535范围以便后续处理
                    x = int((x_norm + 1) * 32767.5)
                    y = int((y_norm + 1) * 32767.5)
                else:
                    # 未校准，使用原始值但限制范围
                    x = max(0, min(65535, x))
                    y = max(0, min(65535, y))
            except Exception as norm_error:
                print(f"[Error] 归一化坐标失败: {norm_error}")
                # 使用原始值但限制范围
                x = max(0, min(65535, x))
                y = max(0, min(65535, y))
            
            # 将xyz数据添加到缓冲区
            try:
                self.gesture_data_buffer.append((x, y, z))
                
                # 增加缓冲区大小：保留最近200个数据点（约0.8秒的数据，假设4ms采样一次）
                # 如果实际采样率较低（约10Hz），200个点可以覆盖约20秒的数据，确保有足够的历史数据用于自适应
                if len(self.gesture_data_buffer) > 200:
                    self.gesture_data_buffer.pop(0)
            except Exception as buffer_error:
                print(f"[Error] 缓冲区操作失败: {buffer_error}")
                return (GESTURE_NONE, "缓冲区操作失败")
            
            # 需要至少8个数据点才能进行可靠的手势分析（降低要求，提高响应速度）
            if len(self.gesture_data_buffer) < 8:
                return (GESTURE_NONE, "数据点不足")
            
            # 改进的静止检测：使用多指标综合判断（使用更多采样点，延长检测窗口）
            try:
                if len(self.gesture_data_buffer) >= 15:
                    recent_points = self.gesture_data_buffer[-15:]  # 延长到15个点进行静止检测，提高准确性
                    x_values = [p[0] for p in recent_points]
                    y_values = [p[1] for p in recent_points]
                    
                    # 计算多个统计指标
                    x_mean = sum(x_values) / len(x_values)
                    y_mean = sum(y_values) / len(y_values)
                    x_variance = sum((x - x_mean) ** 2 for x in x_values) / len(x_values)
                    y_variance = sum((y - y_mean) ** 2 for y in y_values) / len(y_values)
                    x_std = x_variance ** 0.5
                    y_std = y_variance ** 0.5
                    
                    # 计算动态噪声阈值（基于校准数据）
                    if hasattr(self, 'calibration_complete') and self.calibration_complete:
                        noise_threshold = self.adaptive_min_distance * 0.3  # 30%的最小距离作为噪声阈值
                    else:
                        noise_threshold = 400  # 默认噪声阈值
                    
                    # 综合判断：标准差、范围、变化率
                    x_range = max(x_values) - min(x_values)
                    y_range = max(y_values) - min(y_values)
                    
                    # 计算变化率（相邻点的平均变化）
                    x_changes = [abs(x_values[i] - x_values[i-1]) for i in range(1, len(x_values))]
                    y_changes = [abs(y_values[i] - y_values[i-1]) for i in range(1, len(y_values))]
                    avg_x_change = sum(x_changes) / len(x_changes) if x_changes else 0
                    avg_y_change = sum(y_changes) / len(y_changes) if y_changes else 0
                    
                    # 如果所有指标都表明静止，返回NONE
                    if (x_std < noise_threshold and y_std < noise_threshold and
                        x_range < noise_threshold * 2.5 and y_range < noise_threshold * 2.5 and
                        avg_x_change < noise_threshold * 0.5 and avg_y_change < noise_threshold * 0.5):
                        return (GESTURE_NONE, "数据静止")  # 数据太稳定，可能是静止状态
            except Exception as static_error:
                print(f"[Error] 静止检测失败: {static_error}")
            
            # 计算当前速度和加速度（用于动态阈值调整）
            try:
                vx, vy = self.calculate_velocity(self.gesture_data_buffer)
                speed = (vx ** 2 + vy ** 2) ** 0.5
            except Exception as vel_error:
                print(f"[Error] 计算速度失败: {vel_error}")
                return (GESTURE_NONE, "速度计算失败")
            
            # ========== 简化算法：参考DFRobot库的简洁性，提高实时性和流畅性 ==========
            
            # 简化特征提取：使用更大的窗口以利用更多采样点（提高识别准确性）
            def extract_features_simple(buffer, win_size=15):
                """简化特征提取：使用更多采样点，提高识别准确性"""
                if len(buffer) < win_size:
                    return None
                
                # 使用更多历史数据：从缓冲区末尾向前取更多点
                window = buffer[-win_size:]
                x_vals = [p[0] for p in window]
                y_vals = [p[1] for p in window]
                
                # 1. 总位移（核心特征）
                x_displacement = x_vals[-1] - x_vals[0]
                y_displacement = y_vals[-1] - y_vals[0]
                total_displacement = (x_displacement ** 2 + y_displacement ** 2) ** 0.5
                
                # 2. 简化趋势计算：只使用首尾和中间点（减少计算）
                n = len(window)
                mid = n // 2
                x_trend = (x_vals[-1] - x_vals[mid]) / (n - mid) if n > mid else 0
                y_trend = (y_vals[-1] - y_vals[mid]) / (n - mid) if n > mid else 0
                
                # 3. 方向角度（简化计算）
                if x_displacement != 0 or y_displacement != 0:
                    angle = math.atan2(y_displacement, x_displacement) * 180 / math.pi
                    if angle < 0:
                        angle += 360
                else:
                    angle = 0
                
                return {
                    'displacement': total_displacement,
                    'x_displacement': x_displacement,
                    'y_displacement': y_displacement,
                    'x_trend': x_trend,
                    'y_trend': y_trend,
                    'angle': angle
                }
        
            # 提取特征（使用更大的窗口以利用更多采样点，延长自适应时间窗口）
            # 如果采样率较低（约10Hz），使用更大的窗口可以覆盖更长时间的手势，提高自适应能力
            feat = None
            try:
                for win_size in [15, 20, 30, 40]:  # 延长窗口大小，使用更多历史数据，提高自适应准确性
                    feat = extract_features_simple(self.gesture_data_buffer, win_size)
                    if feat is not None:
                        break
            except Exception as feat_error:
                print(f"[Error] 特征提取失败: {feat_error}")
                return (GESTURE_NONE, "特征提取失败")
            
            if feat is None:
                return (GESTURE_NONE, "特征提取失败")
            
            # 优化阈值计算：进一步提高最小位移要求，减少小幅度误判
            try:
                if hasattr(self, 'calibration_complete') and self.calibration_complete:
                    base_threshold = self.adaptive_min_distance * 1.2  # 进一步提高阈值（从1.0提高到1.2），减少误判
                    circle_threshold = self.adaptive_min_circle_distance * 0.8  # 提高圆形手势阈值（从0.7提高到0.8）
                else:
                    base_threshold = 1800  # 进一步提高阈值（从1500提高到1800），减少误判
                    circle_threshold = 5000  # 提高圆形手势阈值（从4000提高到5000）
            except Exception as threshold_error:
                print(f"[Error] 阈值计算失败: {threshold_error}")
                base_threshold = 1800
                circle_threshold = 5000
            
            # 优化速度自适应：提高速度要求
            try:
                speed_factor = max(0.7, min(1.5, speed / 120))  # 进一步提高速度要求（从0.6提高到0.7）
                min_distance = base_threshold * speed_factor * 1.0  # 进一步提高阈值（从0.8提高到1.0），减少误判
            except Exception as speed_error:
                print(f"[Error] 速度自适应计算失败: {speed_error}")
                min_distance = base_threshold
            
            # 检查是否达到最小位移（降低要求）
            try:
                if feat['displacement'] < min_distance:
                    return (GESTURE_NONE, f"位移不足(位移:{feat['displacement']:.0f}, 要求:{min_distance:.0f})")
            except (KeyError, TypeError) as disp_error:
                print(f"[Error] 位移检查失败: {disp_error}")
                return (GESTURE_NONE, "位移检查失败")
            
            # 简化方向判断：参考DFRobot库，优先使用位移和趋势，减少复杂判断
            try:
                x_disp = feat['x_displacement']
                y_disp = feat['y_displacement']
                x_trend = feat['x_trend']
                y_trend = feat['y_trend']
                angle = feat['angle']
            except (KeyError, TypeError) as feat_error:
                print(f"[Error] 特征数据访问失败: {feat_error}")
                return (GESTURE_NONE, "特征数据访问失败")
            
            # 获取当前z值（用于判断是否允许识别上下手势）
            current_z = z  # 使用传入的z值
            try:
                if len(self.gesture_data_buffer) > 0:
                    # 使用缓冲区中最近的z值（更准确）
                    current_z = self.gesture_data_buffer[-1][2]
            except (IndexError, TypeError, AttributeError):
                # 如果缓冲区访问失败，使用传入的z值
                current_z = z
            
            # 计算z值阈值：仅当z值相对较小时才判断上下手势
            # z值较大表示传感器距离物体较近，此时上下手势可能不够准确
            try:
                if hasattr(self, 'calibration_complete') and self.calibration_complete:
                    # 使用校准数据：z值应该小于z_center + z_range * 0.3（即小于中心值+30%范围）
                    z_threshold = self.z_center + self.z_range * 0.3
                else:
                    # 未校准时：使用固定阈值（假设z值小于40000为较小）
                    z_threshold = 40000
            except (AttributeError, TypeError):
                # 如果校准数据访问失败，使用默认阈值
                z_threshold = 40000
        
            # 计算方向占比（简化计算）
            try:
                abs_x = abs(x_disp)
                abs_y = abs(y_disp)
                total_abs = abs_x + abs_y
                
                if total_abs == 0:
                    return (GESTURE_NONE, "总位移为0")
                
                x_ratio = abs_x / total_abs if total_abs > 0 else 0
                y_ratio = abs_y / total_abs if total_abs > 0 else 0
            except Exception as ratio_error:
                print(f"[Error] 方向占比计算失败: {ratio_error}")
                return (GESTURE_NONE, "方向占比计算失败")
            
            # 方向判断阈值：所有手势都需要更大的幅度，提高阈值减少误判
            min_ratio = 0.50  # 主要方向需要占50%以上（上下手势使用，从0.45提高到0.50）
            min_ratio_lr = 0.85  # 左右手势需要占85%以上（从0.80提高到0.85），要求更大的幅度
            
            # 优化判断逻辑：提高左右手势的识别阈值，减少误判
            # 右：X为正且占主导（参考eFilckR：从左到右）- 进一步提高幅度要求
            try:
                if x_disp > 0 and x_trend > 0:
                    # 进一步提高左右手势的识别阈值：需要更大的X方向位移和更高的占比
                    # 要求X占比>=85%且X/Y比>=3.5（从3.0提高到3.5），需要更明显的水平移动
                    if x_ratio >= min_ratio_lr and abs_x > abs_y * 3.5:  # 要求X占比>=85%且X/Y比>=3.5
                        if angle <= 55 or angle >= 305:  # 角度范围更严格（从60/300缩小到55/305）
                            # 额外检查：X方向位移必须足够大（至少是最小距离的3.5倍，从3.0提高到3.5）
                            if abs_x > min_distance * 3.5:
                                reason = (f"向右滑动: X位移={x_disp:.0f}(占比{x_ratio*100:.1f}%), "
                                        f"Y位移={y_disp:.0f}(占比{y_ratio*100:.1f}%), "
                                        f"X/Y比={abs_x/abs_y if abs_y>0 else 0:.2f}, "
                                        f"角度={angle:.1f}°, 总位移={feat['displacement']:.0f}")
                                return (GESTURE_RIGHT, reason)
                
                # 左：X为负且占主导（参考eFilckL：从右到左）- 进一步提高幅度要求
                elif x_disp < 0 and x_trend < 0:
                    # 进一步提高左右手势的识别阈值：需要更大的X方向位移和更高的占比
                    # 要求X占比>=85%且X/Y比>=3.5（从3.0提高到3.5），需要更明显的水平移动
                    if x_ratio >= min_ratio_lr and abs_x > abs_y * 3.5:  # 要求X占比>=85%且X/Y比>=3.5
                        if 125 <= angle <= 235:  # 角度范围更严格（从120-240缩小到125-235）
                            # 额外检查：X方向位移必须足够大（至少是最小距离的3.5倍，从3.0提高到3.5）
                            if abs_x > min_distance * 3.5:
                                reason = (f"向左滑动: X位移={x_disp:.0f}(占比{x_ratio*100:.1f}%), "
                                        f"Y位移={y_disp:.0f}(占比{y_ratio*100:.1f}%), "
                                        f"X/Y比={abs_x/abs_y if abs_y>0 else 0:.2f}, "
                                        f"角度={angle:.1f}°, 总位移={feat['displacement']:.0f}")
                                return (GESTURE_LEFT, reason)
            except Exception as lr_error:
                print(f"[Error] 左右手势判断失败: {lr_error}")
            
            # 上：Y为正且占主导（参考eFilckU：从下到上）
            # 仅当z值相对较小时才判断上下手势
            # 进一步提高阈值（左右：85%占比，3.5倍比例，3.5倍距离；上下：75%占比，2.5倍比例，2.5倍距离）
            try:
                if y_disp > 0 and current_z < z_threshold:
                    # 进一步提高向上手势的识别阈值
                    # 要求Y趋势为正，且Y位移明显大于X位移
                    if y_trend > 0 and abs_y > abs_x * 2.5:  # Y位移需要大于X位移的2.5倍（从2.0提高到2.5）
                        # 要求Y占比>=75%（从65%提高到75%）
                        if y_ratio >= 0.75:
                            # 角度范围：25°到155°（从20-160缩小到25-155，更严格）
                            if 25 <= angle <= 155:
                                # Y方向位移必须足够大（至少是最小距离的2.5倍，从2.0提高到2.5）
                                if abs_y > min_distance * 2.5:
                                    reason = (f"向上滑动: Y位移={y_disp:.0f}(占比{y_ratio*100:.1f}%), "
                                            f"X位移={x_disp:.0f}(占比{x_ratio*100:.1f}%), "
                                            f"Y/X比={abs_y/abs_x if abs_x>0 else 0:.2f}, "
                                            f"角度={angle:.1f}°, 总位移={feat['displacement']:.0f}, Z={current_z:.0f}")
                                    return (GESTURE_UP, reason)
                
                # 下：Y为负且占主导（参考eFilckD：从上到下）
                # 仅当z值相对较小时才判断上下手势
                # 进一步提高阈值
                elif y_disp < 0 and y_trend < 0 and current_z < z_threshold:
                    # 要求Y位移明显大于X位移
                    if abs_y > abs_x * 2.5:  # Y位移需要大于X位移的2.5倍（从2.0提高到2.5）
                        # 要求Y占比>=75%（从65%提高到75%）
                        if y_ratio >= 0.75:
                            # 角度范围：205°到335°（从200-340缩小到205-335，更严格）
                            if 205 <= angle <= 335:
                                # Y方向位移必须足够大（至少是最小距离的2.5倍，从2.0提高到2.5）
                                if abs_y > min_distance * 2.5:
                                    reason = (f"向下滑动: Y位移={y_disp:.0f}(占比{y_ratio*100:.1f}%), "
                                            f"X位移={x_disp:.0f}(占比{x_ratio*100:.1f}%), "
                                            f"Y/X比={abs_y/abs_x if abs_x>0 else 0:.2f}, "
                                            f"角度={angle:.1f}°, 总位移={feat['displacement']:.0f}, Z={current_z:.0f}")
                                    return (GESTURE_DOWN, reason)
            except Exception as ud_error:
                print(f"[Error] 上下手势判断失败: {ud_error}")
            
            # 检测圆形手势
            try:
                if feat['displacement'] > circle_threshold:
                    circle_result = self.detect_circle_direction_advanced()
                    if isinstance(circle_result, tuple):
                        circle_direction, circle_reason = circle_result
                        if circle_direction != GESTURE_NONE:
                            return (circle_direction, circle_reason)
                    elif circle_result != GESTURE_NONE:
                        reason = (f"圆形手势: 总位移={feat['displacement']:.0f}, "
                                 f"X位移={x_disp:.0f}, Y位移={y_disp:.0f}, "
                                 f"角度={angle:.1f}°")
                        return (circle_result, reason)
            except Exception as circle_error:
                print(f"[Error] 圆形手势检测失败: {circle_error}")
            
            return (GESTURE_NONE, f"未匹配: X位移={x_disp:.0f}, Y位移={y_disp:.0f}, "
                                 f"X占比={x_ratio*100:.1f}%, Y占比={y_ratio*100:.1f}%, "
                                 f"角度={angle:.1f}°")
        except Exception as e:
            print(f"[Error] 手势分析发生未预期错误: {e}")
            import traceback
            traceback.print_exc()
            return (GESTURE_NONE, f"分析失败: {str(e)}")
    
    def detect_circle_direction(self) -> int:
        """检测圆形手势的方向（顺时针或逆时针）- 兼容旧接口"""
        return self.detect_circle_direction_advanced()
    
    def detect_circle_direction_advanced(self):
        """检测圆形手势的方向（改进版：使用更精确的算法）
        返回: (gesture_type, reason) 元组或 gesture_type
        """
        if len(self.gesture_data_buffer) < 12:
            return (GESTURE_NONE, "圆形手势点数不足")
        
        # 使用最近的数据点（最多30个）
        buffer = self.gesture_data_buffer[-min(30, len(self.gesture_data_buffer)):]
        
        # 计算中心点（使用加权平均，给中间的点更高权重）
        n = len(buffer)
        weights = [1.0 - abs(i - n/2) / (n/2) for i in range(n)]  # 中间权重高
        total_weight = sum(weights)
        
        center_x = sum(p[0] * w for p, w in zip(buffer, weights)) / total_weight
        center_y = sum(p[1] * w for p, w in zip(buffer, weights)) / total_weight
        
        # 计算每个点相对于中心的角度和距离
        angles = []
        distances = []
        
        for x, y, z in buffer:
            dx = x - center_x
            dy = y - center_y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            
            if dist < 100:  # 距离太近，跳过
                continue
            
            angle = math.atan2(dy, dx)
            angles.append(angle)
            distances.append(dist)
        
        if len(angles) < 10:
            return (GESTURE_NONE, "圆形手势角度点数不足")
        
        # 检查是否形成圆形（距离变化应该较小）
        avg_dist = 0
        dist_std = 0
        if len(distances) > 5:
            avg_dist = sum(distances) / len(distances)
            dist_variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
            dist_std = dist_variance ** 0.5
            
            # 如果距离变化太大，可能不是圆形
            if dist_std > avg_dist * 0.4:
                return (GESTURE_NONE, f"圆形手势距离变化太大(标准差:{dist_std:.0f}, 平均距离:{avg_dist:.0f})")
        
        # 计算角度变化（处理周期性）
        angle_changes = []
        for i in range(1, len(angles)):
            diff = angles[i] - angles[i-1]
            # 处理角度跨越-π到π的情况
            if diff > math.pi:
                diff -= 2 * math.pi
            elif diff < -math.pi:
                diff += 2 * math.pi
            angle_changes.append(diff)
        
        if len(angle_changes) < 5:
            return (GESTURE_NONE, "圆形手势角度变化点数不足")
        
        # 使用加权平均（给中间的变化更高权重）
        weighted_changes = []
        for i, change in enumerate(angle_changes):
            weight = 1.0 - abs(i - len(angle_changes)/2) / (len(angle_changes)/2)
            weighted_changes.append(change * weight)
        
        total_weight = sum(1.0 - abs(i - len(angle_changes)/2) / (len(angle_changes)/2) 
                          for i in range(len(angle_changes)))
        avg_change = sum(weighted_changes) / total_weight if total_weight > 0 else 0
        
        # 检查角度变化的一致性
        change_variance = sum((c - avg_change) ** 2 for c in angle_changes) / len(angle_changes)
        change_std = change_variance ** 0.5
        
        # 如果变化不一致，可能不是圆形
        if change_std > abs(avg_change) * 0.8:
            return (GESTURE_NONE, f"圆形手势角度变化不一致(标准差:{change_std:.3f}, 平均变化:{avg_change:.3f})")
        
        # 判断方向（正值为逆时针，负值为顺时针）
        threshold = 0.03  # 降低阈值以提高灵敏度
        
        # 计算距离一致性（使用之前计算的avg_dist和dist_std）
        if len(distances) > 5 and avg_dist > 0:
            dist_consistency = 1.0 - min(1.0, dist_std / avg_dist)
        else:
            dist_consistency = 0.0
        
        # 计算角度一致性
        angle_consistency = 1.0 - min(1.0, change_std / abs(avg_change)) if avg_change != 0 else 0.0
        total_angle_change = sum(abs(c) for c in angle_changes) * 180 / math.pi  # 转换为度
        
        if avg_change > threshold:
            # 检查是否至少转了半圈
            total_rotation = sum(abs(c) for c in angle_changes)
            if total_rotation > math.pi * 0.8:  # 至少转了80%的圆
                reason = (f"逆时针转圈: 总角度变化={total_angle_change:.1f}°, "
                         f"平均距离={avg_dist:.0f}, 距离一致性={dist_consistency:.2f}, "
                         f"角度一致性={angle_consistency:.2f}")
                return (GESTURE_COUNTERCLOCKWISE, reason)
        elif avg_change < -threshold:
            total_rotation = sum(abs(c) for c in angle_changes)
            if total_rotation > math.pi * 0.8:
                reason = (f"顺时针转圈: 总角度变化={total_angle_change:.1f}°, "
                         f"平均距离={avg_dist:.0f}, 距离一致性={dist_consistency:.2f}, "
                         f"角度一致性={angle_consistency:.2f}")
                return (GESTURE_CLOCKWISE, reason)
        
        return (GESTURE_NONE, f"圆形手势不完整(总旋转:{total_angle_change:.1f}°, 需要:{math.pi*0.8*180/math.pi:.1f}°)")
    
    def serial_receive_thread(self):
        """串口接收线程（改进版：添加超时和性能优化，增强异常处理）"""
        buffer = ""
        error_count = 0
        max_errors = 10  # 最大连续错误次数
        last_data_time = time.time()
        no_data_timeout = 5.0  # 5秒没有数据就警告
        
        while self.running:
            try:
                # 检查串口是否打开
                if not self.serial_conn:
                    print("[Error] 串口对象不存在，等待重连...")
                    time.sleep(1)
                    continue
                
                try:
                    if not self.serial_conn.is_open:
                        print("[Error] 串口未打开，等待重连...")
                        time.sleep(1)
                        continue
                except (AttributeError, OSError) as e:
                    print(f"[Error] 检查串口状态失败: {e}")
                    time.sleep(1)
                    continue
                
                # 使用非阻塞读取，设置超时
                try:
                    # 检查是否有数据（非阻塞）
                    try:
                        in_waiting = self.serial_conn.in_waiting
                    except (AttributeError, OSError) as e:
                        print(f"[Error] 检查串口数据失败: {e}")
                        time.sleep(0.5)
                        continue
                    
                    if in_waiting > 0:
                        # 限制每次读取的数据量，防止一次读取太多导致卡住
                        read_size = min(in_waiting, 1024)
                        try:
                            data = self.serial_conn.read(read_size)
                            if data:
                                buffer += data.decode('utf-8', errors='ignore')
                                last_data_time = time.time()
                        except (UnicodeDecodeError, OSError) as decode_error:
                            print(f"[Error] 串口数据解码错误: {decode_error}")
                            # 清空缓冲区，避免累积错误数据
                            buffer = ""
                            time.sleep(0.1)
                            continue
                        
                        # 限制缓冲区大小，防止内存溢出
                        if len(buffer) > 10000:
                            print("[Warning] 串口缓冲区过大，清空缓冲区")
                            buffer = buffer[-1000:]  # 保留最后1000个字符
                    else:
                        # 没有数据时，检查是否超时
                        if time.time() - last_data_time > no_data_timeout:
                            print(f"[Warning] 超过{no_data_timeout}秒未收到数据，请检查串口连接")
                            last_data_time = time.time()  # 重置，避免重复打印
                except Exception as read_error:
                    print(f"[Error] 串口读取错误: {read_error}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(0.1)
                    continue
                
                # 按行处理（限制处理数量，防止卡住）
                lines_processed = 0
                max_lines_per_loop = 10  # 每次循环最多处理10行
                
                try:
                    while '\n' in buffer and self.running and lines_processed < max_lines_per_loop:
                        try:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            lines_processed += 1
                        except ValueError:
                            # 分割失败，可能buffer格式有问题
                            buffer = ""
                            break
                        
                        if line:
                            # 解析手势数据（格式：X,Y,Z\r\n）
                            try:
                                result = self.parse_gesture_data(line)
                                if result:
                                    x, y, z = result
                                    
                                    # 验证数据有效性
                                    if not isinstance(x, int) or not isinstance(y, int) or not isinstance(z, int):
                                        continue
                                    
                                    # 如果还在校准模式，不进行手势识别
                                    if self.calibration_mode:
                                        try:
                                            self.perform_calibration(x, y, z)
                                        except Exception as calib_error:
                                            print(f"[Error] 校准过程错误: {calib_error}")
                                        continue
                                    
                                    # 每50个数据点打印一次调试信息（校准完成后）
                                    self.debug_count += 1
                                    
                                    # 根据xyz数据分析手势类型（添加超时保护）
                                    try:
                                        # 检查缓冲区是否存在
                                        if not hasattr(self, 'gesture_data_buffer'):
                                            self.gesture_data_buffer = []
                                        
                                        # 使用简单的超时检查：如果缓冲区太大，跳过复杂计算
                                        if len(self.gesture_data_buffer) > 100:
                                            # 缓冲区过大，清理旧数据
                                            self.gesture_data_buffer = self.gesture_data_buffer[-50:]
                                        
                                        # 执行手势分析（限制执行时间）
                                        analysis_start = time.time()
                                        try:
                                            gesture_result = self.analyze_gesture_from_xyz(x, y, z)
                                        except Exception as analysis_inner_error:
                                            print(f"[Error] 手势分析内部错误: {analysis_inner_error}")
                                            import traceback
                                            traceback.print_exc()
                                            continue
                                        
                                        analysis_time = time.time() - analysis_start
                                        
                                        # 如果分析时间过长，警告
                                        if analysis_time > 0.1:  # 超过100ms
                                            print(f"[Warning] 手势分析耗时过长: {analysis_time:.3f}s")
                                        
                                        # 处理返回结果（可能是元组或单个值）
                                        if isinstance(gesture_result, tuple) and len(gesture_result) >= 2:
                                            gesture_type, gesture_reason = gesture_result[0], gesture_result[1]
                                        elif isinstance(gesture_result, tuple) and len(gesture_result) == 1:
                                            gesture_type = gesture_result[0]
                                            gesture_reason = "未知原因"
                                        else:
                                            gesture_type = gesture_result if gesture_result is not None else GESTURE_NONE
                                            gesture_reason = "未知原因"
                                        
                                        if gesture_type != GESTURE_NONE:
                                            # 识别到有效手势，立即清空缓冲区（避免重复识别）
                                            try:
                                                # 先清空缓冲区，确保每个手势动作独立分析
                                                self.gesture_data_buffer.clear()
                                                # 设置忽略期，避免识别到手势返回动作
                                                self.last_gesture_ignore_time = time.time()
                                                # 处理手势（内部会检查冷却期和重复手势，并打印检测信息）
                                                self.process_gesture(gesture_type, x, y, z, gesture_reason)
                                            except Exception as process_error:
                                                print(f"[Error] 处理手势错误: {process_error}")
                                                import traceback
                                                traceback.print_exc()
                                    except Exception as gesture_error:
                                        print(f"[Error] 手势分析错误: {gesture_error}")
                                        import traceback
                                        traceback.print_exc()
                            except Exception as parse_error:
                                # 解析失败，可能是其他数据
                                if len(line) > 0 and not line.startswith('CMD:'):
                                    # 只在调试模式下打印
                                    if self.debug_count % 100 == 0:
                                        try:
                                            print(f"[Serial] Received: {line[:50]}")  # 只打印前50个字符
                                        except:
                                            pass
                except Exception as line_process_error:
                    print(f"[Error] 行处理错误: {line_process_error}")
                    import traceback
                    traceback.print_exc()
                    buffer = ""  # 清空缓冲区，避免累积错误
                
                # 重置错误计数
                error_count = 0
                time.sleep(0.001)  # 减少到1ms延时，提高采样率响应速度
                
            except serial.SerialException as e:
                error_count += 1
                print(f"[Error] 串口异常 ({error_count}/{max_errors}): {e}")
                if error_count >= max_errors:
                    print("[Error] 串口错误过多，停止接收线程")
                    break
                time.sleep(0.5)
            except KeyboardInterrupt:
                print("[System] 接收线程收到中断信号")
                break
            except Exception as e:
                error_count += 1
                print(f"[Error] 串口接收线程错误 ({error_count}/{max_errors}): {e}")
                import traceback
                traceback.print_exc()
                if error_count >= max_errors:
                    print("[Error] 错误过多，停止接收线程")
                    break
                time.sleep(0.1)
    
    def start(self):
        """启动控制器"""
        import traceback
        try:
            # 打开串口
            print(f"[System] Opening serial port {self.port} at {self.baudrate} baud...")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            time.sleep(0.5)  # 等待串口稳定（从2秒减少到0.5秒）
            
            print("[System] Serial port opened successfully")
            print("[System] Starting gesture control music player...")
            
            self.running = True
            
            # 启动接收线程（增强异常处理）
            receive_thread = None
            try:
                def safe_receive_thread():
                    """安全的接收线程包装器"""
                    try:
                        self.serial_receive_thread()
                    except Exception as thread_inner_error:
                        print(f"[Error] 接收线程内部错误: {thread_inner_error}")
                        import traceback
                        traceback.print_exc()
                        # 线程异常不应该导致主程序崩溃
                
                receive_thread = threading.Thread(target=safe_receive_thread, daemon=True)
                receive_thread.start()
                print("[System] 串口接收线程已启动")
            except Exception as thread_error:
                print(f"[Error] 启动接收线程失败: {thread_error}")
                import traceback
                traceback.print_exc()
                # 不抛出异常，让程序继续运行
            
            # 进入校准模式
            print("[System] =========================================")
            print("[System] 进入手势校准模式")
            print("[System] 请在传感器前做几个手势动作（上下左右滑动）")
            print("[System] 校准中...")
            print("[System] =========================================")
            
            # 初始化校准开始时间
            self._calibration_start_time = time.time()
            calibration_start_time = time.time()
            last_warning_time = 0
            last_progress_time = 0
            print("[Calibration] 等待接收数据...")
            
            while not self.calibration_complete and self.running:
                time.sleep(0.1)
                
                # 检查是否超时（延长到30秒，给更多时间收集足够的样本）
                elapsed = time.time() - calibration_start_time
                if elapsed > 30:
                    # 严格要求：必须达到目标样本数才能完成校准
                    if len(self.calibration_data) >= self.calibration_samples:
                        print(f"[Calibration] 校准超时，但已收集足够的样本点 ({len(self.calibration_data)}/{self.calibration_samples})")
                        self.calculate_calibration_parameters()
                        self.calibration_complete = True
                        self.calibration_mode = False
                    else:
                        # 样本数不足，继续等待或提示用户
                        print("[Error] 校准超时，样本数不足！")
                        print(f"[Error] 已收集 {len(self.calibration_data)}/{self.calibration_samples} 个样本（需要至少{self.calibration_samples}个样本）")
                        print("[Error] 请确保：")
                        print("  1. STM32正在发送数据")
                        print("  2. 传感器正常工作")
                        print("  3. 在传感器前做手势动作以收集数据")
                        print("[Error] 将继续等待更多数据...")
                        # 不完成校准，继续等待
                        # 重置超时时间，再给一次机会
                        calibration_start_time = time.time()
                        print("[Calibration] 重新开始计时，继续收集数据...")
                
                # 检查是否长时间没有收到数据（延长到5秒，每5秒提示一次）
                current_time = time.time()
                if current_time - last_warning_time >= 5:
                    last_data_time = getattr(self, '_last_calibration_data_time', calibration_start_time)
                    if current_time - last_data_time > 5:
                        if len(self.calibration_data) == 0:
                            print("[Warning] 未收到任何数据，请检查：")
                            print("  1. STM32是否已连接并运行")
                            print("  2. 串口是否正确（当前: " + self.port + ")")
                            print("  3. 传感器是否正常工作")
                        elif len(self.calibration_data) < self.calibration_samples:
                            print(f"[Calibration] 数据接收较慢，当前: {len(self.calibration_data)}/{self.calibration_samples}")
                    last_warning_time = current_time
                
                # 每2秒显示一次进度（如果有数据）
                if current_time - last_progress_time >= 2:
                    if len(self.calibration_data) > 0:
                        progress = min(100, len(self.calibration_data) / self.calibration_samples * 100)
                        print(f"[Calibration] 进度: {progress:.0f}% ({len(self.calibration_data)}/{self.calibration_samples})")
                    last_progress_time = current_time
            
            if self.calibration_complete:
                print("[System] =========================================")
                print("[System] 校准完成！")
                print(f"[System] X范围: {self.x_min} ~ {self.x_max} (中心: {self.x_center:.0f}, 范围: {self.x_range:.0f})")
                print(f"[System] Y范围: {self.y_min} ~ {self.y_max} (中心: {self.y_center:.0f}, 范围: {self.y_range:.0f})")
                print(f"[System] Z范围: {self.z_min} ~ {self.z_max} (中心: {self.z_center:.0f}, 范围: {self.z_range:.0f})")
                print(f"[System] 自适应阈值: 最小距离={self.adaptive_min_distance:.0f}, 圆形={self.adaptive_min_circle_distance:.0f}")
                print("[System] =========================================")
                print("[System] 开始手势识别，等待手势数据...")
            
            # 显示音乐列表信息
            if len(self.music_files) > 0:
                print(f"[System] 找到 {len(self.music_files)} 首音乐:")
                for i, (file_path, song_name) in enumerate(self.music_files[:5]):  # 只显示前5首
                    print(f"[System]   {i+1}. {song_name}")
                if len(self.music_files) > 5:
                    print(f"[System]   ... 还有 {len(self.music_files) - 5} 首")
            else:
                print("[Warning] 未找到音乐文件！")
            
            # 发送初始歌曲信息和音量
            try:
                time.sleep(0.2)
                if len(self.music_files) > 0:
                    try:
                        # 先发送歌曲信息
                        self.send_current_song_info()
                        
                        # 等待一下，确保歌曲信息已发送
                        time.sleep(0.01)
                        
                        # 然后发送音量信息（确保OLED显示正确的音量）
                        self.send_volume(volume_value=self.volume)
                        
                        print(f"[System] 已发送初始音量到OLED: {self.volume}%")
                    except Exception as send_error:
                        print(f"[Warning] 发送初始信息失败: {send_error}")
                        traceback.print_exc()
                    
                    # 设置初始系统音量（确保系统音量和OLED显示一致）
                    try:
                        # 如果系统音量接口可用，确保系统音量与OLED显示一致
                        if self.system_volume_interface is not None:
                            self.set_system_volume(self.volume)
                        else:
                            print(f"[System] 系统音量接口不可用，仅更新OLED显示: {self.volume}%")
                    except Exception as e:
                        print(f"[Warning] 设置初始音量失败: {e}")
                    
                    # 自动播放第一首
                    try:
                        file_path, _ = self.music_files[self.current_song_index]
                        self.play_music(file_path)
                    except Exception as e:
                        print(f"[Warning] 自动播放失败: {e}")
                        print("[Info] 可以手动使用手势控制播放")
            except Exception as init_error:
                print(f"[Warning] 初始化播放信息时出错: {init_error}")
                import traceback
                traceback.print_exc()
            
            # 主循环（检查音乐播放状态，每秒更新OLED）
            last_oled_update_time = time.time()
            oled_update_interval = 1.0  # 每秒更新一次
            
            try:
                while self.running:
                    try:
                        # 每秒更新一次OLED信息
                        current_time = time.time()
                        if current_time - last_oled_update_time >= oled_update_interval:
                            try:
                                self.send_all_info_to_oled()
                                last_oled_update_time = current_time
                            except Exception as update_error:
                                # 静默失败，避免刷屏
                                pass
                        
                        # 检查音乐播放状态，如果播放结束且不是单曲循环，自动播放下一首
                        if (HAS_PYGAME and getattr(self, 'pygame_available', False) 
                            and hasattr(self, 'is_playing') and self.is_playing):
                            try:
                                if len(self.music_files) > 0:
                                    is_busy = pygame.mixer.music.get_busy()
                                    if not is_busy:
                                        try:
                                            if self.play_mode == "list":
                                                # 列表循环，播放下一首
                                                # 计算新索引
                                                new_index = (self.current_song_index + 1) % len(self.music_files)
                                                
                                                # 更新索引（先更新，确保后续操作使用正确的索引）
                                                self.current_song_index = new_index
                                                
                                                # 获取新歌曲信息（使用更新后的索引）
                                                file_path, song_name = self.music_files[new_index]
                                                
                                                print(f"[Music] Auto next: {song_name} (索引: {new_index})")
                                                
                                                # 先发送歌曲信息到OLED（使用当前索引确保同步）
                                                try:
                                                    self.send_current_song_info(song_index=new_index)
                                                    # 等待OLED更新完成
                                                    time.sleep(0.02)
                                                except Exception as send_err:
                                                    print(f"[Warning] 发送歌曲信息失败: {send_err}")
                                                
                                                # 然后播放音乐（使用索引确保和OLED显示一致）
                                                try:
                                                    self.play_music(song_index=new_index)
                                                except Exception as play_err:
                                                    print(f"[Warning] 播放音乐失败: {play_err}")
                                            elif self.play_mode == "single":
                                                # 单曲循环，重新播放当前首
                                                # 使用当前索引确保一致性
                                                current_index = self.current_song_index
                                                
                                                # 确保OLED显示当前歌曲信息
                                                try:
                                                    self.send_current_song_info(song_index=current_index)
                                                except Exception as send_err:
                                                    print(f"[Warning] 发送歌曲信息失败: {send_err}")
                                                
                                                # 然后播放音乐（使用索引确保和OLED显示一致）
                                                try:
                                                    self.play_music(song_index=current_index)
                                                except Exception as play_err:
                                                    print(f"[Warning] 播放音乐失败: {play_err}")
                                        except (IndexError, AttributeError) as index_err:
                                            print(f"[Warning] 索引错误: {index_err}")
                                            self.is_playing = False
                                        except Exception as auto_play_err:
                                            print(f"[Warning] 自动播放处理失败: {auto_play_err}")
                                            import traceback
                                            traceback.print_exc()
                            except Exception as music_error:
                                # pygame调用失败，重置播放状态
                                print(f"[Warning] 检查音乐播放状态失败: {music_error}")
                                import traceback
                                traceback.print_exc()
                                try:
                                    self.is_playing = False
                                except:
                                    pass
                    except KeyboardInterrupt:
                        print("\n[System] 收到中断信号，正在关闭...")
                        self.running = False
                        break
                    except Exception as loop_error:
                        print(f"[Error] 主循环错误: {loop_error}")
                        import traceback
                        traceback.print_exc()
                        # 不要退出，继续运行
                    
                    try:
                        time.sleep(0.5)  # 检查间隔
                    except:
                        pass
            except KeyboardInterrupt:
                print("\n[System] Shutting down...")
                self.stop()
            except Exception as main_loop_error:
                print(f"[Error] 主循环发生严重错误: {main_loop_error}")
                import traceback
                traceback.print_exc()
                self.stop()
        
        except serial.SerialException as e:
            print(f"[Error] Serial port error: {e}")
            print("[Error] Please check:")
            print("  1. Serial port number is correct")
            print("  2. STM32 is connected")
            print("  3. No other program is using the port")
        except Exception as e:
            print(f"[Error] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()
    
    def stop(self):
        """停止控制器（增强异常处理）"""
        try:
            self.running = False
        except:
            pass
        
        # 停止音乐播放
        try:
            self.stop_music()
        except Exception as stop_music_err:
            print(f"[Warning] 停止音乐失败: {stop_music_err}")
        
        # 关闭串口
        try:
            if hasattr(self, 'serial_conn') and self.serial_conn:
                try:
                    if self.serial_conn.is_open:
                        self.serial_conn.close()
                        print("[System] Serial port closed")
                except Exception as close_err:
                    print(f"[Warning] 关闭串口失败: {close_err}")
        except Exception as serial_err:
            print(f"[Warning] 串口清理失败: {serial_err}")
        
        # 清理pygame
        if HAS_PYGAME:
            try:
                pygame.mixer.quit()
            except Exception as pygame_err:
                print(f"[Warning] 清理pygame失败: {pygame_err}")


def main():
    """主函数"""
    global _global_log_file, _global_log_path
    
    # 使用全局日志文件
    log_file = _global_log_file
    log_file_path = _global_log_path
    
    def log_error(message):
        """记录错误到日志文件和屏幕"""
        _log_crash(message)
    
    try:
        # 默认串口配置
        port = 'COM11'  # Windows默认，Linux/Mac使用 '/dev/ttyUSB0' 或 '/dev/ttyACM0'
        baudrate = 115200
        
        # 从命令行参数获取串口
        if len(sys.argv) > 1:
            port = sys.argv[1]
        if len(sys.argv) > 2:
            baudrate = int(sys.argv[2])
        
        print("=" * 60)
        print("手势控制音乐播放器 - PC端控制器")
        print("=" * 60)
        print(f"串口: {port}")
        print(f"波特率: {baudrate}")
        print("=" * 60)
        print("\n手势控制说明:")
        print("  向左滑动  -> 上一首")
        print("  向右滑动  -> 下一首")
        print("  向左滑动  -> 上一首")
        print("  向右滑动  -> 下一首")
        print("  向上滑动  -> 音量加")
        print("  向下滑动  -> 音量减")
        print("  转圈（顺时针/逆时针） -> 暂停/播放")
        print("=" * 60)
        print()
        
        # 检查依赖库
        print("[System] 检查依赖库...")
        if not HAS_PYCAW:
            print("[Warning] pycaw未安装，系统音量控制功能将不可用")
            print("[Info] 安装命令: pip install pycaw")
        if not HAS_PYGAME:
            print("[Warning] pygame未安装，音乐播放功能将不可用")
            print("[Info] 安装命令: pip install pygame")
        print()
        
        # 创建并启动控制器
        print("[System] 初始化控制器...")
        controller = None
        try:
            controller = MusicPlayerController(port=port, baudrate=baudrate, music_dir='Music')
            print("[System] 启动控制器...")
            controller.start()
        except Exception as controller_error:
            print(f"[Error] 控制器初始化或启动失败: {controller_error}")
            import traceback
            traceback.print_exc()
            # 不要raise，让外层的异常处理来处理
            if controller:
                try:
                    controller.stop()
                except:
                    pass
            raise  # 重新抛出，让外层处理
        
    except KeyboardInterrupt:
        print("\n[System] 用户中断，正在退出...")
        try:
            if 'controller' in locals() and controller:
                controller.stop()
        except:
            pass
        try:
            input("\n按Enter键退出...")
        except:
            pass
        sys.exit(0)
    except Exception as e:
        import traceback
        error_msg = "\n" + "=" * 60 + "\n"
        error_msg += "[Error] 程序运行出错！\n"
        error_msg += "=" * 60 + "\n"
        error_msg += f"错误类型: {type(e).__name__}\n"
        error_msg += f"错误信息: {str(e)}\n"
        error_msg += "\n详细错误信息:\n"
        error_msg += "-" * 60 + "\n"
        try:
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            error_msg += traceback_str
        except Exception as trace_error:
            error_msg += f"无法打印详细错误信息: {trace_error}\n"
        error_msg += "-" * 60 + "\n"
        error_msg += "\n可能的解决方案:\n"
        error_msg += "1. 检查是否安装了所有依赖库: pip install -r requirements.txt\n"
        error_msg += "2. 检查串口是否正确连接\n"
        error_msg += "3. 检查Music文件夹是否存在且包含音乐文件\n"
        error_msg += "4. 如果是在Windows上，确保以管理员权限运行（用于音量控制）\n"
        if log_file_path:
            error_msg += f"5. 查看日志文件获取详细错误信息: {log_file_path}\n"
        else:
            error_msg += "5. 查看 crash_log.txt 文件获取详细错误信息（如果存在）\n"
        error_msg += "=" * 60 + "\n"
        
        print(error_msg)
        
        # 记录到日志文件
        if 'log_error' in locals():
            log_error(error_msg)
        
        # 确保控制器被正确停止
        try:
            if 'controller' in locals() and controller:
                controller.stop()
        except Exception as stop_error:
            print(f"[Warning] 停止控制器时出错: {stop_error}")
        
        # 等待用户输入，防止窗口立即关闭
        try:
            input("\n按Enter键退出...")
        except (EOFError, KeyboardInterrupt):
            # 如果无法读取输入（例如在非交互式环境中），等待一段时间
            import time
            time.sleep(2)
        except Exception as input_error:
            print(f"[Warning] 等待输入时出错: {input_error}")
            import time
            time.sleep(2)
        
        if log_file:
            try:
                log_file.close()
            except:
                pass
        
        sys.exit(1)
    except BaseException as e:
        # 捕获所有其他异常（包括SystemExit）
        import traceback
        error_msg = "\n[Error] 发生未预期的异常:\n"
        try:
            error_msg += ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        except:
            error_msg += str(e) + "\n"
        
        print(error_msg)
        
        # 记录到日志文件
        if 'log_error' in locals():
            log_error(error_msg)
        
        try:
            if 'controller' in locals() and controller:
                controller.stop()
        except:
            pass
        try:
            input("\n按Enter键退出...")
        except:
            import time
            time.sleep(2)
        
        if _global_log_file:
            try:
                _global_log_file.close()
            except:
                pass
        
        sys.exit(1)
    finally:
        # 确保日志文件被关闭
        if _global_log_file:
            try:
                _global_log_file.close()
                _global_log_file = None
            except:
                pass


if __name__ == '__main__':
    # 在最外层添加异常处理，确保任何错误都能被捕获
    try:
        # 确保日志已初始化
        if _global_log_file is None:
            _init_crash_log()
        
        # 记录程序开始运行
        _log_crash("[System] 开始执行 main() 函数")
        
        # 调用主函数
        main()
        
        # 记录程序正常结束
        _log_crash("[System] 程序正常结束")
        
    except KeyboardInterrupt:
        _log_crash("[System] 用户中断程序")
        try:
            input("\n按Enter键退出...")
        except:
            pass
    except Exception as e:
        # 这是最后的异常捕获，确保所有错误都被记录
        error_msg = f"[CRITICAL] 程序在 main() 外层发生异常: {type(e).__name__}: {e}\n"
        try:
            import traceback
            error_msg += "堆栈跟踪:\n"
            error_msg += ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        except:
            error_msg += "无法获取堆栈跟踪\n"
        
        _log_crash(error_msg)
        
        # 尝试直接写入文件
        try:
            if _global_log_path:
                with open(_global_log_path, 'a', encoding='utf-8') as f:
                    f.write(error_msg)
                    f.write("\n按Enter键退出...\n")
        except:
            pass
        
        try:
            input("\n按Enter键退出...")
        except:
            import time
            time.sleep(3)
    finally:
        # 确保日志文件被关闭
        try:
            if _global_log_file:
                _global_log_file.close()
        except:
            pass


