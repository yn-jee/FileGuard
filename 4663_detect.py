import time
import win32con, win32event, win32evtlog
import sys, yaml, os

# 인자로 받은 config.yaml 읽기
if len(sys.argv) < 2:
    print("Usage: python main.py <config.yaml>")
    sys.exit(1)

config_path = sys.argv[1]
with open(config_path, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)


pHandle = win32evtlog.OpenEventLog(None, 'Security')
# Application 로그 오픈
cHandle = win32event.CreateEvent(None, 0, 0, None) 
# 새로운 이벤트를 생성
win32evtlog.NotifyChangeEventLog(pHandle, cHandle)

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
                print("----- 4663 File Access Detected -----")
                print("Time Generated:", ev.TimeGenerated)
                print("Source Name:", ev.SourceName)
                print("Event ID:", eid)
                data = getattr(ev, "StringInserts", None)
                if data:
                    for i, v in enumerate(data, 1):
                        print(f"Field[{i}]: {v}")
                print("-------------------------------------")

    win32event.ResetEvent(cHandle)
