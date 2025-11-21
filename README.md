# SeaPower_ModManager
This is a SeaPower_ModManager/这是一个《海上力量》模组管理器
## 前言
每次选择加载模组时需要一个个点选和等待超长的加载时间，调个加载顺序还要用鼠标点很久。为了方便管理模组，我以在《地狱之门：东线战场》中使用过的一个模组管理器为参考，使用gemini-3-pro-preview编写了一个模组管理器用于管理SeaPower模组的管理器。

## 有什么功能？
- 管理模组的启动/管理
- 通过拖动调整模组的加载顺序
- 模组文字与图片信息预览
- 导出与导入模组预设
- 中/英文界面（默认中文界面）
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/Snipaste_2025-11-21_21-45-26.jpg)
## 工作逻辑
### 模组开启/关闭控制
在
```
C:\Users\{用户名}\AppData\LocalLow\Triassic Games\Sea Power\usersettings.ini
```
中有控制模组启用/关闭的语句：
```
”Mod1Directory = 3411771040,False“
```

### 模组名称正确显示
上文说到的**usersettings.ini**控制模组的语句使用的是创意工坊编号，直接读取编号难以识别需要操作的模组，于是在程序运行的同时读取
```
{path to SteamLibrary}\steamapps\workshop\content\1286220\
```

下的每一个模组文件的**info.ini**并与**usersettings.ini**中的编号配对

### 模组拖动加载顺序
模组控制语句：
```
Mod1Directory = 3411771040,False
```
中，可视为
```
Mod{num}Directory = {mod_code},{True/False}
```
修改其中的**{num}**即可控制模组加载顺序

## 如何使用？
### 基本功能
1.新建文件夹存放程序
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/1.jpg)

2.打开程序设置用户配置文件与创意工坊路径
```
用户配置文件路径参考：
C:\Users\{your_user_name}\AppData\LocalLow\Triassic Games\Sea Power\usersettings.ini
创意工坊路径参考：
E:\SteamLibrary\steamapps\workshop\content\1286220
```

![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/2.jpg)
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/3.jpg)

3.点击**读取/刷新**加载模组列表
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/5.jpg)

4.**双击**切换模组开启/关闭
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/7.jpg)

5.**拖动**选中的模组修改加载顺序
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/8.jpg)

6.点击**保存配置(覆盖备份)** 保存配置
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/9.jpg)

### 模组预设保存
1.保存配置后点击**保存预设**预设文件会自动保存在同目录下“Presets"文件夹内
![image](https://github.com/ORION2004/SeaPower_ModManager/blob/main/image/10.jpg)

2.点击**加载预设**选择需要加载的预设，加载前会检测创意工坊目录内是否有预设内的模组，如没有则会弹窗提醒

3.点击**保存配置(覆盖备份)** 保存配置

### 注意事项

- 仅有首次运行时需要配置路径，设置语言与设置字体大小，设置会保存在同目录下的”ModManagerConfig.json“中，之后运行会自动加载
- 保存配置后“usersettings.ini”会自动在同目录下另存一份“usersettings.ini.bak”作为备份，之后每次保存配置后会覆盖”usersettings.ini.bak“
- 运行前请备份相关文件，如因使用造成文件损坏或丢失一概不负责
- 我不是专业程序员，如果你运行出了任何问题请自行下载源码，将运行结果与错误现象发送给AI询问
- 欢迎转载进行再次开发，不得用于盈利
