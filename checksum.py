def compute_checksum(message):
    bits = ''.join(format(ord(x), '08b') for x in message)
    bit_groups = [bits[i:i+8] for i in range(0, len(bits), 8)]
    bit_sum = '0'
    for i in bit_groups:
        bit_sum = ones_comp_addition(bit_sum, i)
    bit_sum = bit_sum[2:]
    checksum = ''
    for i in range(0, 8, 1):
        if bit_sum[i] == '0':
            checksum = checksum + '1'
        else:
            checksum = checksum + '0'
    return checksum

def ones_comp_addition(byte1, byte2):
    comp_sum = bin(int(byte1, 2) + int(byte2, 2))
    concatenation = ''
    if len(comp_sum[2:]) > 8:
        comp_sum = comp_sum[0:2] + comp_sum[3:]
        comp_sum = bin(int(comp_sum, 2) + 1)
    for i in range(0, 8 - len(comp_sum[2:]), 1):
            concatenation += '0'
    comp_sum = comp_sum[0:2] + concatenation + comp_sum[2:]
    return comp_sum

def check_for_error(message, checksum):
    bits = ''.join(format(ord(x), '08b') for x in message)
    bit_groups = [bits[i:i+8] for i in range(0, len(bits), 8)]
    bit_sum = '0'
    for i in bit_groups:
        bit_sum = ones_comp_addition(bit_sum, i)
    bit_sum = ones_comp_addition(bit_sum, checksum)
    bit_sum = bit_sum[2:]
    #print(bit_sum)
    if bit_sum == '11111111':
        return False
    else:
        return True