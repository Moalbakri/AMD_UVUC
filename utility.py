# Libraries
import numpy

# voltage in Hex.
def voltInHex(volt):
    VID = (1.55 - volt) / 0.00625
    temp = hex(int(VID))
    result = temp.split('x')
    # print(result)
    return result[1]

# get list of voltages in Hex.
def voltValus(lastVolt):
    dupl = []
    for i in numpy.arange(lastVolt, 0.2, -0.001):
        VID = round((1.55 - i) / 0.00625, 3)
        temp = hex(int(VID))
        result1 = temp.split('x')
        dupl.append(result1[1])
    result = list(dict.fromkeys(dupl))
    return result

# voltage from Hex. to De.
def getVoltInD(VID):
    x = int(VID, 16)
    return 1.55 - 0.00625 * x

# get the next frequency
def getFreqInfo(obj):
    defaultFreqSteps = 0
    if obj.freq > 3200:
        defaultFreqSteps = 300
    elif obj.freq > 2000:
        defaultFreqSteps = 200
    else:
        defaultFreqSteps = 100
    defaultFreq = obj.freq - defaultFreqSteps
    return defaultFreq

# get frequency in Hex. for p-states with DID=8
#  fid = (12.5 * DID * (freq / 100)) / 25
def get_freq_hex(freq):
    fid = (12.5 * 8 * (freq / 100)) / 25
    freq_hex = hex(int(fid))
    return freq_hex
