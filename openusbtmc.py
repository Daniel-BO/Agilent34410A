#openusbtmc.py
import usbtmc
#instr =  usbtmc.Instrument(2391, 1543, 'Agilent3441A')
instr =  usbtmc.Instrument(2391, 1543)
print(instr.ask("*IDN?"))