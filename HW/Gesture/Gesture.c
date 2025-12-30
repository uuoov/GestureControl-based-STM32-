/*********************************************************************************************************
*                                              包含头文件
*********************************************************************************************************/
#include "Gesture.h"
#include "SysTick.h"
#include "stm32f10x.h"       // 必须先包含，定义I2C_TypeDef等基础类型
#include "stm32f10x_conf.h"  // 这个文件包含了外设头文件
#include <stdio.h>
#include <string.h>

/*********************************************************************************************************
*                                              内部变量
*********************************************************************************************************/
static sInfo_t info;                      // 手势传感器信息

/*********************************************************************************************************
*                                              内部函数声明
*********************************************************************************************************/
static void I2C_Hardware_Init(void);      // 初始化硬件I2C
static void MGC3130_reset(void);          // 重置传感器
static void EIO0_SetOutput(void);         // 设置EIO0为输出模式
static void EIO0_SetInput(void);          // 设置EIO0为输入模式
static void EIO0_WriteLow(void);          // 将EIO0拉低
static void EIO0_WriteHigh(void);         // 将EIO0拉高
static u8 EIO0_Read(void);                // 读取EIO0引脚状态
static u8 SetRuntimeParameter(u8 *pBuf, u8 size);  // 发送RuntimeParameter命令（Arduino库方式）
static u8 ReadSensorData(u8 *pBuf, u8 size);        // 读取传感器数据（Arduino库方式）
static u8 DisableTouchDetection(void);    // 禁用触摸检测
static u8 DisableApproachDetection(void); // 禁用接近检测
static u8 DisableAirWheel(void);          // 禁用滚轮功能
static u8 DisableGestures(void);          // 禁用手势识别（初始化时禁用，之后启用）
static u8 EnableGestures(void);           // 启用手势识别
static u8 EnableDataOutput(void);         // 启用数据输出
static u8 LockDataOutput(void);           // 锁定数据输出格式

/*********************************************************************************************************
*                                              外部函数实现
*********************************************************************************************************/

/*********************************************************************************************************
* 函数名称：InitGesture
* 函数功能：初始化手势传感器
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：按照Arduino库的方式初始化
*********************************************************************************************************/
void InitGesture(void)
{
    u16 retry_count;  // 重试计数器
    
    // 初始化硬件I2C
    I2C_Hardware_Init();
    
    // 设置EIO0为输入模式
    EIO0_SetInput();
    
    // 重置传感器
    MGC3130_reset();
    
    // 按照Arduino库的方式配置传感器
    
    // 1. 禁用触摸检测（最多重试200次，每次10ms，总共2秒）
    retry_count = 0;
    while (DisableTouchDetection() != 0) {
        retry_count++;
        if (retry_count > 200) {
            printf("[Gesture] ERROR: DisableTouchDetection timeout!\r\n");
            return;
        }
        DelayNms(10);
    }
    
    // 2. 禁用接近检测
    retry_count = 0;
    while (DisableApproachDetection() != 0) {
        retry_count++;
        if (retry_count > 200) {
            printf("[Gesture] ERROR: DisableApproachDetection timeout!\r\n");
            return;
        }
        DelayNms(10);
    }
    
    // 3. 禁用滚轮功能
    retry_count = 0;
    while (DisableAirWheel() != 0) {
        retry_count++;
        if (retry_count > 200) {
            printf("[Gesture] ERROR: DisableAirWheel timeout!\r\n");
            return;
        }
        DelayNms(10);
    }
    
    // 4. 禁用手势识别（初始化时先禁用）
    retry_count = 0;
    while (DisableGestures() != 0) {
        retry_count++;
        if (retry_count > 200) {
            printf("[Gesture] ERROR: DisableGestures timeout!\r\n");
            return;
        }
        DelayNms(10);
    }
    
    // 5. 启用数据输出
    retry_count = 0;
    while (EnableDataOutput() != 0) {
        retry_count++;
        if (retry_count > 200) {
            printf("[Gesture] ERROR: EnableDataOutput timeout!\r\n");
            return;
        }
        DelayNms(10);
    }
    
    // 6. 锁定数据输出格式
    retry_count = 0;
    while (LockDataOutput() != 0) {
        retry_count++;
        if (retry_count > 200) {
            printf("[Gesture] ERROR: LockDataOutput timeout!\r\n");
            return;
        }
        DelayNms(10);
    }
    
    // 7. 启用手势识别
    retry_count = 0;
    while (EnableGestures() != 0) {
        retry_count++;
        if (retry_count > 200) {
            printf("[Gesture] ERROR: EnableGestures timeout!\r\n");
            return;
        }
        DelayNms(10);
    }
    
    // 初始化信息结构体
    memset(&info, 0, sizeof(info));
}

/*********************************************************************************************************
* 函数名称：GestureSensorDataRecv
* 函数功能：接收手势传感器数据（按照Arduino库的方式）
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
void GestureSensorDataRecv(void)
{
    u8 pbuf[24];
    
    // 清空信息结构体（确保xyz为0）
    memset(&info, 0, sizeof(info));
    
    // 读取数据（按照Arduino库的方式）
    if (ReadSensorData(pbuf, 24) != 0) {
        // 验证数据格式：pbuf[3] == 0x91 && pbuf[4] == 0x1E
        if ((pbuf[3] == 0x91) && (pbuf[4] == 0x1E)) {
            // 解析手势信息
            info.gestureInfo = pbuf[8] | (u32)pbuf[9] << 8 | 
                              (u32)pbuf[10] << 16 | (u32)pbuf[11] << 24;
            
            // 解析触摸信息
            info.touchInfo = pbuf[12] | (u32)pbuf[13] << 8 | 
                           (u32)pbuf[14] << 16 | (u32)pbuf[15] << 24;
            
            // 检查是否有AirWheel信息（pbuf[7] & 0x02）
            if (pbuf[7] & 0x02) {
                info.airWheelInfo = pbuf[16] | (u32)pbuf[17] << 8;
            }
            
            // 检查是否有位置信息（pbuf[7] & 0x01）
            if (pbuf[7] & 0x01) {
                // 有位置数据，解析xyz
                u16 raw_x = pbuf[18] | (u16)pbuf[19] << 8;
                u16 raw_y = pbuf[20] | (u16)pbuf[21] << 8;
                u16 raw_z = pbuf[22] | (u16)pbuf[23] << 8;
                
                // 数据有效性检查和限制处理
                // MGC3130的有效值通常在0-60000范围内，超出范围的值可能是异常值
                #define POSITION_MAX_REASONABLE 60000  // 合理最大值
                #define POSITION_MAX_VALUE 65535        // 绝对最大值
                
                // X轴处理：直接使用原始值，只对明显异常的值进行限制
                if (raw_x > POSITION_MAX_REASONABLE) {
                    // 超出合理范围，限制到最大值（保持数据连续性，而不是清零）
                    info.xPosition = POSITION_MAX_VALUE;
                } else {
                    // 在合理范围内，直接使用原始值
                    info.xPosition = raw_x;
                }
                
                // Y轴处理
                if (raw_y > POSITION_MAX_REASONABLE) {
                    info.yPosition = POSITION_MAX_VALUE;
                } else {
                    info.yPosition = raw_y;
                }
                
                // Z轴处理
                if (raw_z > POSITION_MAX_REASONABLE) {
                    info.zPosition = POSITION_MAX_VALUE;
                } else {
                    info.zPosition = raw_z;
                }
            } else {
                // 没有位置信息，确保xyz为0（memset已经清零，这里再次确认）
                info.xPosition = 0;
                info.yPosition = 0;
                info.zPosition = 0;
            }
        } else {
            // 数据格式不匹配，确保xyz为0（memset已经清零，这里再次确认）
            info.xPosition = 0;
            info.yPosition = 0;
            info.zPosition = 0;
            info.gestureInfo = 0;
            
            if (pbuf[4] == 0x1F) {
                // 数据输出格式未锁定，重新锁定
                EnableDataOutput();
                LockDataOutput();
            }
        }
    } else {
        // 读取失败，确保xyz为0（memset已经清零，这里再次确认）
        info.xPosition = 0;
        info.yPosition = 0;
        info.zPosition = 0;
        info.gestureInfo = 0;
        
        // 延时5ms
        DelayNms(5);
    }
}

/*********************************************************************************************************
* 函数名称：GestureGetGestureInfo
* 函数功能：获取手势信息
* 输入参数：无
* 输出参数：无
* 返回值：手势信息
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
u8 GestureGetGestureInfo(void)
{
    return (u8)(info.gestureInfo & 0xFF);
}

/*********************************************************************************************************
* 函数名称：GestureGetPosition
* 函数功能：获取xyz位置信息
* 输入参数：x, y, z - 位置信息指针
* 输出参数：x, y, z - 位置信息
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
void GestureGetPosition(u16 *x, u16 *y, u16 *z)
{
    if (x != NULL) {
        *x = info.xPosition;
    }
    if (y != NULL) {
        *y = info.yPosition;
    }
    if (z != NULL) {
        *z = info.zPosition;
    }
}

/*********************************************************************************************************
*                                              内部函数实现
*********************************************************************************************************/

/*********************************************************************************************************
* 函数名称：I2C_Hardware_Init
* 函数功能：初始化硬件I2C1
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：使用硬件I2C1，PB6=SCL, PB7=SDA
*********************************************************************************************************/
static void I2C_Hardware_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    I2C_InitTypeDef I2C_InitStructure;
    
    // 使能I2C1和GPIOB时钟
    RCC_APB1PeriphClockCmd(I2Cx_CLK, ENABLE);
    RCC_APB2PeriphClockCmd(I2Cx_SCL_GPIO_CLK | I2Cx_SDA_GPIO_CLK, ENABLE);
    
    // 配置I2C1的GPIO：PB6(SCL), PB7(SDA)
    GPIO_InitStructure.GPIO_Pin = I2Cx_SCL_GPIO_PIN | I2Cx_SDA_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;  // 开漏输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(I2Cx_SCL_GPIO_PORT, &GPIO_InitStructure);
    
    // 配置I2C1
    I2C_InitStructure.I2C_Mode = I2C_Mode_I2C;
    I2C_InitStructure.I2C_DutyCycle = I2C_DutyCycle_2;
    I2C_InitStructure.I2C_OwnAddress1 = 0x00;  // 主机模式，不需要地址
    I2C_InitStructure.I2C_Ack = I2C_Ack_Enable;
    I2C_InitStructure.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
    I2C_InitStructure.I2C_ClockSpeed = 100000;  // 100kHz标准速度
    
    I2C_Init(I2Cx, &I2C_InitStructure);
    I2C_Cmd(I2Cx, ENABLE);
    
    printf("[Gesture] Hardware I2C1 initialized (100kHz).\r\n");
}

/*********************************************************************************************************
* 函数名称：SetRuntimeParameter
* 函数功能：发送RuntimeParameter命令（按照Arduino库的方式）
* 输入参数：pBuf - 命令数据，size - 数据长度
* 输出参数：无
* 返回值：实际发送的字节数
* 生成日期：2025年12月30日
* 注    意：Arduino库使用0x10, 0x00, 0x00, 0xA2作为命令头
*********************************************************************************************************/
static u8 SetRuntimeParameter(u8 *pBuf, u8 size)
{
    u8 i;
    
    if (pBuf == NULL) {
        return 0;
    }
    
    // 等待I2C总线空闲
    while (I2C_GetFlagStatus(I2Cx, I2C_FLAG_BUSY));
    
    // 发送起始信号
    I2C_GenerateSTART(I2Cx, ENABLE);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_MODE_SELECT));
    
    // 发送设备地址（写）
    I2C_Send7bitAddress(I2Cx, MGC3130_I2C_ADDR << 1, I2C_Direction_Transmitter);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_TRANSMITTER_MODE_SELECTED));
    
    // 发送命令头：0x10, 0x00, 0x00, 0xA2
    I2C_SendData(I2Cx, 0x10);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_BYTE_TRANSMITTED));
    
    I2C_SendData(I2Cx, 0x00);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_BYTE_TRANSMITTED));
    
    I2C_SendData(I2Cx, 0x00);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_BYTE_TRANSMITTED));
    
    I2C_SendData(I2Cx, 0xA2);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_BYTE_TRANSMITTED));
    
    // 发送数据
    for (i = 0; i < size; i++) {
        I2C_SendData(I2Cx, pBuf[i]);
        while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_BYTE_TRANSMITTED));
    }
    
    // 发送停止信号
    I2C_GenerateSTOP(I2Cx, ENABLE);
    
    return size;
}

/*********************************************************************************************************
* 函数名称：ReadSensorData
* 函数功能：读取传感器数据（按照Arduino库的方式）
* 输入参数：pBuf - 数据缓冲区，size - 要读取的字节数
* 输出参数：pBuf - 读取到的数据
* 返回值：实际读取的字节数，0表示失败
* 生成日期：2025年12月30日
* 注    意：需要先检查TS引脚（EIO0），然后拉低，读取数据，再拉高
*********************************************************************************************************/
static u8 ReadSensorData(u8 *pBuf, u8 size)
{
    u8 i;
    
    if (pBuf == NULL) {
        return 0;
    }
    
    // 检查TS引脚（EIO0），如果为高电平，说明没有数据可读
    if (EIO0_Read() != 0) {
        return 0;  // TS引脚为高，无数据
    }
    
    // 将TS引脚设置为输出模式并拉低
    EIO0_SetOutput();
    EIO0_WriteLow();
    
    // 等待I2C总线空闲
    while (I2C_GetFlagStatus(I2Cx, I2C_FLAG_BUSY));
    
    // 发送起始信号
    I2C_GenerateSTART(I2Cx, ENABLE);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_MODE_SELECT));
    
    // 发送设备地址（读）
    I2C_Send7bitAddress(I2Cx, MGC3130_I2C_ADDR << 1, I2C_Direction_Receiver);
    while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_RECEIVER_MODE_SELECTED));
    
    // 读取数据
    for (i = 0; i < size; i++) {
        if (i == size - 1) {
            // 最后一个字节前，发送NACK
            I2C_AcknowledgeConfig(I2Cx, DISABLE);
        } else {
            // 非最后一个字节，发送ACK
            I2C_AcknowledgeConfig(I2Cx, ENABLE);
        }
        
        // 等待数据接收完成
        while (!I2C_CheckEvent(I2Cx, I2C_EVENT_MASTER_BYTE_RECEIVED));
        pBuf[i] = I2C_ReceiveData(I2Cx);
    }
    
    // 发送停止信号
    I2C_GenerateSTOP(I2Cx, ENABLE);
    
    // 重新使能ACK（为下次读取做准备）
    I2C_AcknowledgeConfig(I2Cx, ENABLE);
    
    // 将TS引脚拉高并恢复为输入模式
    EIO0_WriteHigh();
    EIO0_SetInput();
    
    // 延时5ms（按照Arduino库的做法）
    DelayNms(5);
    
    return size;
}

/*********************************************************************************************************
* 函数名称：DisableTouchDetection
* 函数功能：禁用触摸检测
* 输入参数：无
* 输出参数：无
* 返回值：0表示成功，-1表示失败
*********************************************************************************************************/
static u8 DisableTouchDetection(void)
{
    u8 pBuf[] = {0x97, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00};
    u8 recvBuf[16];
    u8 ret = 1;
    
    SetRuntimeParameter(pBuf, 12);
    DelayNms(10);
    
    if (ReadSensorData(recvBuf, 16) != 0) {
        if (recvBuf[4] == 0xA2) {
            u16 errorCode = ((u16)recvBuf[7] << 8) | recvBuf[6];
            if (errorCode == 0) {
                ret = 0;
            }
        }
    }
    
    return ret;
}

/*********************************************************************************************************
* 函数名称：DisableApproachDetection
* 函数功能：禁用接近检测
* 输入参数：无
* 输出参数：无
* 返回值：0表示成功，-1表示失败
*********************************************************************************************************/
static u8 DisableApproachDetection(void)
{
    u8 pBuf[] = {0x97, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00};
    u8 recvBuf[16];
    u8 ret = 1;
    
    SetRuntimeParameter(pBuf, 12);
    DelayNms(10);
    
    if (ReadSensorData(recvBuf, 16) != 0) {
        if (recvBuf[4] == 0xA2) {
            u16 errorCode = ((u16)recvBuf[7] << 8) | recvBuf[6];
            if (errorCode == 0) {
                ret = 0;
            }
        }
    }
    
    return ret;
}

/*********************************************************************************************************
* 函数名称：DisableAirWheel
* 函数功能：禁用滚轮功能
* 输入参数：无
* 输出参数：无
* 返回值：0表示成功，-1表示失败
*********************************************************************************************************/
static u8 DisableAirWheel(void)
{
    u8 pBuf[] = {0x90, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00};
    u8 recvBuf[16];
    u8 ret = 1;
    
    SetRuntimeParameter(pBuf, 12);
    DelayNms(10);
    
    if (ReadSensorData(recvBuf, 16) != 0) {
        if (recvBuf[4] == 0xA2) {
            u16 errorCode = ((u16)recvBuf[7] << 8) | recvBuf[6];
            if (errorCode == 0) {
                ret = 0;
            }
        }
    }
    
    return ret;
}

/*********************************************************************************************************
* 函数名称：DisableGestures
* 函数功能：禁用手势识别
* 输入参数：无
* 输出参数：无
* 返回值：0表示成功，-1表示失败
*********************************************************************************************************/
static u8 DisableGestures(void)
{
    u8 pBuf[] = {0x85, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    u8 recvBuf[16];
    u8 ret = 1;
    
    SetRuntimeParameter(pBuf, 12);
    DelayNms(10);
    
    if (ReadSensorData(recvBuf, 16) != 0) {
        if (recvBuf[4] == 0xA2) {
            u16 errorCode = ((u16)recvBuf[7] << 8) | recvBuf[6];
            if (errorCode == 0) {
                ret = 0;
            }
        }
    }
    
    return ret;
}

/*********************************************************************************************************
* 函数名称：EnableGestures
* 函数功能：启用手势识别
* 输入参数：无
* 输出参数：无
* 返回值：0表示成功，-1表示失败
*********************************************************************************************************/
static u8 EnableGestures(void)
{
    u8 pBuf[] = {0x85, 0x00, 0x00, 0x00, 0x7F, 0x00, 0x00, 0x00, 0x7F, 0x00, 0x00, 0x00};
    u8 recvBuf[16];
    u8 ret = 1;
    
    SetRuntimeParameter(pBuf, 12);
    DelayNms(10);
    
    if (ReadSensorData(recvBuf, 16) != 0) {
        if (recvBuf[4] == 0xA2) {
            u16 errorCode = ((u16)recvBuf[7] << 8) | recvBuf[6];
            if (errorCode == 0) {
                ret = 0;
            }
        }
    }
    
    return ret;
}

/*********************************************************************************************************
* 函数名称：EnableDataOutput
* 函数功能：启用数据输出
* 输入参数：无
* 输出参数：无
* 返回值：0表示成功，-1表示失败
*********************************************************************************************************/
static u8 EnableDataOutput(void)
{
    u8 pBuf[] = {0xA0, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF};
    u8 recvBuf[16];
    u8 ret = 1;
    
    SetRuntimeParameter(pBuf, 12);
    DelayNms(10);
    
    if (ReadSensorData(recvBuf, 16) != 0) {
        if (recvBuf[4] == 0xA2) {
            u16 errorCode = ((u16)recvBuf[7] << 8) | recvBuf[6];
            if (errorCode == 0) {
                ret = 0;
            }
        }
    }
    
    return ret;
}

/*********************************************************************************************************
* 函数名称：LockDataOutput
* 函数功能：锁定数据输出格式
* 输入参数：无
* 输出参数：无
* 返回值：0表示成功，-1表示失败
*********************************************************************************************************/
static u8 LockDataOutput(void)
{
    u8 pBuf[] = {0xA1, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF};
    u8 recvBuf[16];
    u8 ret = 1;
    
    SetRuntimeParameter(pBuf, 12);
    DelayNms(10);
    
    if (ReadSensorData(recvBuf, 16) != 0) {
        if (recvBuf[4] == 0xA2) {
            u16 errorCode = ((u16)recvBuf[7] << 8) | recvBuf[6];
            if (errorCode == 0) {
                ret = 0;
            }
        }
    }
    
    return ret;
}

/*********************************************************************************************************
* 函数名称：MGC3130_reset
* 函数功能：重置传感器
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：低电平触发重置，持续250ms，然后等待2秒重启
*********************************************************************************************************/
static void MGC3130_reset(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    
    // 使能GPIOB时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    
    // 配置MCLR为推挽输出
    GPIO_InitStructure.GPIO_Pin = MGC3130_MCLR_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(MGC3130_MCLR_GPIO_PORT, &GPIO_InitStructure);
    
    // 拉低MCLR 250ms，然后拉高
    GPIO_ResetBits(MGC3130_MCLR_GPIO_PORT, MGC3130_MCLR_GPIO_PIN);
    DelayNms(250);
    GPIO_SetBits(MGC3130_MCLR_GPIO_PORT, MGC3130_MCLR_GPIO_PIN);
    
    // 等待传感器启动
    DelayNms(500);
}


/*********************************************************************************************************
* 函数名称：EIO0_SetOutput
* 函数功能：设置EIO0引脚为输出模式
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
static void EIO0_SetOutput(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    
    GPIO_InitStructure.GPIO_Pin = MGC3130_EIO0_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(MGC3130_EIO0_GPIO_PORT, &GPIO_InitStructure);
}

/*********************************************************************************************************
* 函数名称：EIO0_SetInput
* 函数功能：设置EIO0引脚为输入模式
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
static void EIO0_SetInput(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    
    GPIO_InitStructure.GPIO_Pin = MGC3130_EIO0_GPIO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(MGC3130_EIO0_GPIO_PORT, &GPIO_InitStructure);
}

/*********************************************************************************************************
* 函数名称：EIO0_WriteLow
* 函数功能：将EIO0引脚拉低
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
static void EIO0_WriteLow(void)
{
    GPIO_ResetBits(MGC3130_EIO0_GPIO_PORT, MGC3130_EIO0_GPIO_PIN);
}

/*********************************************************************************************************
* 函数名称：EIO0_WriteHigh
* 函数功能：将EIO0引脚拉高
* 输入参数：无
* 输出参数：无
* 返回值：无
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
static void EIO0_WriteHigh(void)
{
    GPIO_SetBits(MGC3130_EIO0_GPIO_PORT, MGC3130_EIO0_GPIO_PIN);
}

/*********************************************************************************************************
* 函数名称：EIO0_Read
* 函数功能：读取EIO0引脚状态
* 输入参数：无
* 输出参数：无
* 返回值：引脚状态（0或1）
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************/
static u8 EIO0_Read(void)
{
    return GPIO_ReadInputDataBit(MGC3130_EIO0_GPIO_PORT, MGC3130_EIO0_GPIO_PIN);
}
