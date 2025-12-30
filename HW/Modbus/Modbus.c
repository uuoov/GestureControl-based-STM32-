/*********************************************************************************************************
* 模块名称：Modbus.c
* 功能说明：Modbus协议处理模块实现
* 当前版本：1.0.0
* 作    者：SZLY
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************
* 修改版本：
* 作    者：
* 生成日期：
* 修改内容：
* 修改文件：
*********************************************************************************************************/

/*********************************************************************************************************
*                                              包含头文件
*********************************************************************************************************/
#include "Modbus.h"
#include "stm32f10x_conf.h"
#include <string.h>

/*********************************************************************************************************
*                                              内部变量
*********************************************************************************************************/
// 保持寄存器数组
static u16 s_holding_regs[256] = {0};
// 歌曲名字符串
static u8  s_song_name[32] = {0};
// 歌曲名长度
static u8  s_song_name_len = 0;

/*********************************************************************************************************
*                                              内部函数声明
*********************************************************************************************************/
static u8 ModbusReadHoldingRegs(u8 *req, u8 req_len, u8 *resp);
static u8 ModbusWriteSingleReg(u8 *req, u8 req_len, u8 *resp);
static u8 ModbusWriteMultipleRegs(u8 *req, u8 req_len, u8 *resp);

/*********************************************************************************************************
*                                              内部函数实现
*********************************************************************************************************/

/*********************************************************************************************************
* 函数名称：ModbusCalculateCRC
* 函数功能：计算Modbus CRC16校验值
* 输入参数：buf - 数据缓冲区，len - 数据长度
* 输出参数：无
* 返回值：CRC16校验值
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
u16 ModbusCalculateCRC(u8 *buf, u8 len)
{
    u16 crc = 0xFFFF;
    u8 i, j;
    
    for (i = 0; i < len; i++) {
        crc ^= buf[i];
        for (j = 0; j < 8; j++) {
            if (crc & 0x0001) {
                crc = (crc >> 1) ^ 0xA001;
            } else {
                crc >>= 1;
            }
        }
    }
    
    return crc;
}

/*********************************************************************************************************
* 函数名称：ModbusReadHoldingRegs
* 函数功能：处理读取保持寄存器请求
* 输入参数：req - 请求数据，req_len - 请求长度，resp - 响应缓冲区
* 输出参数：resp - 响应数据
* 返回值：响应长度
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
static u8 ModbusReadHoldingRegs(u8 *req, u8 req_len, u8 *resp)
{
    u16 start_addr = (req[2] << 8) | req[3];
    u16 reg_count = (req[4] << 8) | req[5];
    u8  resp_len = 0;
    u8  i;
    
    // 检查寄存器地址范围
    if (start_addr > 255 || (start_addr + reg_count) > 256) {
        resp[0] = req[0];
        resp[1] = req[1] | 0x80;
        resp[2] = MODBUS_ERR_ILLEGAL_ADDRESS;
        resp_len = 3;
        return resp_len;
    }
    
    // 构建响应帧
    resp[0] = req[0];           // 从机地址
    resp[1] = req[1];           // 功能码
    resp[2] = reg_count * 2;    // 数据字节数
    resp_len = 3;
    
    // 填充数据
    for (i = 0; i < reg_count; i++) {
        resp[resp_len++] = (s_holding_regs[start_addr + i] >> 8) & 0xFF;
        resp[resp_len++] = s_holding_regs[start_addr + i] & 0xFF;
    }
    
    // 特殊处理歌曲名读取
    if (start_addr == REG_SONG_NAME && reg_count > 0) {
        u8 name_idx = 0;
        for (i = 0; i < reg_count; i++) {
            u16 reg_val = 0;
            if (name_idx < s_song_name_len) {
                reg_val = s_song_name[name_idx++];
                if (name_idx < s_song_name_len) {
                    reg_val |= (s_song_name[name_idx++] << 8);
                }
            }
            resp[3 + i * 2] = (reg_val >> 8) & 0xFF;
            resp[4 + i * 2] = reg_val & 0xFF;
        }
    }
    
    return resp_len;
}

/*********************************************************************************************************
* 函数名称：ModbusWriteSingleReg
* 函数功能：处理写入单个寄存器请求
* 输入参数：req - 请求数据，req_len - 请求长度，resp - 响应缓冲区
* 输出参数：resp - 响应数据
* 返回值：响应长度
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
static u8 ModbusWriteSingleReg(u8 *req, u8 req_len, u8 *resp)
{
    u16 reg_addr = (req[2] << 8) | req[3];
    u16 reg_val = (req[4] << 8) | req[5];
    u8 i;
    
    // 检查寄存器地址范围
    if (reg_addr > 255) {
        resp[0] = req[0];
        resp[1] = req[1] | 0x80;
        resp[2] = MODBUS_ERR_ILLEGAL_ADDRESS;
        return 3;
    }
    
    // 写入寄存器
    s_holding_regs[reg_addr] = reg_val;
    
    // 构建响应帧（回显请求）
    for (i = 0; i < 6; i++) {
        resp[i] = req[i];
    }
    
    return 6;
}

/*********************************************************************************************************
* 函数名称：ModbusWriteMultipleRegs
* 函数功能：处理写入多个寄存器请求
* 输入参数：req - 请求数据，req_len - 请求长度，resp - 响应缓冲区
* 输出参数：resp - 响应数据
* 返回值：响应长度
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
static u8 ModbusWriteMultipleRegs(u8 *req, u8 req_len, u8 *resp)
{
    u16 start_addr = (req[2] << 8) | req[3];
    u16 reg_count = (req[4] << 8) | req[5];
    u8  i;
    
    // 检查寄存器地址范围
    if (start_addr > 255 || (start_addr + reg_count) > 256) {
        resp[0] = req[0];
        resp[1] = req[1] | 0x80;
        resp[2] = MODBUS_ERR_ILLEGAL_ADDRESS;
        return 3;
    }
    
    // 写入寄存器
    for (i = 0; i < reg_count; i++) {
        s_holding_regs[start_addr + i] = (req[7 + i * 2] << 8) | req[8 + i * 2];
    }
    
    // 特殊处理歌曲名写入
    if (start_addr == REG_SONG_NAME && reg_count > 0) {
        u8 name_idx = 0;
        for (i = 0; i < reg_count; i++) {
            u16 reg_val = (req[7 + i * 2] << 8) | req[8 + i * 2];
            if (name_idx < sizeof(s_song_name)) {
                s_song_name[name_idx++] = reg_val & 0xFF;
            }
            if (name_idx < sizeof(s_song_name)) {
                s_song_name[name_idx++] = (reg_val >> 8) & 0xFF;
            }
        }
        // 更新歌曲名长度
        s_song_name_len = s_holding_regs[REG_SONG_NAME_LEN];
        if (s_song_name_len > sizeof(s_song_name)) {
            s_song_name_len = sizeof(s_song_name);
        }
    }
    
    // 构建响应帧
    resp[0] = req[0];               // 从机地址
    resp[1] = req[1];               // 功能码
    resp[2] = req[2];               // 起始地址高字节
    resp[3] = req[3];               // 起始地址低字节
    resp[4] = req[4];               // 寄存器数量高字节
    resp[5] = req[5];               // 寄存器数量低字节
    
    return 6;
}

/*********************************************************************************************************
*                                              外部函数实现
*********************************************************************************************************/

/*********************************************************************************************************
* 函数名称：InitModbus
* 函数功能：初始化Modbus模块
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
void InitModbus(void)
{
    // 初始化寄存器值
    s_holding_regs[REG_GESTURE_CMD] = GESTURE_NONE;
    s_holding_regs[REG_VOLUME] = 50;  // 默认音量50%
    s_holding_regs[REG_CURRENT_SONG] = 0;
    s_holding_regs[REG_SONG_NAME_LEN] = 0;
}

/*********************************************************************************************************
* 函数名称：ModbusParseFrame
* 函数功能：解析Modbus请求帧并生成响应
* 输入参数：buf - 请求数据，len - 请求长度，resp - 响应缓冲区
* 输出参数：resp - 响应数据
* 返回值：响应长度，0表示无效帧
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
u8 ModbusParseFrame(u8 *buf, u8 len, u8 *resp)
{
    u8 resp_len = 0;
    u16 crc;
    u16 recv_crc;
    
    // 检查帧长度
    if (len < 5) {
        return 0;
    }
    
    // 验证CRC
    crc = ModbusCalculateCRC(buf, len - 2);
    recv_crc = (buf[len - 1] << 8) | buf[len - 2];
    if (crc != recv_crc) {
        return 0;
    }
    
    // 处理不同功能码
    switch (buf[1]) {
        case MODBUS_FC_READ_HOLDING_REGS:
            resp_len = ModbusReadHoldingRegs(buf, len, resp);
            break;
        case MODBUS_FC_WRITE_SINGLE_REG:
            resp_len = ModbusWriteSingleReg(buf, len, resp);
            break;
        case MODBUS_FC_WRITE_MULTIPLE_REGS:
            resp_len = ModbusWriteMultipleRegs(buf, len, resp);
            break;
        default:
            // 非法功能码
            resp[0] = buf[0];
            resp[1] = buf[1] | 0x80;
            resp[2] = MODBUS_ERR_ILLEGAL_FUNCTION;
            resp_len = 3;
            break;
    }
    
    // 添加CRC
    if (resp_len > 0) {
        u16 crc = ModbusCalculateCRC(resp, resp_len);
        resp[resp_len++] = crc & 0xFF;
        resp[resp_len++] = (crc >> 8) & 0xFF;
    }
    
    return resp_len;
}

/*********************************************************************************************************
* 函数名称：ModbusSetGestureCmd
* 函数功能：设置手势命令
* 输入参数：cmd - 手势命令
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
void ModbusSetGestureCmd(u8 cmd)
{
    s_holding_regs[REG_GESTURE_CMD] = cmd;
}

/*********************************************************************************************************
* 函数名称：ModbusGetGestureCmd
* 函数功能：获取手势命令
* 输入参数：无
* 输出参数：无
* 返回值：手势命令
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
u8 ModbusGetGestureCmd(void)
{
    return (u8)s_holding_regs[REG_GESTURE_CMD];
}

/*********************************************************************************************************
* 函数名称：ModbusSetVolume
* 函数功能：设置音量
* 输入参数：volume - 音量值（0-100）
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
void ModbusSetVolume(u8 volume)
{
    if (volume > 100) {
        volume = 100;
    }
    s_holding_regs[REG_VOLUME] = volume;
}

/*********************************************************************************************************
* 函数名称：ModbusGetVolume
* 函数功能：获取音量
* 输入参数：无
* 输出参数：无
* 返回值：音量值（0-100）
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
u8 ModbusGetVolume(void)
{
    return (u8)s_holding_regs[REG_VOLUME];
}

/*********************************************************************************************************
* 函数名称：ModbusSetCurrentSong
* 函数功能：设置当前歌曲
* 输入参数：song - 歌曲编号
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
void ModbusSetCurrentSong(u16 song)
{
    s_holding_regs[REG_CURRENT_SONG] = song;
}

/*********************************************************************************************************
* 函数名称：ModbusGetCurrentSong
* 函数功能：获取当前歌曲
* 输入参数：无
* 输出参数：无
* 返回值：歌曲编号
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
u16 ModbusGetCurrentSong(void)
{
    return s_holding_regs[REG_CURRENT_SONG];
}

/*********************************************************************************************************
* 函数名称：ModbusSetSongName
* 函数功能：设置歌曲名
* 输入参数：name - 歌曲名字符串，len - 字符串长度
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
void ModbusSetSongName(u8 *name, u8 len)
{
    u8 i;
    
    if (len > sizeof(s_song_name)) {
        len = sizeof(s_song_name);
    }
    memcpy(s_song_name, name, len);
    s_song_name_len = len;
    s_holding_regs[REG_SONG_NAME_LEN] = len;
    
    // 将歌曲名写入保持寄存器
    for (i = 0; i < len; i += 2) {
        u16 reg_val = name[i];
        if (i + 1 < len) {
            reg_val |= (name[i + 1] << 8);
        }
        s_holding_regs[REG_SONG_NAME + (i / 2)] = reg_val;
    }
}

/*********************************************************************************************************
* 函数名称：ModbusGetSongName
* 函数功能：获取歌曲名
* 输入参数：name - 存放歌曲名的缓冲区，len - 输出歌曲名长度
* 输出参数：name - 歌曲名字符串，len - 字符串长度
* 返回值：无
* 生成日期：2025年12月29日
* 注    意：
*********************************************************************************************************/
void ModbusGetSongName(u8 *name, u8 *len)
{
    if (name != NULL) {
        memcpy(name, s_song_name, s_song_name_len);
    }
    if (len != NULL) {
        *len = s_song_name_len;
    }
}
