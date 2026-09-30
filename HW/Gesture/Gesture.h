/*********************************************************************************************************
* 模块名称：Gesture.h
* 功能说明：手势传感器驱动头文件
* 当前版本：1.0.0
* 作    者：Leo Leung
* 生成日期：2025年12月30日
* 注    意：
*********************************************************************************************************
* 修改版本：
* 作    者：
* 生成日期：
* 修改内容：
* 修改文件：
*********************************************************************************************************/

#ifndef __GESTURE_H__
#define __GESTURE_H__

/*********************************************************************************************************
*                                              包含头文件
*********************************************************************************************************/
#include "DataType.h"
#include "stm32f10x.h"  // 需要包含此文件以定义I2C_TypeDef等类型

/*********************************************************************************************************
*                                              定义
*********************************************************************************************************/
// I2C配置
#define I2Cx                      I2C1
#define I2Cx_CLK                  RCC_APB1Periph_I2C1
#define I2Cx_SCL_GPIO_CLK         RCC_APB2Periph_GPIOB
#define I2Cx_SCL_GPIO_PORT        GPIOB
#define I2Cx_SCL_GPIO_PIN         GPIO_Pin_6
#define I2Cx_SDA_GPIO_CLK         RCC_APB2Periph_GPIOB
#define I2Cx_SDA_GPIO_PORT        GPIOB
#define I2Cx_SDA_GPIO_PIN         GPIO_Pin_7

// MCLR引脚配置（用于传感器重置）
#define MGC3130_MCLR_GPIO_PORT    GPIOB
#define MGC3130_MCLR_GPIO_PIN     GPIO_Pin_8  // PB8

// EIO0引脚配置（用于数据就绪检测）
#define MGC3130_EIO0_GPIO_PORT    GPIOB
#define MGC3130_EIO0_GPIO_PIN     GPIO_Pin_9  // PB9

// 手势传感器I2C地址
#define MGC3130_I2C_ADDR          0x42

// 手势信息枚举
typedef enum {
    eNoGesture = 0,           // 无手势
    eGarbageModel,            // 无效模型
    eFilckR,                  // 左到右滑动
    eFilckL,                  // 右到左滑动
    eFilckU,                  // 下到上滑动
    eFilckD,                  // 上到下滑动
    eCircleClockwise,         // 顺时针画圈
    eCircleCounterclockwise,  // 逆时针画圈
} eGestureInfo_t;

// 数据存储结构
typedef struct {
    u32 gestureInfo;      // 手势信息
    u32 touchInfo;        // 触摸信息
    u32 airWheelInfo;     // 滚轮信息
    u16 xPosition;        // X轴位置
    u16 yPosition;        // Y轴位置
    u16 zPosition;        // Z轴位置
} sInfo_t;

/*********************************************************************************************************
*                                              外部函数声明
*********************************************************************************************************/
void InitGesture(void);                  // 初始化手势传感器
void GestureSensorDataRecv(void);       // 接收手势传感器数据
u8 GestureGetGestureInfo(void);         // 获取手势信息
void GestureGetPosition(u16 *x, u16 *y, u16 *z);  // 获取xyz位置信息

#endif /* __GESTURE_H__ */
