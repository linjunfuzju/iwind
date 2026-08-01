#!/usr/bin/env python3
"""
Post-processing script: Process .out files from four subfolders

Processing steps:
1. stressv2: Extract max stress from each .out file, generate CSV
   - Data greater than 355MPa or NaN is changed to 355
2. tiqu: Extract optimal pitch configuration from stressv2 CSV

Usage:
    python3 process_results.py
"""

import os
import re
import math
import csv
import json
import glob
from datetime import datetime
import threading
import signal
import sys

# ============================================================================
# Constants
# ============================================================================

# Get project root directory
_CURRENT_FILE = os.path.abspath(__file__)
_MODIFIED_OPENFAST_DIR = os.path.dirname(_CURRENT_FILE)  # deep_agent/.../servers/zwind
PROJECT_ROOT = os.path.dirname(os.path.dirname(_MODIFIED_OPENFAST_DIR))  # deep_agent

# Tower geometry parameters
TOWER_DIAM_M = 8.3
TOWER_THICK_M = 0.07

# Data truncation threshold
STRESS_THRESHOLD = 355.0

# Base directory (relative to PROJECT_ROOT)
BASE_DIR = os.path.join(PROJECT_ROOT, "simulation_runs")

# Source data folder (batch run timestamp folder, specified via env var or parameter)
SOURCE_DIR = os.environ.get("PROCESS_SOURCE_DIR", os.path.join(BASE_DIR, "20260504_142408"))

# Output directory (overridden via env var PROCESS_OUTPUT_DIR)
OUTPUT_DIR = os.environ.get("PROCESS_OUTPUT_DIR", os.path.join(BASE_DIR, "result_reference_values", "pipeline_output"))

# Four subfolders (overridden via env var PROCESS_SUB_FOLDERS)
_DEFAULT_SUB_FOLDERS = [
    "Earthquake_4g"
]
_env_sub_folders = os.environ.get("PROCESS_SUB_FOLDERS", "")
if _env_sub_folders:
    SUB_FOLDERS = _env_sub_folders.split(",")
else:
    SUB_FOLDERS = _DEFAULT_SUB_FOLDERS

# Failed case records (loaded from batch_results.json)
FAILED_CASES = {}
# Format: {"Typhoon_V40_0_0": {"runtime_seconds": 200}, "Earthquake_9.81_0_0": {"runtime_seconds": 150}}

# Print lock
print_lock = threading.Lock()


# ============================================================================
# Failed case record loading
# ============================================================================

def load_failed_cases():
    """
    Load failed cases from batch_results.json

    Note: Some cases failed to execute and did not generate .out files.
    These cases should be marked as MaxStress=355, Time_at_Max=actual runtime in CSV.
    """
    global FAILED_CASES
    batch_result_files = glob.glob(os.path.join(SOURCE_DIR, "batch_results_*.json"))
    if not batch_result_files:
        print(f"[INFO] batch_results.json not found, skipping failed case loading")
        return

    latest_batch_result = sorted(batch_result_files)[-1]
    print(f"[INFO] Loading failed cases from {os.path.basename(latest_batch_result)}")

    try:
        with open(latest_batch_result, 'r', encoding='utf-8') as f:
            batch_data = json.load(f)

        failed_count = 0
        for item in batch_data:
            if item.get("status") == "failed":
                case = item.get("case", {})
                case_type = case.get("type", "unknown")
                # Get runtime (used to set Time_at_Max)
                runtime_seconds = item.get("runtime_seconds", 0)
                if case_type == "typhoon":
                    key = f"Typhoon_V{case.get('wind_speed')}_{case.get('pitch')}_{case.get('yaw')}"
                else:
                    key = f"Earthquake_{case.get('accel')}_{case.get('pitch')}_{case.get('yaw')}"
                FAILED_CASES[key] = {"runtime_seconds": runtime_seconds}
                failed_count += 1

        print(f"[INFO] {failed_count} cases failed to execute, will be marked as MaxStress=355, Time_at_Max=runtime")
    except Exception as e:
        print(f"[WARNING] Failed to load failed case records: {str(e)}")


def get_case_failed_info(folder_name, filename):
    """
    Check if a case failed to execute (no .out file)

    For earthquake cases, extract actual pitch and yaw from folder name
    For typhoon cases, extract parameters from filename

    Returns:
        dict: {"is_failed": bool, "runtime_seconds": float}
    """
    result = {"is_failed": False, "runtime_seconds": 0}

    if not FAILED_CASES:
        return result

    # Earthquake mode: check if case corresponding to folder name failed
    if folder_name.startswith("Earthquake"):
        folder_params = parse_earthquake_folder_name(folder_name)
        if folder_params:
            key = f"Earthquake_9.81_{int(folder_params['Pitch'])}_{int(folder_params['Yaw'])}"
            if key in FAILED_CASES:
                result["is_failed"] = True
                result["runtime_seconds"] = FAILED_CASES[key].get("runtime_seconds", 0)
                return result

    # Typhoon mode: check from filename
    typhoon_pattern = r'10MW_V(\d+)\.00_P(\d+)\.0_Y(-?\d+)\.0_taifeng\.out'
    match = re.match(typhoon_pattern, filename)
    if match:
        wind_speed = int(match.group(1))
        pitch = int(match.group(2))
        yaw = int(match.group(3))
        key = f"Typhoon_V{wind_speed}_{pitch}_{yaw}"
        if key in FAILED_CASES:
            result["is_failed"] = True
            result["runtime_seconds"] = FAILED_CASES[key].get("runtime_seconds", 0)
            return result

    return result


def is_case_failed(folder_name, filename):
    """Backward compatible interface"""
    return get_case_failed_info(folder_name, filename)["is_failed"]


# ============================================================================
# Signal handling
# ============================================================================

def signal_handler(signum, frame):
    with print_lock:
        print("\n[STOP] Interrupt signal received, stopping...")
    sys.exit(0)


# ============================================================================
# Stress calculation
# ============================================================================

def calculate_stress(Fx, Fy, Fz, Mx, My, Mz):
    """Calculate tower base stress (von Mises)"""
    D = TOWER_DIAM_M
    t = TOWER_THICK_M

    W_n = (math.pi * D**3 / 32) * (1 - ((D - 2*t) / D)**4)
    W_p = 2 * W_n
    A = math.pi * (D * t - t**2)

    sigma_0 = abs(math.sqrt(Mx**2 + My**2) / W_n) + abs(Fz / A)
    tau_0 = abs(Mz / W_p)
    sigma_total = math.sqrt(sigma_0**2 + 3 * tau_0**2) * 1e-3  # MPa

    # Truncation
    if math.isnan(sigma_total) or sigma_total > STRESS_THRESHOLD:
        sigma_total = STRESS_THRESHOLD

    return sigma_total


# ============================================================================
# Parse .out files
# ============================================================================

def parse_out_file(file_path):
    """
    Parse .out file, extract tower base load data

    Returns:
        dict: {
            'time': [...],
            'Fx': [...],
            'Fy': [...],
            'Fz': [...],
            'Mx': [...],
            'My': [...],
            'Mz': [...]
        }
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Find header row
        header_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('Time'):
                header_idx = i
                break

        if header_idx is None:
            raise ValueError(f"Cannot find data header row: {file_path}")

        # Parse header
        header = lines[header_idx].strip().split()
        cols = {v: i for i, v in enumerate(header)}

        # Check required columns
        required_cols = ['Time', 'TwrBsFxt', 'TwrBsFyt', 'TwrBsFzt', 'TwrBsMxt', 'TwrBsMyt', 'TwrBsMzt']
        for col in required_cols:
            if col not in cols:
                raise ValueError(f"Missing required column: {col}")

        # Skip unit row
        data_start_idx = header_idx + 1

        # Extract data
        data = {
            'time': [],
            'Fx': [], 'Fy': [], 'Fz': [],
            'Mx': [], 'My': [], 'Mz': []
        }

        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < len(header):
                continue
            try:
                data['time'].append(float(parts[cols['Time']]))
                data['Fx'].append(float(parts[cols['TwrBsFxt']]))
                data['Fy'].append(float(parts[cols['TwrBsFyt']]))
                data['Fz'].append(float(parts[cols['TwrBsFzt']]))
                data['Mx'].append(float(parts[cols['TwrBsMxt']]))
                data['My'].append(float(parts[cols['TwrBsMyt']]))
                data['Mz'].append(float(parts[cols['TwrBsMzt']]))
            except (ValueError, IndexError):
                continue

        return data

    except Exception as e:
        raise Exception(f"File parsing failed: {str(e)}")


def find_max_stress(file_path):
    """Extract max stress from .out file"""
    data = parse_out_file(file_path)

    if not data['time']:
        raise ValueError(f"No valid data: {file_path}")

    max_stress = 0
    max_time = 0

    for i in range(len(data['time'])):
        stress = calculate_stress(
            data['Fx'][i], data['Fy'][i], data['Fz'][i],
            data['Mx'][i], data['My'][i], data['Mz'][i]
        )
        if stress > max_stress:
            max_stress = stress
            max_time = data['time'][i]

    return max_stress, max_time


# ============================================================================
# Parse filenames
# ============================================================================

def parse_out_filename(filename):
    """
    Parse .out filename, extract parameters

    Typhoon: 10MW_V60.00_P15.0_Y0.0_taifeng.out
    Earthquake: 10MW_V3.00_P15.0_Y0.0_dizhen.out

    Returns:
        dict: {'V': float, 'Pitch': float, 'Yaw': float, 'State': str}
    """
    # Typhoon mode: 10MW_V{wind_speed}_P{pitch}_Y{yaw}_taifeng.out
    typhoon_pattern = r'10MW_V([\d.]+)_P([-\d.]+)_Y([-\d.]+)_taifeng\.out'
    match = re.match(typhoon_pattern, filename)
    if match:
        return {
            'V': float(match.group(1)),
            'Pitch': float(match.group(2)),
            'Yaw': float(match.group(3)),
            'State': 'Idle'
        }

    # Earthquake mode: 10MW_V3.00_P{pitch}_Y{yaw}_dizhen.out
    # Note: P and Y in earthquake .out filename are placeholders 0, real values from parent folder name
    earthquake_pattern = r'10MW_V([\d.]+)_P([-\d.]+)_Y([-\d.]+)_dizhen\.out'
    match = re.match(earthquake_pattern, filename)
    if match:
        return {
            'V': float(match.group(1)),
            'Pitch': float(match.group(2)),  # Placeholder, get real value from folder name
            'Yaw': float(match.group(3)),    # Placeholder, get real value from folder name
            'State': 'Operation'
        }

    raise ValueError(f"Cannot parse filename: {filename}")


def parse_earthquake_folder_name(folder_name):
    """
    Parse actual pitch and yaw from earthquake folder name

    Folder format: Earthquake_g1_Pitch15_Yaw120
                   Earthquake_g2_Pitch45_Yaw-30

    Returns:
        dict: {'Pitch': float, 'Yaw': float}
    """
    pattern = r'Earthquake_g\d+_Pitch(\d+)_Yaw(-?\d+)'
    match = re.search(pattern, folder_name)
    if match:
        return {
            'Pitch': float(match.group(1)),
            'Yaw': float(match.group(2))
        }
    return None


def parse_typhoon_folder_name(folder_name):
    """
    Parse actual V, Pitch and Yaw from typhoon folder name

    Folder format: Typhoon_V40_Pitch0_Yaw-120
                   Typhoon_V60_Pitch15_Yaw30

    Returns:
        dict: {'V': float, 'Pitch': float, 'Yaw': float}
    """
    pattern = r'Typhoon_V(\d+)_Pitch(\d+)_Yaw(-?\d+)'
    match = re.search(pattern, folder_name)
    if match:
        return {
            'V': float(match.group(1)),
            'Pitch': float(match.group(2)),
            'Yaw': float(match.group(3))
        }
    return None


# ============================================================================
# stressv2 processing
# ============================================================================

def get_expected_cases(folder_name):
    """
    Get expected case list

    Returns:
        dict: {case_key: {"pitch": int, "yaw": int, "V": int/float}, ...}
    """
    cases = {}
    if folder_name.startswith("Earthquake"):
        accel = 9.81 if "1g" in folder_name else 19.62
        for pitch in [0, 15, 30, 45, 60, 75, 90]:
            for yaw in [-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150, 180]:
                key = f"Earthquake_{accel}_{pitch}_{yaw}"
                cases[key] = {"accel": accel, "pitch": pitch, "yaw": yaw, "V": 3.0}
    elif folder_name.startswith("Typhoon"):
        wind_speed = 40 if "V40" in folder_name else 60
        for pitch in [0, 15, 30, 45, 60, 75, 90]:
            for yaw in [-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150, 180]:
                key = f"Typhoon_V{wind_speed}_{pitch}_{yaw}"
                cases[key] = {"V": float(wind_speed), "pitch": pitch, "yaw": yaw}
    return cases


def process_stressv2(folder_path, folder_name):
    """
    Process stressv2: Iterate all .out files, extract max stress

    Stress processing rules:
    - Values >= 355 MPa -> Set to 355 MPa (material yield strength upper limit)
    - Failed cases (no .out file) -> MaxStress=355, Time_at_Max=actual runtime

    Returns:
        list: [{'filename': str, 'V': float, 'Pitch': float, 'Yaw': float,
                'MaxStress': float, 'Time_at_Max': float}, ...]
    """
    print("[INFO] Step 1: stressv2 - Extract max stress from each .out file")
    print("       - Stress values >= 355 MPa -> Truncated to 355 MPa (material yield strength limit)")
    print("       - Failed cases (no .out file) -> MaxStress=355, Time_at_Max=actual runtime")

    results = []

    # Get expected cases
    expected_cases = get_expected_cases(folder_name)

    # Search .out files - supports two structures:
    # 1. simulation_runs/{timestamp}/{case_type}/*.out (old structure)
    # 2. simulation_runs/{timestamp}/{case_type}/{session_name}/*.out (current structure)
    out_files = glob.glob(os.path.join(folder_path, "**", "*.out"), recursive=True)
    if not out_files:
        # Compatibility: try direct search under folder_path
        out_files = glob.glob(os.path.join(folder_path, "*.out"))

    with print_lock:
        print(f"  [stressv2] Found {len(out_files)} .out files")

    # Build processed case key set
    processed_keys = set()

    # Iterate .out files, extract data
    for file_path in out_files:
        filename = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, folder_path)
        parts = rel_path.split(os.sep)
        sub_folder_name = parts[0] if len(parts) > 1 else ""

        try:
            params = parse_out_filename(filename)

            # Earthquake mode: extract pitch and yaw from subfolder name
            if sub_folder_name.startswith("Earthquake"):
                folder_params = parse_earthquake_folder_name(sub_folder_name)
                if folder_params:
                    params['Pitch'] = folder_params['Pitch']
                    params['Yaw'] = folder_params['Yaw']
                    params['V'] = 3.0  # Earthquake fixed wind speed

            # Typhoon mode: extract V, Pitch and Yaw from subfolder name
            if sub_folder_name.startswith("Typhoon"):
                folder_params = parse_typhoon_folder_name(sub_folder_name)
                if folder_params:
                    params['V'] = folder_params['V']
                    params['Pitch'] = folder_params['Pitch']
                    params['Yaw'] = folder_params['Yaw']

            # Build case key for deduplication
            case_key = f"{folder_name}_{params['Pitch']}_{params['Yaw']}"
            if case_key in processed_keys:
                continue
            processed_keys.add(case_key)

            max_stress, time_at_max = find_max_stress(file_path)

            # Stress truncation: >=355 or NaN -> 355
            original_stress = max_stress
            if math.isnan(max_stress) or max_stress >= STRESS_THRESHOLD:
                max_stress = STRESS_THRESHOLD
                if math.isnan(original_stress):
                    reason = "NaN value"
                else:
                    reason = f">={STRESS_THRESHOLD} MPa"
                with print_lock:
                    print(f"    [TRUNCATED] {filename}: {original_stress:.2f} MPa -> {reason} -> {max_stress:.2f} MPa")

            results.append({
                'FileName': filename,
                'V_hub_ms': params['V'],
                'Pitch_deg': params['Pitch'],
                'Yaw_deg': params['Yaw'],
                'MaxStress_MPa': max_stress,
                'Time_at_Max_s': time_at_max
            })
            with print_lock:
                print(f"    Processed: {filename} -> {max_stress:.2f} MPa")
        except Exception as e:
            with print_lock:
                print(f"    Skipped: {filename} ({str(e)})")
            continue

    # Handle failed cases (no .out file but has folder)
    failed_with_folder = []
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if not os.path.isdir(item_path):
                continue
            # Check if it's a case folder
            if folder_name.startswith("Earthquake"):
                folder_params = parse_earthquake_folder_name(item)
                if not folder_params:
                    continue
                pitch = int(folder_params['Pitch'])
                yaw = int(folder_params['Yaw'])
                case_key = f"Earthquake_{9.81}_{pitch}_{yaw}"
                if case_key in FAILED_CASES and case_key not in processed_keys:
                    runtime_seconds = FAILED_CASES[case_key].get("runtime_seconds", 0)
                    failed_with_folder.append({
                        'FileName': f"{item}.out",
                        'V_hub_ms': 3.0,
                        'Pitch_deg': pitch,
                        'Yaw_deg': yaw,
                        'MaxStress_MPa': STRESS_THRESHOLD,
                        'Time_at_Max_s': runtime_seconds
                    })
                    processed_keys.add(case_key)
                    with print_lock:
                        print(f"    [FAILED] {item}: MaxStress=355, Time_at_Max={runtime_seconds}s")
            elif folder_name.startswith("Typhoon"):
                folder_params = parse_typhoon_folder_name(item)
                if not folder_params:
                    continue
                V = folder_params['V']
                pitch = int(folder_params['Pitch'])
                yaw = int(folder_params['Yaw'])
                case_key = f"Typhoon_V{int(V)}_{pitch}_{yaw}"
                if case_key in FAILED_CASES and case_key not in processed_keys:
                    runtime_seconds = FAILED_CASES[case_key].get("runtime_seconds", 0)
                    failed_with_folder.append({
                        'FileName': f"{item}.out",
                        'V_hub_ms': V,
                        'Pitch_deg': pitch,
                        'Yaw_deg': yaw,
                        'MaxStress_MPa': STRESS_THRESHOLD,
                        'Time_at_Max_s': runtime_seconds
                    })
                    processed_keys.add(case_key)
                    with print_lock:
                        print(f"    [FAILED] {item}: MaxStress=355, Time_at_Max={runtime_seconds}s")
    except Exception as e:
        with print_lock:
            print(f"    [WARNING] Error checking failed cases: {str(e)}")

    results.extend(failed_with_folder)

    # Statistics
    missing_count = len(expected_cases) - len(processed_keys)
    if missing_count > 0:
        with print_lock:
            print(f"  [INFO] {missing_count} cases missing (no folder)")

    return results


def save_stressv2_csv(results, folder_name):
    """
    Save stressv2 CSV file

    Note:
    - Valid data: stress values truncated to 355
    - Failed cases (no .out file but has folder): MaxStress=355, Time_at_Max=actual runtime
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{folder_name}_stressv2_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print("[INFO] Step 1.1: Save stressv2 CSV")
    print(f"       - Output file: {filename}")
    print(f"       - Total records: {len(results)}")

    # Sort by V, Pitch, Yaw
    results.sort(key=lambda x: (x['V_hub_ms'], x['Pitch_deg'], x['Yaw_deg']))

    # Count failed cases (Time_at_Max < normal simulation time indicates interruption)
    # Normal earthquake simulation TMax=300s, typhoon TMax=1500s
    failed_count = sum(1 for r in results if r['Time_at_Max_s'] < 200)
    if failed_count > 0:
        print(f"       - Completed normally: {len(results) - failed_count}")
        print(f"       - Interrupted/failed: {failed_count} (MaxStress=355)")

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['FileName', 'V_hub_ms', 'Pitch_deg', 'Yaw_deg', 'MaxStress_MPa', 'Time_at_Max_s'])
        writer.writeheader()
        writer.writerows(results)

    return filepath


# ============================================================================
# tiqu processing
# ============================================================================

def process_tiqu(stressv2_results, folder_name):
    """
    Process tiqu: Extract optimal pitch configuration from stressv2 results

    Note:
    - Group by yaw angle, find pitch angle corresponding to minimum stress for each yaw
    - NaN values are ignored (find optimal from valid data)
    - If all data for a yaw angle is NaN, that row will be all NaN

    Returns:
        list: [{'Yaw_deg': float, 'Pitch_Vx_xx': float, 'MinStress_Vx_xx': float}, ...]
    """
    print("[INFO] Step 2: tiqu - Extract optimal pitch configuration from stressv2 results")
    print("       - Group by yaw angle, find pitch angle with minimum stress for each yaw")
    print("       - NaN values are ignored, find optimal only from valid data")

    # Group by yaw angle
    yaw_groups = {}
    for r in stressv2_results:
        yaw = r['Yaw_deg']
        if yaw not in yaw_groups:
            yaw_groups[yaw] = []
        yaw_groups[yaw].append(r)

    # Get all unique yaw angles
    all_yaws = sorted(yaw_groups.keys())

    # Get all unique V values (wind speed)
    all_v_values = sorted(set(r['V_hub_ms'] for r in stressv2_results))

    print(f"       - Yaw angle range: {all_yaws[0]}deg ~ {all_yaws[-1]}deg (total {len(all_yaws)})")
    print(f"       - Wind speed values: {all_v_values}")

    # Build tiqu results
    tiqu_results = []
    for yaw in all_yaws:
        row = {'Yaw_deg': yaw}
        for V in all_v_values:
            # Find pitch angle corresponding to minimum stress for this yaw and wind speed
            candidates = [r for r in yaw_groups[yaw] if abs(r['V_hub_ms'] - V) < 0.01]
            # Filter out NaN values
            valid_candidates = [c for c in candidates if not math.isnan(c['MaxStress_MPa'])]
            if valid_candidates:
                best = min(valid_candidates, key=lambda x: x['MaxStress_MPa'])
                pitch_var = f"Pitch_V{V:.2f}".replace('.', '_')
                stress_var = f"MinStress_V{V:.2f}".replace('.', '_')
                row[pitch_var] = best['Pitch_deg']
                row[stress_var] = best['MaxStress_MPa']
            # If no valid data, corresponding columns won't be in row (remain NaN)
        tiqu_results.append(row)

    return tiqu_results


def save_tiqu_csv(tiqu_results, folder_name):
    """Save tiqu CSV file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{folder_name}_tiqu_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        if tiqu_results:
            writer = csv.DictWriter(f, fieldnames=tiqu_results[0].keys())
            writer.writeheader()
            writer.writerows(tiqu_results)

    return filepath


# ============================================================================
# Main processing function
# ============================================================================

def process_folder(folder_name):
    """Process single subfolder"""
    # Use SOURCE_DIR as source data path
    folder_path = os.path.join(SOURCE_DIR, folder_name)

    if not os.path.exists(folder_path):
        with print_lock:
            print(f"[SKIP] Folder does not exist: {folder_path}")
        return None

    with print_lock:
        print(f"\n{'='*60}")
        print(f"Processing folder: {folder_name}")
        print(f"{'='*60}")

    # 1. stressv2 processing
    with print_lock:
        print(f"[1/2] Executing stressv2 processing...")
    stressv2_results = process_stressv2(folder_path, folder_name)

    if not stressv2_results:
        with print_lock:
            print(f"[WARNING] No data processed: {folder_name}")
        return None

    stressv2_file = save_stressv2_csv(stressv2_results, folder_name)
    with print_lock:
        print(f"  [DONE] stressv2 CSV: {stressv2_file}")

    # 2. tiqu processing
    with print_lock:
        print(f"[2/2] Executing tiqu processing...")
    tiqu_results = process_tiqu(stressv2_results, folder_name)
    tiqu_file = save_tiqu_csv(tiqu_results, folder_name)
    with print_lock:
        print(f"  [DONE] tiqu CSV: {tiqu_file}")

    return {
        'folder': folder_name,
        'stressv2_file': stressv2_file,
        'stressv2_count': len(stressv2_results),
        'tiqu_file': tiqu_file,
        'tiqu_count': len(tiqu_results)
    }


def main():
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("Post-processing script: Generate stressv2 and tiqu CSV")
    print("=" * 60)

    # Load failed case records
    load_failed_cases()

    results = []

    for folder in SUB_FOLDERS:
        print("\n" + "=" * 60)
        print(f"[START] Processing folder: {folder}")
        print("=" * 60)
        result = process_folder(folder)
        if result:
            results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)
    for r in results:
        print(f"\n{r['folder']}:")
        print(f"  - stressv2: {r['stressv2_file']} ({r['stressv2_count']} records)")
        print(f"  - tiqu: {r['tiqu_file']} ({r['tiqu_count']} records)")

    print("\n" + "=" * 60)
    print("[INFO] Visualization notes:")
    print("       - NaN values in stressv2 CSV will display as 355 MPa during visualization")
    print("       - NaN values in tiqu CSV indicate no valid data for that yaw angle")
    print("=" * 60)


if __name__ == "__main__":
    main()
