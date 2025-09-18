# 抖音通讯录批量关注工具

一个通过ADB长连接自动化操作抖音应用，批量关注通讯录好友的Python工具。

## 功能特性

- 🔗 **ADB长连接管理**：稳定的设备连接和命令执行
- 🔍 **智能UI分析**：解析Android界面XML，智能识别按钮和控件
- 🤖 **自动化导航**：自动导航到抖音的通讯录页面
- 👥 **批量关注**：批量关注通讯录中的好友
- 📊 **详细报告**：生成操作日志和结果报告
- 🛡️ **安全控制**：操作间隔控制，避免被检测

## 系统要求

- Python 3.7+
- Android设备（已开启USB调试）
- ADB工具
- 抖音应用

## 安装和设置

### 1. 环境准备

确保你的系统已安装Python 3.7或更高版本：
```bash
python --version
```

### 2. ADB设置

#### Windows系统：
1. 下载Android SDK Platform Tools
2. 将adb.exe所在目录添加到系统PATH
3. 或者将adb.exe复制到项目目录

#### macOS/Linux系统：
```bash
# macOS (使用Homebrew)
brew install android-platform-tools

# Ubuntu/Debian
sudo apt install android-tools-adb

# CentOS/RHEL
sudo yum install android-tools
```

### 3. 手机设置

1. **开启开发者选项**：
   - 设置 → 关于手机 → 连续点击"版本号"7次

2. **开启USB调试**：
   - 设置 → 开发者选项 → USB调试

3. **授权ADB调试**：
   - 连接USB后，手机会弹出授权对话框，选择"始终允许"

4. **安装抖音应用**：
   - 确保已安装最新版本的抖音
   - 确保已登录账号
   - 确保已授权通讯录访问权限

### 4. 验证连接

```bash
adb devices
```

应该显示类似输出：
```
List of devices attached
your_device_id    device
```

## 使用方法

### 交互式模式（推荐）

```bash
python main.py
```

进入交互式菜单，选择相应功能：
- UI分析模式：分析当前屏幕元素
- 自动关注模式：执行批量关注流程

### 命令行模式

#### UI分析模式
```bash
# 分析当前屏幕
python main.py --analyze

# 指定设备分析
python main.py --analyze --device your_device_id
```

#### 自动关注模式
```bash
# 批量关注（默认10个）
python main.py --auto-follow

# 关注指定数量
python main.py --auto-follow --count 5

# 指定设备和数量
python main.py --auto-follow --device your_device_id --count 20
```

## 使用流程

### 自动化操作流程

1. **设备连接检查**
2. **启动抖音应用**
3. **导航到"我"页面**
4. **点击"添加朋友"**
5. **进入"通讯录"页面**
6. **批量关注联系人**

### 手动准备步骤

在运行自动化脚本前，建议先手动完成以下步骤：

1. 解锁手机屏幕
2. 确保抖音应用已登录
3. 手动检查通讯录权限是否已授权
4. 确保网络连接正常

## 配置说明

编辑 `config.ini` 文件来自定义配置：

```ini
[OPERATION]
# 操作间隔（秒），避免操作过快
operation_delay = 2.0

[FOLLOW]
# 默认最大关注数量
default_max_count = 10

[SAFETY]
# 是否启用操作确认
enable_confirmation = true
```

## 输出文件

工具运行时会生成以下文件：

- `douyin_auto_YYYYMMDD.log`：操作日志
- `follow_result_YYYYMMDD_HHMMSS.json`：关注结果统计
- `douyin_ui_analysis_YYYYMMDD_HHMMSS.txt`：UI分析报告
- `douyin_ui_YYYYMMDD_HHMMSS.xml`：界面XML结构（可选）

## 示例输出

### 成功执行示例
```
✅ 工作流程执行成功！

步骤执行状态：
  ✅ 设备连接
  ✅ 启动抖音
  ✅ 导航到个人资料
  ✅ 导航到添加朋友
  ✅ 导航到通讯录
  ✅ 批量关注

关注统计：
  总处理数量: 8
  成功关注: 6
  关注失败: 1
  跳过数量: 1

详细处理结果：
   1. 张三 - ✅ 成功关注
   2. 李四 - ✅ 成功关注
   3. 王五 - ⏭️ 跳过
   4. 赵六 - ✅ 成功关注
   ...
```

## 故障排除

### 常见问题

1. **设备未检测到**
   ```
   解决方案：
   - 检查USB连接
   - 确保USB调试已开启
   - 尝试重新连接设备
   - 运行 adb kill-server && adb start-server
   ```

2. **抖音启动失败**
   ```
   解决方案：
   - 确保抖音应用已安装
   - 检查应用包名是否正确
   - 手动启动抖音确认是否正常
   ```

3. **找不到界面元素**
   ```
   解决方案：
   - 使用UI分析模式查看当前屏幕
   - 检查抖音版本是否过新/过旧
   - 调整config.ini中的关键词配置
   ```

4. **操作被中断**
   ```
   解决方案：
   - 增加operation_delay设置
   - 确保手机屏幕保持亮屏
   - 关闭其他可能影响的应用
   ```

### 调试模式

启用详细日志以便调试：
```bash
python main.py --log-level DEBUG
```

## 安全和注意事项

### ⚠️ 重要提醒

1. **使用频率控制**：避免短时间内大量关注，可能触发抖音的反作弊机制
2. **账号安全**：建议使用测试账号，避免主账号被限制
3. **网络环境**：建议在稳定的网络环境下使用
4. **设备保护**：确保设备电量充足，避免操作中断

### 建议的使用策略

- 每次关注数量不超过20个
- 每天使用次数不超过3次
- 关注间隔设置为2-3秒
- 定期更新抖音版本以保持兼容性

## 技术原理

### 核心组件

1. **ADB连接管理**（`adb_connection.py`）
   - 管理ADB连接和命令执行
   - 提供屏幕操作接口（点击、滑动等）

2. **UI元素分析**（`ui_analyzer.py`）
   - 解析Android UI XML结构
   - 智能识别按钮和控件位置

3. **抖音自动化操作**（`douyin_automator.py`）
   - 实现抖音应用的导航逻辑
   - 批量关注操作流程

4. **主程序入口**（`main.py`）
   - 命令行参数处理
   - 交互式用户界面

### XML智能分析

工具通过分析Android界面的XML结构来定位按钮：

1. **获取UI结构**：使用 `uiautomator dump` 导出当前界面XML
2. **解析XML**：递归解析所有UI元素及其属性
3. **元素匹配**：根据文本、资源ID、类名等属性匹配目标元素
4. **坐标计算**：从bounds属性计算元素中心坐标
5. **点击操作**：使用 `input tap` 命令点击计算出的坐标

## 版本历史

- **v1.0.0**：初始版本，支持基本的批量关注功能

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和平台服务条款。

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。

## 联系方式

如有问题或建议，请通过GitHub Issues联系。