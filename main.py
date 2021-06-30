# Libraries
import os
import signal
import datetime
import subprocess
from utility import voltValus, getVoltInD, getFreqInfo
from pathlib import Path
import time


def main():
    # the path of the Database / name of Database = myData
    my_file = Path("/home/myData")
    # Max Frequency
    defaultFreq = 3500
    # Min Frequency
    min_freq = 800
    # Max Voltage
    defaultVolt = 1.32
    # name of the user
    user = subprocess.run(
        "whoami",
        shell=True, capture_output=True, text=True)
    # Base information of CPU
    metadata_ = subprocess.run(
        "cat /proc/cpuinfo | grep 'vendor' | uniq && cat /proc/cpuinfo | grep 'model name' | uniq && cat /proc/cpuinfo | grep processor | wc -l",
        shell=True, capture_output=True, text=True)
    # Check the existence of the Database
    if my_file.is_file():
        from Database import session, undervolt, Benchmark_execution, Benchmarks, machine

        machine_ = session.query(machine).order_by(machine.id.desc()).first().metadata_
        #   get next Frequency and voltage and check machine
        if machine_ == metadata_.stdout:
            obj = session.query(undervolt).order_by(undervolt.id.desc()).first()

            if (session.query(undervolt).filter(undervolt.freq == obj.freq).count() == 1):
                from clear import clear_freq
                defaultFreq = obj.freq
                clear_freq(obj.freq)
                defaultVolt = session.query(undervolt).join(Benchmark_execution).filter(
                    Benchmark_execution.benchmarking == True).order_by(undervolt.id.desc()).first().voltage
            else:
                defaultFreq = getFreqInfo(obj)
                defaultVolt = obj.voltage
        else:
            machine_ = machine(host_name=user.stdout, metadata=metadata_.stdout)
            session.add(machine_)
            session.flush()
            session.commit()
    # create the Database if not exist
    else:
        from Database import session, undervolt, machine, Benchmark_execution, Benchmarks

        machine_ = machine(host_name=user.stdout, metadata_=metadata_.stdout)
        session.add(machine_)
        session.flush()
        session.commit()
    if defaultFreq >= min_freq:
        #   oc mode on and set the Frequency
        subprocess.run("zenstates --no-gui --oc-enable", shell=True)
        subprocess.run("zenstates --no-gui --oc-frequency " + str(defaultFreq), shell=True)
        #   get the list of the voltages for the loop
        voltageList = voltValus(defaultVolt)
        i = 0
        #   begin the process of the undervolting
        while i < len(voltageList):
            volt = voltageList[i]
            #       set the voltage and then save the information in 'undervolt' table
            subprocess.run("zenstates --no-gui --oc-vid " + str(volt), shell=True)
            temp = undervolt(freq=defaultFreq, voltage=getVoltInD('0x' + volt))
            session.add(temp)
            #       save the numbers of Benchmarks and the start time in Benchmark_execution table
            temp2 = Benchmark_execution(Benchmark_anz=2, time_start=datetime.datetime.now(),
                                        undervolt=temp)
            session.add(temp2)
            #       path and kind of Benchmark
            bench1 = Benchmarks(bench_art='Integer',
                                execution_command='~/test/config && runcpu --config=try1 --output_format text  --threads=32 657.xz_s',
                                Benchmark_execution=temp2)
            session.add(bench1)
            session.flush()
            session.commit()
            #       execute the values script/ 0 means do not save the temperature
            kindP = subprocess.Popen('python3.8 values.py 0', shell=True, preexec_fn=os.setsid)
            #       execute the first Benchmark
            x = subprocess.run(
                "cd ~/test && . ./shrc && cd config &&  cp test.cfg try1.cfg &&  runcpu --config=try1 --output_format text  --threads=32 657.xz_s",
                shell=True, capture_output=True, text=True)
            #       kill/stop values program
            os.killpg(os.getpgid(kindP.pid), signal.SIGTERM)
            print(x.stdout)
            re = x.stdout.split()
            #       check error
            if "Error:" in re:
                print("******/////// Error /////////******")
                time.sleep(1)
                subprocess.run("zenstates --no-gui --oc-disable", shell=True)
                #           restart the computer
                time.sleep(1)
                subprocess.run('sudo /opt/local/bin/reboot-node', shell=True)
                time.sleep(10)
            # no errors -> save the first benchmark information
            session.query(Benchmarks).filter(
                Benchmarks.id == session.query(Benchmarks).order_by(Benchmarks.id.desc()).first().id).update(
                {Benchmarks.finished: True})
            bench2 = Benchmarks(bench_art='Float',
                                execution_command='~/test/config && runcpu --config=try1  --copies=32 --output_format text  --threads=32 644.nab_s',
                                Benchmark_execution=temp2)
            session.add(bench2)
            session.flush()
            session.commit()
            #       execute a Benchmark
            kindP2 = subprocess.Popen('python3.8 values.py 1', shell=True, preexec_fn=os.setsid)
            y = subprocess.run(
                "cd ~/test && . ./shrc && cd config &&  cp test.cfg try1.cfg &&  runcpu --config=try1  --copies=32 --output_format text  --threads=32 644.nab_s",
                shell=True, capture_output=True, text=True)
            #       kill/stop values program
            os.killpg(os.getpgid(kindP2.pid), signal.SIGTERM)
            print(y.stdout)
            re1 = y.stdout.split()
            #       check error
            if "Error:" in re1:
                print("******/////// Error /////////******")
                subprocess.run("zenstates --no-gui --oc-disable", shell=True)
                time.sleep(1)
                #           restart
                subprocess.run("sudo /opt/local/bin/reboot-node", shell=True)
                time.sleep(10)
            #       no errors -> save the information of the second benchmark
            session.query(Benchmark_execution).filter(
                Benchmark_execution.id == session.query(Benchmark_execution).order_by(
                    Benchmark_execution.id.desc()).first().id).update(
                {Benchmark_execution.benchmarking: True})
            session.query(Benchmark_execution).filter(
                Benchmark_execution.id == session.query(Benchmark_execution).order_by(
                    Benchmark_execution.id.desc()).first().id).update(
                {Benchmark_execution.time_end: datetime.datetime.now()})
            #       execution time for the Benchmarks
            duration = session.query(Benchmark_execution).order_by(
                Benchmark_execution.id.desc()).first().time_end - session.query(Benchmark_execution).order_by(
                Benchmark_execution.id.desc()).first().time_start
            session.query(Benchmark_execution).filter(
                Benchmark_execution.id == session.query(Benchmark_execution).order_by(
                    Benchmark_execution.id.desc()).first().id).update(
                {Benchmark_execution.duration: duration.seconds})
            #       Benchmarking successes
            session.query(Benchmarks).filter(
                Benchmarks.id == session.query(Benchmarks).order_by(Benchmarks.id.desc()).first().id).update(
                {Benchmarks.finished: True})
            session.flush()
            session.commit()
            #       check the range of the voltage
            if getVoltInD('0x' + volt) >= 1.0:
                i += 16
            else:
                i += 1
            print(volt)
            print(i)
            time.sleep(1)
    else:
        print("Die Frequenz liegt unter der minimalen Grenze")


if __name__ == "__main__":
    main()
