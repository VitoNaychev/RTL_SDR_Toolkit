import pyModeS as pms

# msg = '0d00a81d01fbb9'
# msg = 'ba42420ee9619b'
# msg = '0500a81d431600'
msg = 'b146420e564601'

print('Downlink Format', pms.df(msg))
print('ICAO', pms.icao(msg))
print('CRC', pms.crc(msg, encode=False))

print(pms.hex2bin(msg))

