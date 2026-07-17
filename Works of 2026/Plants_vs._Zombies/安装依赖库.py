import importlib.util
import itertools
import subprocess
import sys
import threading
import time

# 优先使用国内镜像；如果失败，会自动切换到官方源
MIRROR_URL = 'https://pypi.tuna.tsinghua.edu.cn/simple'
OFFICIAL_URL = 'https://pypi.org/simple'

# pip包名、导入名、说明
PACKAGES = [
    ('requests', 'requests', 'AI 接口请求库'),
    ('pygame', 'pygame', '游戏运行核心库'),
    ('pygame-textinput', 'pygame_textinput', '文本输入组件'),
]

PIP_SOURCES = [
    ('清华镜像源', MIRROR_URL),
    ('官方源', OFFICIAL_URL),
]


def safe_input(message):
    try:
        input(message)
    except (EOFError, KeyboardInterrupt):
        pass


def print_line(char='=', width=60):
    print(char * width)


def spinner_chars():
    for char in itertools.cycle(['|', '/', '-', '\\']):
        yield char


def show_progress(stop_event, message):
    spinner = spinner_chars()
    while not stop_event.is_set():
        sys.stdout.write('\r{} {}...'.format(next(spinner), message))
        sys.stdout.flush()
        time.sleep(0.12)
    sys.stdout.write('\r' + ' ' * 90 + '\r')
    sys.stdout.flush()


def run_command(command, message):
    stop_event = threading.Event()
    progress_thread = threading.Thread(
        target=show_progress,
        args=(stop_event, message),
        daemon=True,
    )
    progress_thread.start()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
    finally:
        stop_event.set()
        progress_thread.join(timeout=1)

    return result


def run_pip(args, message):
    return run_command([sys.executable, '-m', 'pip'] + args, message)


def module_exists(import_name):
    return importlib.util.find_spec(import_name) is not None


def get_last_error(result):
    output = (result.stderr or result.stdout or '').strip()
    if not output:
        return '没有返回详细错误'

    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return '没有返回详细错误'

    # 优先显示真正的错误行，避免只显示 pip notice
    for line in reversed(lines):
        lower = line.lower()
        if 'error' in lower or 'failed' in lower or 'could not' in lower or 'no matching distribution' in lower:
            return line
    return lines[-1]


def check_pip_available():
    result = run_command(
        [sys.executable, '-m', 'pip', '--version'],
        '正在检查 pip',
    )
    if result.returncode == 0:
        print('✓ pip 可用：{}'.format((result.stdout or '').strip()))
        return True

    print('! 当前 Python 环境未检测到可用 pip，正在尝试启用 ensurepip...')
    ensure = run_command(
        [sys.executable, '-m', 'ensurepip', '--upgrade'],
        '正在启用 pip',
    )
    if ensure.returncode == 0:
        print('✓ pip 已启用')
        return True

    print('✗ pip 不可用：{}'.format(get_last_error(ensure)))
    return False


def install_package(pip_name, import_name):
    if module_exists(import_name):
        print('✓ {} 已安装，跳过'.format(pip_name))
        return True

    for source_name, source_url in PIP_SOURCES:
        host = source_url.split('/')[2]
        args = [
            'install',
            pip_name,
            '-i',
            source_url,
            '--trusted-host',
            host,
            '--disable-pip-version-check',
            '--no-input',
        ]

        result = run_pip(args, '正在通过{}安装 {}'.format(source_name, pip_name))
        if result.returncode == 0:
            if module_exists(import_name):
                print('✓ {} 安装成功（{}）'.format(pip_name, source_name))
                return True
            print('! {} 安装命令已完成，但导入验证失败'.format(pip_name))
        else:
            print('! {}安装失败：{}'.format(source_name, get_last_error(result)))

        if source_name != PIP_SOURCES[-1][0]:
            print('  正在切换源重试...')

    print('✗ {} 安装失败'.format(pip_name))
    return False


def verify_packages():
    print('\n正在进行最终验证...')
    failed = []
    for pip_name, import_name, _note in PACKAGES:
        if module_exists(import_name):
            print('✓ {} 可正常导入'.format(import_name))
        else:
            print('✗ {} 仍无法导入'.format(import_name))
            failed.append(pip_name)
    return failed


def print_banner():
    print_line()
    print('              PVZ 同人游戏依赖库安装工具')
    print_line()
    print('Python 版本：{}'.format(sys.version.split()[0]))
    print('Python 路径：{}'.format(sys.executable))
    print('优先镜像：{}'.format(MIRROR_URL))
    print_line('-')
    print('需要安装 / 检查的依赖：')
    for pip_name, _import_name, note in PACKAGES:
        print('  • {:<18} {}'.format(pip_name, note))
    print_line()
    print()


def main():
    print_banner()

    if not check_pip_available():
        print('\n无法继续安装。请重新安装 Python，并勾选 pip 组件。')
        safe_input('\n按回车键退出...')
        return

    print()
    success_count = 0
    total = len(PACKAGES)

    try:
        for index, (pip_name, import_name, _note) in enumerate(PACKAGES, start=1):
            print('[{}/{}] {}'.format(index, total, pip_name))
            if install_package(pip_name, import_name):
                success_count += 1
            print()
    except KeyboardInterrupt:
        print('\n\n用户中断了安装。')
        safe_input('\n按回车键退出...')
        return

    failed_verify = verify_packages()

    print('\n' + '=' * 60)
    if success_count == total and not failed_verify:
        print('  所有依赖安装并验证完成，可以运行游戏了！')
    else:
        print('  部分依赖可能未安装成功。')
        if failed_verify:
            print('  未通过验证的库：{}'.format(', '.join(failed_verify)))
        print('  建议：')
        print('  1. 检查网络连接后重新运行本脚本')
        print('  2. 确认正在使用正确的 Python 环境')
        print('  3. 如仍失败，可尝试以管理员身份运行')
    print('=' * 60)

    safe_input('\n按回车键退出...')


if __name__ == '__main__':
    main()
