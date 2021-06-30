import subprocess
import sys
from time import sleep

from AMDEnergie import get_corelist, get_energy_unit, get_energy, read_energy
from Database import RaplDatum, session, undervolt

# time to wait for the warming up
corelist = get_corelist()
energy_unit = get_energy_unit()
last_energydata = read_energy(corelist)
undervolt_id = session.query(undervolt).order_by(undervolt.id.desc()).first().id
# flag for the Heating-phase
flag = int(sys.argv[1])
sleep(1)
while True:
    curent_temperature = 0
    #   when 1 start to save the temperature
    if flag == 1:
        x = subprocess.run(
            "sensors",
            shell=True, capture_output=True, text=True)
        re = x.stdout.split()
        j = 0
        for j in range(0, len(re)):
            if re[j] == "Tdie:":
                for i in range(1, len(re[j + 1])):
                    if re[j + 1][i] == '°':
                        curent_temperature = re[j + 1][1:i]
                        break
    #   read and get the energy of all cores
    energydata = read_energy(corelist)
    coreenergy, aktiveCore = get_energy(last_energydata, energy_unit, energydata)
    #   save the information of temperature, energy and number of active cores
    temp2 = RaplDatum(undervolt_id=undervolt_id, temperature=curent_temperature, aktive_core=aktiveCore,
                      core_j=coreenergy)
    session.add(temp2)
    session.flush()
    session.commit()
    last_energydata = energydata
    sleep(1)
