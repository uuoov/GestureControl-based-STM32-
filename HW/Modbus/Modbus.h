/*********************************************************************************************************
* 模块名称：Modbus.h
* 功能说明：Modbus协议处理模块头文件
* 当前版本：1.0.0
* 作    者：Leo Leung
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************
* 修改版本：
* 作    者：
* 生成日期：
* 修改内容：
* 修改文件：
*********************************************************************************************************/

#ifndef __MODBUS_H__
#define __MODBUS_H__

/*********************************************************************************************************
*                                              包含头文件
*********************************************************************************************************/
#include "DataType.h"

/*********************************************************************************************************
*                                              定义
*********************************************************************************************************/
// Modbus功能码
#define MODBUS_FC_READ_COILS           0x01
#define MODBUS_FC_READ_DISCRETE_INPUTS 0x02
#define MODBUS_FC_READ_HOLDING_REGS    0x03
#define MODBUS_FC_READ_INPUT_REGS      0x04
#define MODBUS_FC_WRITE_SINGLE_COIL    0x05
#define MODBUS_FC_WRITE_SINGLE_REG     0x06
#define MODBUS_FC_WRITE_MULTIPLE_COILS 0x0F
#define MODBUS_FC_WRITE_MULTIPLE_REGS  0x10

// Modbus错误码
#define MODBUS_ERR_ILLEGAL_FUNCTION    0x01
#define MODBUS_ERR_ILLEGAL_ADDRESS     0x02
#define MODBUS_ERR_ILLEGAL_DATA_VALUE  0x03
#define MODBUS_ERR_SLAVE_DEVICE_FAILURE 0x04

// Modbus寄存器地址
#define REG_GESTURE_CMD                0x0000  // 手势命令寄存器
#define REG_VOLUME                     0x0001  // 音量寄存器
#define REG_CURRENT_SONG               0x0002  // 当前歌曲寄存器
#define REG_SONG_NAME_LEN              0x0003  // 歌曲名长度寄存器
#define REG_SONG_NAME                  0x0004  // 歌曲名寄存器起始地址

// 手势命令定义
#define GESTURE_NONE                   0x00
#define GESTURE_LEFT                   0x01    // 向左滑动：上一首
#define GESTURE_RIGHT                  0x02    // 向右滑动：下一首
#define GESTURE_UP                     0x03    // 向上滑动：音量加
#define GESTURE_DOWN                   0x04    // 向下滑动：音量减
#define GESTURE_CLOCKWISE              0x05    // 顺时针转圈：单曲循环
#define GESTURE_COUNTERCLOCKWISE       0x06    // 逆时针转圈：列表循环

// Modbus帧最大长度
#define MODBUS_MAX_FRAME_LEN           256

/*********************************************************************************************************
*                                              结构体定义
*********************************************************************************************************/
// Modbus帧结构体
typedef struct {
    u8  addr;           // 从机地址
    u8  func;           // 功能码
    u8  data[MODBUS_MAX_FRAME_LEN - 4];  // 数据区
    u16 data_len;       // 数据长度
    u16 crc;            // CRC校验
}ModbusFrame_t;

/*********************************************************************************************************
*                                              外部函数声明
*********************************************************************************************************/
void InitModbus(void);                                 // 初始化Modbus模块
u8  ModbusParseFrame(u8 *buf, u8 len, u8 *resp);       // 解析Modbus帧并生成响应
u16 ModbusCalculateCRC(u8 *buf, u8 len);               // 计算CRC校验
void ModbusSetGestureCmd(u8 cmd);                      // 设置手势命令
u8  ModbusGetGestureCmd(void);                         // 获取手势命令
void ModbusSetVolume(u8 volume);                       // 设置音量
u8  ModbusGetVolume(void);                             // 获取音量
void ModbusSetCurrentSong(u16 song);                   // 设置当前歌曲
u16 ModbusGetCurrentSong(void);                        // 获取当前歌曲
void ModbusSetSongName(u8 *name, u8 len);              // 设置歌曲名
void ModbusGetSongName(u8 *name, u8 *len);             // 获取歌曲名

#endif /* __MODBUS_H__ */
