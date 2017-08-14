from datetime import datetime
import subprocess
import time
import multiprocessing as mp

#
# When should this script fire off
#
trigger_time = datetime(2017, 8, 10, 15, 48)

triggered = False

results = []
def log_result(result):
    results.append(result)

def run_script(script):
    args = ['python']
    args += script
    print("Running: ", args)
    with subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=None) as proc:
        proc.wait()
        return proc.returncode

while not triggered:
    now = datetime.now()
    if now >= trigger_time:

        print('Downloading data...')
        scripts = [['get_GOES.py', str(channel)] for channel in range(1, 17)]
        scripts.insert(0, ['get_ASOS.py'])
        with mp.Pool(processes=6) as pool:
            for script in scripts:
                pool.apply_async(run_script, args=(script,), callback=log_result)
            pool.close()
            pool.join()

        print('Making Animations...')
        with mp.Pool(processes=4) as pool:
            scripts = [['goes_animations.py', str(channel)] for channel in range(1, 17)]
            # Append the surface maps here as well
            scripts = scripts + ['temperature_change_map.py', 'temperature_map.py']
            for script in scripts:
                pool.apply_async(run_script, args=(script,), callback=log_result)
            pool.close()
            pool.join()

        triggered = True
        
    else:
        minutes_to_run = round((trigger_time - now).total_seconds() / 60.0)
        print('Script will fire in {} minutes'.format(minutes_to_run))
        time.sleep(60)
