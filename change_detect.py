import sys, logging, yaml
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

# 인자로 받은 config.yaml 읽기
if len(sys.argv) < 2:
    print("Usage: python main.py <config.yaml>")
    sys.exit(1)

config_path = sys.argv[1]
with open(config_path, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# 디렉터리 경로 가져오기
path = cfg.get("directory")
if not path:
    print("config.yaml에 'directory' 키가 없습니다.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
event_handler = LoggingEventHandler()
observer = Observer()
observer.schedule(event_handler, path, recursive=True)
observer.start()
try:
    while observer.is_alive():
        observer.join(1)
finally:
    observer.stop()
    observer.join()
