import sys
import time, datetime
import threading
import sched


def time_until(t_end, t_now = None):
    if t_now is None:
        t_now = datetime.datetime.now()
    return t_end - t_now

def job(i):
    print("\nRunning job: ", i+1)
    time.sleep(5)
    print("Job {} completed.".format(i+1))


def noop():
    return None



scheduler = sched.scheduler(time.time, time.sleep)

for i in range(3):
    if scheduler.empty():
        scheduler.enter(15, 1, noop)
        t = threading.Thread(target=scheduler.run)
        t.start()
    while not(scheduler.empty()):
        tnext = scheduler.queue[0][0]
        print("Time until next job:", tnext - time.time())
        sys.stdout.write("\033[F")
        time.sleep(0.1)
    scheduler.enter(15, 1, noop)
    t = threading.Thread(target=scheduler.run)
    t.start()    
    job(i)




