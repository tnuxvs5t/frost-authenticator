# Frost Authenticator

Frost Authenticator 是一个面向 Ubuntu 的本地离线 TOTP Authenticator，使用 **PyQt6** 构建桌面界面，使用加密保险库存储验证码密钥。它的用途是作为 **Google Authenticator 的桌面替代方案**：为 Google、GitHub 以及其他支持 Authenticator App / TOTP 的网站生成登录所需的二次验证代码。

- **需要**：Python 3.12
- **推荐环境**：Ubuntu 24.04 LTS
- **数据位置**：`~/.local/share/frost-authenticator/vault.json`
- **运行方式**：本地离线运行，不依赖云同步


## 用途：通用网站 2FA Authenticator

Frost Authenticator 用于替代手机端 Google Authenticator、Microsoft Authenticator 的“验证码生成器”部分，承担网站登录时的 2FA / MFA 验证码角色。

典型使用场景：

- 登录 Google 账号时，输入由 Frost Authenticator 生成的 6 位验证码；
- 登录 GitHub 时，输入由 Frost Authenticator 生成的 two-factor authentication code；
- 登录支持“Authenticator app”“Google Authenticator”“TOTP”“Time-based one-time password”的网站时，使用 Frost 保存该网站提供的二维码或 Base32 密钥；
- 把验证码生成器放在 Ubuntu 桌面上，而不是依赖手机、浏览器插件或云同步服务。

工作方式很简单：网站在开启 2FA 时通常会显示一个二维码，或提供一段手动输入密钥。这个二维码/密钥本质上是一个 TOTP 种子。Frost Authenticator 将它保存在本地加密保险库中，并按时间生成一次性验证码。之后每次登录该网站时，打开 Frost，复制当前验证码，填入网站的 2FA 输入框即可。

适用网站包括但不限于：

- Google / Gmail / Google Workspace；
- GitHub；
- GitLab；
- Microsoft、Amazon、Cloudflare、Discord、Proton、Tailscale 等支持标准 TOTP 的服务；
- 自建系统、服务器面板、VPN、内网后台等支持 `otpauth://totp/...` 的登录系统。

边界也要说清楚：Frost Authenticator 支持的是标准 TOTP 验证码，不是短信验证码、邮件验证码、硬件安全密钥、Passkey/WebAuthn、推送确认或某些厂商私有的设备绑定登录流程。如果网站要求“打开手机 App 点确认”，那不是 Frost 的目标；如果网站给你二维码让你用 Google Authenticator 扫描，通常就是 Frost 的目标。

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

## 为什么使用 Frost Authenticator，而不是 KeePassXC 等竞品？

先说冰冷事实：KeePassXC 是成熟、强大、跨平台的密码管理器。它可以保存密码，也可以为条目生成 TOTP 验证码；[KeePassXC 官方用户指南](https://keepassxc.org/docs/KeePassXC_UserGuide)也说明，配置后它能像 Google Authenticator 一类应用那样计算 TOTP，并可配合复制粘贴、浏览器扩展和 Auto-Type 使用。  

Frost Authenticator 的目标不是“在所有维度击败 KeePassXC”，而是解决一个更窄、更明确的问题：**在 Ubuntu 桌面上，把二次验证代码从密码管理器的主工作流中拆出来，做成一个专注、轻量、可审计、离线的本地 TOTP 工具。**

### 1. 2FA 应该尽量和密码分离

如果密码和 TOTP 种子放在同一个大保险库里，一旦这个保险库被解锁、导出、同步错误或被恶意进程读取，攻击者可能同时拿到“你知道的东西”（密码）和“你拥有的第二因素种子”。KeePassXC 官方指南也提醒：把 TOTP 和密码放在同一个数据库中会削弱二次验证的优势；如果追求最大安全性，应把 TOTP 放在单独的数据库中，只在需要时解锁。

Frost Authenticator 默认就是这种拆分思路：

- 不保存登录密码；
- 不做浏览器密码填充；
- 不接管 passkey、SSH Agent、Auto-Type 等大范围身份能力；
- 只保存 TOTP 所需的最小字段；
- 只在需要验证码时打开。

这不是“功能少”的缺陷，而是有意缩小攻击面。Frost 的优势在于边界清楚：它不是你的总钥匙串，而是你的验证码盒子。

### 2. 专用工具比全能工具更不容易误操作

全能密码管理器的价值在于集中管理：密码、URL、备注、附件、自定义字段、浏览器扩展、自动输入、密码健康检查、导入导出、同步方案等。问题是，这些能力也会带来更复杂的状态和更多入口。

Frost Authenticator 刻意只保留 Authenticator 的核心动作：

1. 添加 TOTP；
2. 查看当前验证码；
3. 复制验证码；
4. 编辑或删除账号；
5. 从 URI / 二维码导入。

这让日常使用路径更短：打开、解锁、复制、关闭。对于“我只想在 Ubuntu 上有一个本地验证码器”的用户，少一步配置、少一个概念、少一次误点，就是实际优势。

### 3. Ubuntu-first，而不是跨平台妥协

KeePassXC 的跨平台能力很强，这是它的优势。但 Frost Authenticator 的取舍相反：它直接面向 Ubuntu 24.04 + Python 3.12 + PyQt6 的桌面使用场景。

因此 Frost 可以把安装、运行、桌面入口和数据位置写得非常明确：

- 推荐 Ubuntu 24.04 LTS；
- 使用项目内 `.venv`，不污染系统 Python；
- 提供 `install.sh` 一键安装；
- 提供 `.desktop` 启动器；
- 默认保险库路径固定为 `~/.local/share/frost-authenticator/vault.json`；
- 提供 `scripts/reset_global.sh` 做全局重置并自动备份。

这类“窄平台优化”不如跨平台宏大，但对 Ubuntu 用户更直接、更可控。

### 4. 更容易审计和改造

Frost Authenticator 是小型 Python/PyQt6 项目。核心逻辑集中在几个文件中：

- `totp.py`：HOTP / TOTP 算法；
- `vault.py`：本地保险库加密与读写；
- `otpauth.py`：`otpauth://` URI 解析；
- `app.py`：桌面界面。

这意味着你可以较快读完关键路径：TOTP 是怎么生成的、密钥是怎么保存的、复制按钮做了什么、保险库写到哪里。对个人工具来说，可理解性本身就是安全属性：你更容易发现它没有做什么，也更容易按自己的威胁模型修改它。

### 5. 不绑定云，也不诱导同步

Frost Authenticator 默认不提供云同步、不要求账号登录、不接浏览器插件、不上传验证码种子。备份策略由用户自己决定：备份本地 `vault.json`，并单独记住主密码。

这牺牲了多设备便利性，换来的是更清晰的数据路径。对于只在一台可信 Ubuntu 机器上使用验证码的场景，这种“笨但透明”的方案更容易控制。

### 6. 什么时候不该选 Frost？

如果你需要下面这些能力，KeePassXC 或其他成熟密码管理器可能更合适：

- 同时管理密码、密钥、备注和附件；
- 浏览器自动填充；
- Auto-Type；
- passkey / SSH Agent 等高级集成；
- 多平台长期同步工作流；
- 更成熟的安全审计历史和社区生态。

Frost 的强项不是“功能最多”，而是**职责单一、边界清楚、Ubuntu 本地体验直接、TOTP 与密码管理解耦**。如果你已经用 KeePassXC 管密码，Frost 更适合作为旁边那个独立的二次验证工具，而不是替代整个密码管理器。

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


## 全局重置

如果需要把 Frost Authenticator 恢复到首次运行状态，可以执行：

```bash
./scripts/reset_global.sh
```

它会重置：

- `~/.local/share/frost-authenticator`
- `~/.config/frost-authenticator`
- `~/.cache/frost-authenticator`
- Ubuntu 桌面启动器与图标

安全边界：脚本会把已有本地数据移动到带时间戳的备份目录，而不是直接删除。备份位置类似：

```text
~/.local/share/frost-authenticator-backups/reset-YYYYmmdd-HHMMSS
```

如果只想重置本地数据、保留桌面启动器：

```bash
./scripts/reset_global.sh --keep-desktop
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
