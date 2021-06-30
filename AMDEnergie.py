import os
import re
from ctypes import c_uint
from subprocess import check_output
from natsort import natsorted, ns

"""
AMD PPR  = https://www.amd.com/system/files/TechDocs/54945_PPR_Family_17h_Models_00h-0Fh.pdf
AMD OSRR = https://developer.amd.com/wp-content/resources/56255_3_03.PDF
based on: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/hwmon/amd_energy.c
based on: https://github.com/djselbeck/rapl-read-ryzen/blob/master/ryzen.c
based on: https://github.com/ocerman/zenmonitor/blob/master/src/ss/msr.c
"""
FREQUENCY_MSR = 0xC0010293
ENERGY_PWR_UNIT_MSR = 0xC0010299
ENERGY_CORE_MSR = 0xC001029A
ENERGY_PKG_MSR = 0xC001029B
AMD_ENERGY_UNIT_MASK = 0x01F00
AMD_ENERGY_MASK = 0xFFFFFFFF

UINT_MAX = c_uint(-1).value


def get_corelist():
    corelist = []
    siblinglist = []
    cpulist = [cpu for cpu in os.listdir('/sys/devices/system/cpu/') if re.match('cpu(\d+)', cpu)]
    for cpu in natsorted(cpulist, alg=ns.IGNORECASE):
        with open('/sys/devices/system/cpu/' + cpu + '/topology/thread_siblings_list') as fp:
            siblings = fp.readline().rstrip().split(',')
            for i in siblings:
                if i in siblinglist:
                    break
            else:
                siblinglist.append(siblings[0])
                with open('/sys/devices/system/cpu/' + cpu + '/topology/physical_package_id') as fp:
                    package = int(fp.readline())
                    try:
                        corelist[package].append(int(siblings[0]))
                    except IndexError:
                        for i in range(len(corelist), package + 1):
                            corelist.append([])
                        corelist[package] = [int(siblings[0])]

    return corelist


def get_energy_unit():
    out = check_output(["sudo", "rdmsr", "-c", str(ENERGY_PWR_UNIT_MSR)])
    data = int(out, 16)

    energy_unit = (data & AMD_ENERGY_UNIT_MASK) >> 8

    # AMD_TIME_UNIT_MASK = 0xF0000
    # AMD_POWER_UNIT_MASK = 0xF
    # power_unit = (data & AMD_POWER_UNIT_MASK)
    # time_unit = (data & AMD_TIME_UNIT_MASK) >> 16

    return 1 / pow(2, energy_unit)


def read_energy(corelist):
    energydata = []
    coredata = check_output(["sudo", "rdmsr", "-c", str(ENERGY_CORE_MSR), "-a"])
    pkgdata = check_output(["sudo", "rdmsr", "-c", str(ENERGY_PKG_MSR), "-a"])
    for index, data in enumerate(zip(coredata.splitlines(), pkgdata.splitlines())):
        for package, packagecores in enumerate(corelist):
            if index in packagecores:
                try:
                    energydata[package][1].append(int(data[0], 16))
                except IndexError:
                    energydata.append((int(data[1], 16), [int(data[0], 16)]))

    return energydata


def diff_energy(new, old):
    energydata = []
    package_combined = zip(new, old)
    for packageenergy in package_combined:
        coredata = []
        core_combined = zip(packageenergy[0][1], packageenergy[1][1])
        for core in core_combined:
            diff = core[0] - core[1]
            if diff < 0:
                diff = UINT_MAX - core[1] + core[0]
            coredata.append(diff)
        diff = packageenergy[0][0] - packageenergy[1][0]
        if diff < 0:
            diff = UINT_MAX - packageenergy[1][0] + packageenergy[0][0]
        energydata.append((diff, coredata))

    return energydata


def read_frequency(corelist):
    frequencyfactor = 200.0  # / 1000.0
    effective_frequencydata = []
    scaling_frequencydata = []
    corefrequencies = check_output(["sudo", "rdmsr", "-c", str(FREQUENCY_MSR), "-a"])
    for index, data in enumerate(corefrequencies.splitlines()):
        for package, packagecores in enumerate(corelist):
            if index in packagecores:
                with open('/sys/devices/system/cpu/cpu' + str(index) + '/cpufreq/scaling_cur_freq') as fp:
                    scaling_frequency = int(fp.readline()) / 1000

                try:
                    scaling_frequencydata[package].append(scaling_frequency)
                except IndexError:
                    scaling_frequencydata.append([scaling_frequency])

                data = int(data, 16)
                ratio = (data & 0xff) / ((data >> 8) & 0x3F)
                effective_frequency = ratio * frequencyfactor

                try:
                    effective_frequencydata[package].append(effective_frequency)
                except IndexError:
                    effective_frequencydata.append([effective_frequency])

    return scaling_frequencydata, effective_frequencydata


def print_energy(data, energy_unit):
    for package, packagedata in enumerate(data):
        packageenergy = packagedata[0] * energy_unit
        coreenergy = list(map(lambda x: x * energy_unit, packagedata[1]))
        print("Package " + str(package) + " " + str(packageenergy) + "Cores Summe: " + str(sum(coreenergy)))
        print("\t Cores joule: " + str(coreenergy))
def get_energy(last_energydata,energy_unit,energydata):
    data=diff_energy(energydata, last_energydata)
    for package, packagedata in enumerate(data):
        packageenergy = packagedata[0] * energy_unit
        coreenergy = list(map(lambda x: x * energy_unit, packagedata[1]))
        aktiveCore=0
        maxi=max(coreenergy)
        if maxi>=0.1:
          x=maxi*0.7
          for i in coreenergy:
            if i>=x:
              aktiveCore+=1
        return sum(coreenergy),aktiveCore


'''
corelist = get_corelist()
frequencies = read_frequency(corelist)
print(corelist)
print(check_output(["bash", "/tmp/freq.sh"]))
print(frequencies)

energy_unit = get_energy_unit()
print(energy_unit)
last_energydata = read_energy(corelist)
print(last_energydata)
sleep(1)
for i in range(0, 1000):
    energydata = read_energy(corelist)
    scaling_frequencydata, effective_frequencydata = read_frequency(corelist)

    diff = diff_energy(energydata, last_energydata)
    print_energy(diff, energy_unit)

    print("\t scaling   Frequencies: " + str(scaling_frequencydata[0]))
    print("\t effective Frequencies: " + str(effective_frequencydata[0]))
    last_energydata = energydata
    sleep(1)

'''