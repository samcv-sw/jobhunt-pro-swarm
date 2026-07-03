import os

log_files = ["sam_max.log", "error_log.txt", "auto_pilot_log.txt", "run_logs.txt"]

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"=== LAST 100 LINES OF {log_file} ===")
        try:
            with open(log_file, "rb") as f:
                # Seek to end and read last 100 lines
                f.seek(0, 2)
                file_size = f.tell()
                
                # Read backwards to find 100 newlines
                buffer_size = 8192
                lines_found = 0
                data = b""
                pos = file_size
                
                while pos > 0 and lines_found < 101:
                    to_read = min(buffer_size, pos)
                    pos -= to_read
                    f.seek(pos)
                    chunk = f.read(to_read)
                    data = chunk + data
                    lines_found = data.count(b"\n")
                
                # Split and get last 100 lines
                lines = data.split(b"\n")
                last_100 = lines[-100:]
                for line in last_100:
                    print(line.decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
        print("\n" + "="*50 + "\n")
    else:
        print(f"Log file {log_file} does not exist.\n")
