import sys, os, glob, yaml, threading
import tkinter as tk
from tkinter import messagebox

from open_detect import run_open_detecter        # 파일 오픈(4663), 백업 파일 생성
from change_detect import run_change_detecter     # 파일 변경 감지(콜백 호출)

def load_config():
    if len(sys.argv) < 2:
        print("Usage: python main.py config.yaml")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_latest_backup_for(filepath, cfg, project_dir):
    # 백업 폴더에서 원본 파일의 백업 파일을 찾음
    watch_root = os.path.normcase(os.path.normpath(cfg.get("directory", "")))
    backup_root = os.path.normpath(os.path.join(project_dir, cfg.get("backup_dir", "backup")))

    fullpath = os.path.normcase(os.path.normpath(filepath))
    try:
        rel = os.path.relpath(fullpath, watch_root)
    except ValueError:
        # 감시 루트 외 경로일 수 있음
        return None

    base_no_ts, ext = os.path.splitext(os.path.join(backup_root, rel))
    pattern = base_no_ts + ".*" + ext  # 타임스탬프가 중간에 들어감
    cands = glob.glob(pattern)
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)

if __name__ == "__main__":
    cfg = load_config()
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Tk 초기화 (항상 맨 앞에 오도록)
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    # 변경 감지 콜백
    def on_file_modified(filepath):
        latest = find_latest_backup_for(filepath, cfg, project_dir)
        if latest:
            messagebox.showinfo(
                "파일 변경 감지",
                f"파일 변경이 감지되었습니다.\n\n원본: {filepath}\n백업 파일: {latest}\n\n필요 시 수동으로 백업본을 복사해 복구하세요.",
                parent=root
            )
        else:
            # 해당 원본에 대한 백업이 없을 때
            backup_root = os.path.join(project_dir, cfg.get("backup_dir", "backup"))
            messagebox.showinfo(
                "파일 변경 감지",
                f"파일 변경이 감지되었습니다.\n\n원본: {filepath}\n백업 파일을 찾지 못했습니다.\n백업 폴더를 확인하세요:\n{backup_root}",
                parent=root
            )

    # 4663 감지
    t_open = threading.Thread(target=run_open_detecter, args=(cfg,), daemon=True)
    t_open.start()

    # 변경 감지
    t_change = threading.Thread(target=run_change_detecter, args=(cfg, on_file_modified), daemon=True)
    t_change.start()

    print("메인 루프 시작 (Ctrl+C 종료)")
    root.mainloop()
