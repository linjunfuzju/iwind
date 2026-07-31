
# rainbow_yu openfast.tool.openfast_5MW_Land_DLL_WTurb 🐋✨

from deepwind_app.tool.base import BaseTool
import requests

_openfast_5MW_Land_DLL_WTurb_DESCRIPTION = """这个工具是用来：这是5MW风力发电机在陆地平台上的工具，主要用于静态风力机性能评估，适用于陆上风电机组的载荷分析与性能预测。并且模拟结果后对结果进行总结。
"""

class openfast_5MW_Land_DLL_WTurb(BaseTool):
    name: str = "openfast_5MW_Land_DLL_WTurb"
    description: str = _openfast_5MW_Land_DLL_WTurb_DESCRIPTION
    parameters: dict = {
    "type": "object",
    "properties": {
        "fst": {
            "type": "object",
            "description": "Parameters extracted from 5MW_Land_DLL_WTurb.fst",
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
                    "type": "string",
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
        "aerodyn": {
            "type": "object",
            "description": "Parameters extracted from NRELOffshrBsline5MW_Onshore_AeroDyn.dat",
            "properties": {
                "Echo": {
                    "type": "boolean",
                    "description": "Echo the input to \"<rootname>.AD.ech\"? (flag)"
                },
                "DTAero": {
                    "type": "string",
                    "description": "Time interval for aerodynamic calculations {or \"default\"} (s)",
                    "enum": [
                        "or \"default"
                    ]
                },
                "Wake_Mod": {
                    "type": "number",
                    "description": "Wake/induction model (switch) {0=none, 1=BEMT, 3=OLAF} [Wake_Mod cannot be 2 or 3 when linearizing]"
                },
                "TwrPotent": {
                    "type": "number",
                    "description": "Type tower influence on wind based on potential flow around the tower (switch) {0=none, 1=baseline potential flow, 2=potential flow with Bak correction}"
                },
                "TwrShadow": {
                    "type": "number",
                    "description": "Calculate tower influence on wind based on downstream tower shadow (switch) {0=none, 1=Powles model, 2=Eames model}"
                },
                "TwrAero": {
                    "type": "boolean",
                    "description": "Calculate tower aerodynamic loads? (flag)"
                },
                "CavitCheck": {
                    "type": "boolean",
                    "description": "Perform cavitation check? (flag) [UA_Mod must be 0 when CavitCheck=true]"
                },
                "Buoyancy": {
                    "type": "boolean",
                    "description": "Include buoyancy effects? (flag)"
                },
                "NacelleDrag": {
                    "type": "boolean",
                    "description": "Include Nacelle Drag effects? (flag)"
                },
                "CompAA": {
                    "type": "boolean",
                    "description": "Flag to compute AeroAcoustics calculation [used only when Wake_Mod = 1 or 2]"
                },
                "AA_InputFile": {
                    "type": "string",
                    "description": "AeroAcoustics input file [used only when CompAA=true]"
                },
                "AirDens": {
                    "type": "string",
                    "description": "Air density (kg/m^3)"
                },
                "KinVisc": {
                    "type": "string",
                    "description": "Kinematic viscosity of working fluid (m^2/s)"
                },
                "SpdSound": {
                    "type": "string",
                    "description": "Speed of sound in working fluid (m/s)"
                },
                "Patm": {
                    "type": "string",
                    "description": "Atmospheric pressure (Pa) [used only when CavitCheck=True]"
                },
                "Pvap": {
                    "type": "string",
                    "description": "Vapour pressure of working fluid (Pa) [used only when CavitCheck=True]"
                },
                "BEM_Mod": {
                    "type": "number",
                    "description": "BEM model {1=legacy NoSweepPitchTwist, 2=polar} (switch) [used for all Wake_Mod to determine output coordinate system]"
                },
                "Skew_Mod": {
                    "type": "number",
                    "description": "Skew model {0=No skew model, -1=Remove non-normal component for linearization, 1=skew model active}"
                },
                "SkewMomCorr": {
                    "type": "boolean",
                    "description": "Turn the skew momentum correction on or off [used only when Skew_Mod=1]"
                },
                "SkewRedistr_Mod": {
                    "type": "integer",
                    "description": "Type of skewed-wake correction model (switch) {0=no redistribution, 1=Glauert/Pitt/Peters, default=1} [used only when Skew_Mod=1]",
                    "enum": []
                },
                "SkewRedistrFactor": {
                    "type": "string",
                    "description": "Constant used in Pitt/Peters skewed wake model {or \"default\" is 15/32*pi} (-) [used only when Skew_Mod=1 and SkewRedistr_Mod=1]",
                    "enum": [
                        "or \"default\" is 15",
                        "32*pi"
                    ]
                },
                "TipLoss": {
                    "type": "boolean",
                    "description": "Use the Prandtl tip-loss model? (flag) [unused when Wake_Mod=0 or 3]"
                },
                "HubLoss": {
                    "type": "boolean",
                    "description": "Use the Prandtl hub-loss model? (flag) [unused when Wake_Mod=0 or 3]"
                },
                "TanInd": {
                    "type": "boolean",
                    "description": "Include tangential induction in BEMT calculations? (flag) [unused when Wake_Mod=0 or 3]"
                },
                "AIDrag": {
                    "type": "boolean",
                    "description": "Include the drag term in the axial-induction calculation? (flag) [unused when Wake_Mod=0 or 3]"
                },
                "TIDrag": {
                    "type": "boolean",
                    "description": "Include the drag term in the tangential-induction calculation? (flag) [unused when Wake_Mod=0,3 or TanInd=FALSE]"
                },
                "IndToler": {
                    "type": "string",
                    "description": "Convergence tolerance for BEMT nonlinear solve residual equation {or \"default\"} (-) [unused when Wake_Mod=0 or 3]",
                    "enum": [
                        "or \"default"
                    ]
                },
                "MaxIter": {
                    "type": "number",
                    "description": "Maximum number of iteration steps (-) [unused when Wake_Mod=0]"
                },
                "SectAvg": {
                    "type": "boolean",
                    "description": "Use sector averaging (flag)"
                },
                "SectAvgWeighting": {
                    "type": "number",
                    "description": "Weighting function for sector average {1=Uniform, default=1} within a sector centered on the blade (switch) [used only when SectAvg=True]"
                },
                "SectAvgNPoints": {
                    "type": "integer",
                    "description": "Number of points per sectors (-) {default=5} [used only when SectAvg=True]",
                    "enum": []
                },
                "SectAvgPsiBwd": {
                    "type": "integer",
                    "description": "Backward azimuth relative to blade where the sector starts (<=0) {default=-60} (deg) [used only when SectAvg=True]",
                    "enum": []
                },
                "SectAvgPsiFwd": {
                    "type": "integer",
                    "description": "Forward azimuth relative to blade where the sector ends (>=0) {default=60} (deg) [used only when SectAvg=True]",
                    "enum": []
                },
                "DBEMT_Mod": {
                    "type": "number",
                    "description": "Type of dynamic BEMT (DBEMT) model {0=No Dynamic Wake, -1=Frozen Wake for linearization, 1:constant tau1, 2=time-dependent tau1, 3=constant tau1 with continuous formulation} (-)"
                },
                "tau1_const": {
                    "type": "number",
                    "description": "Time constant for DBEMT (s) [used only when DBEMT_Mod=1 or 3]"
                },
                "OLAF": {
                    "type": "string",
                    "description": "- cOnvecting LAgrangian Filaments (Free Vortex Wake) Theory Options  ================== [used only when Wake_Mod=3]"
                },
                "OLAFInputFileName": {
                    "type": "string",
                    "description": "Input file for OLAF [used only when Wake_Mod=3]"
                },
                "AoA34": {
                    "type": "integer",
                    "description": "Sample the angle of attack (AoA) at the 3/4 chord or the AC point {default=True} [always used]",
                    "enum": []
                },
                "UA_Mod": {
                    "type": "number",
                    "description": "Unsteady Aero Model Switch (switch) {0=Quasi-steady (no UA), 2=B-L Gonzalez, 3=B-L Minnema/Pierce, 4=B-L HGM 4-states, 5=B-L HGM+vortex 5 states, 6=Oye, 7=Boeing-Vertol}"
                },
                "FLookup": {
                    "type": "boolean",
                    "description": "Flag to indicate whether a lookup for f' will be calculated (TRUE) or whether best-fit exponential equations will be used (FALSE); if FALSE S1-S4 must be provided in airfoil input files (flag) [used only when UA_Mod>0]"
                },
                "IntegrationMethod": {
                    "type": "number",
                    "description": "Switch to indicate which integration method UA uses (1=RK4, 2=AB4, 3=ABM4, 4=BDF2)"
                },
                "UAStartRad": {
                    "type": "number",
                    "description": "Starting radius for dynamic stall (fraction of rotor radius [0.0,1.0]) [used only when UA_Mod>0; if line is missing UAStartRad=0]"
                },
                "UAEndRad": {
                    "type": "number",
                    "description": "Ending radius for dynamic stall (fraction of rotor radius [0.0,1.0]) [used only when UA_Mod>0; if line is missing UAEndRad=1]"
                },
                "AFTabMod": {
                    "type": "number",
                    "description": "Interpolation method for multiple airfoil tables {1=1D interpolation on AoA (first table only); 2=2D interpolation on AoA and Re; 3=2D interpolation on AoA and UserProp} (-)"
                },
                "InCol_Alfa": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the angle of attack (-)"
                },
                "InCol_Cl": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the lift coefficient (-)"
                },
                "InCol_Cd": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the drag coefficient (-)"
                },
                "InCol_Cm": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the pitching-moment coefficient; use zero if there is no Cm column (-)"
                },
                "InCol_Cpmin": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the Cpmin coefficient; use zero if there is no Cpmin column (-)"
                },
                "NumAFfiles": {
                    "type": "number",
                    "description": "Number of airfoil files used (-)"
                },
                "AFNames": {
                    "type": "string",
                    "description": "Airfoil file names (NumAFfiles lines) (quoted strings)"
                },
                "UseBlCm": {
                    "type": "boolean",
                    "description": "Include aerodynamic pitching moment in calculations? (flag)"
                },
                "ADBlFile(1)": {
                    "type": "string",
                    "description": "Name of file containing distributed aerodynamic properties for Blade #1 (-)"
                },
                "ADBlFile(2)": {
                    "type": "string",
                    "description": "Name of file containing distributed aerodynamic properties for Blade #2 (-) [unused if NumBl < 2]"
                },
                "ADBlFile(3)": {
                    "type": "string",
                    "description": "Name of file containing distributed aerodynamic properties for Blade #3 (-) [unused if NumBl < 3]"
                },
                "VolHub": {
                    "type": "number",
                    "description": "Hub volume (m^3)"
                },
                "HubCenBx": {
                    "type": "number",
                    "description": "Hub center of buoyancy x direction offset (m)"
                },
                "VolNac": {
                    "type": "number",
                    "description": "Nacelle volume (m^3)"
                },
                "TFinAero": {
                    "type": "boolean",
                    "description": "Calculate tail fin aerodynamics model (flag)"
                },
                "TFinFile": {
                    "type": "string",
                    "description": "Input file for tail fin aerodynamics [used only when TFinAero=True]"
                },
                "NumTwrNds": {
                    "type": "number",
                    "description": "Number of tower nodes used in the analysis (-) [used only when TwrPotent/=0, TwrShadow/=0, TwrAero=True, or Buoyancy=True]"
                },
                "TwrElev_TwrDiam_TwrCd_TwrTI_TwrCb": {
                    "type": "array",
                    "description": "Table data columns: TwrElev, TwrDiam, TwrCd, TwrTI, TwrCb",
                    "items": {
                        "type": "object",
                        "properties": {
                            "TwrElev": {
                                "type": "number"
                            },
                            "TwrDiam": {
                                "type": "number"
                            },
                            "TwrCd": {
                                "type": "number"
                            },
                            "TwrTI": {
                                "type": "number"
                            },
                            "TwrCb": {
                                "type": "number"
                            }
                        }
                    }
                },
                "SumPrint": {
                    "type": "boolean",
                    "description": "Generate a summary file listing input options and interpolated properties to \"<rootname>.AD.sum\"? (flag)"
                },
                "NBlOuts": {
                    "type": "number",
                    "description": "Number of blade node outputs [0 - 9] (-)"
                },
                "NTwOuts": {
                    "type": "number",
                    "description": "Number of tower node outputs [0 - 9] (-)"
                },
                "BldNd_BladesOut": {
                    "type": "number",
                    "description": "Number of blades to output all node information at.  Up to number of blades on turbine. (-)"
                },
                "BldNd_BlOutNd": {
                    "type": "string",
                    "description": "Specify a portion of the nodes to output. {\"ALL\", \"Tip\", \"Root\", or a list of node numbers} (-)",
                    "enum": [
                        "ALL",
                        "Tip",
                        "Root",
                        "or a list of node numbers"
                    ]
                }
            }
        },
        "aerodyn15": {
            "type": "object",
            "description": "Parameters extracted from NRELOffshrBsline5MW_Onshore_AeroDyn15.dat",
            "properties": {
                "Echo": {
                    "type": "boolean",
                    "description": "Echo the input to \"<rootname>.AD.ech\"?  (flag)"
                },
                "DTAero": {
                    "type": "string",
                    "description": "Time interval for aerodynamic calculations {or \"default\"} (s)",
                    "enum": [
                        "or \"default"
                    ]
                },
                "WakeMod": {
                    "type": "number",
                    "description": "Type of wake/induction model (switch) {0=none, 1=BEMT, 2=DBEMT, 3=OLAF} [WakeMod cannot be 2 or 3 when linearizing]"
                },
                "AFAeroMod": {
                    "type": "number",
                    "description": "Type of blade airfoil aerodynamics model (switch) {1=steady model, 2=Beddoes-Leishman unsteady model} [AFAeroMod must be 1 when linearizing]"
                },
                "TwrPotent": {
                    "type": "number",
                    "description": "Type tower influence on wind based on potential flow around the tower (switch) {0=none, 1=baseline potential flow, 2=potential flow with Bak correction}"
                },
                "TwrShadow": {
                    "type": "number",
                    "description": "Calculate tower influence on wind based on downstream tower shadow (switch) {0=none, 1=Powles model, 2=Eames model}"
                },
                "TwrAero": {
                    "type": "boolean",
                    "description": "Calculate tower aerodynamic loads? (flag)"
                },
                "FrozenWake": {
                    "type": "boolean",
                    "description": "Assume frozen wake during linearization? (flag) [used only when WakeMod=1 and when linearizing]"
                },
                "CavitCheck": {
                    "type": "boolean",
                    "description": "Perform cavitation check? (flag) [AFAeroMod must be 1 when CavitCheck=true]"
                },
                "Buoyancy": {
                    "type": "boolean",
                    "description": "Include buoyancy effects? (flag)"
                },
                "CompAA": {
                    "type": "boolean",
                    "description": "Flag to compute AeroAcoustics calculation [used only when WakeMod = 1 or 2]"
                },
                "AA_InputFile": {
                    "type": "string",
                    "description": "AeroAcoustics input file [used only when CompAA=true]"
                },
                "AirDens": {
                    "type": "string",
                    "description": "Air density (kg/m^3)"
                },
                "KinVisc": {
                    "type": "string",
                    "description": "Kinematic viscosity of working fluid (m^2/s)"
                },
                "SpdSound": {
                    "type": "string",
                    "description": "Speed of sound in working fluid (m/s)"
                },
                "Patm": {
                    "type": "string",
                    "description": "Atmospheric pressure (Pa) [used only when CavitCheck=True]"
                },
                "Pvap": {
                    "type": "string",
                    "description": "Vapour pressure of working fluid (Pa) [used only when CavitCheck=True]"
                },
                "SkewMod": {
                    "type": "number",
                    "description": "Type of skewed-wake correction model (switch) {1=uncoupled, 2=Pitt/Peters, 3=coupled} [unused when WakeMod=0 or 3]"
                },
                "SkewModFactor": {
                    "type": "string",
                    "description": "Constant used in Pitt/Peters skewed wake model {or \"default\" is 15/32*pi} (-) [used only when SkewMod=2; unused when WakeMod=0 or 3]",
                    "enum": [
                        "or \"default\" is 15",
                        "32*pi"
                    ]
                },
                "TipLoss": {
                    "type": "boolean",
                    "description": "Use the Prandtl tip-loss model? (flag) [unused when WakeMod=0 or 3]"
                },
                "HubLoss": {
                    "type": "boolean",
                    "description": "Use the Prandtl hub-loss model? (flag) [unused when WakeMod=0 or 3]"
                },
                "TanInd": {
                    "type": "boolean",
                    "description": "Include tangential induction in BEMT calculations? (flag) [unused when WakeMod=0 or 3]"
                },
                "AIDrag": {
                    "type": "boolean",
                    "description": "Include the drag term in the axial-induction calculation? (flag) [unused when WakeMod=0 or 3]"
                },
                "TIDrag": {
                    "type": "boolean",
                    "description": "Include the drag term in the tangential-induction calculation? (flag) [unused when WakeMod=0,3 or TanInd=FALSE]"
                },
                "IndToler": {
                    "type": "string",
                    "description": "Convergence tolerance for BEMT nonlinear solve residual equation {or \"default\"} (-) [unused when WakeMod=0 or 3]",
                    "enum": [
                        "or \"default"
                    ]
                },
                "MaxIter": {
                    "type": "number",
                    "description": "Maximum number of iteration steps (-) [unused when WakeMod=0]"
                },
                "DBEMT_Mod": {
                    "type": "number",
                    "description": "Type of dynamic BEMT (DBEMT) model {1=constant tau1, 2=time-dependent tau1, 3=constant tau1 with continuous formulation} (-) [used only when WakeMod=2]"
                },
                "tau1_const": {
                    "type": "number",
                    "description": "Time constant for DBEMT (s) [used only when WakeMod=2 and DBEMT_Mod=1 or 3]"
                },
                "OLAF": {
                    "type": "string",
                    "description": "- cOnvecting LAgrangian Filaments (Free Vortex Wake) Theory Options  ================== [used only when WakeMod=3]"
                },
                "OLAFInputFileName": {
                    "type": "string",
                    "description": "Input file for OLAF [used only when WakeMod=3]"
                },
                "UAMod": {
                    "type": "number",
                    "description": "Unsteady Aero Model Switch (switch) {2=B-L Gonzalez, 3=B-L Minnema/Pierce, 4=B-L HGM 4-states, 5=B-L 5 states, 6=Oye, 7=Boeing-Vertol} [used only when AFAeroMod=2]"
                },
                "FLookup": {
                    "type": "boolean",
                    "description": "Flag to indicate whether a lookup for f' will be calculated (TRUE) or whether best-fit exponential equations will be used (FALSE); if FALSE S1-S4 must be provided in airfoil input files (flag) [used only when AFAeroMod=2]"
                },
                "AFTabMod": {
                    "type": "number",
                    "description": "Interpolation method for multiple airfoil tables {1=1D interpolation on AoA (first table only); 2=2D interpolation on AoA and Re; 3=2D interpolation on AoA and UserProp} (-)"
                },
                "InCol_Alfa": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the angle of attack (-)"
                },
                "InCol_Cl": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the lift coefficient (-)"
                },
                "InCol_Cd": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the drag coefficient (-)"
                },
                "InCol_Cm": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the pitching-moment coefficient; use zero if there is no Cm column (-)"
                },
                "InCol_Cpmin": {
                    "type": "number",
                    "description": "The column in the airfoil tables that contains the Cpmin coefficient; use zero if there is no Cpmin column (-)"
                },
                "NumAFfiles": {
                    "type": "number",
                    "description": "Number of airfoil files used (-)"
                },
                "AFNames": {
                    "type": "string",
                    "description": "Airfoil file names (NumAFfiles lines) (quoted strings)"
                },
                "UseBlCm": {
                    "type": "boolean",
                    "description": "Include aerodynamic pitching moment in calculations?  (flag)"
                },
                "ADBlFile(1)": {
                    "type": "string",
                    "description": "Name of file containing distributed aerodynamic properties for Blade #1 (-)"
                },
                "ADBlFile(2)": {
                    "type": "string",
                    "description": "Name of file containing distributed aerodynamic properties for Blade #2 (-) [unused if NumBl < 2]"
                },
                "ADBlFile(3)": {
                    "type": "string",
                    "description": "Name of file containing distributed aerodynamic properties for Blade #3 (-) [unused if NumBl < 3]"
                },
                "VolHub": {
                    "type": "number",
                    "description": "Hub volume (m^3)"
                },
                "HubCenBx": {
                    "type": "number",
                    "description": "Hub center of buoyancy x direction offset (m)"
                },
                "VolNac": {
                    "type": "number",
                    "description": "Nacelle volume (m^3)"
                },
                "NacCenB": {
                    "type": "array",
                    "description": "Position of nacelle center of buoyancy from yaw bearing in nacelle coordinates (m)"
                },
                "TFinAero": {
                    "type": "boolean",
                    "description": "Calculate tail fin aerodynamics model (flag)"
                },
                "TFinFile": {
                    "type": "string",
                    "description": "Input file for tail fin aerodynamics [used only when TFinAero=True]"
                },
                "NumTwrNds": {
                    "type": "number",
                    "description": "Number of tower nodes used in the analysis  (-) [used only when TwrPotent/=0, TwrShadow/=0, TwrAero=True, or Buoyancy=True]"
                },
                "TwrElev_TwrDiam_TwrCd_TwrTI_TwrCb": {
                    "type": "array",
                    "description": "Table data columns: TwrElev, TwrDiam, TwrCd, TwrTI, TwrCb",
                    "items": {
                        "type": "object",
                        "properties": {
                            "TwrElev": {
                                "type": "number"
                            },
                            "TwrDiam": {
                                "type": "number"
                            },
                            "TwrCd": {
                                "type": "number"
                            },
                            "TwrTI": {
                                "type": "number"
                            },
                            "TwrCb": {
                                "type": "number"
                            }
                        }
                    }
                },
                "SumPrint": {
                    "type": "boolean",
                    "description": "Generate a summary file listing input options and interpolated properties to \"<rootname>.AD.sum\"?  (flag)"
                },
                "NBlOuts": {
                    "type": "number",
                    "description": "Number of blade node outputs [0 - 9] (-)"
                },
                "NTwOuts": {
                    "type": "number",
                    "description": "Number of tower node outputs [0 - 9]  (-)"
                }
            }
        },
        "elastodyn": {
            "type": "object",
            "description": "Parameters extracted from NRELOffshrBsline5MW_Onshore_ElastoDyn.dat",
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
                "NBlGages": {
                    "type": "number",
                    "description": "Number of blade nodes that have strain gages for output [0 to 9] (-)"
                },
                "\"OoPDefl1\"_-_Blade_1_out-of-plane_and_in-plane_deflections_and_tip_twist": {
                    "type": "array",
                    "description": "Table data columns: \"OoPDefl1\", -, Blade, 1, out-of-plane, and, in-plane, deflections, and, tip, twist",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"OoPDefl1\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Blade": {
                                "type": "number"
                            },
                            "1": {
                                "type": "number"
                            },
                            "out-of-plane": {
                                "type": "number"
                            },
                            "and": {
                                "type": "number"
                            },
                            "in-plane": {
                                "type": "number"
                            },
                            "deflections": {
                                "type": "number"
                            },
                            "tip": {
                                "type": "number"
                            },
                            "twist": {
                                "type": "number"
                            }
                        }
                    }
                },
                "\"BldPitch1\"_-_Blade_1_pitch_angle": {
                    "type": "array",
                    "description": "Table data columns: \"BldPitch1\", -, Blade, 1, pitch, angle",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "\"RotSpeed\"_-_Low-speed_shaft_and_high-speed_shaft_speeds": {
                    "type": "array",
                    "description": "Table data columns: \"RotSpeed\", -, Low-speed, shaft, and, high-speed, shaft, speeds",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "\"TTDspFA\"_-_Tower_fore-aft_and_side-to-side_displacements_and_top_twist": {
                    "type": "array",
                    "description": "Table data columns: \"TTDspFA\", -, Tower, fore-aft, and, side-to-side, displacements, and, top, twist",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"TTDspFA\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Tower": {
                                "type": "number"
                            },
                            "fore-aft": {
                                "type": "number"
                            },
                            "and": {
                                "type": "number"
                            },
                            "side-to-side": {
                                "type": "number"
                            },
                            "displacements": {
                                "type": "number"
                            },
                            "top": {
                                "type": "number"
                            },
                            "twist": {
                                "type": "number"
                            }
                        }
                    }
                },
                "\"Spn2MLxb1\"_-_Blade_1_local_edgewise_and_flapwise_bending_moments_at_span_station_2_(approx._50%_span)": {
                    "type": "array",
                    "description": "Table data columns: \"Spn2MLxb1\", -, Blade, 1, local, edgewise, and, flapwise, bending, moments, at, span, station, 2, (approx., 50%, span)",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "\"RootFxb1\"_-_Out-of-plane_shear,_in-plane_shear,_and_axial_forces_at_the_root_of_blade_1": {
                    "type": "array",
                    "description": "Table data columns: \"RootFxb1\", -, Out-of-plane, shear,, in-plane, shear,, and, axial, forces, at, the, root, of, blade, 1",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"RootFxb1\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Out-of-plane": {
                                "type": "number"
                            },
                            "shear,": {
                                "type": "number"
                            },
                            "in-plane": {
                                "type": "number"
                            },
                            "and": {
                                "type": "number"
                            },
                            "axial": {
                                "type": "number"
                            },
                            "forces": {
                                "type": "number"
                            },
                            "at": {
                                "type": "number"
                            },
                            "the": {
                                "type": "number"
                            },
                            "root": {
                                "type": "number"
                            },
                            "of": {
                                "type": "number"
                            },
                            "blade": {
                                "type": "number"
                            },
                            "1": {
                                "type": "number"
                            }
                        }
                    }
                },
                "\"YawBrFxp\"_-_Fore-aft_shear,_side-to-side_shear,_and_vertical_forces_at_the_top_of_the_tower_(not_rotating_with_nacelle_yaw)": {
                    "type": "array",
                    "description": "Table data columns: \"YawBrFxp\", -, Fore-aft, shear,, side-to-side, shear,, and, vertical, forces, at, the, top, of, the, tower, (not, rotating, with, nacelle, yaw)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"YawBrFxp\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Fore-aft": {
                                "type": "number"
                            },
                            "shear,": {
                                "type": "number"
                            },
                            "side-to-side": {
                                "type": "number"
                            },
                            "and": {
                                "type": "number"
                            },
                            "vertical": {
                                "type": "number"
                            },
                            "forces": {
                                "type": "number"
                            },
                            "at": {
                                "type": "number"
                            },
                            "the": {
                                "type": "number"
                            },
                            "top": {
                                "type": "number"
                            },
                            "of": {
                                "type": "number"
                            },
                            "tower": {
                                "type": "number"
                            },
                            "(not": {
                                "type": "number"
                            },
                            "rotating": {
                                "type": "number"
                            },
                            "with": {
                                "type": "number"
                            },
                            "nacelle": {
                                "type": "number"
                            },
                            "yaw)": {
                                "type": "number"
                            }
                        }
                    }
                },
                "\"TwrBsFxt\"_-_Fore-aft_shear,_side-to-side_shear,_and_vertical_forces_at_the_base_of_the_tower_(mudline)": {
                    "type": "array",
                    "description": "Table data columns: \"TwrBsFxt\", -, Fore-aft, shear,, side-to-side, shear,, and, vertical, forces, at, the, base, of, the, tower, (mudline)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "\"TwrBsFxt\"": {
                                "type": "number"
                            },
                            "-": {
                                "type": "number"
                            },
                            "Fore-aft": {
                                "type": "number"
                            },
                            "shear,": {
                                "type": "number"
                            },
                            "side-to-side": {
                                "type": "number"
                            },
                            "and": {
                                "type": "number"
                            },
                            "vertical": {
                                "type": "number"
                            },
                            "forces": {
                                "type": "number"
                            },
                            "at": {
                                "type": "number"
                            },
                            "the": {
                                "type": "number"
                            },
                            "base": {
                                "type": "number"
                            },
                            "of": {
                                "type": "number"
                            },
                            "tower": {
                                "type": "number"
                            },
                            "(mudline)": {
                                "type": "number"
                            }
                        }
                    }
                }
            }
        },
        "tower": {
            "type": "object",
            "description": "Parameters extracted from NRELOffshrBsline5MW_Onshore_ElastoDyn_Tower.dat",
            "properties": {
                "NTwInpSt": {
                    "type": "number",
                    "description": "Number of input stations to specify tower geometry"
                },
                "TwrFADmp(1)": {
                    "type": "number",
                    "description": "Tower 1st fore-aft mode structural damping ratio (%)"
                },
                "TwrFADmp(2)": {
                    "type": "number",
                    "description": "Tower 2nd fore-aft mode structural damping ratio (%)"
                },
                "TwrSSDmp(1)": {
                    "type": "number",
                    "description": "Tower 1st side-to-side mode structural damping ratio (%)"
                },
                "TwrSSDmp(2)": {
                    "type": "number",
                    "description": "Tower 2nd side-to-side mode structural damping ratio (%)"
                },
                "FAStTunr(1)": {
                    "type": "number",
                    "description": "Tower fore-aft modal stiffness tuner, 1st mode (-)"
                },
                "FAStTunr(2)": {
                    "type": "number",
                    "description": "Tower fore-aft modal stiffness tuner, 2nd mode (-)"
                },
                "SSStTunr(1)": {
                    "type": "number",
                    "description": "Tower side-to-side stiffness tuner, 1st mode (-)"
                },
                "SSStTunr(2)": {
                    "type": "number",
                    "description": "Tower side-to-side stiffness tuner, 2nd mode (-)"
                },
                "AdjTwMa": {
                    "type": "number",
                    "description": "Factor to adjust tower mass density (-)"
                },
                "AdjFASt": {
                    "type": "number",
                    "description": "Factor to adjust tower fore-aft stiffness (-)"
                },
                "AdjSSSt": {
                    "type": "number",
                    "description": "Factor to adjust tower side-to-side stiffness (-)"
                },
                "HtFract_TMassDen_TwFAStif_TwSSStif": {
                    "type": "array",
                    "description": "Table data columns: HtFract, TMassDen, TwFAStif, TwSSStif",
                    "items": {
                        "type": "object",
                        "properties": {
                            "HtFract": {
                                "type": "number"
                            },
                            "TMassDen": {
                                "type": "number"
                            },
                            "TwFAStif": {
                                "type": "number"
                            },
                            "TwSSStif": {
                                "type": "number"
                            }
                        }
                    }
                },
                "TwFAM1Sh(2)": {
                    "type": "number",
                    "description": "Mode 1, coefficient of x^2 term"
                },
                "TwFAM1Sh(3)": {
                    "type": "number",
                    "description": ", coefficient of x^3 term"
                },
                "TwFAM1Sh(5)": {
                    "type": "number",
                    "description": ", coefficient of x^5 term"
                },
                "TwFAM2Sh(4)": {
                    "type": "number",
                    "description": ", coefficient of x^4 term"
                },
                "TwFAM2Sh(6)": {
                    "type": "number",
                    "description": ", coefficient of x^6 term"
                },
                "TwSSM1Sh(2)": {
                    "type": "number",
                    "description": "Mode 1, coefficient of x^2 term"
                },
                "TwSSM1Sh(4)": {
                    "type": "number",
                    "description": ", coefficient of x^4 term"
                },
                "TwSSM1Sh(6)": {
                    "type": "number",
                    "description": ", coefficient of x^6 term"
                },
                "TwSSM2Sh(3)": {
                    "type": "number",
                    "description": ", coefficient of x^3 term"
                },
                "TwSSM2Sh(5)": {
                    "type": "number",
                    "description": ", coefficient of x^5 term"
                }
            }
        },
        "servodyn": {
            "type": "object",
            "description": "Parameters extracted from NRELOffshrBsline5MW_Onshore_ServoDyn.dat",
            "properties": {
                "Echo": {
                    "type": "boolean",
                    "description": "Echo input data to <RootName>.ech (flag)"
                },
                "DT": {
                    "type": "string",
                    "description": "Communication interval for controllers (s) (or \"default\")"
                },
                "PCMode": {
                    "type": "number",
                    "description": "Pitch control mode {0: none, 3: user-defined from routine PitchCntrl, 4: user-defined from Simulink/Labview, 5: user-defined from Bladed-style DLL} (switch)"
                },
                "TPCOn": {
                    "type": "number",
                    "description": "Time to enable active pitch control (s) [unused when PCMode=0]"
                },
                "TPitManS(1)": {
                    "type": "number",
                    "description": "Time to start override pitch maneuver for blade 1 and end standard pitch control (s)"
                },
                "TPitManS(2)": {
                    "type": "number",
                    "description": "Time to start override pitch maneuver for blade 2 and end standard pitch control (s)"
                },
                "TPitManS(3)": {
                    "type": "number",
                    "description": "Time to start override pitch maneuver for blade 3 and end standard pitch control (s) [unused for 2 blades]"
                },
                "PitManRat(1)": {
                    "type": "number",
                    "description": "Pitch rate at which override pitch maneuver heads toward final pitch angle for blade 1 (deg/s)"
                },
                "PitManRat(2)": {
                    "type": "number",
                    "description": "Pitch rate at which override pitch maneuver heads toward final pitch angle for blade 2 (deg/s)"
                },
                "PitManRat(3)": {
                    "type": "number",
                    "description": "Pitch rate at which override pitch maneuver heads toward final pitch angle for blade 3 (deg/s) [unused for 2 blades]"
                },
                "BlPitchF(1)": {
                    "type": "number",
                    "description": "Blade 1 final pitch for pitch maneuvers (degrees)"
                },
                "BlPitchF(2)": {
                    "type": "number",
                    "description": "Blade 2 final pitch for pitch maneuvers (degrees)"
                },
                "BlPitchF(3)": {
                    "type": "number",
                    "description": "Blade 3 final pitch for pitch maneuvers (degrees) [unused for 2 blades]"
                },
                "VSContrl": {
                    "type": "number",
                    "description": "Variable-speed control mode {0: none, 1: simple VS, 3: user-defined from routine UserVSCont, 4: user-defined from Simulink/Labview, 5: user-defined from Bladed-style DLL} (switch)"
                },
                "GenModel": {
                    "type": "number",
                    "description": "Generator model {1: simple, 2: Thevenin, 3: user-defined from routine UserGen} (switch) [used only when VSContrl=0]"
                },
                "GenEff": {
                    "type": "number",
                    "description": "Generator efficiency [ignored by the Thevenin and user-defined generator models] (%)"
                },
                "GenTiStr": {
                    "type": "string",
                    "description": "Method to start the generator {T: timed using TimGenOn, F: generator speed using SpdGenOn} (flag)",
                    "enum": [
                        "T: timed using TimGenOn",
                        "F: generator speed using SpdGenOn"
                    ]
                },
                "GenTiStp": {
                    "type": "integer",
                    "description": "Method to stop the generator {T: timed using TimGenOf, F: when generator power = 0} (flag)",
                    "enum": [
                        "T"
                    ]
                },
                "SpdGenOn": {
                    "type": "number",
                    "description": "Generator speed to turn on the generator for a startup (HSS speed) (rpm) [used only when GenTiStr=False]"
                },
                "TimGenOn": {
                    "type": "number",
                    "description": "Time to turn on the generator for a startup (s) [used only when GenTiStr=True]"
                },
                "TimGenOf": {
                    "type": "number",
                    "description": "Time to turn off the generator (s) [used only when GenTiStp=True]"
                },
                "VS_RtGnSp": {
                    "type": "number",
                    "description": "Rated generator speed for simple variable-speed generator control (HSS side) (rpm) [used only when VSContrl=1]"
                },
                "VS_RtTq": {
                    "type": "number",
                    "description": "Rated generator torque/constant generator torque in Region 3 for simple variable-speed generator control (HSS side) (N-m) [used only when VSContrl=1]"
                },
                "VS_Rgn2K": {
                    "type": "number",
                    "description": "Generator torque constant in Region 2 for simple variable-speed generator control (HSS side) (N-m/rpm^2) [used only when VSContrl=1]"
                },
                "VS_SlPc": {
                    "type": "number",
                    "description": "Rated generator slip percentage in Region 2 1/2 for simple variable-speed generator control (%) [used only when VSContrl=1]"
                },
                "SIG_SlPc": {
                    "type": "number",
                    "description": "Rated generator slip percentage (%) [used only when VSContrl=0 and GenModel=1]"
                },
                "SIG_SySp": {
                    "type": "number",
                    "description": "Synchronous (zero-torque) generator speed (rpm) [used only when VSContrl=0 and GenModel=1]"
                },
                "SIG_RtTq": {
                    "type": "number",
                    "description": "Rated torque (N-m) [used only when VSContrl=0 and GenModel=1]"
                },
                "SIG_PORt": {
                    "type": "number",
                    "description": "Pull-out ratio (Tpullout/Trated) (-) [used only when VSContrl=0 and GenModel=1]"
                },
                "TEC_Freq": {
                    "type": "number",
                    "description": "Line frequency [50 or 60] (Hz) [used only when VSContrl=0 and GenModel=2]"
                },
                "TEC_NPol": {
                    "type": "number",
                    "description": "Number of poles [even integer > 0] (-) [used only when VSContrl=0 and GenModel=2]"
                },
                "TEC_SRes": {
                    "type": "number",
                    "description": "Stator resistance (ohms) [used only when VSContrl=0 and GenModel=2]"
                },
                "TEC_RRes": {
                    "type": "number",
                    "description": "Rotor resistance (ohms) [used only when VSContrl=0 and GenModel=2]"
                },
                "TEC_VLL": {
                    "type": "number",
                    "description": "Line-to-line RMS voltage (volts) [used only when VSContrl=0 and GenModel=2]"
                },
                "TEC_SLR": {
                    "type": "number",
                    "description": "Stator leakage reactance (ohms) [used only when VSContrl=0 and GenModel=2]"
                },
                "TEC_RLR": {
                    "type": "number",
                    "description": "Rotor leakage reactance (ohms) [used only when VSContrl=0 and GenModel=2]"
                },
                "TEC_MR": {
                    "type": "number",
                    "description": "Magnetizing reactance (ohms) [used only when VSContrl=0 and GenModel=2]"
                },
                "HSSBrMode": {
                    "type": "number",
                    "description": "HSS brake model {0: none, 1: simple, 3: user-defined from routine UserHSSBr, 4: user-defined from Simulink/Labview, 5: user-defined from Bladed-style DLL} (switch)"
                },
                "THSSBrDp": {
                    "type": "number",
                    "description": "Time to initiate deployment of the HSS brake (s)"
                },
                "HSSBrDT": {
                    "type": "number",
                    "description": "Time for HSS-brake to reach full deployment once initiated (sec) [used only when HSSBrMode=1]"
                },
                "HSSBrTqF": {
                    "type": "number",
                    "description": "Fully deployed HSS-brake torque (N-m)"
                },
                "YCMode": {
                    "type": "number",
                    "description": "Yaw control mode {0: none, 3: user-defined from routine UserYawCont, 4: user-defined from Simulink/Labview, 5: user-defined from Bladed-style DLL} (switch)"
                },
                "TYCOn": {
                    "type": "number",
                    "description": "Time to enable active yaw control (s) [unused when YCMode=0]"
                },
                "YawNeut": {
                    "type": "number",
                    "description": "Neutral yaw position--yaw spring force is zero at this yaw (degrees)"
                },
                "YawSpr": {
                    "type": "number",
                    "description": "Nacelle-yaw spring constant (N-m/rad)"
                },
                "YawDamp": {
                    "type": "number",
                    "description": "Nacelle-yaw damping constant (N-m/(rad/s))"
                },
                "TYawManS": {
                    "type": "number",
                    "description": "Time to start override yaw maneuver and end standard yaw control (s)"
                },
                "YawManRat": {
                    "type": "number",
                    "description": "Yaw maneuver rate (in absolute value) (deg/s)"
                },
                "NacYawF": {
                    "type": "number",
                    "description": "Final yaw angle for override yaw maneuvers (degrees)"
                },
                "AfCmode": {
                    "type": "number",
                    "description": "Airfoil control mode {0: none, 1: cosine wave cycle, 4: user-defined from Simulink/Labview, 5: user-defined from Bladed-style DLL} (switch)"
                },
                "AfC_Mean": {
                    "type": "number",
                    "description": "Mean level for cosine cycling or steady value (-) [used only with AfCmode==1]"
                },
                "AfC_Amp": {
                    "type": "number",
                    "description": "Amplitude for for cosine cycling of flap signal (-) [used only with AfCmode==1]"
                },
                "AfC_Phase": {
                    "type": "number",
                    "description": "Phase relative to the blade azimuth (0 is vertical) for for cosine cycling of flap signal (deg) [used only with AfCmode==1]"
                },
                "NumBStC": {
                    "type": "number",
                    "description": "Number of blade structural controllers (integer)"
                },
                "BStCfiles": {
                    "type": "string",
                    "description": "Name of the files for blade structural controllers (quoted strings) [unused when NumBStC==0]"
                },
                "NumNStC": {
                    "type": "number",
                    "description": "Number of nacelle structural controllers (integer)"
                },
                "NStCfiles": {
                    "type": "string",
                    "description": "Name of the files for nacelle structural controllers (quoted strings) [unused when NumNStC==0]"
                },
                "NumTStC": {
                    "type": "number",
                    "description": "Number of tower structural controllers (integer)"
                },
                "TStCfiles": {
                    "type": "string",
                    "description": "Name of the files for tower structural controllers (quoted strings) [unused when NumTStC==0]"
                },
                "NumSStC": {
                    "type": "number",
                    "description": "Number of substructure structural controllers (integer)"
                },
                "SStCfiles": {
                    "type": "string",
                    "description": "Name of the files for substructure structural controllers (quoted strings) [unused when NumSStC==0]"
                },
                "CCmode": {
                    "type": "number",
                    "description": "Cable control mode {0: none, 4: user-defined from Simulink/Labview, 5: user-defined from Bladed-style DLL} (switch)"
                },
                "DLL_FileName": {
                    "type": "string",
                    "description": "Name/location of the dynamic library {.dll [Windows] or .so [Linux]} in the Bladed-DLL format (-) [used only with Bladed Interface]",
                    "enum": [
                        ".dll [Windows] or .so [Linux]"
                    ]
                },
                "DLL_InFile": {
                    "type": "string",
                    "description": "Name of input file sent to the DLL (-) [used only with Bladed Interface]"
                },
                "DLL_ProcName": {
                    "type": "string",
                    "description": "Name of procedure in DLL to be called (-) [case sensitive; used only with DLL Interface]"
                },
                "DLL_DT": {
                    "type": "string",
                    "description": "Communication interval for dynamic library (s) (or \"default\") [used only with Bladed Interface]"
                },
                "DLL_Ramp": {
                    "type": "boolean",
                    "description": "Whether a linear ramp should be used between DLL_DT time steps [introduces time shift when true] (flag) [used only with Bladed Interface]"
                },
                "BPCutoff": {
                    "type": "number",
                    "description": "Cutoff frequency for low-pass filter on blade pitch from DLL (Hz) [used only with Bladed Interface]"
                },
                "NacYaw_North": {
                    "type": "number",
                    "description": "Reference yaw angle of the nacelle when the upwind end points due North (deg) [used only with Bladed Interface]"
                },
                "Ptch_Cntrl": {
                    "type": "number",
                    "description": "Record 28: Use individual pitch control {0: collective pitch; 1: individual pitch control} (switch) [used only with Bladed Interface]"
                },
                "Ptch_SetPnt": {
                    "type": "number",
                    "description": "Record  5: Below-rated pitch angle set-point (deg) [used only with Bladed Interface]"
                },
                "Ptch_Min": {
                    "type": "number",
                    "description": "Record  6: Minimum pitch angle (deg) [used only with Bladed Interface]"
                },
                "Ptch_Max": {
                    "type": "number",
                    "description": "Record  7: Maximum pitch angle (deg) [used only with Bladed Interface]"
                },
                "PtchRate_Min": {
                    "type": "number",
                    "description": "Record  8: Minimum pitch rate (most negative value allowed) (deg/s) [used only with Bladed Interface]"
                },
                "PtchRate_Max": {
                    "type": "number",
                    "description": "Record  9: Maximum pitch rate  (deg/s) [used only with Bladed Interface]"
                },
                "Gain_OM": {
                    "type": "number",
                    "description": "Record 16: Optimal mode gain (Nm/(rad/s)^2) [used only with Bladed Interface]"
                },
                "GenSpd_MinOM": {
                    "type": "number",
                    "description": "Record 17: Minimum generator speed (rpm) [used only with Bladed Interface]"
                },
                "GenSpd_MaxOM": {
                    "type": "number",
                    "description": "Record 18: Optimal mode maximum speed (rpm) [used only with Bladed Interface]"
                },
                "GenSpd_Dem": {
                    "type": "number",
                    "description": "Record 19: Demanded generator speed above rated (rpm) [used only with Bladed Interface]"
                },
                "GenTrq_Dem": {
                    "type": "number",
                    "description": "Record 22: Demanded generator torque above rated (Nm) [used only with Bladed Interface]"
                },
                "GenPwr_Dem": {
                    "type": "number",
                    "description": "Record 13: Demanded power (W) [used only with Bladed Interface]"
                },
                "DLL_NumTrq": {
                    "type": "number",
                    "description": "Record 26: No. of points in torque-speed look-up table {0 = none and use the optimal mode parameters; nonzero = ignore the optimal mode PARAMETERs by setting Record 16 to 0.0} (-) [used only with Bladed Interface]"
                },
                "GenSpd_TLU_GenTrq_TLU": {
                    "type": "array",
                    "description": "Table data columns: GenSpd_TLU, GenTrq_TLU",
                    "items": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "SumPrint": {
                    "type": "boolean",
                    "description": "Print summary data to <RootName>.sum (flag) (currently unused)"
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
                "\"GenPwr\"_-_Electrical_generator_power_and_torque": {
                    "type": "array",
                    "description": "Table data columns: \"GenPwr\", -, Electrical, generator, power, and, torque",
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
            for module_name in ['fst', 'aerodyn', 'aerodyn15', 'elastodyn', 'tower', 'servodyn']:
                if module_name in kwargs:
                    payload["updates"][module_name] = kwargs[module_name]

            url = "http://localhost:8002/openfast/r_test/openfast_5MW_Land_DLL_WTurb"
            response = requests.post(url, json=payload, timeout=600)
            response.raise_for_status()
            return {"result": response.json()}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}
        