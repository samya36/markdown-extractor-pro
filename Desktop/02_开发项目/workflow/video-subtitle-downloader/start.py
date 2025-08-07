#!/usr/bin/env python3
"""
增强版视频字幕下载器启动脚本
支持YouTube访问限制绕过和AI字幕生成
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_requirements():
    """检查必要的依赖"""
    print("🔍 检查系统环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本需要3.8或更高")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  FFmpeg未安装或未在PATH中")
        print("   请访问 https://ffmpeg.org/download.html 下载安装")
        return False
    
    return True

def setup_environment():
    """设置环境"""
    print("\n📦 设置Python环境...")
    
    # 创建虚拟环境
    venv_path = Path("venv")
    if not venv_path.exists():
        print("创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # 确定虚拟环境的Python路径
    if os.name == 'nt':  # Windows
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:  # macOS/Linux
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"
    
    # 升级pip
    print("升级pip...")
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    
    # 安装依赖
    requirements_file = Path("backend") / "requirements.txt"
    if requirements_file.exists():
        print("安装Python依赖...")
        subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
    
    return python_path

def setup_frontend():
    """设置前端环境"""
    print("\n🎨 设置前端环境...")
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ 前端目录不存在")
        return False
    
    # 检查Node.js
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True)
        print("✅ Node.js已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js未安装，请访问 https://nodejs.org/ 下载安装")
        return False
    
    # 安装前端依赖
    os.chdir(frontend_path)
    
    if Path("package-lock.json").exists() or Path("yarn.lock").exists():
        print("安装前端依赖...")
        if Path("yarn.lock").exists():
            subprocess.run(["yarn", "install"], check=True)
        else:
            subprocess.run(["npm", "install"], check=True)
    
    os.chdir("..")
    return True

def start_backend(python_path, host="0.0.0.0", port=8000):
    """启动后端服务"""
    print(f"\n🚀 启动后端服务 (http://{host}:{port})...")
    
    # 切换到backend目录
    backend_path = Path("backend")
    os.chdir(backend_path)
    
    # 使用enhanced_main.py启动增强版API
    main_file = "enhanced_main.py"
    if not Path(main_file).exists():
        print(f"❌ {main_file} 不存在")
        return False
    
    # 启动uvicorn服务
    cmd = [
        str(python_path), "-m", "uvicorn", 
        "enhanced_main:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    return True

def start_frontend():
    """启动前端服务"""
    print("\n🌐 启动前端服务...")
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ 前端目录不存在")
        return False
    
    os.chdir(frontend_path)
    
    # 启动前端开发服务器
    if Path("yarn.lock").exists():
        subprocess.run(["yarn", "start"])
    else:
        subprocess.run(["npm", "start"])
    
    return True

def print_usage_info():
    """打印使用说明"""
    print("\n" + "="*60)
    print("🎉 增强版视频字幕下载器启动成功！")
    print("="*60)
    print("📱 前端界面: http://localhost:3000")
    print("🔧 后端API:  http://localhost:8000")
    print("📖 API文档:  http://localhost:8000/docs")
    print("="*60)
    print("\n🆕 新功能:")
    print("• 🚫 YouTube访问限制绕过")
    print("• 🔒 代理服务器支持")
    print("• 🤖 AI字幕生成 (Whisper)")
    print("• 📋 任务队列管理")
    print("• 🔄 重试和错误恢复")
    print("• 📊 系统状态监控")
    print("• 🌐 支持数百个视频平台")
    print("\n💡 使用提示:")
    print("• 如遇YouTube限制，请在代理设置中添加代理服务器")
    print("• AI字幕生成需要下载Whisper模型，首次使用会较慢")
    print("• 任务管理页面可以查看下载进度和历史记录")
    print("• 支持批量语言和格式选择")
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="增强版视频字幕下载器")
    parser.add_argument("--mode", choices=["setup", "backend", "frontend", "full"], 
                       default="full", help="运行模式")
    parser.add_argument("--host", default="0.0.0.0", help="后端服务主机")
    parser.add_argument("--port", type=int, default=8000, help="后端服务端口")
    parser.add_argument("--skip-check", action="store_true", help="跳过环境检查")
    
    args = parser.parse_args()
    
    print("🎬 增强版视频字幕下载器")
    print("支持YouTube访问限制绕过 + AI字幕生成")
    print("-" * 50)
    
    # 检查环境
    if not args.skip_check and not check_requirements():
        print("❌ 环境检查失败，请解决上述问题后重试")
        sys.exit(1)
    
    try:
        if args.mode in ["setup", "full"]:
            # 设置后端环境
            python_path = setup_environment()
            
            # 设置前端环境
            if not setup_frontend():
                print("❌ 前端环境设置失败")
                sys.exit(1)
        
        if args.mode == "backend":
            # 只启动后端
            python_path = Path("venv/bin/python") if os.name != 'nt' else Path("venv/Scripts/python.exe")
            start_backend(python_path, args.host, args.port)
        elif args.mode == "frontend":
            # 只启动前端
            start_frontend()
        elif args.mode == "full":
            print_usage_info()
            print("\n选择启动模式:")
            print("1. 启动后端服务")
            print("2. 启动前端服务")
            print("3. 退出")
            
            while True:
                choice = input("\n请选择 (1/2/3): ").strip()
                if choice == "1":
                    start_backend(python_path, args.host, args.port)
                    break
                elif choice == "2":
                    start_frontend()
                    break
                elif choice == "3":
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请输入 1、2 或 3")
    
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()