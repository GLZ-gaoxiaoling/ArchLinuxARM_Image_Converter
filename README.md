# Arch Linux ARM 镜像转换工具
- 参考资料:InSnh-Gd老师发布于知乎的文章[在M1 PD和VMware Fusion或QEMU/KVM上运行Arch Linux ARM](https://zhuanlan.zhihu.com/p/429072991)
## 项目简介

本工具用于将 Arch Linux ARM 的 tar.gz 基础包转换为虚拟机可用的镜像格式（如 qcow2、VMDK 等），支持快速部署 ARM 架构的虚拟机环境。

## 功能特性

- 自动下载最新版 Arch Linux ARM 基础包（支持官方和清华镜像源）
- 创建指定大小的 qcow2 虚拟磁盘镜像
- 自动分区（EFI 系统分区 + 根分区）
- 支持转换为 VMware (VMDK) 和 Parallels 格式
- 跨平台支持（macOS/Linux）
- 详细的日志输出和错误处理

## 安装要求

### macOS

```bash
brew install qemu gptfdisk multipath-tools libarchive
```

### Debian/Ubuntu

```bash
sudo apt install qemu-utils kpartx gdisk dosfstools e2fsprogs libarchive-tools
```

### Arch Linux

```bash
sudo pacman -S qemu multipath-tools gptfdisk dosfstools e2fsprogs libarchive
```

## 使用方法

### 基本使用

```bash
python3 convert_alarm.py --output alarm.qcow2 --size 128G --mirror tsinghua
```

### 参数说明

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `--output` | `-o` | alarm.qcow2 | 输出镜像文件名 |
| `--size` | `-s` | 128G | 镜像大小（如 64G, 128G） |
| `--mirror` | `-m` | tsinghua | 下载镜像源（official/tsinghua） |
| `--convert-to` | `-c` | 无 | 转换为指定格式（vmdk/parallels） |
| `--force` | `-f` | 无 | 强制覆盖已存在文件 |

### 转换示例

转换为 VMware VMDK 格式：

```bash
python3 convert_alarm.py --output alarm.vmdk --convert-to vmdk
```

## 注意事项

1. 需要至少 2GB 可用磁盘空间用于下载基础包
2. 创建镜像需要 root 权限（Linux）或管理员权限（macOS）
3. 建议在 SSD 上运行以获得最佳性能

## 许可证

MIT License