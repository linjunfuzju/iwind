from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import re
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator

router = APIRouter(prefix="/tools")

# Tower geometry parameters
TOWER_DIAM_M = 8.3
TOWER_THICK_M = 0.038


class OptimalPitchExtractorParams(BaseModel):
    csv_files: Optional[List[str]] = None
    csv_dir: Optional[str] = None
    output_plot: Optional[str] = "/app/plots/optimal_pitch.png"
    output_csv: Optional[str] = "/app/plots/optimal_pitch_origin.csv"


def generate_iea_airfoil(r: float, R_total: float, n_pts: int = 100):
    """Generate airfoil cross section coordinates for the IEA 10MW RWT blade."""
    if r <= 13.35:
        theta = np.linspace(np.pi, -np.pi, n_pts)
        x = 0.5 * np.cos(theta) + 0.25
        y = 0.5 * np.sin(theta)
    else:
        max_t = 0.50
        min_t = 0.211
        t = max_t - (max_t - min_t) * ((r - 13.35) / (R_total - 13.35)) ** 0.5
        x_half = np.linspace(0, 1, n_pts // 2)
        yt = 5 * t * (
            0.2969 * np.sqrt(x_half)
            - 0.1260 * x_half
            - 0.3516 * x_half ** 2
            + 0.2843 * x_half ** 3
            - 0.1015 * x_half ** 4
        )
        x = np.concatenate([x_half, x_half[::-1]])
        y = np.concatenate([yt, -yt[::-1]])
    return x, y


class TiquPlotParams(BaseModel):
    csv_files: Optional[List[str]] = None
    csv_dir: Optional[str] = None
    output_dir: Optional[str] = "/app/result_reference_values"


def plot_single_tiqu(csv_path: str, output_dir: str, dpi: int = 300) -> dict:
    """
    Generate visualization plot for a single tiqu CSV file.

    Following tiqu.m logic:
    - X-axis: Yaw Angle (deg), range -180 ~ 180
    - Y-axis: Best Pitch Angle (deg), range 0 ~ 90
    - Blue solid line: Optimal pitch angle vs yaw angle curve
    - Gray dashed line: Linear complementarity assumption (Pitch = 90 - |Yaw|)
    """
    try:
        df = pd.read_csv(csv_path)
        filename = os.path.splitext(os.path.basename(csv_path))[0]

        # Determine legend label (extracted from filename)
        # Filename format: Earthquake_1g_tiqu_YYYYMMDD_HHMMSS.csv or Typhoon_V40_tiqu.csv
        name_parts = filename.replace('_tiqu', '').split('_')
        if len(name_parts) >= 2:
            legend_label = f"{name_parts[0]}_{name_parts[1]}" if name_parts[0] in ['Earthquake', 'Typhoon'] else name_parts[0]
        else:
            legend_label = name_parts[0] if name_parts else filename

        fig, ax = plt.subplots(figsize=(10, 6))

        yaw_col = 'Yaw_deg'
        pitch_cols = [c for c in df.columns if c.startswith('Pitch_')]

        # Plot theoretical line Pitch = 90 - |Yaw|
        theoretical_yaw = np.arange(-180, 181, 10)
        theoretical_pitch = np.maximum(0, 90 - np.abs(theoretical_yaw))
        ax.plot(theoretical_yaw, theoretical_pitch, '--', color=[0.5, 0.5, 0.5],
                linewidth=2, label='Linear Complementarity (Pitch = 90 - |Yaw|)')

        # Plot optimal pitch angle curve
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        for idx, pitch_col in enumerate(pitch_cols):
            v_label = pitch_col.replace('Pitch_', 'V=').replace('_', '.')
            ax.plot(df[yaw_col], df[pitch_col], '-o', linewidth=2, markersize=6,
                    color=colors[idx % len(colors)],
                    label=f'Optimal Pitch {v_label}')

        ax.set_xlabel('Yaw Angle (deg)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Best Pitch Angle (deg)', fontsize=12, fontweight='bold')
        ax.set_title(f'{legend_label} - Optimal Pitch vs Yaw', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([-180, 180])
        ax.set_ylim([0, 95])
        ax.set_xticks(np.arange(-180, 181, 30))
        ax.set_yticks(np.arange(0, 91, 15))

        output_path = os.path.join(output_dir, f"{filename}.png")
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(output_path, dpi=dpi)
        plt.close(fig)

        return {"status": "success", "plot_path": output_path, "csv_path": csv_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def plot_comparison_tiqu(csv_files: List[str], output_dir: str, dpi: int = 300) -> dict:
    """
    Generate comparison plot for multiple tiqu CSV files (2x2 grid layout).

    Generates simultaneously:
    1. Overview: tiqu_comparison.png (2x2 layout)
    2. Sub-plots: named by case, e.g. "Earthquake_1g - Optimal_Pitch_by_Yaw.png"

    Layout:
    - Row 1: Typhoon data - Left: V40, Right: V60
    - Row 2: Earthquake data - Left: 1g, Right: 2g

    Each subplot:
    - X-axis: Yaw Angle (deg), range -180 ~ 180
    - Y-axis: Best Pitch Angle (deg), range 0 ~ 90
    - Blue solid line: Optimal pitch angle vs yaw angle curve
    - Gray dashed line: Linear complementarity assumption (Pitch = 90 - |Yaw|)
    """
    try:
        # Classification
        earthquake_files = []
        typhoon_v40_files = []
        typhoon_v60_files = []

        for csv_path in csv_files:
            if not os.path.exists(csv_path):
                continue
            filename = os.path.basename(csv_path).lower()
            if 'earthquake' in filename:
                earthquake_files.append(csv_path)
            elif 'typhoon' in filename:
                if 'v40' in filename or 'v4_0' in filename:
                    typhoon_v40_files.append(csv_path)
                elif 'v60' in filename or 'v6_0' in filename:
                    typhoon_v60_files.append(csv_path)

        # Determine layout
        n_cols = 2
        n_rows = 2

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 10))

        def get_case_name(filename):
            """Extract case name from filename, e.g. Earthquake_1g"""
            name = os.path.basename(filename)
            name = name.replace('_tiqu.csv', '').replace('_tiqu_', '_')
            # Remove timestamp
            import re
            name = re.sub(r'_\d{8}_\d{6}', '', name)
            return name

        def plot_single_subax(df, ax, title):
            """Plot single sub-axis"""
            # Theoretical line Pitch = 90 - |Yaw|
            theoretical_yaw = np.arange(-180, 181, 10)
            theoretical_pitch = np.maximum(0, 90 - np.abs(theoretical_yaw))
            ax.plot(theoretical_yaw, theoretical_pitch, '--', color=[0.5, 0.5, 0.5],
                    linewidth=2, label='Linear Complementarity (Pitch = 90 - |Yaw|)')

            # Optimal pitch angle curve
            pitch_cols = [c for c in df.columns if c.startswith('Pitch_')]
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            for idx, pitch_col in enumerate(pitch_cols):
                ax.plot(df['Yaw_deg'], df[pitch_col], '-o', linewidth=2, markersize=5,
                        color=colors[idx % len(colors)],
                        label=f'Optimal Pitch {pitch_col.replace("Pitch_", "V=").replace("_", ".")}')

            ax.set_xlabel('Yaw Angle (deg)', fontsize=10)
            ax.set_ylabel('Best Pitch Angle (deg)', fontsize=10)
            ax.set_title(title, fontsize=11, fontweight='bold')
            ax.legend(loc='best', fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_xlim([-180, 180])
            ax.set_ylim([0, 95])
            ax.set_xticks(np.arange(-180, 181, 60))
            ax.set_yticks(np.arange(0, 91, 15))

        def plot_single_case(df, case_name, output_dir):
            """Generate subplot for single case"""
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_single_subax(df, ax, case_name)
            output_path = os.path.join(output_dir, f"{case_name} - Optimal_Pitch_by_Yaw.png")
            fig.savefig(output_path, dpi=dpi)
            plt.close(fig)
            return output_path

        # Generate individual subplots first
        all_output_files = []

        # Typhoon subplots
        if typhoon_v40_files:
            df = pd.read_csv(typhoon_v40_files[0])
            case_name = get_case_name(typhoon_v40_files[0])
            output_path = plot_single_case(df, case_name, output_dir)
            all_output_files.append(output_path)

        if typhoon_v60_files:
            df = pd.read_csv(typhoon_v60_files[0])
            case_name = get_case_name(typhoon_v60_files[0])
            output_path = plot_single_case(df, case_name, output_dir)
            all_output_files.append(output_path)

        # Earthquake subplots - sort by filename to ensure 1g comes first
        earthquake_files_sorted = sorted(earthquake_files, key=lambda x: '1g' in x.lower())
        for ef in earthquake_files_sorted:
            df = pd.read_csv(ef)
            case_name = get_case_name(ef)
            output_path = plot_single_case(df, case_name, output_dir)
            all_output_files.append(output_path)

        # Row 1: Typhoon (top row)
        # Left column: Typhoon V40
        if typhoon_v40_files:
            df = pd.read_csv(typhoon_v40_files[0])
            plot_single_subax(df, axes[0, 0], '(a) Typhoon V40')
        else:
            axes[0, 0].set_visible(False)

        # Right column: Typhoon V60
        if typhoon_v60_files:
            df = pd.read_csv(typhoon_v60_files[0])
            plot_single_subax(df, axes[0, 1], '(b) Typhoon V60')
        else:
            axes[0, 1].set_visible(False)

        # Row 2: Earthquake (bottom row) - sort by filename to ensure 1g on left, 2g on right
        # Note: '1g' in x.lower() returns True/False, False(0) comes before True(1)
        # So use '2g' as key to make 1g come first
        earthquake_files_sorted = sorted(earthquake_files, key=lambda x: '2g' in x.lower())
        if len(earthquake_files_sorted) >= 1:
            df = pd.read_csv(earthquake_files_sorted[0])
            plot_single_subax(df, axes[1, 0], '(c) Earthquake 1g')
        else:
            axes[1, 0].set_visible(False)

        if len(earthquake_files_sorted) >= 2:
            df = pd.read_csv(earthquake_files_sorted[1])
            plot_single_subax(df, axes[1, 1], '(d) Earthquake 2g')
        else:
            axes[1, 1].set_visible(False)

        plt.tight_layout()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f"tiqu_comparison_{timestamp}.png")
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(output_path, dpi=dpi)
        plt.close(fig)

        return {"status": "success", "plot_path": output_path, "sub_plots": all_output_files}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def extract_optimal_pitch(csv_files: List[str], output_plot: str, output_csv: str, dpi: int = 300):
    """Extract optimal pitch from multiple CSV files and generate visualization"""
    try:
        all_data = []
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                all_data.append(df)

        if not all_data:
            return {"error": "No valid CSV files found"}

        data = pd.concat(all_data, ignore_index=True)

        if not all(col in data.columns for col in ["V_hub_ms", "Yaw_deg", "Pitch_deg", "MaxStress_MPa"]):
            return {"error": "CSV must contain columns: V_hub_ms, Yaw_deg, Pitch_deg, MaxStress_MPa"}

        wind_speeds = np.sort(np.unique(data["V_hub_ms"].values))
        all_yaws = np.sort(np.unique(data["Yaw_deg"].values))

        directory = os.path.dirname(output_plot)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        directory = os.path.dirname(output_csv)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        export_data = {"Yaw_deg": all_yaws}
        fig, ax = plt.subplots(figsize=(12, 8))

        # Create 2D grid for background color map
        Yaw_mesh, V_mesh = np.meshgrid(all_yaws, wind_speeds)
        Stress_mesh = np.full_like(Yaw_mesh, np.nan, dtype=float)

        for i, V in enumerate(wind_speeds):
            data_V = data[abs(data["V_hub_ms"] - V) < 1e-4]
            for j, Y in enumerate(all_yaws):
                data_VY = data_V[abs(data_V["Yaw_deg"] - Y) < 1e-4]
                if not data_VY.empty:
                    # Use mean of all matching MaxStress_MPa as background value
                    Stress_mesh[i, j] = data_VY["MaxStress_MPa"].mean()

        # Draw background color map
        vmin = np.nanmin(Stress_mesh)
        vmax = np.nanmax(Stress_mesh)
        pcolormesh = ax.pcolormesh(Yaw_mesh, V_mesh, Stress_mesh,
                                    cmap="RdYlBu_r", shading="auto", alpha=0.7,
                                    vmin=vmin, vmax=vmax)

        # Add colorbar
        cbar = fig.colorbar(pcolormesh, ax=ax, shrink=0.8, aspect=25, pad=0.02)
        cbar.set_label("MaxMaxStress_MPa", fontsize=12, fontweight="bold")

        # Overlay optimal pitch curves on background
        for V in wind_speeds:
            data_V = data[abs(data["V_hub_ms"] - V) < 1e-4]
            best_pitch = np.zeros(len(all_yaws))
            min_stress = np.zeros(len(all_yaws))

            for j, Y in enumerate(all_yaws):
                data_VY = data_V[abs(data_V["Yaw_deg"] - Y) < 1e-4]
                if not data_VY.empty:
                    min_idx = data_VY["MaxStress_MPa"].idxmin()
                    best_pitch[j] = data_V.loc[min_idx, "Pitch_deg"]
                    min_stress[j] = data_V.loc[min_idx, "MaxStress_MPa"]
                else:
                    best_pitch[j] = np.nan
                    min_stress[j] = np.nan

            var_pitch = f"Pitch_V{V:.2f}".replace(".", "_")
            var_stress = f"MinStress_V{V:.2f}".replace(".", "_")
            export_data[var_pitch] = best_pitch
            export_data[var_stress] = min_stress

            ax.plot(all_yaws, best_pitch, "-o", color="black",
                    linewidth=2.5, markersize=9, markerfacecolor="w",
                    label=f"V = {V:.2f} m/s")

        ax.set_xlabel("Yaw Angle (deg)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Wind Speed (m/s)", fontsize=12, fontweight="bold")
        ax.set_title("Optimal Pitch Angle by Wind Speed & Yaw\n(Background: MaxMaxStress_MPa)", fontsize=14)
        ax.legend(loc="upper right", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([-180, 180])
        ax.set_xticks(np.arange(-180, 181, 30))

        fig.savefig(output_plot, dpi=dpi)
        plt.close(fig)

        export_df = pd.DataFrame(export_data)
        export_df.to_csv(output_csv, index=False)

        return {
            "plot": output_plot,
            "csv": output_csv
        }
    except Exception as e:
        return {"error": str(e)}


def generate_airfoil_distribution(output_path: str, dpi: int = 300):
    """Generate 3D airfoil distribution plot"""
    try:
        # IEA 10MW data
        r_stations = np.array([
            0.000, 3.336, 6.673, 10.009, 13.346, 16.682, 20.018, 23.354,
            26.691, 30.027, 33.364, 36.700, 40.037, 43.374, 46.710,
            50.046, 53.382, 56.719, 60.055, 63.391, 66.728, 70.065,
            73.401, 76.736, 80.073, 83.410, 86.746, 90.083, 93.419, 96.755,
        ])
        chord = np.array([
            4.600, 4.603, 4.722, 5.008, 5.412, 5.801, 6.016, 5.982, 5.827,
            5.609, 5.346, 5.053, 4.746, 4.434, 4.126, 3.822, 3.530, 3.252,
            2.992, 2.748, 2.524, 2.317, 2.128, 1.958, 1.803, 1.660, 1.522,
            1.343, 1.051, 0.096,
        ])

        visual_af_id = np.array([
            1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3,
            4, 4, 4, 5, 5, 5, 5, 5, 5, 5,
        ])
        af_names = ["Cylinder", "FFA-W3-330", "FFA-W3-270", "FFA-W3-241", "FFA-W3-211"]

        n_stations = len(r_stations)
        R_total = r_stations[-1]

        color_blue = [0.15, 0.45, 0.75]
        color_orange = [0.85, 0.40, 0.15]

        fig = plt.figure(figsize=(13, 6))
        ax = fig.add_subplot(111, projection="3d")

        # Draw airfoil cross-sections
        for i in range(n_stations):
            x_norm, y_norm = generate_iea_airfoil(r_stations[i], R_total)
            x_scaled = (x_norm - 0.25) * chord[i]
            y_scaled = y_norm * chord[i]

            face_color = color_blue if visual_af_id[i] % 2 == 1 else color_orange

            verts_3d = [(r_stations[i], yi, zi) for yi, zi in zip(x_scaled, y_scaled)]
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection
            ax.add_collection3d(Poly3DCollection([verts_3d], facecolors=face_color, edgecolors="k",
                                                 alpha=0.65, linewidths=0.5))

        # Engineering annotations
        unique_ids = np.unique(visual_af_id)
        for k, current_id in enumerate(unique_ids):
            idx = np.where(visual_af_id == current_id)[0]
            r_start = r_stations[idx[0]]
            r_end = r_stations[idx[-1]]

            if k > 1:
                prev_idx = np.where(visual_af_id == unique_ids[k - 1])[0]
                r_start = (r_stations[idx[0]] + r_stations[prev_idx[-1]]) / 2
            if k < len(unique_ids) - 1:
                next_idx = np.where(visual_af_id == unique_ids[k + 1])[0]
                r_end = (r_stations[idx[-1]] + r_stations[next_idx[0]]) / 2

            r_mid = (r_start + r_end) / 2
            name_str = af_names[current_id - 1]

            y_dim = 0
            if current_id % 2 == 1:
                z_dim = 4.8
                text_z = z_dim + 0.4
                valign = "bottom"
            else:
                z_dim = -4.8
                text_z = z_dim - 0.4
                valign = "top"

            tick = 0.35
            ax.plot3D([r_start, r_start], [y_dim, y_dim], [0, z_dim], "k--", linewidth=1.0)
            ax.plot3D([r_end, r_end], [y_dim, y_dim], [0, z_dim], "k--", linewidth=1.0)
            ax.plot3D([r_start, r_end], [y_dim, y_dim], [z_dim, z_dim], "k-", linewidth=1.2)
            ax.plot3D([r_start, r_start], [y_dim, y_dim], [z_dim - tick, z_dim + tick], "k-", linewidth=1.2)
            ax.plot3D([r_end, r_end], [y_dim, y_dim], [z_dim - tick, z_dim + tick], "k-", linewidth=1.2)
            ax.text(r_mid, y_dim, text_z, name_str, color="k", fontsize=12, fontweight="bold",
                    horizontalalignment="center", verticalalignment=valign)

        # Reference line
        ax.plot3D([0, R_total + 5], [0, 0], [0, 0], "r-.", linewidth=1.2)
        ax.text(R_total / 2 + 5, -1.0, 0, "Pitch Axis", color="r", fontsize=12, fontweight="bold")

        # Formatting
        ax.set_xlabel("Blade Span (m)", fontsize=13, fontweight="bold")
        ax.set_ylabel("Chordwise Position (m)", fontsize=13, fontweight="bold")
        ax.set_zlabel("Thickness (m)", fontsize=13, fontweight="bold")
        ax.set_title("IEA 10MW RWT Airfoil Distribution (FFA-W3 Series)", fontsize=15, fontweight="bold")
        ax.set_xticks(np.arange(0, 101, 20))
        ax.set_yticks(np.arange(-4, 5, 2))
        ax.set_xlim([-5, R_total + 5])
        ax.set_ylim([-4, 4])
        ax.set_zlim([-6.5, 6.5])
        ax.view_init(elev=25, azim=-15)

        # Ensure output directory exists
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        plt.tight_layout()
        fig.savefig(output_path, dpi=dpi)
        plt.close(fig)

        return {"plot": output_path}
    except Exception as e:
        return {"error": str(e)}


def generate_twist_evolution(output_path: str, dpi: int = 300, r_transition: float = 10.0):
    """Generate 3D twist evolution plot"""
    try:
        # AeroDyn v15 data
        r_stations = np.array([
            0.000, 3.336, 6.673, 10.009, 13.346, 16.682, 20.018, 23.354,
            26.691, 30.027, 33.364, 36.700, 40.037, 43.374, 46.710,
            50.046, 53.382, 56.719, 60.055, 63.391, 66.728, 70.065,
            73.401, 76.736, 80.073, 83.410, 86.746, 90.083, 93.419, 96.755,
        ])
        chord = np.array([
            4.600, 4.603, 4.722, 5.008, 5.412, 5.801, 6.016, 5.982, 5.827,
            5.609, 5.346, 5.053, 4.746, 4.434, 4.126, 3.822, 3.530, 3.252,
            2.992, 2.748, 2.524, 2.317, 2.128, 1.958, 1.803, 1.660, 1.522,
            1.343, 1.051, 0.096,
        ])
        twist_deg = np.array([
            12.000, 12.000, 11.997, 12.022, 11.569, 10.039, 8.077, 6.584,
            5.661, 5.010, 4.447, 3.931, 3.440, 2.938, 2.391, 1.800, 1.182,
            0.551, -0.077, -0.687, -1.263, -1.792, -2.262, -2.648, -2.943,
            -3.129, -3.136, -2.863, -2.046, -0.037,
        ])
        n_sections = len(r_stations)
        R = r_stations[-1]

        # Base airfoil shape
        t = 0.18
        x_af = np.linspace(0, 1, 100)
        y_af = 5 * t * (
            0.2969 * np.sqrt(x_af)
            - 0.1260 * x_af
            - 0.3516 * x_af ** 2
            + 0.2843 * x_af ** 3
            - 0.1015 * x_af ** 4
        )
        x_base = np.concatenate([x_af, x_af[::-1]])
        y_base = np.concatenate([y_af, -y_af[::-1]])

        phi = np.concatenate([np.linspace(np.pi, 0, 100), np.linspace(0, -np.pi, 100)])

        # Generate 3D surface
        X = np.zeros((2 * len(x_af), n_sections))
        Y = np.zeros((2 * len(x_af), n_sections))
        Z = np.zeros((2 * len(x_af), n_sections))
        C = np.zeros((2 * len(x_af), n_sections))

        for i in range(n_sections):
            c = chord[i]
            r = r_stations[i]

            x_af_scaled = x_base * c - 0.25 * c
            y_af_scaled = y_base * c
            x_circ_scaled = (c / 2) * np.cos(phi)
            y_circ_scaled = (c / 2) * np.sin(phi)

            if r <= r_transition:
                weight = np.cos((r / r_transition) * (np.pi / 2))
            else:
                weight = 0

            x_mixed = weight * x_circ_scaled + (1 - weight) * x_af_scaled
            y_mixed = weight * y_circ_scaled + (1 - weight) * y_af_scaled

            theta = np.deg2rad(twist_deg[i])
            x_rot = x_mixed * np.cos(theta) - y_mixed * np.sin(theta)
            y_rot = x_mixed * np.sin(theta) + y_mixed * np.cos(theta)

            X[:, i] = r
            Y[:, i] = x_rot
            Z[:, i] = y_rot
            C[:, i] = twist_deg[i]

        fig = plt.figure(figsize=(12, 5.5))
        ax = fig.add_subplot(111, projection="3d")

        surf = ax.plot_surface(X, Y, Z, facecolors=plt.cm.jet(C / (C.max() - C.min() + 1e-12)),
                               edgecolor="none", alpha=0.85, linewidth=0, antialiased=True)

        # Reference line
        ax.plot3D([0, R + 5], [0, 0], [0, 0], "r-.", linewidth=2.5)
        ax.text(R / 2, 1.5, 0.5, "Pitch Axis", color="r", fontsize=12, fontweight="bold")

        # Root and tip chord annotations
        idx_LE = 0
        idx_TE = 100
        root_chord = np.array([
            [X[idx_LE, 0], X[idx_TE, 0]],
            [Y[idx_LE, 0], Y[idx_TE, 0]],
            [Z[idx_LE, 0], Z[idx_TE, 0]],
        ])
        ax.plot(root_chord[0, :], root_chord[1, :], root_chord[2, :], "b-", linewidth=3)
        ax.text(root_chord[0, 0], root_chord[1, 1] + 0.5, root_chord[2, 1] + 1.0,
                f"Root (Cylinder, Twist: {twist_deg[0]:.1f}°)", color="b", fontsize=12, fontweight="bold")

        tip_chord = np.array([
            [X[idx_LE, -1], X[idx_TE, -1]],
            [Y[idx_LE, -1], Y[idx_TE, -1]],
            [Z[idx_LE, -1], Z[idx_TE, -1]],
        ])
        ax.plot(tip_chord[0, :], tip_chord[1, :], tip_chord[2, :], "g-", linewidth=3)
        ax.text(tip_chord[0, 0] - 18, tip_chord[1, 1] + 0.5, tip_chord[2, 1] + 1.0,
                f"Tip Chord (Twist: {twist_deg[-1]:.2f}°)", color=[0, 0.5, 0], fontsize=12, fontweight="bold")

        # Formatting
        ax.set_xlabel("Spanwise Coordinate (m)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Chordwise Coordinate (m)", fontsize=12, fontweight="bold")
        ax.set_zlabel("Thickness (m)", fontsize=12, fontweight="bold")
        ax.set_title("3D Aerodynamic Twist Evolution (Exact AeroDyn Formulation)", fontsize=14, fontweight="bold")

        cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=20, pad=0.1)
        cbar.set_label("Local Twist Angle (deg)", fontsize=12, fontweight="bold")
        ax.set_xlim([-2, 100])
        ax.set_ylim([-6, 6])
        ax.set_zlim([-3, 3])
        ax.view_init(elev=35, azim=-30)

        # Ensure output directory exists
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        plt.tight_layout()
        fig.savefig(output_path, dpi=dpi)
        plt.close(fig)

        return {"plot": output_path}
    except Exception as e:
        return {"error": str(e)}


SIMULATION_WORKSPACE = "/app/simulation_runs"


@router.post("/optimal_pitch_extractor")
async def optimal_pitch_extractor_endpoint(params: OptimalPitchExtractorParams):
    """Extract optimal pitch from multiple simulation result CSVs and generate visualization"""
    try:
        csv_files = params.csv_files or []
        csv_dir = params.csv_dir

        if csv_dir:
            dir_path = csv_dir if csv_dir.startswith('/app') else os.path.join(SIMULATION_WORKSPACE, csv_dir)
            for f in os.listdir(dir_path):
                if f.endswith('.csv') and f.startswith('Stress'):
                    csv_files.append(os.path.join(dir_path, f))

        if not csv_files:
            raise HTTPException(status_code=400, detail="No CSV files provided")

        output_plot = params.output_plot or "/app/plots/optimal_pitch.png"
        output_csv = params.output_csv or "/app/plots/optimal_pitch_origin.csv"

        result = extract_optimal_pitch(csv_files, output_plot, output_csv)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "status": "success",
            "plot_url": result["plot"],
            "csv_url": result["csv"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/airfoil_distribution")
async def plot_airfoil_distribution():
    """Generate 3D airfoil distribution plot"""
    try:
        output_path = "/app/plots/airfoil_distribution.png"
        result = generate_airfoil_distribution(output_path)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "status": "success",
            "plot_url": "/plots/airfoil_distribution.png"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tiqu_plot")
async def tiqu_plot_endpoint(params: TiquPlotParams):
    """Generate visualization plots for tiqu CSV files (one plot per CSV)"""
    try:
        csv_files = params.csv_files or []
        csv_dir = params.csv_dir

        if csv_dir:
            dir_path = csv_dir if csv_dir.startswith('/app') else os.path.join("/app/result_reference_values", csv_dir)
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.endswith('.csv') and '_tiqu_' in f:
                        csv_files.append(os.path.join(dir_path, f))

        if not csv_files:
            raise HTTPException(status_code=400, detail="No CSV files provided")

        output_dir = params.output_dir or "/app/result_reference_values"
        os.makedirs(output_dir, exist_ok=True)

        results = []
        # Generate one plot per CSV file
        for csv_path in csv_files:
            result = plot_single_tiqu(csv_path, output_dir)
            results.append(result)

        # Generate comparison plot (if more than 1 CSV file)
        if len(csv_files) > 1:
            comparison_result = plot_comparison_tiqu(csv_files, output_dir)
            results.append({
                "status": comparison_result.get("status"),
                "plot_path": comparison_result.get("plot_path"),
                "type": "comparison"
            })

        return {
            "status": "success",
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/twist_evolution")
async def plot_twist_evolution(r_transition: float = 10.0):
    """Generate 3D twist evolution plot"""
    try:
        output_path = "/app/plots/twist_evolution.png"
        result = generate_twist_evolution(output_path, r_transition=r_transition)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "status": "success",
            "plot_url": "/plots/twist_evolution.png"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
