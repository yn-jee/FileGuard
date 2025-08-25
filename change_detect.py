import sys, logging, yaml
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler


def run_change_detecter(cfg, on_modified):
    # 디렉터리 경로 가져오기
    path = cfg.get("directory")
    if not path:
        print("config.yaml에 'directory' 키가 없습니다.")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    class _CallbackHandler(FileSystemEventHandler): # 팝업 시의 콜백 함수
        def on_modified(self, event):
            if not event.is_directory:
                on_modified(event.src_path)
    event_handler = _CallbackHandler()    
    
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()
