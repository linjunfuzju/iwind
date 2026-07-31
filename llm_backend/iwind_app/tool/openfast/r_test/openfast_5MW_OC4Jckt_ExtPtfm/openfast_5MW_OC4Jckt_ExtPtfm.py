
# rainbow_yu openfast.tool.openfast_5MW_OC4Jckt_ExtPtfm 🐋✨

from deepwind_app.tool.base import BaseTool
import requests

_openfast_5MW_OC4Jckt_ExtPtfm_DESCRIPTION = """这个工具是用来：这是OC4 Jacket平台的扩展平台工具，可能用于更复杂的风机平台模拟，包括更大的平台配置或新的模拟环境。并且模拟结果后对结果进行总结。
"""

class openfast_5MW_OC4Jckt_ExtPtfm(BaseTool):
    name: str = "openfast_5MW_OC4Jckt_ExtPtfm"
    description: str = _openfast_5MW_OC4Jckt_ExtPtfm_DESCRIPTION
    parameters: dict = {
    "type": "object",
    "properties": {
        "fst": {
            "type": "object",
            "description": "Parameters extracted from 5MW_OC4Jckt_ExtPtfm.fst",
            "properties": {
                "Echo": {
                    "type": "boolean",
                    "description": "Echo input data to <RootName>.ech (flag)"
                },
                "AbortLevel": {
                    "type": "string",
                    "description": "Error level when simulation should abort (string) {\"WARNING\", \"SEVERE\", \"FATAL\"}",
                    "enum": [
                        "WARNING",
                        "SEVERE",
                        "FATAL"
                    ]
                },
                "TMax": {
                    "type": "number",
                    "description": "Total run time (s)"
                },
                "DT": {
                    "type": "number",
                    "description": "Recommended module time step (s)"
                },
                "InterpOrder": {
                    "type": "number",
                    "description": "Interpolation order for input/output time history (-) {1=linear, 2=quadratic}"
                },
                "NumCrctn": {
                    "type": "number",
                    "description": "Number of correction iterations (-) {0=explicit calculation, i.e., no corrections}"
                },
                "DT_UJac": {
                    "type": "number",
                    "description": "Time between calls to get Jacobians (s)"
                },
                "UJacSclFact": {
                    "type": "number",
                    "description": "Scaling factor used in Jacobians (-)"
                },
                "CompElast": {
                    "type": "number",
                    "description": "Compute structural dynamics (switch) {1=ElastoDyn; 2=ElastoDyn + BeamDyn for blades}"
                },
                "CompInflow": {
                    "type": "number",
                    "description": "Compute inflow wind velocities (switch) {0=still air; 1=InflowWind; 2=external from OpenFOAM}"
                },
                "CompAero": {
                    "type": "number",
                    "description": "Compute aerodynamic loads (switch) {0=None; 1=AeroDyn v14; 2=AeroDyn v15}"
                },
                "CompServo": {
                    "type": "number",
                    "description": "Compute control and electrical-drive dynamics (switch) {0=None; 1=ServoDyn}"
                },
                "CompHydro": {
                    "type": "number",
                    "description": "Compute hydrodynamic loads (switch) {0=None; 1=HydroDyn}"
                },
                "CompSub": {
                    "type": "number",
                    "description": "Compute sub-structural dynamics (switch) {0=None; 1=SubDyn; 2=External Platform MCKF}"
                },
                "CompMooring": {
                    "type": "number",
                    "description": "Compute mooring system (switch) {0=None; 1=MAP++; 2=FEAMooring; 3=MoorDyn; 4=OrcaFlex}"
                },
                "CompIce": {
                    "type": "number",
                    "description": "Compute ice loads (switch) {0=None; 1=IceFloe; 2=IceDyn}"
                },
                "MHK": {
                    "type": "number",
                    "description": "MHK turbine type (switch) {0=Not an MHK turbine; 1=Fixed MHK turbine; 2=Floating MHK turbine}"
                },
                "Gravity": {
                    "type": "number",
                    "description": "Gravitational acceleration (m/s^2)"
                },
                "AirDens": {
                    "type": "number",
                    "description": "Air density (kg/m^3)"
                },
                "WtrDens": {
                    "type": "number",
                    "description": "Water density (kg/m^3)"
                },
                "KinVisc": {
                    "type": "number",
                    "description": "Kinematic viscosity of working fluid (m^2/s)"
                },
                "SpdSound": {
                    "type": "number",
                    "description": "Speed of sound in working fluid (m/s)"
                },
                "Patm": {
                    "type": "number",
                    "description": "Atmospheric pressure (Pa) [used only for an MHK turbine cavitation check]"
                },
                "Pvap": {
                    "type": "number",
                    "description": "Vapour pressure of working fluid (Pa) [used only for an MHK turbine cavitation check]"
                },
                "WtrDpth": {
                    "type": "number",
                    "description": "Water depth (m)"
                },
                "MSL2SWL": {
                    "type": "number",
                    "description": "Offset between still-water level and mean sea level (m) [positive upward]"
                },
                "EDFile": {
                    "type": "string",
                    "description": "Name of file containing ElastoDyn input parameters (quoted string)"
                },
                "BDBldFile(1)": {
                    "type": "string",
                    "description": "Name of file containing BeamDyn input parameters for blade 1 (quoted string)"
                },
                "BDBldFile(2)": {
                    "type": "string",
                    "description": "Name of file containing BeamDyn input parameters for blade 2 (quoted string)"
                },
                "BDBldFile(3)": {
                    "type": "string",
                    "description": "Name of file containing BeamDyn input parameters for blade 3 (quoted string)"
                },
                "InflowFile": {
                    "type": "string",
                    "description": "Name of file containing inflow wind input parameters (quoted string)"
                },
                "AeroFile": {
                    "type": "string",
                    "description": "Name of file containing aerodynamic input parameters (quoted string)"
                },
                "ServoFile": {
                    "type": "string",
                    "description": "Name of file containing control and electrical-drive input parameters (quoted string)"
                },
                "HydroFile": {
                    "type": "string",
                    "description": "Name of file containing hydrodynamic input parameters (quoted string)"
                },
                "SubFile": {
                    "type": "string",
                    "description": "Name of file containing sub-structural input parameters (quoted string)"
                },
                "MooringFile": {
                    "type": "string",
                    "description": "Name of file containing mooring system input parameters (quoted string)"
                },
                "IceFile": {
                    "type": "string",
                    "description": "Name of file containing ice input parameters (quoted string)"
                },
                "SumPrint": {
                    "type": "boolean",
                    "description": "Print summary data to \"<RootName>.sum\" (flag)"
                },
                "SttsTime": {
                    "type": "number",
                    "description": "Amount of time between screen status messages (s)"
                },
                "ChkptTime": {
                    "type": "number",
                    "description": "Amount of time between creating checkpoint files for potential restart (s)"
                },
                "DT_Out": {
                    "type": "number",
                    "description": "Time step for tabular output (s) (or \"default\")"
                },
                "TStart": {
                    "type": "number",
                    "description": "Time to begin tabular output (s)"
                },
                "OutFileFmt": {
                    "type": "number",
                    "description": "Format for tabular (time-marching) output file (switch) {0: uncompressed binary [<RootName>.outb], 1: text file [<RootName>.out], 2: binary file [<RootName>.outb], 3: both 1 and 2}"
                },
                "TabDelim": {
                    "type": "string",
                    "description": "Use tab delimiters in text tabular output file? (flag) {uses spaces if false}",
                    "enum": [
                        "uses spaces if false"
                    ]
                },
                "OutFmt": {
                    "type": "string",
                    "description": "Format used for text tabular output, excluding the time channel.  Resulting field should be 10 characters. (quoted string)"
                },
                "Linearize": {
                    "type": "boolean",
                    "description": "Linearization analysis (flag)"
                },
                "CalcSteady": {
                    "type": "boolean",
                    "description": "Calculate a steady-state periodic operating point before linearization? [unused if Linearize=False] (flag)"
                },
                "TrimCase": {
                    "type": "number",
                    "description": "Controller parameter to be trimmed {1:yaw; 2:torque; 3:pitch} [used only if CalcSteady=True] (-)"
                },
                "TrimTol": {
                    "type": "number",
                    "description": "Tolerance for the rotational speed convergence [used only if CalcSteady=True] (-)"
                },
                "TrimGain": {
                    "type": "number",
                    "description": "Proportional gain for the rotational speed error (>0) [used only if CalcSteady=True] (rad/(rad/s) for yaw or pitch; Nm/(rad/s) for torque)"
                },
                "Twr_Kdmp": {
                    "type": "number",
                    "description": "Damping factor for the tower [used only if CalcSteady=True] (N/(m/s))"
                },
                "Bld_Kdmp": {
                    "type": "number",
                    "description": "Damping factor for the blades [used only if CalcSteady=True] (N/(m/s))"
                },
                "NLinTimes": {
                    "type": "number",
                    "description": "Number of times to linearize (-) [>=1] [unused if Linearize=False]"
                },
                "LinInputs": {
                    "type": "number",
                    "description": "Inputs included in linearization (switch) {0=none; 1=standard; 2=all module inputs (debug)} [unused if Linearize=False]"
                },
                "LinOutputs": {
                    "type": "number",
                    "description": "Outputs included in linearization (switch) {0=none; 1=from OutList(s); 2=all module outputs (debug)} [unused if Linearize=False]"
                },
                "LinOutJac": {
                    "type": "boolean",
                    "description": "Include full Jacobians in linearization output (for debug) (flag) [unused if Linearize=False; used only if LinInputs=LinOutputs=2]"
                },
                "LinOutMod": {
                    "type": "boolean",
                    "description": "Write module-level linearization output files in addition to output for full system? (flag) [unused if Linearize=False]"
                },
                "WrVTK": {
                    "type": "number",
                    "description": "VTK visualization data output: (switch) {0=none; 1=initialization dataonly; 2=animation; 3=mode shapes}"
                },
                "VTK_type": {
                    "type": "number",
                    "description": "Type of VTK visualization data: (switch) {1=surfaces; 2=basic meshes (lines/points); 3=all meshes (debug)} [unused if WrVTK=0]"
                },
                "VTK_fields": {
                    "type": "string",
                    "description": "Write mesh fields to VTK data files? (flag) {true/false} [unused if WrVTK=0]",
                    "enum": [
                        "true",
                        "false"
                    ]
                },
                "VTK_fps": {
                    "type": "number",
                    "description": "Frame rate for VTK output (frames per second){will use closest integer multiple of DT} [used only if WrVTK=2 or WrVTK=3]"
                }
            }
        },
        "se": {
            "type": "object",
            "description": "Parameters extracted from ExtPtfm.dat",
            "properties": {
                "Comment_describing_the_model": {
                    "type": "array",
                    "description": "Table data columns: Comment, describing, the, model",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "Echo": {
                    "type": "boolean",
                    "description": "Echo input data to <RootName>.ech (flag)"
                },
                "DT": {
                    "type": "string",
                    "description": "Communication interval for controllers (s) (or \"default\")"
                },
                "IntMethod": {
                    "type": "number",
                    "description": "Integration Method {1:RK4; 2:AB4, 3:ABM4} (switch)"
                },
                "FileFormat": {
                    "type": "number",
                    "description": "File Format {0:Guyan; 1:FlexASCII} (switch)"
                },
                "Red_FileName": {
                    "type": "string",
                    "description": "Path of the file containing Guyan/Craig-Bampton inputs (-)"
                },
                "RedCst_FileName": {
                    "type": "string",
                    "description": "Path of the file containing Guyan/Craig-Bampton constant inputs (-) (currently unused)"
                },
                "ActiveDOFList": {
                    "type": "array",
                    "description": "List of CB modes index that are active, [unused if NActiveDOFList<=0]"
                },
                "NInitPosList": {
                    "type": "number",
                    "description": "Number of initial positions listed in InitPosList, using 0 implies all DOF initialized to 0  (integer)"
                },
                "InitPosList": {
                    "type": "array",
                    "description": "List of initial positions for the CB modes  [unused if NInitPosList<=0 or EquilStart=True]"
                },
                "NInitVelList": {
                    "type": "number",
                    "description": "Number of initial positions listed in InitVelList, using 0 implies all DOF initialized to 0  (integer)"
                },
                "InitVelList": {
                    "type": "array",
                    "description": "List of initial velocities for the CB modes  [unused if NInitVelPosList<=0 or EquilStart=True]"
                },
                "SumPrint": {
                    "type": "boolean",
                    "description": "Print summary data to <RootName>.sum (flag)"
                },
                "OutFile": {
                    "type": "number",
                    "description": "Switch to determine where output will be placed: {1: in module output file only; 2: in glue code output file only; 3: both} (currently unused)"
                },
                "TabDelim": {
                    "type": "boolean",
                    "description": "Use tab delimiters in text tabular output file? (flag) (currently unused)"
                },
                "OutFmt": {
                    "type": "string",
                    "description": "Format used for text tabular output (except time).  Resulting field should be 10 characters. (quoted string) (currently unused)"
                },
                "TStart": {
                    "type": "number",
                    "description": "Time to begin tabular output (s) (currently unused)"
                },
                "\"IntrfFx\"_-_Platform_interface_force_-_Directed_along_the_x-direction_(N)": {
                    "type": "array",
                    "description": "Table data columns: \"IntrfFx\", -, Platform, interface, force, -, Directed, along, the, x-direction, (N)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"IntrfFx\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Platform": {
                                "type": "number"
                            },
                            "interface": {
                                "type": "number"
                            },
                            "force": {
                                "type": "number"
                            },
                            "Directed": {
                                "type": "number"
                            },
                            "along": {
                                "type": "number"
                            },
                            "the": {
                                "type": "number"
                            },
                            "x-direction": {
                                "type": "number"
                            },
                            "(N)": {
                                "type": "number"
                            }
                        }
                    }
                },
                "\"InpF_Fx\"_-_Reduced_Input_force_at_interface_point_-_Directed_along_the_x-direction_(N)": {
                    "type": "array",
                    "description": "Table data columns: \"InpF_Fx\", -, Reduced, Input, force, at, interface, point, -, Directed, along, the, x-direction, (N)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"InpF_Fx\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Reduced": {
                                "type": "number"
                            },
                            "Input": {
                                "type": "number"
                            },
                            "force": {
                                "type": "number"
                            },
                            "at": {
                                "type": "number"
                            },
                            "interface": {
                                "type": "number"
                            },
                            "point": {
                                "type": "number"
                            },
                            "Directed": {
                                "type": "number"
                            },
                            "along": {
                                "type": "number"
                            },
                            "the": {
                                "type": "number"
                            },
                            "x-direction": {
                                "type": "number"
                            },
                            "(N)": {
                                "type": "number"
                            }
                        }
                    }
                },
                "\"CBQ_001\"_-_Modal_displacement_of_internal_Craig-Bampton_mode_number_XXX_(-)": {
                    "type": "array",
                    "description": "Table data columns: \"CBQ_001\", -, Modal, displacement, of, internal, Craig-Bampton, mode, number, XXX, (-)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"CBQ_001\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Modal": {
                                "type": "number"
                            },
                            "displacement": {
                                "type": "number"
                            },
                            "of": {
                                "type": "number"
                            },
                            "internal": {
                                "type": "number"
                            },
                            "Craig-Bampton": {
                                "type": "number"
                            },
                            "mode": {
                                "type": "number"
                            },
                            "number": {
                                "type": "number"
                            },
                            "XXX": {
                                "type": "number"
                            },
                            "(-)": {
                                "type": "number"
                            }
                        }
                    }
                }
            }
        },
        "elastodyn": {
            "type": "object",
            "description": "Parameters extracted from ExtPtfm_SE.dat",
            "properties": {
                "5.07244708e-11": {
                    "type": "number",
                    "description": "4.23103689e-11  5.67542783e-10 -5.28236955e+06  2.84384853e-10  3.60609453e+02 -4.21795932e-12  5.68434189e-14 -3.49587026e-12 -1.11910481e-13 -6.94910796e-12  1.71286635e+02 -2.67720068e-10 -5.19584376e-13  2.93098879e-13  6.61626264e+01 -1.92928340e-10 -1.12265752e-12 -1.76164254e+02  3.88521215e-10 -9.52127266e-13  7.49622586e-13  1.58440372e-10 -9.54272988e+01  2.84217094e-13  8.52651283e-14  5.09814413e-13 -4.95956670e+01 -1.36008182e-09 -3.62643943e-13"
                },
                "9.62255787e+05": {
                    "type": "number",
                    "description": "3.00720954e-10  5.28204269e+06  2.42627584e-11  1.74721822e-09  6.66533495e-12  3.60594532e+02 -4.54924987e-12 -2.33058017e-12  2.45847787e-12  1.11199938e-12  2.66871858e-10  1.71280791e+02 -1.98419059e-12 -6.85673740e-13  1.92540650e-10  6.61575677e+01  3.02868841e-12  3.88151733e-10  1.76097008e+02  1.63424829e-12 -4.26325641e-14  9.55355779e+01  1.57776014e-10  2.84217094e-13  2.20268248e-13  4.19220214e-13  1.36034473e-09 -4.95618190e+01  2.58222263e-13"
                },
                "5.28204269e+06": {
                    "type": "number",
                    "description": "5.52211488e-09  6.71710431e+07  5.19372141e-09  6.36789574e-09  3.24149596e-11  6.82513608e+03 -1.16585852e-10 -5.76392267e-11 -4.14956958e-12  3.13775672e-11  4.05203338e-09  2.57258734e+03 -4.54747351e-12  1.40971679e-11  3.27209904e-09  1.11887783e+03  2.27942110e-11  4.00615363e-09  1.80141709e+03 -8.52651283e-13  2.27373675e-12  1.02076670e+03  1.69688974e-09 -1.45519152e-11 -8.41282599e-12 -1.75077730e-11  2.16663807e-08 -7.90339629e+02  4.68378114e-11"
                },
                "1.73266631e-09": {
                    "type": "number",
                    "description": "2.40072354e-10  6.83355703e-09 -2.81868825e-09  1.02967449e+07 -2.61479727e-12 -2.33200126e-11  5.63008746e-01 -2.55342290e+03 -1.35041311e-10 -1.06531672e-10 -4.72510919e-11  1.47011292e-11 -3.20996563e-11  2.84217094e-14 -3.25428573e-12 -1.70530257e-13 -2.06057393e-13  7.10542736e-14 -1.98951966e-13  3.49587026e-12 -1.98408716e-01  2.10320650e-12  1.56319402e-12  2.13731255e-11 -1.14981199e+03  1.53477231e-12 -3.16902060e-12  1.29318778e-12  3.02257525e-12"
                },
                "3.60609453e+02_6.66533495e-12_1.77635684e-15_3.24149596e-11_-6.82540351e+03_-2.61479727e-12_1.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00": {
                    "type": "array",
                    "description": "Table data columns: 3.60609453e+02, 6.66533495e-12, 1.77635684e-15, 3.24149596e-11, -6.82540351e+03, -2.61479727e-12, 1.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00",
                    "items": {
                        "type": "object",
                        "properties": {
                            "3.60609453e+02": {
                                "type": "number"
                            },
                            "6.66533495e-12": {
                                "type": "number"
                            },
                            "1.77635684e-15": {
                                "type": "number"
                            },
                            "3.24149596e-11": {
                                "type": "number"
                            },
                            "-6.82540351e+03": {
                                "type": "number"
                            },
                            "-2.61479727e-12": {
                                "type": "number"
                            },
                            "1.00000000e+00": {
                                "type": "number"
                            },
                            "0.00000000e+00": {
                                "type": "number"
                            }
                        }
                    }
                },
                "1.70093408e+00": {
                    "type": "number",
                    "description": "2.98665579e-01 -1.27235487e-01 -2.32742574e+09 -8.89638805e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00"
                },
                "8.43407974e+07": {
                    "type": "number",
                    "description": "3.47132372e-01  2.32742570e+09  2.35131553e+00  2.22409205e+01  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00  0.00000000e+00"
                },
                "0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_8.27071909e+02_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00": {
                    "type": "array",
                    "description": "Table data columns: 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 8.27071909e+02, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00",
                    "items": {
                        "type": "object",
                        "properties": {
                            "0.00000000e+00": {
                                "type": "number"
                            },
                            "8.27071909e+02": {
                                "type": "number"
                            }
                        }
                    }
                },
                "1.03756979e-03": {
                    "type": "number",
                    "description": "1.82186007e-04 -7.76135866e-05 -1.98341136e+06 -5.42679668e-03  3.84806348e+01 -4.50098439e-13  6.06576123e-15 -3.73044315e-13 -1.19419674e-14 -7.41539310e-13  1.82779968e+01 -2.85684085e-11 -5.54448487e-14  3.12765813e-14  7.06021387e+00 -2.05873832e-11 -1.19798784e-13 -1.87984875e+01  4.14590989e-11 -1.01601501e-13  7.99922262e-14  1.69071721e-11 -1.01830471e+01  3.03288061e-14  9.09864184e-15  5.44022960e-14 -5.29235362e+00 -1.45134332e-10 -3.86977351e-14"
                },
                "1.54130201e+05": {
                    "type": "number",
                    "description": "2.11750779e-04  1.98337646e+06  1.43430248e-03  1.35669617e-02  7.11257893e-13  3.84790425e+01 -4.85450453e-13 -2.48696210e-13  2.62344173e-13  1.18661454e-13  2.84778960e-11  1.82773732e+01 -2.11732978e-13 -7.31682448e-14  2.05460128e-11  7.05967405e+00  3.23191340e-13  4.14196714e-11  1.87913117e+01  1.74390635e-13 -4.54932092e-15  1.01946015e+01  1.68362785e-11  3.03288061e-14  2.35048248e-14  4.47349890e-14  1.45162386e-10 -5.28874170e+00  2.75548977e-14"
                },
                "3.84806348e+01_7.11257893e-13_1.89555038e-16_3.45900034e-12_-7.28338809e+02_-2.79025016e-13_6.11223865e-01_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00_0.00000000e+00": {
                    "type": "array",
                    "description": "Table data columns: 3.84806348e+01, 7.11257893e-13, 1.89555038e-16, 3.45900034e-12, -7.28338809e+02, -2.79025016e-13, 6.11223865e-01, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00",
                    "items": {
                        "type": "object",
                        "properties": {
                            "3.84806348e+01": {
                                "type": "number"
                            },
                            "7.11257893e-13": {
                                "type": "number"
                            },
                            "1.89555038e-16": {
                                "type": "number"
                            },
                            "3.45900034e-12": {
                                "type": "number"
                            },
                            "-7.28338809e+02": {
                                "type": "number"
                            },
                            "-2.79025016e-13": {
                                "type": "number"
                            },
                            "6.11223865e-01": {
                                "type": "number"
                            },
                            "0.00000000e+00": {
                                "type": "number"
                            }
                        }
                    }
                },
                "0.0000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000_0.00000000E+000": {
                    "type": "array",
                    "description": "Table data columns: 0.0000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000, 0.00000000E+000",
                    "items": {
                        "type": "object",
                        "properties": {
                            "0.0000": {
                                "type": "number"
                            },
                            "0.00000000E+000": {
                                "type": "number"
                            }
                        }
                    }
                }
            }
        },
        "tower": {
            "type": "object",
            "description": "Parameters extracted from NRELOffshrBsline5MW_OC4Jacket_ElastoDyn.dat",
            "properties": {
                "Echo": {
                    "type": "boolean",
                    "description": "Echo input data to \"<RootName>.ech\" (flag)"
                },
                "Method": {
                    "type": "number",
                    "description": "Integration method: {1: RK4, 2: AB4, or 3: ABM4} (-)"
                },
                "DT": {
                    "type": "string",
                    "description": "Integration time step (s)"
                },
                "FlapDOF1": {
                    "type": "boolean",
                    "description": "First flapwise blade mode DOF (flag)"
                },
                "FlapDOF2": {
                    "type": "boolean",
                    "description": "Second flapwise blade mode DOF (flag)"
                },
                "EdgeDOF": {
                    "type": "boolean",
                    "description": "First edgewise blade mode DOF (flag)"
                },
                "TeetDOF": {
                    "type": "boolean",
                    "description": "Rotor-teeter DOF (flag) [unused for 3 blades]"
                },
                "DrTrDOF": {
                    "type": "boolean",
                    "description": "Drivetrain rotational-flexibility DOF (flag)"
                },
                "GenDOF": {
                    "type": "boolean",
                    "description": "Generator DOF (flag)"
                },
                "YawDOF": {
                    "type": "boolean",
                    "description": "Yaw DOF (flag)"
                },
                "TwFADOF1": {
                    "type": "boolean",
                    "description": "First fore-aft tower bending-mode DOF (flag)"
                },
                "TwFADOF2": {
                    "type": "boolean",
                    "description": "Second fore-aft tower bending-mode DOF (flag)"
                },
                "TwSSDOF1": {
                    "type": "boolean",
                    "description": "First side-to-side tower bending-mode DOF (flag)"
                },
                "TwSSDOF2": {
                    "type": "boolean",
                    "description": "Second side-to-side tower bending-mode DOF (flag)"
                },
                "PtfmSgDOF": {
                    "type": "boolean",
                    "description": "Platform horizontal surge translation DOF (flag)"
                },
                "PtfmSwDOF": {
                    "type": "boolean",
                    "description": "Platform horizontal sway translation DOF (flag)"
                },
                "PtfmHvDOF": {
                    "type": "boolean",
                    "description": "Platform vertical heave translation DOF (flag)"
                },
                "PtfmRDOF": {
                    "type": "boolean",
                    "description": "Platform roll tilt rotation DOF (flag)"
                },
                "PtfmPDOF": {
                    "type": "boolean",
                    "description": "Platform pitch tilt rotation DOF (flag)"
                },
                "PtfmYDOF": {
                    "type": "boolean",
                    "description": "Platform yaw rotation DOF (flag)"
                },
                "OoPDefl": {
                    "type": "number",
                    "description": "Initial out-of-plane blade-tip displacement (meters)"
                },
                "IPDefl": {
                    "type": "number",
                    "description": "Initial in-plane blade-tip deflection (meters)"
                },
                "BlPitch(1)": {
                    "type": "number",
                    "description": "Blade 1 initial pitch (degrees)"
                },
                "BlPitch(2)": {
                    "type": "number",
                    "description": "Blade 2 initial pitch (degrees)"
                },
                "BlPitch(3)": {
                    "type": "number",
                    "description": "Blade 3 initial pitch (degrees) [unused for 2 blades]"
                },
                "TeetDefl": {
                    "type": "number",
                    "description": "Initial or fixed teeter angle (degrees) [unused for 3 blades]"
                },
                "Azimuth": {
                    "type": "number",
                    "description": "Initial azimuth angle for blade 1 (degrees)"
                },
                "RotSpeed": {
                    "type": "number",
                    "description": "Initial or fixed rotor speed (rpm)"
                },
                "NacYaw": {
                    "type": "number",
                    "description": "Initial or fixed nacelle-yaw angle (degrees)"
                },
                "TTDspFA": {
                    "type": "number",
                    "description": "Initial fore-aft tower-top displacement (meters)"
                },
                "TTDspSS": {
                    "type": "number",
                    "description": "Initial side-to-side tower-top displacement (meters)"
                },
                "PtfmSurge": {
                    "type": "number",
                    "description": "Initial or fixed horizontal surge translational displacement of platform (meters)"
                },
                "PtfmSway": {
                    "type": "number",
                    "description": "Initial or fixed horizontal sway translational displacement of platform (meters)"
                },
                "PtfmHeave": {
                    "type": "number",
                    "description": "Initial or fixed vertical heave translational displacement of platform (meters)"
                },
                "PtfmRoll": {
                    "type": "number",
                    "description": "Initial or fixed roll tilt rotational displacement of platform (degrees)"
                },
                "PtfmPitch": {
                    "type": "number",
                    "description": "Initial or fixed pitch tilt rotational displacement of platform (degrees)"
                },
                "PtfmYaw": {
                    "type": "number",
                    "description": "Initial or fixed yaw rotational displacement of platform (degrees)"
                },
                "NumBl": {
                    "type": "number",
                    "description": "Number of blades (-)"
                },
                "TipRad": {
                    "type": "number",
                    "description": "The distance from the rotor apex to the blade tip (meters)"
                },
                "HubRad": {
                    "type": "number",
                    "description": "The distance from the rotor apex to the blade root (meters)"
                },
                "HubCM": {
                    "type": "number",
                    "description": "Distance from rotor apex to hub mass [positive downwind] (meters)"
                },
                "UndSling": {
                    "type": "number",
                    "description": "Undersling length [distance from teeter pin to the rotor apex] (meters) [unused for 3 blades]"
                },
                "Delta3": {
                    "type": "number",
                    "description": "Delta-3 angle for teetering rotors (degrees) [unused for 3 blades]"
                },
                "AzimB1Up": {
                    "type": "number",
                    "description": "Azimuth value to use for I/O when blade 1 points up (degrees)"
                },
                "ShftGagL": {
                    "type": "number",
                    "description": "Distance from rotor apex [3 blades] or teeter pin [2 blades] to shaft strain gages [positive for upwind rotors] (meters)"
                },
                "NacCMxn": {
                    "type": "number",
                    "description": "Downwind distance from the tower-top to the nacelle CM (meters)"
                },
                "NacCMyn": {
                    "type": "number",
                    "description": "Lateral  distance from the tower-top to the nacelle CM (meters)"
                },
                "NacCMzn": {
                    "type": "number",
                    "description": "Vertical distance from the tower-top to the nacelle CM (meters)"
                },
                "NcIMUyn": {
                    "type": "number",
                    "description": "Lateral  distance from the tower-top to the nacelle IMU (meters)"
                },
                "NcIMUzn": {
                    "type": "number",
                    "description": "Vertical distance from the tower-top to the nacelle IMU (meters)"
                },
                "Twr2Shft": {
                    "type": "number",
                    "description": "Vertical distance from the tower-top to the rotor shaft (meters)"
                },
                "TowerHt": {
                    "type": "number",
                    "description": "Height of tower relative to ground level [onshore], MSL [offshore wind or floating MHK], or seabed [fixed MHK] (meters)"
                },
                "TowerBsHt": {
                    "type": "number",
                    "description": "Height of tower base relative to ground level [onshore], MSL [offshore wind or floating MHK], or seabed [fixed MHK] (meters)"
                },
                "PtfmCMxt": {
                    "type": "number",
                    "description": "Downwind distance from the ground level [onshore], MSL [offshore wind or floating MHK], or seabed [fixed MHK] to the platform CM (meters)"
                },
                "PtfmCMyt": {
                    "type": "number",
                    "description": "Lateral distance from the ground level [onshore], MSL [offshore wind or floating MHK], or seabed [fixed MHK] to the platform CM (meters)"
                },
                "PtfmCMzt": {
                    "type": "number",
                    "description": "Vertical distance from the ground level [onshore], MSL [offshore wind or floating MHK], or seabed [fixed MHK] to the platform CM (meters)"
                },
                "PtfmRefzt": {
                    "type": "number",
                    "description": "Vertical distance from the ground level [onshore], MSL [offshore wind or floating MHK], or seabed [fixed MHK] to the platform reference point (meters)"
                },
                "TipMass(1)": {
                    "type": "number",
                    "description": "Tip-brake mass, blade 1 (kg)"
                },
                "TipMass(2)": {
                    "type": "number",
                    "description": "Tip-brake mass, blade 2 (kg)"
                },
                "TipMass(3)": {
                    "type": "number",
                    "description": "Tip-brake mass, blade 3 (kg) [unused for 2 blades]"
                },
                "HubMass": {
                    "type": "number",
                    "description": "Hub mass (kg)"
                },
                "HubIner": {
                    "type": "number",
                    "description": "Hub inertia about rotor axis [3 blades] or teeter axis [2 blades] (kg m^2)"
                },
                "GenIner": {
                    "type": "number",
                    "description": "Generator inertia about HSS (kg m^2)"
                },
                "NacMass": {
                    "type": "number",
                    "description": "Nacelle mass (kg)"
                },
                "NacYIner": {
                    "type": "number",
                    "description": "Nacelle inertia about yaw axis (kg m^2)"
                },
                "YawBrMass": {
                    "type": "number",
                    "description": "Yaw bearing mass (kg)"
                },
                "PtfmMass": {
                    "type": "number",
                    "description": "Platform mass (kg)"
                },
                "PtfmRIner": {
                    "type": "number",
                    "description": "Platform inertia for roll tilt rotation about the platform CM (kg m^2)"
                },
                "PtfmPIner": {
                    "type": "number",
                    "description": "Platform inertia for pitch tilt rotation about the platform CM (kg m^2)"
                },
                "PtfmYIner": {
                    "type": "number",
                    "description": "Platform inertia for yaw rotation about the platform CM (kg m^2)"
                },
                "BldNodes": {
                    "type": "number",
                    "description": "Number of blade nodes (per blade) used for analysis (-)"
                },
                "BldFile(1)": {
                    "type": "string",
                    "description": "Name of file containing properties for blade 1 (quoted string)"
                },
                "BldFile(2)": {
                    "type": "string",
                    "description": "Name of file containing properties for blade 2 (quoted string)"
                },
                "BldFile(3)": {
                    "type": "string",
                    "description": "Name of file containing properties for blade 3 (quoted string) [unused for 2 blades]"
                },
                "TeetMod": {
                    "type": "number",
                    "description": "Rotor-teeter spring/damper model {0: none, 1: standard, 2: user-defined from routine UserTeet} (switch) [unused for 3 blades]"
                },
                "TeetDmpP": {
                    "type": "number",
                    "description": "Rotor-teeter damper position (degrees) [used only for 2 blades and when TeetMod=1]"
                },
                "TeetDmp": {
                    "type": "number",
                    "description": "Rotor-teeter damping constant (N-m/(rad/s)) [used only for 2 blades and when TeetMod=1]"
                },
                "TeetCDmp": {
                    "type": "number",
                    "description": "Rotor-teeter rate-independent Coulomb-damping moment (N-m) [used only for 2 blades and when TeetMod=1]"
                },
                "TeetSStP": {
                    "type": "number",
                    "description": "Rotor-teeter soft-stop position (degrees) [used only for 2 blades and when TeetMod=1]"
                },
                "TeetHStP": {
                    "type": "number",
                    "description": "Rotor-teeter hard-stop position (degrees) [used only for 2 blades and when TeetMod=1]"
                },
                "TeetSSSp": {
                    "type": "number",
                    "description": "Rotor-teeter soft-stop linear-spring constant (N-m/rad) [used only for 2 blades and when TeetMod=1]"
                },
                "TeetHSSp": {
                    "type": "number",
                    "description": "Rotor-teeter hard-stop linear-spring constant (N-m/rad) [used only for 2 blades and when TeetMod=1]"
                },
                "GBoxEff": {
                    "type": "number",
                    "description": "Gearbox efficiency (%)"
                },
                "GBRatio": {
                    "type": "number",
                    "description": "Gearbox ratio (-)"
                },
                "DTTorSpr": {
                    "type": "number",
                    "description": "Drivetrain torsional spring (N-m/rad)"
                },
                "DTTorDmp": {
                    "type": "number",
                    "description": "Drivetrain torsional damper (N-m/(rad/s))"
                },
                "Furling": {
                    "type": "boolean",
                    "description": "Read in additional model properties for furling turbine (flag) [must currently be FALSE)"
                },
                "FurlFile": {
                    "type": "string",
                    "description": "Name of file containing furling properties (quoted string) [unused when Furling=False]"
                },
                "TwrNodes": {
                    "type": "number",
                    "description": "Number of tower nodes used for analysis (-)"
                },
                "TwrFile": {
                    "type": "string",
                    "description": "Name of file containing tower properties (quoted string)"
                },
                "SumPrint": {
                    "type": "boolean",
                    "description": "Print summary data to \"<RootName>.sum\" (flag)"
                },
                "OutFile": {
                    "type": "number",
                    "description": "Switch to determine where output will be placed: {1: in module output file only; 2: in glue code output file only; 3: both} (currently unused)"
                },
                "TabDelim": {
                    "type": "boolean",
                    "description": "Use tab delimiters in text tabular output file? (flag) (currently unused)"
                },
                "OutFmt": {
                    "type": "string",
                    "description": "Format used for text tabular output (except time).  Resulting field should be 10 characters. (quoted string) (currently unused)"
                },
                "TStart": {
                    "type": "number",
                    "description": "Time to begin tabular output (s) (currently unused)"
                },
                "DecFact": {
                    "type": "number",
                    "description": "Decimation factor for tabular output {1: output every time step} (-) (currently unused)"
                },
                "NTwGages": {
                    "type": "number",
                    "description": "Number of tower nodes that have strain gages for output [0 to 9] (-)"
                },
                "TwrGagNd": {
                    "type": "number",
                    "description": "List of tower nodes that have strain gages [1 to TwrNodes] (-) [unused if NTwGages=0]"
                },
                "NBlGages": {
                    "type": "number",
                    "description": "Number of blade nodes that have strain gages for output [0 to 9] (-)"
                },
                "\"BldPitch1\"_-_Blade_1_pitch_angle": {
                    "type": "array",
                    "description": "Table data columns: \"BldPitch1\", -, Blade, 1, pitch, angle",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "Spn2MLyb1\"": {
                    "type": "array",
                    "description": "Blade 1 local edgewise and flapwise bending moments at span station 2 (approx. 50% span)"
                },
                "\"RootFxc1_,_RootFyc1_,_RootFzc1\"_-_Out-of-plane_shear,_in-plane_shear,_and_axial_forces_at_the_root_of_blade_1": {
                    "type": "array",
                    "description": "Table data columns: \"RootFxc1, ,, RootFyc1, ,, RootFzc1\", -, Out-of-plane, shear,, in-plane, shear,, and, axial, forces, at, the, root, of, blade, 1",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "\"YawBrFxp_,_YawBrFyp_,_YawBrFzp\"_-_Fore-aft_shear,_side-to-side_shear,_and_vertical_forces_at_the_top_of_the_tower_(not_rotating_with_nacelle_yaw)": {
                    "type": "array",
                    "description": "Table data columns: \"YawBrFxp, ,, YawBrFyp, ,, YawBrFzp\", -, Fore-aft, shear,, side-to-side, shear,, and, vertical, forces, at, the, top, of, the, tower, (not, rotating, with, nacelle, yaw)",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "\"PtfmSurge,_PtfmSway_,_PtfmHeave\"_-_TP_translational_displacements": {
                    "type": "array",
                    "description": "Table data columns: \"PtfmSurge,, PtfmSway, ,, PtfmHeave\", -, TP, translational, displacements",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        }
    },
    "required": []
}

    async def execute(self, **kwargs):
        try:
            # 包装成服务端预期格式
            payload = {"updates": {}}
            for module_name in ['fst', 'se', 'elastodyn', 'tower']:
                if module_name in kwargs:
                    payload["updates"][module_name] = kwargs[module_name]

            url = "http://localhost:8002/openfast/r_test/openfast_5MW_OC4Jckt_ExtPtfm"
            response = requests.post(url, json=payload, timeout=600)
            response.raise_for_status()
            return {"result": response.json()}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}
        