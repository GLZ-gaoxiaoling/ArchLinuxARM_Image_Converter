#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arch Linux ARM 镜像转换工具
将 Arch Linux ARM 的 tar.gz 转换为虚拟机可用的镜像格式

Usage:
    python convert_alarm.py --output alarm.qcow2 --size 128G --mirror tsinghua
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# 常量定义
REQUIRED_SPACE_GB = 2  # 下载所需最小磁盘空间（GB）
DEFAULT_IMAGE_SIZE = "128G"  # 默认镜像大小
DEFAULT_OUTPUT_FILE = "alarm.qcow2"  # 默认输出文件名
MIRRORS = {
    "official": "http://os.archlinuxarm.org/os/ArchLinuxARM-aarch64-latest.tar.gz",
    "tsinghua": "https://mirrors.tuna.tsinghua.edu.cn/archlinuxarm/os/ArchLinuxARM-aarch64-latest.tar.gz"
}
DEPENDENCIES = {
    "darwin": {
        "qemu-img": "brew install qemu",
        "kpartx": "brew install kpartx",
        "gdisk": "brew install gptfdisk",
        "mkfs.vfat": "通常包含在dosfstools包中",
        "mkfs.ext4": "通常包含在e2fsprogs包中",
        "bsdtar": "brew install libarchive"
    },
    "linux": {
        "debian": {
            "qemu-img": "apt install qemu-utils",
            "kpartx": "apt install kpartx",
            "gdisk": "apt install gdisk",
            "mkfs.vfat": "apt install dosfstools",
            "mkfs.ext4": "apt install e2fsprogs",
            "bsdtar": "apt install libarchive-tools"
        },
        "arch": {
            "qemu-img": "pacman -S qemu",
            "kpartx": "pacman -S multipath-tools",
            "gdisk": "pacman -S gptfdisk",
            "mkfs.vfat": "pacman -S dosfstools",
            "mkfs.ext4": "pacman -S e2fsprogs",
            "bsdtar": "pacman -S libarchive"
        }
    }
}

def check_dependencies() -> None:
    """
    检查并安装必要的依赖工具
    """
    package_manager = None
    required = {}

    if sys.platform == 'darwin':
        package_manager = 'brew'
        required = DEPENDENCIES["darwin"]
    else:
        try:
            with open('/etc/os-release') as f:
                os_release = f.read().lower()
                if 'debian' in os_release or 'ubuntu' in os_release:
                    package_manager = 'apt'
                    required = DEPENDENCIES["linux"]["debian"]
                elif 'arch' in os_release or 'manjaro' in os_release:
                    package_manager = 'pacman'
                    required = DEPENDENCIES["linux"]["arch"]
                else:
                    logging.error("不支持的操作系统，请手动安装依赖工具")
                    sys.exit(1)
        except FileNotFoundError:
            logging.error("无法确定Linux发行版，请手动安装依赖工具")
            sys.exit(1)

    missing = [cmd for cmd, _ in required.items() if not shutil.which(cmd)]

    if missing:
        logging.error(f"缺少必要的工具({package_manager}):")
        for cmd in missing:
            logging.error(f"  - {cmd}: {required[cmd]}")
        logging.info("请先安装上述工具后再运行本脚本。")
        sys.exit(1)

def download_alarm(output_file: str, mirror: str = "tsinghua") -> None:
    """
    下载 Arch Linux ARM 基础包
    :param output_file: 输出文件路径
    :param mirror: 镜像源 (official 或 tsinghua)
    """
    url = MIRRORS.get(mirror, MIRRORS["tsinghua"])
    logging.info(f"正在从 {url} 下载 Arch Linux ARM 基础包...")

    required_space = REQUIRED_SPACE_GB * 1024**3  # 转换为字节
    stat = os.statvfs(os.path.dirname(output_file))
    available_space = stat.f_frsize * stat.f_bavail

    if available_space < required_space:
        logging.error(f"磁盘空间不足，需要至少 {REQUIRED_SPACE_GB}GB 可用空间")
        sys.exit(1)

    try:
        cmd = ["curl", "-#", "-o", output_file, url]
        subprocess.run(cmd, check=True)
        logging.info("下载完成！")
    except subprocess.CalledProcessError as e:
        logging.error(f"下载失败: {e}")
        if os.path.exists(output_file):
            os.remove(output_file)
        sys.exit(1)
    except KeyboardInterrupt:
        logging.warning("下载被用户中断")
        if os.path.exists(output_file):
            os.remove(output_file)
        sys.exit(1)

def create_image(output_file: str, size: str = DEFAULT_IMAGE_SIZE) -> None:
    """
    创建并格式化 qcow2 镜像
    :param output_file: 输出文件路径
    :param size: 镜像大小 (例如 '128G')
    """
    try:
        size_num = int(size[:-1])
        size_unit = size[-1].upper()
        if size_unit not in ['K', 'M', 'G', 'T']:
            raise ValueError
    except (ValueError, IndexError):
        logging.error(f"无效的镜像大小格式: {size}, 请使用类似 '128G' 的格式")
        sys.exit(1)

    logging.info(f"正在创建 {size} 大小的 qcow2 镜像...")

    if os.path.exists(output_file):
        logging.warning(f"输出文件 {output_file} 已存在")
        confirm = input("是否覆盖? (y/N): ").strip().lower()
        if confirm != 'y':
            logging.info("操作已取消")
            sys.exit(0)

    try:
        result = subprocess.run(["qemu-img", "create", "-f", "qcow2", output_file, size],
                                stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True)
        logging.info("镜像创建完成！")
        if result.stderr:
            logging.warning(f"镜像创建警告: {result.stderr.decode('utf-8').strip()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"创建镜像失败: {e.stderr.decode('utf-8').strip() if e.stderr else e}")
        if os.path.exists(output_file):
            os.remove(output_file)
        sys.exit(1)
    except KeyboardInterrupt:
        logging.warning("操作被用户中断")
        if os.path.exists(output_file):
            os.remove(output_file)
        sys.exit(1)

    logging.info("正在为镜像分区...")
    try:
        result = subprocess.run(["gdisk", output_file],
                                input=b"o\nn\n\n\n+300M\nef00\nn\n\n\n\n\nw\ny\n",
                                stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True)
        logging.info("分区完成！")
        if result.stderr:
            logging.warning(f"分区警告: {result.stderr.decode('utf-8').strip()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"分区失败: {e.stderr.decode('utf-8').strip() if e.stderr else e}")
        logging.info("请检查磁盘空间是否充足，并确保有足够的权限。")
        sys.exit(1)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="Arch Linux ARM 镜像转换工具",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_FILE,
                        help=f"输出 qcow2 镜像文件名 (默认: %(default)s)")
    parser.add_argument("--size", "-s", default=DEFAULT_IMAGE_SIZE,
                        help=f"镜像大小，如 128G (默认: %(default)s)")
    parser.add_argument("--mirror", "-m", default="tsinghua",
                        choices=["official", "tsinghua"],
                        help="下载镜像源: official(官方)或 tsinghua(清华) (默认: %(default)s)")
    parser.add_argument("--convert-to", "-c",
                        choices=["vmdk", "parallels"],
                        help="转换为 VMware(vmdk) 或 Parallels 格式")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制覆盖已存在的文件而不提示")

    args = parser.parse_args()

    logging.info("=== Arch Linux ARM 镜像转换工具 ===")
    logging.info("1. 检查必要工具...")
    check_dependencies()

    tar_file = "ArchLinuxARM-aarch64-latest.tar.gz"

    logging.info("2. 下载基础包...")
    if not os.path.exists(tar_file):
        download_alarm(tar_file, args.mirror)
    else:
        logging.info(f"发现已存在的 {tar_file}，跳过下载")

    logging.info("3. 创建镜像...")
    create_image(args.output, args.size)

if __name__ == "__main__":
    main()