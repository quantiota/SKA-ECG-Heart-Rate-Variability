# SKA Heart Rate Variability

**Heart Rate Variability (HRV) Exploration with Structured Knowledge Accumulation (SKA) and Entropy-Based Learning**

This project applies the SKA entropy learning framework to heart rate variability (HRV) time series, aiming to discover new informational regimes and subtle physiological patterns not accessible with classical statistics or supervised machine learning.



## Features

- Real-time HRV analysis using entropy-driven SKA learning
- Extraction of regime transitions and entropy trajectories
- Visualization tools for HRV time series, entropy, and state transitions
- Open-source sample code, datasets, and reproducible figures



## Quick Start

1. Clone this repo  
   `git clone https://github.com/quantiota/SKA-Heart-Rate-Variability.git`
2. Install requirements  
   `pip install -r requirements.txt`
3. Run analysis notebook or script (see `notebooks/` or `scripts/`)



## Example Figures

> _Add here a key HRV entropy trajectory or regime plot demonstrating unique SKA insights._



## Why SKA for HRV?

- **Unsupervised regime change detection** in HRV
- **Quantifies entropy** even during stable heart rate segments
- **Reveals subtle physiological transitions** invisible to classical HRV analysis

## Relation to SKA Quantitative Finance

This repository is part of a broader SKA research program on entropy-driven regime transitions in real-time dynamical systems.

The first empirical discovery of a SKA binary information flow was obtained in the quantitative finance repository:


[SKA-quantitative-finance]( https://github.com/quantiota/SKA-quantitative-finance)


In that work, market microstructure is encoded through three entropy regimes:

```
neutral = 00
bull    = 01
bear    = 10
```
and each transition becomes a 4-bit word:

```
neutral → neutral = 0000
neutral → bull    = 0001
neutral → bear    = 0010
bull → neutral    = 0100
bear → neutral    = 1000
```
The central hypothesis of SKA-HRV is that physiological signals may also express hidden health-related structure through entropy-regime sequences.

In this sense, SKA-HRV investigates whether the heart, like the market, produces a measurable binary information flow — not as a metaphor, but as a real sequence structure derived from entropy learning.


## Collaboration & Citation

### 👥 **Collaboration Call: HRV + Machine Learning Researchers**

We seek collaboration with **established HRV researchers who have published in HRV analysis and machine learning** to explore SKA's entropy-based regime discovery in physiological time series.

#### What We Bring:
- **Novel SKA entropy framework:** Proven in market regime detection, now applied to HRV
- **Real-time, beat-by-beat entropy computation**
- **Detection of hidden regime cycling** and subtle state transitions
- **Open-source, reproducible code and methodology**

#### Ideal Collaborator:
- **Published HRV researchers** with clinical/medical datasets
- **Machine learning expertise** in time series or physiological signal processing
- **Interest in information-theoretic approaches** to biosignals
- **Willing to co-author research papers/validation studies**

#### Example Collaboration Areas:
- Clinical validation on cardiac datasets (ICU, ambulatory, sleep, etc.)
- Comparison of SKA vs. traditional HRV metrics (RMSSD, pNN50, SDNN, etc.)
- Applications in real-time monitoring: sports, critical care, neurocardiology
- Methodology papers: Information theory meets physiology

#### Citation

If you use or extend this project, please cite:  
Bouarfa Mahi. "Structured Knowledge Accumulation: An Autonomous Framework for Layer-Wise Entropy Reduction in Neural Learning." [arXiv:2503.13942](https://arxiv.org/abs/2503.13942)

**Contact:** Bouarfa Mahi — _especially interested in collaboration with those having access to large HRV datasets or clinical validation environments._



## License

MIT



*SKA-HRV-Analysis bridges the gap between modern information theory and physiological data science*