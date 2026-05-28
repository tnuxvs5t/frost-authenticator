# Frost Authenticator

Frost Authenticator 是一个面向 Ubuntu 的本地离线 TOTP Authenticator，使用 **PyQt6** 构建桌面界面，使用加密保险库存储验证码密钥。

- **需要**：Python 3.12
- **推荐环境**：Ubuntu 24.04 LTS
- **数据位置**：`~/.local/share/frost-authenticator/vault.json`
- **运行方式**：本地离线运行，不依赖云同步

## 功能

- TOTP 一次性验证码生成
- 支持 SHA1 / SHA256 / SHA512
- 支持 6 / 7 / 8 位验证码
- 支持自定义刷新周期
- 添加、编辑、删除账号
- 从 `otpauth://totp/...` URI 导入
- 从二维码图片导入
- 一键复制验证码，30 秒后尝试自动清空剪贴板
- 本地保险库加密：PBKDF2-HMAC-SHA256 + Fernet
- Ubuntu 桌面启动器安装

## 安装

### 1. 安装系统依赖

Ubuntu 24.04 推荐：

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip libxcb-cursor0 libxkbcommon-x11-0 libegl1 libgl1
```

也可以让安装器尝试安装系统依赖：

```bash
./install.sh --system-deps
```

### 2. 克隆并安装

```bash
git clone https://github.com/tnuxvs5t/frost-authenticator.git
cd frost-authenticator
./install.sh
```

安装器会：

1. 检查 Python 3.12；
2. 创建 `.venv`；
3. 安装 Python 依赖；
4. 安装桌面启动器。

## 运行

```bash
./run.sh
```

或在 Ubuntu 应用菜单中搜索：

```text
Frost Authenticator
```

首次运行会要求创建主密码。主密码不会保存；忘记主密码将无法恢复保险库内容。

## 导入账号

### 从 URI 导入

复制形如下面的字符串：

```text
otpauth://totp/Issuer:Account?secret=BASE32SECRET&issuer=Issuer
```

然后点击应用里的“从剪贴板 URI 导入”。

### 从二维码图片导入

保存二维码图片，然后点击“从二维码图片导入”。二维码解码由 OpenCV 完成。

## 开发与测试

安装开发依赖：

```bash
./install.sh --dev --no-desktop
```

运行测试：

```bash
.venv/bin/python -m pytest
```

## 卸载桌面启动器

```bash
./scripts/uninstall_desktop.sh
```

这只会删除桌面启动器和图标，不会删除保险库。

如需删除本地保险库，请手动删除：

```bash
rm ~/.local/share/frost-authenticator/vault.json
```

## 安全边界

Frost Authenticator 会加密本地保险库文件，但它不替代：

- Ubuntu 登录密码；
- 全盘加密；
- 系统补丁；
- 密码管理器；
- 账号恢复码备份。

运行中的应用会在内存里处理密钥和验证码。请只在可信设备上使用，并妥善备份 `vault.json` 与账号恢复码。
