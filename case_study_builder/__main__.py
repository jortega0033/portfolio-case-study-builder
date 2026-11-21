"""CLI: python -m case_study_builder --data-dir DIR --port PORT"""

from __future__ import annotations

import argparse
import signal
import sqlite3
import sys
import threading

from .server import create_server
from .storage import SchemaTooNew


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("port must be an integer") from None
    if not 0 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 0 and 65535")
    return port


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="case_study_builder")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--port", required=True, type=_port)
    args = parser.parse_args(argv)

    try:
        server = create_server(args.data_dir, args.port)
    except SchemaTooNew as e:
        print(f"error: {e}", file=sys.stderr, flush=True)
        return 2
    except sqlite3.Error as e:
        print(f"error: cannot open database: {e}", file=sys.stderr, flush=True)
        return 1
    except OSError as e:
        print(f"error: cannot start server: {e}", file=sys.stderr, flush=True)
        return 1

    def stop(signum, frame):
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, stop)

    print(f"Serving on http://127.0.0.1:{server.server_address[1]}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
