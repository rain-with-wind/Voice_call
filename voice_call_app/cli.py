"""命令行接口 —— 解析参数并启动语音通话。"""

import argparse
import signal

from .config import VoiceCallConfig
from .windows import enable_utf8_console


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="直接 TCP 语音通话工具，支持可选密码认证和端到端加密。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用示例:\n"
            "  启动服务端:\n"
            "    python voice_call.py --mode server --port 5000\n\n"
            "  启动客户端:\n"
            "    python voice_call.py --mode client --host 192.168.1.100 --port 5000\n\n"
            "  加密通话:\n"
            "    python voice_call.py --mode server --port 5000 --encrypt --password 我的密码\n"
            "    python voice_call.py --mode client --host 192.168.1.100 --port 5000 --encrypt --password 我的密码\n"
        ),
    )
    parser.add_argument("--mode", choices=["server", "client"], required=True,
                        help="运行模式: server (服务端/接听) 或 client (客户端/拨打)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="客户端模式下要连接的服务端地址")
    parser.add_argument("--port", type=int, default=5000,
                        help="TCP 端口号")
    parser.add_argument("--password", "-p", default=None,
                        help="共享密码，用于通话认证")
    parser.add_argument("--encrypt", action="store_true",
                        help="启用基于密码的 Fernet 端到端加密（需同时指定 --password）")
    parser.add_argument("--rate", type=int, default=48000,
                        help="音频采样率 (Hz)")
    parser.add_argument("--channels", type=int, default=1,
                        help="音频声道数")
    parser.add_argument("--chunk", type=int, default=1024,
                        help="每次发送的音频帧大小")
    parser.add_argument("--input-device", type=int, default=None,
                        help="手动指定输入设备编号（麦克风）")
    parser.add_argument("--output-device", type=int, default=None,
                        help="手动指定输出设备编号（扬声器）")
    parser.add_argument("--list-devices", action="store_true",
                        help="仅列出所有音频设备后退出")
    return parser


def main() -> None:
    enable_utf8_console()
    parser = build_parser()
    args = parser.parse_args()
    from .engine import VoiceCall

    config = VoiceCallConfig(
        host="0.0.0.0",
        port=args.port,
        chunk=args.chunk,
        rate=args.rate,
        channels=args.channels,
        password=args.password,
        use_encryption=args.encrypt,
        input_device_index=args.input_device,
        output_device_index=args.output_device,
    )

    if args.list_devices:
        from .audio import AudioIO
        AudioIO.list_devices_static()
        return

    call = VoiceCall(config)

    def handle_signal(_signum, _frame) -> None:
        print("\n\n[提示] 正在退出通话...")
        call.stop()

    signal.signal(signal.SIGINT, handle_signal)

    if args.mode == "server":
        call.start_server()
    else:
        call.connect_to_server(args.host)
