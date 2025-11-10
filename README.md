# Shape Dynamics of Epithelium During Foregut Splitting

Code for the analysis of curvature and shape dynamics of the foregut epithelium accompanying:  
**Yan et al. (2025)** — *“Convergent flow-mediated mesenchymal force drives embryonic foregut constriction and splitting.”* bioRxiv.

---

## Overview

This repository provides tools for:

1. **Experimental Analysis** -- Quantifying the shape dynamics of the foregut epithelium from segmented microscopy videos.  
2. **Theoretical Modeling** -- Numerically solving diffusion equation for curved source in *Mathematica*.


## 1. Experimental Shape Analysis

### Files
- `Shape_Analysis.py` -- Main Python script for outline extraction and shape analysis.  
- `ExtractOutline.ijm` -- ImageJ macro used to extract epithelial outlines.  
- `CurvatureExtraction.nb` -- Mathematica notebook for curvature and geometric measurements.  

### Data
A single video is uploaded here. The full data set of segmented and pre-segmentation videos is available at https://doi.org/10.5281/zenodo.17576089. The segmentation was performed using **Segment Anything Model 2 (SAM2)** (see https://github.com/yanrui21/Foregut_septation_N).

### Requirements
- Python (tested on 3.11)  
- ImageJ / Fiji  
- Mathematica (tested on 14.2)  

### Workflow

1. **Run `Shape_Analysis.py`**
   
   - This script automatically calls the ImageJ macro `ExtractOutline.ijm`.  
   - You may need to modify the ImageJ installation path inside the Python script.

3. **Outline Extraction**
   
   - The ImageJ macro extracts the outer 1D contour from each frame of a 2D epithelial slice.  
   - The resulting coordinates are saved as text files (Coords_XXXX.txt) along with the analyzed frames.

4. **Shape properties of outline**
   
   - The Python script finally computes various properties of the outline using OpenCV and saves these (`Properties.txt` and `moments.txt`).
   - Furthermore, a list of all files that were analyzed is created (`list_data.csv`).

6. **Run `CurvatureExtraction.nb`**
   
   - Imports the data extracted in previous steps as well as associated metadata saved in `Metadata.xlsx` for each sample.
   - Fits a B-spline to each outline and computes curvature together with other geometric measures such as the area and neck width.
   - Results for each sample are exported as `.csv` files and plots of them as function of time are saved as `.png` files.  
   - Additionally, a GIF is generated that overlays: original segmentation + spline + automatically detected neck points to allow. This allows easy visual verification of automated analysis.

8. **Statistical Comparison**
   
   - Geometric measures are plotted for all samples of a developmental stage
   - Averages of each developmental stage are compared for wild type and various cases where the samples are chemically or mechanically perturbed
   
---

## 2. Diffusion with a Curved Source

### File
- `DiffusionCurvedSource.nb`

### Requirements
- Mathematica (tested on 14.2)  

### Description
A Mathematica notebook solving the diffusion equation in the presence of a curved (semi-circular) source using `NDSolve'FEM'`.
Different source radii are considered and compared to analytical approximations to study how curvature affects diffusion dynamics.
The plots presented in the paper are created.

---

## Citation

```
@article{Yan2025ForegutSplitting,
  author  = {Yan, Rui and Hoffmann, Ludwig A. and Oikonomou, Panagiotis and Li, Deng and Lee, ChangHee and Gill, Hasreet and Mongera, Alessandro and Nerurkar, Nandan L. and Mahadevan, L. and Tabin, Clifford J.},
  title   = {Convergent flow-mediated mesenchymal force drives embryonic foregut constriction and splitting},
  journal = {bioRxiv},
  year    = {2025},
  doi     = {10.1101/2025.01.22.634318},
  url     = {https://www.biorxiv.org/content/10.1101/2025.01.22.634318v2}
}
