/*********************************************************************************************************
* 模块名称：OLED.c   
* 摘    要：OLED显示屏模块，4线串行接口，CS、DC、SCK、DIN、RES
* 当前版本：1.0.0
* 作    者：SZLY(COPYRIGHT 2018 - 2020 SZLY. All rights reserved.)
* 完成日期：2020年01月01日
* 内    容：
* 注    意：OLED的显存
            存放格式如下.
            [0]0 1 2 3 ... 127
            [1]0 1 2 3 ... 127
            [2]0 1 2 3 ... 127
            [3]0 1 2 3 ... 127
            [4]0 1 2 3 ... 127
            [5]0 1 2 3 ... 127
            [6]0 1 2 3 ... 127
            [7]0 1 2 3 ... 127                                                                   
**********************************************************************************************************
* 取代版本：
* 作    者：
* 完成日期： 
* 修改内容：
* 修改文件： 
*********************************************************************************************************/

/*********************************************************************************************************
*                                              包含头文件
*********************************************************************************************************/
#include "OLED.h"
#include "stm32f10x_conf.h"
#include "OLEDFont.h"
#include "SysTick.h"

/*********************************************************************************************************
*                                              宏定义
*********************************************************************************************************/
#define OLED_CMD 0      //命令
#define OLED_DATA 1     //结构

//OLED 端口定义
#define CLR_OLED_CS()  GPIO_ResetBits(GPIOB,GPIO_Pin_12)   //CS，片选
#define SET_OLED_CS()  GPIO_SetBits(GPIOB,GPIO_Pin_12)

#define CLR_OLED_RES()  GPIO_ResetBits(GPIOB,GPIO_Pin_14)  //RES，复位
#define SET_OLED_RES()  GPIO_SetBits(GPIOB,GPIO_Pin_14)

#define CLR_OLED_DC()  GPIO_ResetBits(GPIOC,GPIO_Pin_3)    //DC，复位
#define SET_OLED_DC()  GPIO_SetBits(GPIOC,GPIO_Pin_3)

#define CLR_OLED_SCK()  GPIO_ResetBits(GPIOB,GPIO_Pin_13)  //SCK，复位
#define SET_OLED_SCK()  GPIO_SetBits(GPIOB,GPIO_Pin_13)

#define CLR_OLED_DIN()  GPIO_ResetBits(GPIOB,GPIO_Pin_15)  //DIN，复位
#define SET_OLED_DIN()  GPIO_SetBits(GPIOB,GPIO_Pin_15)

/*********************************************************************************************************
*                                              枚举结构体定义
*********************************************************************************************************/

/*********************************************************************************************************
*                                              内部变量
*********************************************************************************************************/
 static u8 s_arrOLEDGRAM[128][8];   //OLED 显存缓冲区
 
/*********************************************************************************************************
*                                              内部函数声明
*********************************************************************************************************/
static void ConfigOLEDGPIO(void);             //配置 OLED 的 GPIO
static void ConfigOLEDReg(void);             //配置 OLED 的 SSD1306 寄存器

static void OLEDWriteByte(u8 dat, u8 cmd);    //向 SSD1306 写入1字节
static void OLEDDrawPoint(u8 x, u8 y, u8 t);  //在 OLED 屏指定位置画点

static u32 ClacPow(u8 m ,u8 n);               //计算m的n次方

/*********************************************************************************************************
*                                              内部函数实现
*********************************************************************************************************/
/*********************************************************************************************************
* 函数名称：ConfigOLEDGPIO
* 函数功能：配置 OLED 的 GPIO
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
static void ConfigOLEDGPIO(void)
{
  GPIO_InitTypeDef GPIO_InitStructure;
  
  //使能 RCC 相关时钟
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB,ENABLE);    //使能 GPIOB 的时钟
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC,ENABLE);    //使能 GPIOC 的时钟
  
  //配置 PB13 （OLED_SCK）
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_13;              //设置引脚
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;        //设置模式
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;       //设置 I/O 输出速度
  GPIO_Init(GPIOB,&GPIO_InitStructure);                   //根据参数初始化 GPIO
  GPIO_SetBits(GPIOB,GPIO_Pin_13);                        //设置初始状态为高电平
  
  //配置 PB15 （OLED_DIN）
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_15;              //设置引脚
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;        //设置模式
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;       //设置 I/O 输出速度
  GPIO_Init(GPIOB,&GPIO_InitStructure);                   //根据参数初始化 GPIO
  GPIO_SetBits(GPIOB,GPIO_Pin_15);                        //设置初始状态为高电平
  
  //配置 PB14 （OLED_RES）
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_14;              //设置引脚
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;        //设置模式
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;       //设置 I/O 输出速度
  GPIO_Init(GPIOB,&GPIO_InitStructure);                   //根据参数初始化 GPIO
  GPIO_SetBits(GPIOB,GPIO_Pin_14);                        //设置初始状态为高电平
  
  //配置 PB12 （OLED_CS）
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_12;              //设置引脚
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;        //设置模式
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;       //设置 I/O 输出速度
  GPIO_Init(GPIOB,&GPIO_InitStructure);                   //根据参数初始化 GPIO
  GPIO_SetBits(GPIOB,GPIO_Pin_12);                        //设置初始状态为高电平
  
  //配置 PC3 （OLED_DC）
  GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;              //设置引脚
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;        //设置模式
  GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;       //设置 I/O 输出速度
  GPIO_Init(GPIOC,&GPIO_InitStructure);                   //根据参数初始化 GPIO
  GPIO_SetBits(GPIOC,GPIO_Pin_3);                        //设置初始状态为高电平
}

/*********************************************************************************************************
* 函数名称：ConfigOLEEDReg
* 函数功能：配置 SSD1306 的寄存器
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
static void ConfigOLEDReg(void)
{
  OLEDWriteByte(0xAE, OLED_CMD);    //关闭显示
  
  OLEDWriteByte(0xD5, OLED_CMD);    //设置时钟分频系数、振荡频率
  OLEDWriteByte(0x50, OLED_CMD);    //[3:0]为分频系数，[7:4]为振荡频率、
  
  OLEDWriteByte(0xA8, OLED_CMD);    //设置驱动路数
  OLEDWriteByte(0x3F, OLED_CMD);    //默认为 0x3F(1/64)
  
  OLEDWriteByte(0xD3, OLED_CMD);    //设置显示路径
  OLEDWriteByte(0x00, OLED_CMD);    //默认为 0
  
  OLEDWriteByte(0x40, OLED_CMD);    //设置开始行
  
  OLEDWriteByte(0x8D, OLED_CMD);    //设置电荷泵
  OLEDWriteByte(0x14, OLED_CMD);    //bit2 用于设置开启（1）/关闭（0）

  OLEDWriteByte(0x20, OLED_CMD);    //设置内存地址模式
  OLEDWriteByte(0x02, OLED_CMD);    //[1:0]，00-列地址模式，01-行地址模式，10-页地址模式（默认值）
  
  OLEDWriteByte(0xA1, OLED_CMD);    //设置段重定义，bit0 为 0，列地址0->SEG0,bit0 为 1，列地址0->>SRG127
  
  OLEDWriteByte(0xC0, OLED_CMD);    //设置COM扫描方向，bit3 为 0，普通模式，bit3 为 1，重定义模式
  
  OLEDWriteByte(0xDA, OLED_CMD);    //设置COM硬件扫描方向
  OLEDWriteByte(0x12, OLED_CMD);    //[5:4]为硬件引脚配置信息
  
  OLEDWriteByte(0x81, OLED_CMD);    //设置对比度
  OLEDWriteByte(0xEF, OLED_CMD);    //1~255，默认为0x7F（亮度设置，越大越亮）
  
  OLEDWriteByte(0xD9, OLED_CMD);    //设置预充电周期
  OLEDWriteByte(0xF1, OLED_CMD);    //[3:0]为 PHASE1，[7:4]为 PHASE2
  
  OLEDWriteByte(0xDB, OLED_CMD);    //设置 VCOMH 电压倍率
  OLEDWriteByte(0x30, OLED_CMD);    //[6:4]，000->0.65*VCC，001->0.77*VCC，011->0.83*VCC
  
  OLEDWriteByte(0xA4, OLED_CMD);    //全局显示开启，bit0 为 1，开启，bit0 为 0，关闭
  
  OLEDWriteByte(0xA6, OLED_CMD);    //设置显示方式，bit0 为 1，反相显示，bit0 为 0，正常显示
  
  OLEDWriteByte(0xAF, OLED_CMD);    //开启显示
}

/*********************************************************************************************************
* 函数名称：OLEDWriteByte
* 函数功能：向 SSD1306 写入 1字节
* 输入参数：u8 dat, u8 cmd
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
static void OLEDWriteByte(u8 dat, u8 cmd)
{
  i16 i;
  
  //判断要写入数据还是命令
  if(OLED_CMD == cmd)       //如果标志 cmd 为传入命令时
  {
    CLR_OLED_DC();          //DC 输出低电平用来读/写命令
  }
  else if(OLED_DATA ==cmd)  //如果标志 cmd 为传入数据时
  {
    SET_OLED_DC();          //DC 输出高电平用来读/写数据
  }
  
  CLR_OLED_CS();            //CS 输出低电平，为写入数据或命令做准备
  
  for(i = 0;i < 8;i++)        //循环 8 次，从高到低去取出写入的数据或命令
  {
    CLR_OLED_SCK();         //SCK 输出低电平，为写入数据做准备
    
    if(dat & 0x80)          //判断要写入的数据或命令的最高位是 1 还是 0
    {
      SET_OLED_DIN();       //要写入的数据或命令的最高位是 1， DIN 输出高电平表示 1
    }
    else
    {
      CLR_OLED_DIN();       //要写入的数据或命令的最高位是 0， DIN 输出低电平表示 0
    }
    SET_OLED_SCK();         //SCK 输出高电平， DIN 的状态不再变化，此时写入数据线的数据
    
    dat <<= 1;              //左移一位，次高位移到最高位
  }
  
  SET_OLED_CS();            //OLED 的 CS 输出高电平，不再写入数据或命令
  SET_OLED_DC();            //OLED 的 DC 输出高电平
}

/*********************************************************************************************************
* 函数名称：OLEDDrawPoint
* 函数功能：在 OLED 屏指定位置画点
* 输入参数：u8 x, u8 y, u8 t
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
static void OLEDDrawPoint(u8 x, u8 y, u8 t)
{
  u8 pos;                           //存放所在的页数
  u8 bx;                            //存放点所在的屏幕的行号
  u8 temp;                          //用来存放画点位置相对于字节的位
  
  if(x > 127 || y > 63)             //如果指定位置超过额定范围
  {
    return;                         //返回空，函数结束
  }
  
  pos = 7 - y / 8;                  //求指定位置所在的页数
  bx = y % 8;                       //求指定位置在上面求出页数中的行号
  temp = 1 << (7 - bx);             //(7-bx) 求出对应 SSD1306 的行号，并将字节中相应的位置为 1
  
  if(t)                             //判断填充标志为 1还是 0 
  {
    s_arrOLEDGRAM[x][pos] |= temp;  //如果填充标志为 1，指定点填充
  }
  else
  {
    s_arrOLEDGRAM[x][pos] &= ~temp;  //如果填充标志为 0，指定点清空
  }
}

/*********************************************************************************************************
* 函数名称：ClacPow
* 函数功能：计算m的n次方
* 输入参数：u8 m ,u8 n
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
static u32 ClacPow(u8 m ,u8 n)
{
  u32 result = 1;       //定义用来存放结果的变量
  
  while(n--)            //随着每次循环，n 递减，直至为 0
  {
    result *= m;        //循环 n 次，相当于 n 个 m相乘
  }
  
  return result;        //返回 m 的 n 次方
}

/*********************************************************************************************************
*                                              API函数实现
*********************************************************************************************************/
/*********************************************************************************************************
* 函数名称：InitOLED
* 函数功能：初始化 OLED
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void InitOLED(void)
{
  ConfigOLEDGPIO();     //配置 OLED 的 GPIO
  
  CLR_OLED_RES();
  DelayNms(10);
  SET_OLED_RES();       //RES 的引脚务必拉高
  DelayNms(10);
  
  ConfigOLEDReg();      //配置 OLED 的寄存器

  OLEDClear();          //清除 OLED 显示屏内容
}

/*********************************************************************************************************
* 函数名称：OLEDDisplayOn
* 函数功能：开启 OLED 显示
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void OLEDDisplayOn(void)
{
  //打开/关闭电荷泵，第一字节 0x8D 为命令字，第二字节设置值，0x10-关闭电荷泵，0x14-打开电荷泵
  OLEDWriteByte(0x8D,OLED_CMD);   //第一字节 0x8D 为命令字
  OLEDWriteByte(0x14,OLED_CMD);   //0x14-打开电荷泵
  
  //设置显示开关，0xAE-关闭显示，0xAF-开启显示
  OLEDWriteByte(0xAF,OLED_CMD);   //开启显示
}

/*********************************************************************************************************
* 函数名称：OLEDDisplayOff
* 函数功能：关闭 OLED 显示
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void OLEDDisplayOff(void)
{
  //打开/关闭电荷泵，第一字节 0x8D 为命令字，第二字节设置值，0x10-关闭电荷泵，0x14-打开电荷泵
  OLEDWriteByte(0x8D,OLED_CMD);   //第一字节 0x8D 为命令字
  OLEDWriteByte(0x10,OLED_CMD);   //0x10-关闭电荷泵
  
  //设置显示开关，0xAE-关闭显示，0xAF-开启显示
  OLEDWriteByte(0xAE,OLED_CMD);   //关闭显示
}

/*********************************************************************************************************
* 函数名称：OLEDRefreshGRAM
* 函数功能：将 STM32 的 GRAM 写入 SSD1306 的 GRAM
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void OLEDRefreshGRAM(void)
{
  u8 i;
  u8 n;
  
  for(i = 0; i < 8; i++)                                //遍历每一页
  {
    OLEDWriteByte(0xb0 + i, OLED_CMD);                  //设置页地址
    OLEDWriteByte(0x00, OLED_CMD);                      //设置显示地址-列低地址位
    OLEDWriteByte(0x10, OLED_CMD);                      //设置显示地址-列高地址位
    for(n = 0; n < 128; n++)                             //遍历每一页
    {
      //通过循环将 STM32 的 GRAM 写入 SSD1306 的 GRAM
      OLEDWriteByte(s_arrOLEDGRAM[n][i],OLED_DATA);
    }
  }
}

/*********************************************************************************************************
* 函数名称：OLEDClear
* 函数功能：清屏函数，清完屏整个屏幕是黑色的，和没点亮一样
* 输入参数：void
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void OLEDClear(void)
{
  u8 i;
  u8 n;
  
  for(i = 0; i < 8; i++)             //遍历每一页
  {
    for(n = 0; n< 128; n++)         //遍历每一列
    {
      s_arrOLEDGRAM[n][i] = 0x00;   //将指定点清零
    }
  }
  
  OLEDRefreshGRAM();                //将 STM32 的 GRAM 写入 SSD1306 的 GRAM
}

/*********************************************************************************************************
* 函数名称：OLEDShowChar
* 函数功能：在指定位置显示一个字符
* 输入参数：u8 x,u8 y,u8 size,u8 mode
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void OLEDShowChar(u8 x,u8 y,u8 chr,u8 size,u8 mode)
{
  u8 temp;                              //用来存放字符顺向逐列式的相对位置
  u8 t1;                                //循环计数器1
  u8 t2;                                //循环计数器2
  u8 y0 = y;                            //当前操作的行数
  
  chr = chr -' ';                       //得到相对于空格（ASCⅡ码为0x20）的偏移值，求出 chr 在数组中的索引
  
  for(t1 = 0; t1 < size; t1++)          //循环逐列显示
  {
    if(size == 12)                      //判断字号大小，选择相对的顺向逐列式
    {
      temp = g_iASCII1206[chr][t1];     //取出字符在 g_iASCII1206 数组中的第 t1 列
    }
    else
    {
      temp = g_iASCII1608[chr][t1];     //取出字符在 g_iASCII1608 数组中的第 t1 列
    }
    
    for(t2 = 0; t2 < 8; t2++)           //在一个字符的第 t2 列的横向范围（8像素）内显示点
    {
      if(temp & 0x80)                   //取出 temp 的最高位，并判断是 0 还是 1
      {
        OLEDDrawPoint(x, y , mode);     //如果 temp 的最高位为 1.填充指定位置的点
      }
      else
      {
        OLEDDrawPoint(x, y, !mode);     //如果 temp 的最高位为 0.清除指定位置的点
      }
      
      temp <<= 1;                       //左移一位，次高位移到最高位
      y++;                              //进入下一行
      
      if((y - y0) == size)              //如果显示完一列
      {
        y = y0;                         //符号回到原来的位置
        x++;                            //进入下一列
        break;                          //跳出上面带#的循环
      }
    }
  }
}

/*********************************************************************************************************
* 函数名称：OLEDShowNum
* 函数功能：在指定位置显示数字
* 输入参数：u8 x, u8 y, u32 num, u8 len, u8 size
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void OLEDShowNum(u8 x, u8 y, u32 num, u8 len, u8 size)
{
  u8 t;                                                       //循环计数器
  u8 temp;                                                    //用来存放要显示数字的各个位
  u8 enshow = 0;                                              //区分 0 是否为高位 0 标志位
  
  for(t = 0;t < len; t++)
  {
    temp = (num / ClacPow(10, len - t - 1)) % 10;             //从高到低取出要显示数字的各个位，存到 temp 中
    if(enshow == 0 && t < (len - 1))                          //如果标志 enshow 为 0 并且 还未取到最后一位
    {
      if(temp == 0)                                           //如果 temp 等于 0
      {
        OLEDShowChar(x + (size / 2) * t, y, ' ', size, 1);    //此时的 0 在高位，用空格替代
        continue;                                             //提前结束本次循环，进入下一次循环
      }
      else
      {
        enshow = 1;                                           //否则将标志 enshow 置为 1
      }
    }
    OLEDShowChar(x + (size / 2) * t, y, temp + '0', size, 1); //在指定位置显示得到的数字
  }
}

/*********************************************************************************************************
* 函数名称：OLEDShowString
* 函数功能：在指定位置显示字符串
* 输入参数：u8 x, u8 y, const u8* p
* 输出参数：void
* 返 回 值：void
* 创建日期：2024年03月19日
* 注    意：
*********************************************************************************************************/
void OLEDShowString(u8 x, u8 y, const u8* p)
{
  #define MAX_CHAR_POSX 122           //OLED 屏幕横向的最大范围
  #define MAX_CHAR_POSY 58            //OLED 屏幕纵向的最大范围
  
  while(*p != '\0')                   //指针不等于结束符是，循环进入
  {
    if(x > MAX_CHAR_POSX)             //如果 x 超出指定最大范围，x 赋值为 0
    {
      x = 0;
      y += 16;                        //显示到下一行左端
    }
    
    if(y > MAX_CHAR_POSY)             //如果 y 超出指定最大范围，x 和 y 均赋值为 0
    {
      y = x =0;                       //清除 OLED 屏幕内容
      OLEDClear();                    //显示到 OLED 屏幕左上角
    }
    
    OLEDShowChar(x, y, *p, 16, 1);    //指定位置显示一个字符
    
    x += 8;                           //一个字符横向占 8 像素点
    p++;                              //指针指向下一个字符
  }
}
