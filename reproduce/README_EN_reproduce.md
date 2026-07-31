# ZWind Wind Turbine Simulation Reproduction Manual

> This project reproduces all 336 simulation cases from the paper **IWind: IEA 10MW Offshore Wind Turbine Extreme Loading Dataset**.

---

## ⚠️ Before You Start — Please Confirm Both Points

1. **Time cost**: Full batch simulation (336 cases) takes approximately **48 hours**. Ensure your machine can run for an extended period.
2. **Storage space**: Complete simulation results require approximately **73 GB** of disk space. Ensure you have sufficient space before starting.

---

## 📦 File Overview

The following files should be present in this directory:

| File | Description |
|------|-------------|
| `run_simulation.py` | Batch simulation script (fully automated execution of 336 cases) |
| `zwind_llm.py` | Interactive simulation script (single simulation via natural language), can be packaged as EXE for distribution |
| `zwind_reproduce_v5.tar.gz` | **Docker image** (to be downloaded, ~500 MB), contains simulation environment and API service |

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
https://download.scidb.cn/download?fileId=91c538bf6a6beae43dd3fa7f45a276c9&path=/V1/zwind_reproduce_v5.tar.gz&username=linjunfu@zju.edu.cn&fileName=zwind_reproduce_v5.tar.gz
```

After downloading, ensure the filename remains **`zwind_reproduce_v5.tar.gz`**, then place it in the same directory as `run_simulation.py` and `zwind_llm.py`. The script will automatically load the image.

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

### Method 1: Single Interactive Simulation (Recommended for New Users)

Use `zwind_llm.py` (or packaged `zwind_llm.exe`) to describe your simulation needs in natural language.

**Run with Python:**
```bash
python zwind_llm.py
```

**Run EXE:**
```bash
./zwind_llm.exe
```

Supported simulation parameters:
- **Typhoon**: Wind speed 40 / 60 m/s
- **Earthquake**: Acceleration 1g (9.81) / 2g (19.62) / 4g (39.24) m/s²
- **Pitch angle**: 0°, 15°, 30°, 45°, 60°, 75°, 90°
- **Yaw angle**: -150°, -120°, -90°, -60°, -30°, 0°, 30°, 60°, 90°, 120°, 150°, 180°

---

### Method 2: Full Batch Simulation (336 Cases)

Use `run_simulation.py` for fully automated **simulation → post-processing → visualization** pipeline.

```bash
python run_simulation.py
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
docker stop zwind-batch
python run_simulation.py  # Will resume from where it left off; completed cases will not be re-run
```

---

## 📂 Output Structure

```
simulation_runs/
├── Typhoon_V40/       # Typhoon 40m/s results
├── Typhoon_V60/       # Typhoon 60m/s results
├── Earthquake_1g/     # Earthquake 1g results
└── Earthquake_2g/     # Earthquake 2g results
```

Each case contains `.csv` time-series data and `.png` visualization images.

---

## ❓ FAQ

**Q: Docker is not running?**
> Please start Docker Desktop first, then run the scripts.

**Q: Image load failed?**
> Verify that `zwind_reproduce_v5.tar.gz` is in the same directory as the scripts and the filename has not been modified.

**Q: Port is already in use?**
> Scripts use port 8005 (batch) and 8006 (interactive) by default. Ensure these ports are not occupied by other programs.

**Q: Batch simulation was interrupted?**
> Simulation results are saved in `simulation_runs/`. Re-running the script will resume from the interruption point without re-running completed cases.

---

## 📚 Distribution Checklist

When sharing this project with others, please provide:

- `run_simulation.py` (batch simulation script)
- `zwind_llm.py` (interactive simulation script / EXE)
- **Docker image download link** (provide the link only; user downloads ~500 MB)
- **Complete dataset download link** (optional, for users who prefer not to run simulations themselves, ~73 GB)

> Note: `zwind_reproduce_v5.tar.gz` is large; it is recommended to provide only the download link. The `.py` files are small and can be distributed directly via email or cloud drive.

---

Contact the project maintainer for further questions.
