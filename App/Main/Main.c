/*********************************************************************************************************
* 模块名称：Main.c
* 简    介：该文件主要负责硬件初始化和main函数
* 当前版本：1.0.0
* 作    者：SZLY(COPYRIGHT 2018 - 2020 SZLY. All rights reserved.)
* 创建日期：2020年01月01日
* 数    据：
* 注    意：注意勾选Options for Target 'Target1'->Code Generation->Use MicroLIB，否则printf无法使用                                                                 34→**********************************************************************************************************
* 更新版本：
* 作    者：
* 更新日期：
* 更新数据：
* 更新文件：
*********************************************************************************************************/

/*********************************************************************************************************
*                                              包含头文件
*********************************************************************************************************/
#include "Main.h"
#include "stm32f10x_conf.h"
#include "DataType.h"
#include "NVIC.h"
#include "SysTick.h"
#include "RCC.h"
#include "Timer.h"
#include "UART1.h"
#include "LED.h"
#include "OLED.h"
#include "RunClock.h"
#include "Modbus.h"
#include "Gesture.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/*********************************************************************************************************
*                                              �궨��
*********************************************************************************************************/

/*********************************************************************************************************
*                                              内部变量
*********************************************************************************************************/
static u8 TimeString[20] = {'\0'};
static u8 g_uart_rx_buf[128] = {0};  // UART接收缓冲区（文本协议，不需要那么大）
static u8 g_uart_rx_len = 0;                         // UART接收长度
static u8 g_song_name[32] = {0};                     // 当前歌曲名
static u8 g_song_name_len = 0;                       // 歌曲名长度
static u8 g_display_update_flag = 0;                 // 显示更新标志
static u8 g_send_counter = 0;                        // 发送计数器，用于控制发送频率

/*********************************************************************************************************
*                                              结构体类型定义
*********************************************************************************************************/

/*********************************************************************************************************
*                                              内部函数声明
*********************************************************************************************************/
static  void  InitSoftware(void);   //初始化软件相关模块
static  void  InitHardware(void);   //初始化硬件相关模块
static  void  Proc2msTask(void);    //2ms定时任务
static  void  Proc1SecTask(void);   //1s定时任务

/*********************************************************************************************************
*                                              内部函数实现
*********************************************************************************************************/
/*********************************************************************************************************
* 函数名称：InitSoftware
* 函数功能：将所有软件相关的模块初始化函数放在此处
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 生成日期：2018年01月01日
* 注    意：
*********************************************************************************************************/
static  void  InitSoftware(void)
{
  InitRunClock();
}

/*********************************************************************************************************
* 函数名称：InitHardware
* 函数功能：将所有硬件相关的模块初始化函数放在此处
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 生成日期：2018年01月01日
* 注    意：
*********************************************************************************************************/
static  void  InitHardware(void)
{
  SystemInit();       //系统初始化
  InitRCC();          //初始化RCC模块
  InitNVIC();         //初始化NVIC模块
  InitUART1(115200);  //初始化UART模块
  InitTimer();        //初始化Timer模块
  InitLED();          //初始化LED模块
  InitSysTick();      //初始化SysTick模块
  InitOLED();         //初始化 OLED 模块
  InitModbus();       //初始化Modbus模块
  InitGesture();      //初始化手势传感器模块

}

/*********************************************************************************************************
* 函数名称：Proc2msTask
* 函数功能：2ms定时任务 
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 生成日期：2018年01月01日
* 注    意：
*********************************************************************************************************/
static  void  Proc2msTask(void)
{  
  if(Get2msFlag())  //判断2ms标志状态
  {
    u8 rx_len;
    u8 sensor_gesture;
    u16 x_pos, y_pos, z_pos;
    char data_buf[64];
    char *cmd_end;  // 命令解析相关变量
    char *cmd;
    char *name_start;
    u8 gesture, volume, name_len;
    u16 song;
    u8 processed_len;
    u8 data_len, sent_len;
    
    LEDFlicker(250);//LED闪烁指示
    RunClockPer2Ms(); //时钟模块，每2ms执行一次   
    
    // 采集手势传感器数据
    GestureSensorDataRecv();
    
    // 获取当前手势信息和xyz位置
    sensor_gesture = GestureGetGestureInfo();
    GestureGetPosition(&x_pos, &y_pos, &z_pos);
    
    // 控制发送频率：每2ms发送一次（每秒500次），进一步提高数据更新频率以增强灵敏度
    // 在115200波特率下，发送约20字节需要约1.7ms，每2ms发送一次可以保证稳定传输
    g_send_counter++;
    if (g_send_counter >= 1) {  // 1 * 2ms = 2ms，进一步提高发送频率（从2降到1）
        g_send_counter = 0;
        
        // 如果三轴数据都为0，则不发送（传感器未检测到位置数据）
        if (x_pos != 0 || y_pos != 0 || z_pos != 0) {
            // 发送格式：X,Y,Z\r\n
            data_len = sprintf(data_buf, "%d,%d,%d\r\n", 
                                  x_pos, y_pos, z_pos);
            sent_len = WriteUART1((u8*)data_buf, data_len);
            
            // 如果发送缓冲区满（返回长度小于请求长度），说明发送速度跟不上
            // 这种情况下数据会被丢弃，但不会阻塞主循环
            if (sent_len < data_len) {
                // 缓冲区满，可以考虑进一步降低发送频率
                // 这里不做处理，让系统自然调节
            }
        }
    }
    
    // 检查UART接收数据（简单文本协议）
    rx_len = ReadUART1(g_uart_rx_buf + g_uart_rx_len, 128 - g_uart_rx_len);
    if (rx_len > 0) {
        g_uart_rx_len += rx_len;
        g_uart_rx_buf[g_uart_rx_len] = '\0';  // 确保字符串结束
        
        // 查找完整的命令（以\r\n结尾）
        cmd_end = strstr((char*)g_uart_rx_buf, "\r\n");
        if (cmd_end != NULL) {
            *cmd_end = '\0';  // 截断命令
            
            // 解析命令
            // 格式：CMD:TYPE,VALUE1,VALUE2,...\r\n
            if (strncmp((char*)g_uart_rx_buf, "CMD:", 4) == 0) {
                cmd = (char*)g_uart_rx_buf + 4;
                
                // 解析手势命令：CMD:GESTURE,1
                if (strncmp(cmd, "GESTURE,", 8) == 0) {
                    gesture = (u8)atoi(cmd + 8);
                    ModbusSetGestureCmd(gesture);
                    g_display_update_flag = 1;
                }
                // 解析音量：CMD:VOLUME,50
                else if (strncmp(cmd, "VOLUME,", 7) == 0) {
                    volume = (u8)atoi(cmd + 7);
                    ModbusSetVolume(volume);
                    g_display_update_flag = 1;
                }
                // 解析歌曲编号：CMD:SONG,0
                else if (strncmp(cmd, "SONG,", 5) == 0) {
                    song = (u16)atoi(cmd + 5);
                    ModbusSetCurrentSong(song);
                    g_display_update_flag = 1;
                }
                // 解析歌曲名：CMD:NAME,14,Song 1 - Happy
                else if (strncmp(cmd, "NAME,", 5) == 0) {
                    name_start = strchr(cmd + 5, ',');
                    if (name_start != NULL) {
                        *name_start = '\0';
                        name_len = (u8)atoi(cmd + 5);
                        name_start++;
                        
                        // 复制歌曲名
                        if (name_len > 31) name_len = 31;
                        memcpy(g_song_name, name_start, name_len);
                        g_song_name[name_len] = '\0';
                        g_song_name_len = name_len;
                        ModbusSetSongName(g_song_name, g_song_name_len);
                        g_display_update_flag = 1;
                    }
                }
            }
            
            // 清除已处理的命令
            processed_len = (u8)(cmd_end - (char*)g_uart_rx_buf) + 2;  // +2 for \r\n
            if (processed_len <= g_uart_rx_len) {
                memmove(g_uart_rx_buf, g_uart_rx_buf + processed_len, g_uart_rx_len - processed_len);
                g_uart_rx_len -= processed_len;
                g_uart_rx_buf[g_uart_rx_len] = '\0';  // 确保字符串结束
            } else {
                g_uart_rx_len = 0;
            }
        } else if (g_uart_rx_len >= 128) {
            // 缓冲区溢出，清除
            g_uart_rx_len = 0;
        }
    }
    
    Clr2msFlag();   //清除2ms标志

  }
}

/*********************************************************************************************************
* 函数名称：Proc1SecTask
* 函数功能：1s定时任务 
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 生成日期：2018年01月01日
* 注    意：
*********************************************************************************************************/
static  void  Proc1SecTask(void)
{ 
  u8 volume;
  u16 current_song;
  u8 gesture_cmd;
  char gesture_str[20];
  
  if(Get1SecFlag()) //判断1s标志状态
  {
    // 获取当前播放信息（从Modbus寄存器读取，由PC端设置）
    ModbusGetSongName(g_song_name, &g_song_name_len);
    volume = ModbusGetVolume();
    current_song = ModbusGetCurrentSong();
    gesture_cmd = ModbusGetGestureCmd();
    
    // 根据手势命令显示对应的操作
    switch(gesture_cmd) {
        case GESTURE_NONE: strcpy(gesture_str, "None"); break;
        case GESTURE_LEFT: strcpy(gesture_str, "Prev Song"); break;
        case GESTURE_RIGHT: strcpy(gesture_str, "Next Song"); break;
        case GESTURE_UP: strcpy(gesture_str, "Vol +"); break;
        case GESTURE_DOWN: strcpy(gesture_str, "Vol -"); break;
        case GESTURE_CLOCKWISE: strcpy(gesture_str, "Single Loop"); break;
        case GESTURE_COUNTERCLOCKWISE: strcpy(gesture_str, "List Loop"); break;
        default: strcpy(gesture_str, "Unknown"); break;
    }
    
    // 更新OLED显示（优化显示布局）
    if (g_display_update_flag || Get1SecFlag()) {
        OLEDClear();
        
        // 显示标题（居中显示）
        OLEDShowString(12, 0, "Music Player");
        
        // 显示当前歌曲（优化布局）
        OLEDShowString(0, 16, "Song:");
        if (g_song_name_len > 0) {
            // 如果歌曲名太长，尝试滚动显示或截断
            u8 display_len = g_song_name_len > 14 ? 14 : g_song_name_len;  // 减少到14字符以适应布局
            u8 display_name[15];
            memcpy(display_name, g_song_name, display_len);
            display_name[display_len] = '\0';
            OLEDShowString(32, 16, display_name);
        } else {
            OLEDShowString(32, 16, "No Song");
        }
        
        // 显示歌曲编号和音量（优化布局）
        sprintf((char*)TimeString, "No.%d", current_song + 1);  // 显示从1开始的编号
        OLEDShowString(0, 32, TimeString);
        
        // 显示音量（优化位置）
        sprintf((char*)TimeString, "Vol:%d%%", volume);
        OLEDShowString(56, 32, TimeString);
        
        // 显示当前手势命令（优化显示）
        OLEDShowString(0, 48, "Gesture:");
        // 根据手势类型显示不同的信息
        if (gesture_cmd != GESTURE_NONE) {
            OLEDShowString(56, 48, (const u8*)gesture_str);
        } else {
            OLEDShowString(56, 48, "Ready");
        }
        
        OLEDRefreshGRAM();
        g_display_update_flag = 0;
    }
    
    Clr1SecFlag();  //清除1s标志
  }    
}

/*********************************************************************************************************
* 函数名称：main
* 函数功能：主函数 
* 输入参数：void
* 输出参数：void
* 返 回 值：int
* 生成日期：2018年01月01日
* 注    意：
*********************************************************************************************************/
int main(void)
{ 
  // 先初始化软件和硬件，包括UART1
  InitSoftware();   //初始化软件相关模块
  InitHardware();   //初始化硬件相关模块，包括UART1

  while(1)
  {
    Proc2msTask();  //2ms定时任务
    Proc1SecTask(); //1s定时任务   
  }
}
