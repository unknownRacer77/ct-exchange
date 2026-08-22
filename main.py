import subprocess
import threading

def run_crawler():
    subprocess.run(["python", "crawler.py"])

def run_checker():
    subprocess.run(["python", "event_checker.py"])

if __name__ == "__main__":
    t1 = threading.Thread(target=run_crawler)
    t2 = threading.Thread(target=run_checker)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()