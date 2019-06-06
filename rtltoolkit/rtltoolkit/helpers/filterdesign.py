# A Python Class for calculating the capacitor
# values for a Chebyshev Direct Coupled Band Pass
# Filter with a parallel resonator structure and
# a Top C Inverter
#
# All equations are taken from:
# http://iowahills.com/RF%20Filters/The%20Design%20of%20Direct%20Coupled%20Band%20Pass%20Filters.pdf
#
# Chebyshev element values:
# http://www.rfcafe.com/references/electrical/cheby-proto-values.htm
#
# Paralel Resonator
#   -----------
#      |  |
#      3  =
#      3  |
#      |  |
#   -----------
#
#   Top C Inverter
#  -------||------
#    |          |
#    =          =
#    |          |
#  ---------------
#

import numpy as np

class FilterDesign():
    # Butterworth Filter Lowpass Prototype Element Values
    # http://www.rfcafe.com/references/electrical/butter-proto-values.htm

    coefs = np.array([[0],
                      [2.0],
                      [1.41421, 1.41421],
                      [1.0, 2.0, 1.0],
                      [0.76537, 1.84776, 1.84776, 0.76537],
                      [0.61803, 1.61803, 2.0, 1.61803, 0.61803],
                      [0.51764, 1.41421, 1.93185, 1.93185, 1.41421, 0.51764],
                      [0.44504, 1.24698, 1.80194, 2.0, 1.80194, 1.24698, 0.44504],
                      [0.39018, 1.11114, 1.66294, 1.96157, 1.96157, 1.66294, 1.11114, 0.39018],
                      [0.34730, 1.0, 1.53209, 1.87938, 2.0, 1.87938, 1.53209, 1.0, 0.34730]])

    def __init__(self, poles, bw, L, Rs = 50, Rl = 50):
        self.poles = poles # Number of poles(defines the order of the filter)
        self.bw = bw                # Filter bandwidth
        self.L = np.array(L)        # Resonator inductor values
        self.Rs = Rs                # Source impedance
        self.Rl = Rl                # Load impedace

    def calculate_Q(center_freq, bandwidth):
        Q = int(center_freq / bandwidth)
        return Q

    def calculate_resonator(center_freq, L_val, w):
        C = 1 / (w ** 2 * L_val)
        return C

    def calculate_impedance(Q, prot_values, L, w):
        Z = Q * w * np.array(prot_values) * L
        return Z

    def calculate_inverter(Z, w):
        Ic = [1 / (np.sqrt(Z[i]*Z[i + 1]) * w) for i in range(0, len(Z) - 1)]
        return Ic

    def calculate_matching_input(Rs, Z, w):
        Cin = 1 / (Rs * w * np.sqrt(Z[0] / Rs - 1))
        return Cin

    def calculate_matching_output(Rl, Z, w):
        Cout = 1 / (Rl * w * np.sqrt(Z[-1] / Rl - 1))
        return Cout

    def calculate_input_shunt(Rs, Z, w):
        Cin_s = np.sqrt(Z[0] / Rs - 1) / (w * Z[0])
        return Cin_s

    def calculate_output_shunt(Rl, Z, w):
        Cout_s = np.sqrt(Z[-1] / Rl - 1) / (w * Z[-1])
        return Cout_s

    def update_first_resonator(C, Cin_s, Ic):
        C = C - Cin_s - Ic
        return C

    def update_last_resonator(C, Cout_s, Ic):
        C = C - Cout_s - Ic
        return C

    def update_mid_resonators(C, Ic):
        C = [C[i + 1] - Ic[i] - Ic[i + 1] for i in range(len(Ic) - 1)]
        return C

    def calculate(self, center_freq):
        # Angular frequency
        w = 2 * np.pi * center_freq
        # Q factor
        Q = FilterDesign.calculate_Q(center_freq, self.bw)
        # Resonator capacitor values
        C = FilterDesign.calculate_resonator(center_freq, self.L, w)
        # Resonator impedances
        prot_values = FilterDesign.coefs[self.poles]
        Z = FilterDesign.calculate_impedance(Q, prot_values, self.L, w)
        # Inverter capacitor values
        Ic = FilterDesign.calculate_inverter(Z, w)
        # Matching input series capacitor
        Cin = FilterDesign.calculate_matching_input(self.Rs, Z, w)
        # Matching output series capacitor
        Cout = FilterDesign.calculate_matching_output(self.Rl, Z, w)
        # Matching input shunt capacitor
        Cin_s = FilterDesign.calculate_input_shunt(self.Rs, Z, w)
        # Matching output shunt capacitor
        Cout_s = FilterDesign.calculate_output_shunt(self.Rl, Z, w)
        # Recalculate resonator values
        Cf = FilterDesign.update_first_resonator(C[0], Cin_s, Ic[0])
        Cl = FilterDesign.update_last_resonator(C[0], Cout_s, Ic[-1])
        C = FilterDesign.update_mid_resonators(C, Ic)
        C = np.insert(C, 0, Cf)
        C = np.append(C, Cl)

        vals = {}
        vals['C'] = C
        vals['Ic'] = np.array(Ic)
        vals['Cin'] = Cin
        vals['Cout'] = Cout

        return vals
