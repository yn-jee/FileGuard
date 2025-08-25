import os, sys, yaml, shutil, time
import win32con, win32event, win32evtlog
from datetime import datetime


def run_open_detecter(cfg):
    watch_root = os.path.normcase(os.path.normpath(cfg.get("directory", "")))
    script_root = os.path.dirname(os.path.abspath(__file__))
    backup_root = os.path.normpath(os.path.join(script_root, cfg.get("backup_dir", "backup")))
    os.makedirs(backup_root, exist_ok=True)

    extensions = set(cfg.get("extensions", []))  # 감시 확장자 집합
    if not extensions:
        print("config.yaml에 'extensions' 항목이 없습니다. 모든 파일을 감시합니다.")


    pHandle = win32evtlog.OpenEventLog(None, 'Security')
    # Application 로그 오픈
    cHandle = win32event.CreateEvent(None, 0, 0, None) 
    # 새로운 이벤트를 생성
    win32evtlog.NotifyChangeEventLog(pHandle, cHandle)


    # 실행 시점 이후의 로그만 처리하도록
    start_time = datetime.now()
    print("Watching Security log for 4663 (File access) events...")

    flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    while True:
        # 새 이벤트가 올라올 때까지 최대 5초 대기
        rc = win32event.WaitForSingleObject(cHandle, 5000)
        if rc == win32con.WAIT_TIMEOUT:
            continue  # 새 이벤트가 없는 경우 다시 대기

        # 이벤트 발생
        while True:
            events = win32evtlog.ReadEventLog(pHandle, flags, 0)
            if not events:
                break
            for ev in events:
                eid = ev.EventID & 0xFFFF
                if eid == 4663:
                    data = getattr(ev, "StringInserts", None)
                    if not data:
                        continue

                    filepath = None
                    for d in data:
                        if ":" in d and "\\" in d:  # 단순 경로 판별
                            filepath = d
                            break

                    # !! 파일 생성 시의 python.exe의 접근은 제외해야 함
                    # 무한 루프 방지
                    proc_seen = False
                    for d in data:
                        if isinstance(d, str) and d.lower().endswith(".exe") and "python.exe" in d.lower():
                            proc_seen = True
                            break
                    if proc_seen:
                        continue
                    
                    if filepath:
                        if ev.TimeGenerated < start_time:
                            continue

                        # 하위 루트만 감시하기
                        fullpath = os.path.normcase(os.path.normpath(filepath))
                        if not fullpath.startswith(watch_root + os.sep):
                            continue

                        ext = os.path.splitext(filepath)[1].lower()
                        if not extensions or ext in extensions:
                            print("----- 4663 File Access Detected -----")
                            print("Time Generated:", ev.TimeGenerated)
                            print("Source Name:", ev.SourceName)
                            print("Event ID:", eid)
                            if data:
                                for i, v in enumerate(data, 1):
                                    print(f"Field[{i}]: {v}")

                                # 백업하기
                                try:
                                    rel = os.path.relpath(fullpath, watch_root)
                                    dest_base = os.path.join(backup_root, rel)
                                    os.makedirs(os.path.dirname(dest_base), exist_ok=True)
                                    ts = time.strftime("%Y%m%d-%H%M%S") # 백업 파일 생성 시점기록
                                    base, e2 = os.path.splitext(dest_base)
                                    dest = f"{base}.{ts}{e2}"
                                    shutil.copy2(fullpath, dest)
                                    print("Backup ->", dest)
                                except Exception as ex:
                                    print("backup failed:", ex)

                            print("-------------------------------------")

        win32event.ResetEvent(cHandle)
