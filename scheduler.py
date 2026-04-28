import time
import datetime
from core.blocker import block_sites, unblock_sites

def run_scheduler(start_hour=9, end_hour=17):
    print("⏰ Scheduler started...")
    print(f"🔒 Block time: {start_hour}:00 AM to {end_hour}:00 PM")
    
    while True:
        current_time = datetime.datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        print(f"\n🕐 Current time: {current_hour}:{current_minute:02d}")
        
        if start_hour <= current_hour < end_hour:
            print("📵 Work hours - Blocking sites...")
            block_sites()
        else:
            print("✅ Off hours - Unblocking sites...")
            unblock_sites()
        
        time.sleep(60)  # Check every 60 seconds