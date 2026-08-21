# IEA 10MW Offshore Wind Turbine Extreme Loading Simulation Reproduction

> This project reproduces all **336 simulation cases** from the paper **IWind: IEA 10MW Offshore Wind Turbine Extreme Loading Dataset**.

---

## ⚠️ Before You Start — Please Confirm Both Points

1. **Time cost**: Full batch simulation (336 cases) takes approximately **48 hours**. Ensure your machine can run for an extended period.
2. **Storage space**: Complete simulation results require approximately **73 GB** of disk space. Ensure you have sufficient space before starting.

---

## 📦 File Overview

The following files should be present in this directory:

| File | Description |
|------|-------------|
| `single_simulation.py` | Interactive single-case simulation script (natural language input). Supports typhoon and earthquake simulations via LLM-powered chat interface. |
| `batch_simulation.py` | Batch simulation script for fully automated execution of all 336 cases. Supports resume after interruption. |
| `process_results.py` | Post-processing script that extracts maximum stress from simulation `.out` files and generates stressv2 and tiqu CSV files. |
| `visualization.py` | Visualization script that generates plots from processed CSV data (optimal pitch vs yaw curves, comparison plots, heatmaps). |
| `example_case/` | Example Docker container with pre-configured simulation environment for testing. |
| `*.tar.gz` | **Docker image** (~500 MB), contains simulation environment and API service. Any `.tar.gz` file in this directory will be automatically detected. |

---

## 🔧 Requirements

- **OS**: Windows / macOS / Linux
- **Docker Desktop**: Must be installed and running ([Download](https://docs.docker.com/desktop/))
- **Disk space**: ≥ 80 GB (with margin)
- **Runtime**: Batch simulation ~48 hours; single simulation ~5–15 minutes

---

## 📥 Required Download: Docker Image

> The Docker image must be downloaded before running the scripts. Place it in the **same directory** as the `.py` files.

**Download link:**
```
https://download.scidb.cn/download?fileId=b08e8bbb59e043a519f18c32d325dcb2&path=/V2/Iwind_reproduce_v5.tar.gz&username=linjunfu@zju.edu.cn&fileName=Iwind_reproduce_v5.tar.gz
```

After downloading, **rename the file to end with `.tar.gz`** (e.g., `anything.tar.gz`) and place it in the same directory as the scripts. The scripts will automatically find and load any `.tar.gz` file in the directory - no specific filename is required.

> **Note:** The image tag is automatically detected and corrected if needed. The loaded image will be tagged as `zwind-reproduce:v4`.

---

## 📥 Optional Download: Complete Simulation Dataset (~73 GB)

> If you do not want to run the simulations yourself (48 hours), you can directly download our completed full dataset.

**Download link:**
```
https://download.scidb.cn/download?fileId=7f69b3482faaf09f7be562bf036cb3c0&path=/V1/IWind_IEA10MW_Offshore_Wind_Turbine_Extreme_Loading_Dataset.tar.zst&username=linjunfu@zju.edu.cn&fileName=IWind_IEA10MW_Offshore_Wind_Turbine_Extreme_Loading_Dataset.tar.zst
```

After downloading and extracting, you will get the `simulation_runs/` directory containing all 336 cases with complete simulation results (CSV time-series data + PNG visualizations).

---

## 🚀 Usage

### Step 1: Run Simulations

#### Method A: Single Interactive Simulation (Recommended for New Users)

Use `single_simulation.py` to describe your simulation needs in natural language.

```bash
python single_simulation.py
```

**Features:**
- LLM-powered natural language interface
- Supports typhoon and earthquake simulations
- Interactive parameter confirmation before execution
- Real-time streaming responses from LLM

**Supported simulation parameters:**
- **Typhoon**: Wind speed 40 / 60 m/s
- **Earthquake**: Acceleration 1g (9.81) / 2g (19.62) / 4g (39.24) m/s²
- **Pitch angle**: 0°, 15°, 30°, 45°, 60°, 75°, 90°
- **Yaw angle**: -150°, -120°, -90°, -60°, -30°, 0°, 30°, 60°, 90°, 120°, 150°, 180°

#### Method B: Full Batch Simulation (336 Cases)

Use `batch_simulation.py` for fully automated batch simulation.

```bash
python batch_simulation.py
```

**Batch case configuration:**

| Case Type | Parameters | # Cases |
|-----------|------------|---------|
| Typhoon 40m/s | Wind speed 40 m/s | 84 cases |
| Typhoon 60m/s | Wind speed 60 m/s | 84 cases |
| Earthquake 1g | Acceleration 9.81 m/s² | 84 cases |
| Earthquake 2g | Acceleration 19.62 m/s² | 84 cases |
| **Total** | | **336 cases** |

> ⚠️ Estimated time: ~48 hours. You may interrupt with `Ctrl+C` at any time. The container will be retained in the background and data will not be lost.

**Resume after interruption:**
```bash
# The script will automatically resume from where it left off; completed cases will not be re-run
python batch_simulation.py
```

---

### Step 2: Post-Processing (Optional)

After simulations complete, use `process_results.py` to extract and process data from simulation output files.

```bash
python process_results.py
```

**What this script does:**

1. **stressv2 processing**: Reads all `.out` files from simulation results, extracts maximum tower base stress (von Mises) for each case
   - Stress values ≥ 355 MPa are truncated to 355 MPa (material yield strength limit)
   - Failed cases (no .out file) are marked as MaxStress=355
   - Generates CSV file with columns: `FileName`, `V_hub_ms`, `Pitch_deg`, `Yaw_deg`, `MaxStress_MPa`, `Time_at_Max_s`

2. **tiqu processing**: From stressv2 results, extracts optimal pitch angle for each yaw angle
   - Groups by yaw angle, finds pitch angle corresponding to minimum stress
   - NaN values are ignored (optimal found from valid data only)
   - Generates CSV file with columns: `Yaw_deg`, `Pitch_Vx_xx` (optimal pitch per wind speed), `MinStress_Vx_xx` (corresponding stress)

**Output:**
- `*_stressv2_*.csv` - Max stress data for all cases (84 records per case type)
- `*_tiqu_*.csv` - Optimal pitch configuration per yaw angle (12 records per case type)

**Environment variables (optional):**
- `PROCESS_SOURCE_DIR` - Source directory containing simulation results (default: `simulation_runs/20260504_142408`)
- `PROCESS_OUTPUT_DIR` - Output directory for CSV files (default: `simulation_runs/result_reference_values/pipeline_output`)
- `PROCESS_SUB_FOLDERS` - Comma-separated list of subfolders to process (default: `Earthquake_4g`)

---

### Step 3: Visualization (Optional)

Use `visualization.py` to generate plots from processed CSV data.

```bash
# This script runs as a FastAPI service inside the Docker container
# Access via HTTP endpoints:
#   POST /tools/tiqu_plot       - Generate optimal pitch plots
#   POST /tools/optimal_pitch_extractor - Extract and plot optimal pitch
#   POST /tools/airfoil_distribution    - Generate 3D airfoil plot
#   POST /tools/twist_evolution         - Generate 3D twist evolution plot
```

**Visualization outputs:**
- **Optimal pitch vs Yaw plot** (`*_optimal_pitch.png`): Shows optimal pitch angle as function of yaw angle with theoretical line (Pitch = 90 - |Yaw|)
- **Comparison plot** (`tiqu_comparison_*.png`): 2x2 grid comparing Typhoon V40, V60, Earthquake 1g, 2g
- **Background stress heatmap**: Max stress visualization with optimal pitch overlay
- **3D airfoil distribution**: IEA 10MW RWT blade airfoil sections
- **3D twist evolution**: Aerodynamic twist along blade span

---

## 📂 Output Structure

```
simulation_runs/
├── Typhoon_V40/                          # Typhoon 40m/s simulation results
│   ├── Typhoon_V40_Pitch0_Yaw-150/       # Individual case folder
│   │   ├── 10MW_V40.00_P0.0_Y-150.0_taifeng.out  # OpenFAST output file
│   │   └── ...
│   ├── Typhoon_V40_Pitch0_Yaw-120/
│   │   └── ...
│   └── ... (84 case folders total)
├── Typhoon_V60/                          # Typhoon 60m/s simulation results (84 cases)
├── Earthquake_1g/                        # Earthquake 1g simulation results (84 cases)
├── Earthquake_2g/                        # Earthquake 2g simulation results (84 cases)
└── result_reference_values/
    └── pipeline_output/
        ├── Typhoon_V40_stressv2_*.csv    # Post-processed stress data
        ├── Typhoon_V40_tiqu_*.csv        # Optimal pitch configuration
        ├── Typhoon_V60_stressv2_*.csv
        ├── Typhoon_V60_tiqu_*.csv
        ├── Earthquake_1g_stressv2_*.csv
        ├── Earthquake_1g_tiqu_*.csv
        ├── Earthquake_2g_stressv2_*.csv
        └── Earthquake_2g_tiqu_*.csv
```

### Output File Descriptions

| Output Type | File Pattern | Description |
|-------------|--------------|-------------|
| Raw simulation | `*_taifeng.out` | OpenFAST typhoon output: Time, WindVxi, RotSpeed, BldPitch, TwrBsFxt, TwrBsFyt, TwrBsFzt, TwrBsMxt, TwrBsMyt, TwrBsMzt, etc. |
| Raw simulation | `*_dizhen.out` | OpenFAST earthquake output (seismic simulation) |
| Post-processed stress | `*_stressv2_*.csv` | CSV: FileName, V_hub_ms, Pitch_deg, Yaw_deg, MaxStress_MPa, Time_at_Max_s |
| Optimal pitch | `*_tiqu_*.csv` | CSV: Yaw_deg, Pitch_V3_00, MinStress_V3_00, ... (per wind speed) |
| Visualization | `*.png` | Optimal pitch curves, comparison plots, 3D visualizations |

---

## 📊 Data Processing Pipeline

```
┌─────────────────────────┐
│    single_simulation    │  Run single case (interactive, ~5-15 min)
│    or                   │
│    batch_simulation     │  Run all 336 cases (~48 hours)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│    simulation_runs/     │  Raw .out files (73 GB total)
│    (Typhoon_*,          │
│     Earthquake_*)       │  84 case folders per case type
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   process_results.py    │  Extract max stress, generate CSV
│                         │  - stressv2: MaxStress per case
│                         │  - tiqu: Optimal pitch per yaw
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   *_stressv2_*.csv      │  84 records per case type
│   *_tiqu_*.csv          │  12 records per case type
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   visualization.py      │  Generate plots
│   (FastAPI endpoints)   │  - Optimal pitch curves
│                         │  - Comparison plots (2x2)
│                         │  - Stress heatmaps
└─────────────────────────┘
```

---

## ❓ FAQ

**Q: Docker is not running?**
> Please start Docker Desktop first, then run the scripts.

**Q: Image load failed?**
> Verify that any `.tar.gz` file is in the same directory as the scripts. The script automatically searches for any `.tar.gz` file using multiple strategies (case-insensitive, fallback to directory listing). Ensure the file is not corrupted.

**Q: Port is already in use?**
> Scripts use port 8005 (batch) and 8006 (interactive/single) by default. Ensure these ports are not occupied by other programs. You can check with: `netstat -an | grep 800`

**Q: Batch simulation was interrupted?**
> Simulation results are saved incrementally to `simulation_runs/`. Re-running the script will resume from where it left off without re-running completed cases.

**Q: What does the .out file contain?**
> Each `.out` file contains time-series data from OpenFAST simulation including:
> - Time, wind speed, rotor speed, blade pitch
> - Tower base forces (Fx, Fy, Fz) and moments (Mx, My, Mz)
> - Nacelle position, yaw error, generator torque, etc.

**Q: Can I rename the Docker image file?**
> Yes! The scripts automatically detect any `.tar.gz` file in the directory regardless of filename. Just make sure it ends with `.tar.gz`.

**Q: How does the image auto-tagging work?**
> After loading a `.tar.gz` image, the script automatically finds any `zwind-reproduce` image and tags it as `zwind-reproduce:v4` if needed. This handles cases where the image has a different tag (e.g., `latest` or `v5`).

---

## 📚 Distribution Checklist

When sharing this project with others, please provide:

- `single_simulation.py` (interactive simulation script)
- `batch_simulation.py` (batch simulation script)
- `process_results.py` (post-processing script)
- `visualization.py` (visualization script)
- **Docker image download link** (provide the link only; user downloads ~500 MB)
- **Complete dataset download link** (optional, for users who prefer not to run simulations themselves, ~73 GB)

> Note: The Docker image (`.tar.gz`) is large (~500 MB); it is recommended to provide only the download link. The `.py` files are small and can be distributed directly via email or cloud drive.

---

## 🔑 Key Simulation Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| Wind Speed | 40, 60 m/s | Typhoon wind speeds |
| Acceleration | 9.81, 19.62, 39.24 m/s² | Earthquake intensities (1g, 2g, 4g) |
| Pitch Angle | 0°, 15°, 30°, 45°, 60°, 75°, 90° | Blade pitch angle |
| Yaw Angle | -150° to 180° (12 values) | Nacelle yaw error |

**Total combinations per case type:**
- 7 pitch angles × 12 yaw angles = **84 cases per case type**
- 4 case types × 84 cases = **336 total cases**

**Stress calculation (von Mises):**
```
σ_total = sqrt(σ₀² + 3·τ₀²) × 1e-3  [MPa]
where:
  σ₀ = |sqrt(Mx² + My²) / W_n| + |Fz / A|
  τ₀ = |Mz / W_p|
  W_n = (π·D³/32) × (1 - ((D-2t)/D)⁴)
  W_p = 2 × W_n
  A = π·(D·t - t²)
  D = 8.3 m (tower diameter)
  t = 0.07 m (tower thickness)
```

**Truncation rule:** Values ≥ 355 MPa (material yield strength) are truncated to 355 MPa.

---

Contact the project maintainer for further questions.
