# This file is part of icspacket.
# Copyright (C) 2025-present  MatrixEditor @ github
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import enum


class LN_Class(enum.Enum):  # IEC61850 7-4
    """Logical Node (LN) classes"""

    ANCR = "Neutral current regulator"  # 5.9.2 LN
    ARCO = "Reactive power control"  # 5.9.3 LN
    ATCC = "Automatic tap changer controller"  # 5.9.4 LN
    AVCO = "Voltage control"  # 5.9.5 LN
    CALH = "Alarm handling"  # 5.6.2 LN
    CCGR = "Cooling group control"  # 5.6.3 LN
    CILO = "Interlocking"  # 5.6.4 LN
    CPOW = "Point-on-wave switching"  # 5.6.5 LN
    CSWI = "Switch controller"  # 5.6.6 LN
    GAPC = "Generic automatic process control"  # 5.7.1 LN
    GGIO = "Generic process I/O"  # 5.7.2 LN
    GSAL = "Generic security application"  # 5.7.3 LN
    IARC = "Archiving"  # 5.8.1 LN
    IHMI = "Human machine interface"  # 5.8.2 LN
    ITCI = "Telecontrol interface"  # 5.8.3 LN
    ITMI = "Telemonitoring interface"  # 5.8.4 LN
    LLN0 = "Logical node zero"  # 5.3.4 LN
    LPHD = "Physical device information"  # 5.3.2 LN
    MDIF = "Differential measurements"  # 5.10.2 LN
    MHAI = "Harmonics or interharmonics"  # 5.10.3 LN
    MHAN = "Non phase related harmonics or interharmonics"  # 5.10.4 LN
    MMTR = "Metering"  # 5.10.5 LN
    MMXN = "Non phase related Measurement"  # 5.10.6 LN
    MMXU = "Measurement"  # 5.10.7 LN
    MSQI = "Sequence and imbalance"  # 5.10.8 LN
    MSTA = "Metering Statistics"  # 5.10.9 LN
    PDIF = "Differential"  # 5.4.2 LN
    PDIR = "Direction comparison"  # 5.4.3 LN
    PDIS = "Distance"  # 5.4.4 LN
    PDOP = "Directional overpower"  # 5.4.5 LN
    PDUP = "Directional underpower"  # 5.4.6 LN
    PFRC = "Rate of change of frequency"  # 5.4.7 LN
    PHAR = "Harmonic restraint"  # 5.4.8 LN
    PHIZ = "Ground detector"  # 5.4.9 LN
    PIOC = "Instantaneous overcurrent"  # 5.4.10 LN
    PMRI = "Motor restart inhibition"  # 5.4.11 LN
    PMSS = "Motor starting time supervision"  # 5.4.12 LN
    POPF = "Over power factor"  # 5.4.13 LN
    PPAM = "Phase angle measuring"  # 5.4.14 LN
    PSCH = "Protection scheme"  # 5.4.15 LN
    PSDE = "Sensitive directional earthfault"  # 5.4.16 LN
    PTEF = "Transient earth fault"  # 5.4.17 LN
    PTOC = "Time overcurrent"  # 5.4.18 LN
    PTOF = "Overfrequency"  # 5.4.19 LN
    PTOV = "Overvoltage"  # 5.4.20 LN
    PTRC = "Protection trip conditioning"  # 5.4.21 LN
    PTTR = "Thermal overload"  # 5.4.22 LN
    PTUC = "Undercurrent"  # 5.4.23 LN
    PTUF = "Underfrequency"  # 5.4.26 LN
    PTUV = "Undervoltage"  # 5.4.24 LN
    PUPF = "Underpower factor"  # 5.4.25 LN
    PVOC = "Voltage controlled time overcurrent"  # 5.4.27 LN
    PVPH = "Volts per Hz"  # 5.4.28 LN
    PZSU = "Zero speed or underspeed"  # 5.4.29 LN
    RADR = "Disturbance recorder channel analogue"  # 5.5.3 LN
    RBDR = "Disturbance recorder channel binary"  # 5.5.4 LN
    RBRF = "Breaker failure"  # 5.5.6 LN
    RDIR = "Directional element"  # 5.5.7 LN
    RDRE = "Disturbance recorder function"  # 5.5.2 LN
    RDRS = "Disturbance record handling"  # 5.5.5 LN
    RFLO = "Fault locator"  # 5.5.8 LN
    RPSB = "Power swing detection/blocking"  # 5.5.9 LN
    RREC = "Autoreclosing"  # 5.5.10 LN
    RSYN = "Synchronism-check or synchronising"  # 5.5.11 LN
    SARC = "Monitoring and diagnostics for arcs"  # 5.11.2 LN
    SIMG = "Insulation medium supervision (gas)"  # 5.11.3 LN

    @staticmethod
    def from_lname(ln_name: str) -> "LN_Class | None":
        ln_name = ln_name.upper()[:min(4, len(ln_name))]
        for ln_class in list(LN_Class):
            if ln_class.name == ln_name:
                return ln_class


class LN_Group(enum.Enum):
    """Logical Node (LN) groups"""

    # prefixed with G_
    A = "Automatic Control"
    C = "Supervisory control"
    G = "Generic Function References"
    I = "Interfacing and Archiving"
    L = "System Logical Nodes"
    M = "Metering and Measurement"
    P = "Protection Functions"
    R = "Protection Related Functions"
    S = "Sensors, Monitoring"
    T = "Instrument Transformer"
    X = "Switchgear"
    Y = "Power Transformer and Related Functions"
    Z = "Further (power system) Equipment"


class DATA_Class(enum.Enum):
    """Common DATA classes"""

    ACD = "Directional protection activation information"  # 7.3.7
    ACT = "Protection activation information"  # 7.3.6
    APC = "Controllable analogue process value"  # 7.5.8
    ASG = "Analogue setting"  # 7.7.2
    BAC = "Binary controlled analog process value"  # 7.5.9
    BCR = "Binary counter reading"  # 7.3.9
    BSC = "Binary controlled step position information"  # 7.5.6
    CMV = "Complex measured value"  # 7.4.3
    CSD = "Curve shape description"  # 7.8.4
    CSG = "Curve shape setting"  # 7.7.4
    CUG = "Currency setting group"  # 7.6.7
    CURVE = "Setting curve"  # 7.7.3
    DEL = "Phase to phase related measured values of a three-phase system"  # 7.4.6
    DPC = "Controllable double point"  # 7.5.3
    DPL = "Device name plate"  # 7.8.2
    DPS = "Double point status"  # 7.3.3
    ENC = "Controllable enumerated status"  # 7.5.5
    ENG = "Enumerated status setting"  # 7.6.4
    ENS = "Enumerated status"  # 7.3.5
    HDEL = "Harmonic value for DEL"  # 7.4.10
    HMV = "Harmonic value"  # 7.4.8
    HST = "Histogram"  # 7.3.10
    HWYE = "Harmonic value for WYE"  # 7.4.9
    INC = "Controllable integer status"  # 7.5.4
    ING = "Integer status setting"  # 7.6.3
    INS = "Integer status"  # 7.3.4
    ISC = "Integer controlled step position information"  # 7.5.7
    LPL = "Logical node name plate"  # 7.8.3
    MV = "Measured value"  # 7.4.2
    ORG = "Object reference setting"  # 7.6.5
    SAV = "Sampled value"  # 7.4.4
    SEC = "Security violation counting"  # 7.3.8
    SEQ = "Sequence"  # 7.4.7
    SPC = "Controllable single point"  # 7.5.2
    SPG = "Single point setting"  # 7.6.2
    SPS = "Single point status"  # 7.3.2
    TSG = "Time setting group"  # 7.6.6
    VSG = "Visible string setting"  # 7.6.8
    VSS = "Visible string status "  # 7.3.11
    WYE = "Phase to ground/neutral related measured values of a three-phase system"  # 7.4.5

    @staticmethod
    def from_name(datname: str, /) -> "DATA_Class | None":
        name = datname.upper()
        for data_class in list(DATA_Class):
            if data_class.name == name[:min(len(data_class.name), len(name))]:
                return data_class


class FC(enum.Enum):  # Functional Constraint
    """Functional Constraints"""

    BL = "Blocking"
    BR = "Buffered report"
    CF = "Configuration"
    CO = "Control"
    DC = "Description"
    EX = "Extended definition (application name space)"
    GO = "Goose control"
    GS = "Gsse control"
    LG = "Logging"
    MS = "Multicast sampled value control"
    MX = "Measurands (analogue values)"
    OR = "Operate received"
    RP = "Unbuffered report"
    SE = "Setting group editable"
    SG = "Setting group"
    SP = "Setting (outside setting group)"
    SR = "Service response"
    ST = "Status information"
    SV = "Substitution"
    US = "Unicast sampled value control"
    XX = "All"
