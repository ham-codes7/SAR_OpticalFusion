# Literature Review and Research Gaps

SAR–optical fusion for all-weather land-cover change detection · Innovative Design Project · Review I

**108 peer-reviewed journal articles**, 1980–2022 (67 from 2015 onward), sorted into 9 groups. Every entry was checked against Crossref: the DOI resolves and the record is typed as a journal article. Conference papers, preprints, theses and book chapters were left out.

Most-cited venues: IEEE Transactions on Geoscience and Remote Sensing (16); Remote Sensing of Environment (13); Remote Sensing (13); ISPRS Journal of Photogrammetry and Remote Sensing (10); IEEE Geoscience and Remote Sensing Magazine (7); International Journal of Remote Sensing (5); Information Fusion (4); IEEE Geoscience and Remote Sensing Letters (4).

## 1. How the literature is classified

The groups follow our pipeline: why the problem exists (A), how fusion is done (B, D), how it is judged (C), the neighbouring cloud-gap problem (E), the downstream task (F, G, H), and how results are scored (I).

| Group | Theme | Papers | What we take from it | Common limitation |
|---|---|---|---|---|
| A | Sensors, SAR preprocessing and the cloud problem | 12 | Why the problem exists and how each sensor's data must be prepared. | Preprocessing is usually tuned for flat terrain; cloud masks are imperfect, so masked optical data still leaks errors. |
| B | Classical pixel-level fusion (CS and MRA), including SAR–optical | 21 | The IHS, PCA and wavelet methods we implement, and how SAR–optical variants differ from pansharpening. | Mostly evaluated visually or with image-quality metrics, at single sites. |
| C | Fusion quality assessment | 5 | The SSIM, SAM, MI, Q and QNR metrics we report. | They measure similarity to a source image, not usefulness for a task. |
| D | Learning-based and feature/decision-level fusion | 18 | Alternatives to pixel-level fusion; the stacked-band (feature-level) baseline. | Large labelled datasets needed; rarely compared with classical fusion under one detector. |
| E | SAR-guided cloud removal and gap filling | 7 | Closest neighbour to our 'works under cloud' claim. | Judged by how well pixels are reconstructed (PSNR/SSIM), not by downstream change detection. |
| F | Change-detection methods, including cross-sensor | 14 | Our detector design (difference features, CVA-style) and alternatives. | Fusion is usually treated as given; it is not the variable being tested. |
| G | Forest-loss monitoring (optical, SAR, fused) | 13 | The forest-loss task and its reference data. | Concentrated in flat lowland tropics (Amazon, Congo, Guiana). |
| H | Urban and land-cover applications of Sentinel-1 + Sentinel-2 | 8 | The urban-growth task. | Each study varies site, sensor and classifier at once, so results are hard to compare. |
| I | Reference data, accuracy assessment and platforms | 10 | How we score: labels, metrics, area accuracy; platform choice. | Global 10 m products disagree and are built from Sentinel-2. |
| | **Total** | **108** | | |

## 2. Reviewed papers by group

### A. Sensors, SAR preprocessing and the cloud problem (12)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [1] | Torres et al. (2012) | Remote Sensing of Environment | Sentinel-1 mission design: C-band SAR, IW mode, dual polarisation (VV+VH). |
| [2] | Drusch et al. (2012) | Remote Sensing of Environment | Sentinel-2 MSI mission: 13 bands at 10–60 m, 5-day revisit. |
| [3] | Moreira et al. (2013) | IEEE Geoscience and Remote Sensing Magazine | SAR fundamentals: imaging geometry, backscatter, polarimetry, interferometry. |
| [4] | Lee (1980) | IEEE Transactions on Pattern Analysis and Machine Intelligence | Local-statistics adaptive speckle filter (Lee filter). |
| [5] | Lee (1981) | Computer Graphics and Image Processing | Refined Lee filter: edge-aligned windows that keep boundaries sharp. |
| [6] | Argenti et al. (2013) | IEEE Geoscience and Remote Sensing Magazine | Taxonomy and benchmark of despeckling filters; trade-off between noise and detail. |
| [7] | Small (2011) | IEEE Transactions on Geoscience and Remote Sensing | Radiometric terrain flattening (gamma-nought) for SAR over slopes. |
| [8] | Truckenbrodt et al. (2019) | Data | Best-practice processing chain for Sentinel-1 analysis-ready backscatter. |
| [9] | Mullissa et al. (2021) | Remote Sensing | Sentinel-1 analysis-ready preparation in Earth Engine (border noise, speckle, terrain). |
| [10] | Whitcraft et al. (2015) | Remote Sensing of Environment | Measures cloud cover during growing seasons worldwide; tropics and monsoon regions are worst affected. |
| [11] | King et al. (2013) | IEEE Transactions on Geoscience and Remote Sensing | Long-term MODIS cloud climatology: where and when cloud persists. |
| [12] | Skakun et al. (2022) | Remote Sensing of Environment | Comparison of cloud-masking algorithms; thin cloud and shadow are often missed. |

### B. Classical pixel-level fusion (CS and MRA), including SAR–optical (21)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [13] | Pohl & Genderen (1998) | International Journal of Remote Sensing | Foundational review: fusion levels (pixel, feature, decision) and classical methods. |
| [14] | Tu et al. (2001) | Information Fusion | Recasts IHS-like fusion in a fast general form and explains its spectral distortion. |
| [15] | Vivone et al. (2015) | IEEE Transactions on Geoscience and Remote Sensing | Benchmark of component-substitution vs multiresolution fusion using the Wald and QNR protocols. |
| [16] | Nunez et al. (1999) | IEEE Transactions on Geoscience and Remote Sensing | Additive (à trous) wavelet fusion of multispectral and panchromatic images. |
| [17] | Amolins et al. (2007) | ISPRS Journal of Photogrammetry and Remote Sensing | Review and comparison of wavelet fusion variants; results depend on basis and depth. |
| [18] | Mallat (1989) | IEEE Transactions on Pattern Analysis and Machine Intelligence | Theory of multiresolution wavelet decomposition. |
| [19] | Ghassemian (2016) | Information Fusion | Survey of remote-sensing fusion methods by category. |
| [20] | Zhang (2010) | International Journal of Image and Data Fusion | Status, trends and open issues of multi-source fusion. |
| [21] | Li et al. (2017) | Information Fusion | Survey of pixel-level fusion: multiresolution, sparse, learning-based methods and metrics. |
| [22] | Kulkarni & Rege (2020) | Information Fusion | Review of pixel-level SAR–optical fusion and the quality metrics used to judge it. |
| [23] | Alparone et al. (2004) | IEEE Transactions on Geoscience and Remote Sensing | Generalised intensity modulation: injects SAR texture into Landsat ETM+. |
| [24] | Chibani (2006) | ISPRS Journal of Photogrammetry and Remote Sensing | Integrates SAR features into SPOT multispectral imagery with the à trous wavelet. |
| [25] | Hong et al. (2009) | Photogrammetric Engineering & Remote Sensing | Hybrid wavelet + IHS fusion of high-resolution SAR with moderate-resolution multispectral. |
| [26] | Pal et al. (2007) | ISPRS Journal of Photogrammetry and Remote Sensing | PCA fusion of ERS-2 SAR with Indian IRS-1C LISS-III for geological interpretation. |
| [27] | Abdikan et al. (2014) | International Journal of Digital Earth | Compares several fusion methods on multi-sensor SAR + optical imagery using quality metrics. |
| [28] | Sanli et al. (2017) | Journal of the Indian Society of Remote Sensing | Evaluates fusion of PALSAR/RADARSAT-1 with SPOT for land-cover classification. |
| [29] | Aiazzi et al. (2006) | Photogrammetric Engineering & Remote Sensing | MTF-matched multiresolution (GLP) fusion. |
| [30] | Schmitt & Zhu (2016) | IEEE Geoscience and Remote Sensing Magazine | Overview of data fusion in remote sensing; sets out the specific SAR–optical challenges. |
| [31] | Ghamisi et al. (2019) | IEEE Geoscience and Remote Sensing Magazine | Comprehensive review of multisource and multitemporal fusion. |
| [32] | Gomez-Chova et al. (2015) | Proceedings of the IEEE | Review of multimodal classification and the levels at which modalities can be fused. |
| [33] | Joshi et al. (2016) | Remote Sensing | Review of optical + radar fusion for land-use mapping and monitoring. |

### C. Fusion quality assessment (5)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [34] | Wang et al. (2004) | IEEE Transactions on Image Processing | SSIM: structural similarity index. |
| [35] | Wang & Bovik (2002) | IEEE Signal Processing Letters | Universal image quality index (Q). |
| [36] | Kruse et al. (1993) | Remote Sensing of Environment | Introduces the spectral angle mapper (SAM). |
| [37] | Qu et al. (2002) | Electronics Letters | Mutual information as a fusion performance measure. |
| [38] | Alparone et al. (2008) | Photogrammetric Engineering & Remote Sensing | QNR: assessing fusion quality without a reference image. |

### D. Learning-based and feature/decision-level fusion (18)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [39] | Zhu et al. (2017) | IEEE Geoscience and Remote Sensing Magazine | Review of deep learning in remote sensing. |
| [40] | Zhu et al. (2021) | IEEE Geoscience and Remote Sensing Magazine | Deep learning for SAR: models, pitfalls, domain gap, label scarcity. |
| [41] | Hong et al. (2021) | IEEE Transactions on Geoscience and Remote Sensing | Multimodal deep learning framework for remote-sensing classification. |
| [42] | Masi et al. (2016) | Remote Sensing | CNN-based pansharpening (PNN). |
| [43] | Scarpa et al. (2018) | Remote Sensing | CNN that fuses Sentinel-1 and Sentinel-2 to estimate optical features under cloud. |
| [44] | Ienco et al. (2019) | ISPRS Journal of Photogrammetry and Remote Sensing | Deep multi-source network on Sentinel-1 + Sentinel-2 time series for land cover. |
| [45] | Benedetti et al. (2018) | IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing | M3Fusion: multiscale, multimodal, multitemporal deep fusion. |
| [46] | Zhang & Xu (2018) | International Journal of Applied Earth Observation and Geoinformation | Compares pixel-, feature- and decision-level SAR–optical integration for urban land cover. |
| [47] | Zhang et al. (2015) | IEEE Geoscience and Remote Sensing Letters | Shows how feature normalisation changes the result of optical–SAR fusion. |
| [48] | Waske & Benediktsson (2007) | IEEE Transactions on Geoscience and Remote Sensing | Decision fusion of SVMs for multisensor classification. |
| [49] | Waske & Linden (2008) | IEEE Transactions on Geoscience and Remote Sensing | Decision fusion of SAR and optical imagery. |
| [50] | Shao et al. (2016) | Remote Sensing | Decision-level optical–SAR fusion for impervious-surface mapping. |
| [51] | Belgiu & Drăguţ (2016) | ISPRS Journal of Photogrammetry and Remote Sensing | Review of random forests in remote sensing. |
| [52] | Ma et al. (2019) | ISPRS Journal of Photogrammetry and Remote Sensing | Meta-analysis of deep learning in remote-sensing applications. |
| [53] | Reyes et al. (2019) | Remote Sensing | cGAN SAR-to-optical translation: what it can and cannot do. |
| [54] | Wang et al. (2019) | IEEE Access | Supervised CycleGAN for SAR-to-optical translation. |
| [55] | Ye et al. (2017) | IEEE Transactions on Geoscience and Remote Sensing | Multimodal registration using structural similarity of oriented gradients. |
| [56] | Hughes et al. (2018) | Remote Sensing | GAN-mined hard negatives for SAR–optical patch matching. |

### E. SAR-guided cloud removal and gap filling (7)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [57] | Meraner et al. (2020) | ISPRS Journal of Photogrammetry and Remote Sensing | DSen2-CR: deep residual cloud removal for Sentinel-2 guided by Sentinel-1. |
| [58] | Ebel et al. (2021) | IEEE Transactions on Geoscience and Remote Sensing | Global, all-season dataset and model for SAR-guided cloud removal. |
| [59] | Shen et al. (2015) | IEEE Geoscience and Remote Sensing Magazine | Technical review of missing-information reconstruction. |
| [60] | Bermudez et al. (2019) | IEEE Geoscience and Remote Sensing Letters | cGAN synthesis of optical imagery from SAR and multitemporal optical data. |
| [61] | Gao et al. (2020) | Remote Sensing | GAN-based cloud removal fusing high-resolution optical and SAR imagery. |
| [62] | Zhang et al. (2018) | IEEE Transactions on Geoscience and Remote Sensing | Unified spatial–temporal–spectral CNN for missing-data reconstruction. |
| [63] | Garioud et al. (2021) | Remote Sensing of Environment | Recurrent regression from Sentinel-1 to optical vegetation indices for continuous monitoring. |

### F. Change-detection methods, including cross-sensor (14)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [64] | Singh (1989) | International Journal of Remote Sensing | Foundational review of digital change-detection techniques. |
| [65] | Lu et al. (2004) | International Journal of Remote Sensing | Taxonomy of change-detection techniques. |
| [66] | Hussain et al. (2013) | ISPRS Journal of Photogrammetry and Remote Sensing | Change detection from pixel-based to object-based methods. |
| [67] | Bovolo & Bruzzone (2007) | IEEE Transactions on Geoscience and Remote Sensing | Change vector analysis in polar coordinates. |
| [68] | Bazi et al. (2005) | IEEE Transactions on Geoscience and Remote Sensing | Unsupervised SAR change detection: log-ratio with a generalised Gaussian model. |
| [69] | Gong et al. (2016) | IEEE Transactions on Neural Networks and Learning Systems | Deep neural networks for SAR change detection. |
| [70] | Shi et al. (2020) | Remote Sensing | Review of AI-based change detection and its open challenges. |
| [71] | Liu et al. (2018) | IEEE Transactions on Neural Networks and Learning Systems | Deep coupling network for change detection between optical and radar images. |
| [72] | Luppino et al. (2019) | IEEE Transactions on Geoscience and Remote Sensing | Image regression for change detection across different sensors. |
| [73] | Mercier et al. (2008) | IEEE Transactions on Geoscience and Remote Sensing | Conditional copulas for change detection across different sensors. |
| [74] | Touati et al. (2020) | IEEE Transactions on Image Processing | Markov-random-field model for multimodal change detection. |
| [75] | Saha et al. (2019) | IEEE Transactions on Geoscience and Remote Sensing | Deep change vector analysis for multiple-change detection. |
| [76] | Zhu (2017) | ISPRS Journal of Photogrammetry and Remote Sensing | Review of Landsat time-series change detection. |
| [77] | Woodcock et al. (2020) | Remote Sensing of Environment | Argues for moving from two-date change detection to continuous monitoring. |

### G. Forest-loss monitoring (optical, SAR, fused) (13)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [78] | Hansen et al. (2013) | Science | Global Forest Change: Landsat-based annual forest loss (Global Forest Watch). |
| [79] | Hansen et al. (2016) | Environmental Research Letters | GLAD humid-tropics forest disturbance alerts, optical only. |
| [80] | Reiche et al. (2015) | Remote Sensing of Environment | Fuses Landsat and SAR time series to detect tropical deforestation. |
| [81] | Reiche et al. (2016) | Nature Climate Change | Makes the case for combining optical and radar data in tropical forest monitoring. |
| [82] | Reiche et al. (2021) | Environmental Research Letters | RADD: Sentinel-1 forest disturbance alerts for the Congo Basin. |
| [83] | Bouvet et al. (2018) | Remote Sensing | Uses the SAR shadowing effect to detect deforestation in Sentinel-1 time series. |
| [84] | Ballère et al. (2021) | Remote Sensing of Environment | Sentinel-1 disturbance alerts in French Guiana and how they compare with optical alerts. |
| [85] | Doblas et al. (2020) | Remote Sensing | Tunes near-real-time Sentinel-1 deforestation detection in the Amazon. |
| [86] | Watanabe et al. (2018) | IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing | Early-stage deforestation detection with L-band SAR. |
| [87] | Joshi et al. (2015) | Environmental Research Letters | Maps deforestation and degradation dynamics with radar. |
| [88] | Mitchell et al. (2017) | Carbon Balance and Management | Remote-sensing approaches to degradation monitoring for REDD+ reporting. |
| [89] | Reddy et al. (2016) | Biodiversity and Conservation | Deforestation in India, 1930–2013; identifies the North-East as a hotspot. |
| [90] | Lele & Joshi (2009) | Environmental Monitoring and Assessment | Forest-cover change and critical areas in North-East India, 1972–1999. |

### H. Urban and land-cover applications of Sentinel-1 + Sentinel-2 (8)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [91] | Steinhausen et al. (2018) | International Journal of Applied Earth Observation and Geoinformation | Sentinel-1 + Sentinel-2 for land-use and land-cover mapping in a monsoon region of India. |
| [92] | Clerici et al. (2017) | Journal of Maps | Sentinel-1A + Sentinel-2A fusion for land-cover mapping in Colombia. |
| [93] | Tavares et al. (2019) | Sensors | Sentinel-1 + Sentinel-2 for urban land-cover mapping in Belém, Brazil. |
| [94] | Haas & Ban (2017) | Remote Sensing Applications: Society and Environment | Sentinel-1A + Sentinel-2A fusion for urban ecosystem-service mapping. |
| [95] | Taubenböck et al. (2012) | Remote Sensing of Environment | Monitors megacity growth from space with optical and SAR data. |
| [96] | Esch et al. (2013) | IEEE Geoscience and Remote Sensing Letters | Automated settlement masks from TanDEM-X SAR. |
| [97] | Hu et al. (2018) | ISPRS International Journal of Geo-Information | Sentinel-1 dual-pol features for local-climate-zone classification. |
| [98] | Kussul et al. (2017) | IEEE Geoscience and Remote Sensing Letters | Deep learning for land-cover and crop classification from multi-temporal optical + SAR. |

### I. Reference data, accuracy assessment and platforms (10)

| # | Study | Venue | Contribution |
|---|---|---|---|
| [99] | Brown et al. (2022) | Scientific Data | Dynamic World: near-real-time 10 m land cover from Sentinel-2. |
| [100] | Venter et al. (2022) | Remote Sensing | Compares three 10 m global land-cover products (incl. Esri / Impact Observatory) and finds substantial disagreement. |
| [101] | Olofsson et al. (2014) | Remote Sensing of Environment | Good practice for land-change accuracy assessment and area estimation. |
| [102] | Foody (2002) | Remote Sensing of Environment | Status and pitfalls of land-cover accuracy assessment. |
| [103] | Pontius & Millones (2011) | International Journal of Remote Sensing | Argues against Kappa; proposes quantity and allocation disagreement. |
| [104] | Wulder et al. (2018) | International Journal of Remote Sensing | Land cover 2.0: dense, continuous land-cover monitoring. |
| [105] | Gorelick et al. (2017) | Remote Sensing of Environment | Google Earth Engine platform. |
| [106] | Tamiminia et al. (2020) | ISPRS Journal of Photogrammetry and Remote Sensing | Meta-analysis of Earth Engine applications. |
| [107] | Gomes et al. (2020) | Remote Sensing | Overview of big Earth-observation data platforms. |
| [108] | Friedman (2001) | The Annals of Statistics | Gradient boosting machines. |

## 3. Research gaps

Eight gaps, each backed by the papers above. G1–G3 are the gaps from Review 0; G4–G8 are new. Each gap names the evidence, what this project does about it, and how that is measured. "Rarely" means rarely among the papers reviewed here.

### G1. There is no true reference image for SAR–optical fusion.

- **Evidence:** Fusion quality is judged by degrading a source image and comparing against it (Wald protocol), or with no-reference indices [15], [38]. This comes from pansharpening, where the panchromatic and multispectral bands measure the same physical quantity. SAR and optical do not, so no source image is a valid reference [13], [21], [22].
- **Our response:** We never score the fused image against a source image. Fused inputs are scored on a downstream task against land-cover reference labels.
- **Measured by:** Precision, recall and F1 against reference change maps.

### G2. The cross-modal gap between radar backscatter and surface reflectance is still open.

- **Evidence:** SAR and optical differ in geometry, radiometry and noise [30], [40]. Learned SAR-to-optical translation still produces artefacts and has clear limits [53], [54]. Even registering the two needs dedicated methods [55], [56], and change detection across sensors is a research area of its own [71]–[74].
- **Our response:** We do not claim to close the gap; we measure what it costs on a real task.
- **Measured by:** F1 difference between radar-only, optical-only and each fused input, using the same detector.

### G3. Image-quality metrics are rarely checked against how useful the fused image actually is.

- **Evidence:** Most SAR–optical fusion studies rank methods by SSIM, SAM, ERGAS, entropy or mutual information [22], [25]–[27], [34]–[37]. Few go on to test a downstream task [28], and wavelet results change with basis and depth [17], so a metric ranking may not carry over to the task.
- **Our response:** Quality metrics are reported next to task F1 for every fused input. If they disagree, that disagreement is a result.
- **Measured by:** SSIM, SAM, ERGAS, entropy and MI per method, compared with F1 rank.

### G4. SAR-guided cloud robustness is judged by how well pixels are reconstructed, not by whether the task still works under cloud.

- **Evidence:** Cloud cover is heaviest in tropical and monsoon regions [10], [11], and cloud masks are imperfect [12]. SAR-guided cloud removal [57], [58], [60], [61] and gap-filling [59], [62], [63] are scored by how closely they reconstruct pixels (PSNR, SSIM, SAM). Studies that combine optical and SAR for forest monitoring show the benefit in timeliness [80], [81], [84], but rarely under controlled, varying levels of cloud.
- **Our response:** A cloud stress test: synthetic cloud covering a set fraction of the optical image, with every input re-scored by the same detector.
- **Measured by:** F1 for each input, clear vs 35% cloud (already in `model_card.json`).

### G5. Fusion methods are rarely compared under one fixed detector across more than one kind of change.

- **Evidence:** Sentinel-1 + Sentinel-2 studies change the site, the sensor combination and the classifier together [91]–[94], and comparisons between fusion methods are usually made at one site for one task [27], [28]. Reviews note that results are site- and method-specific [13], [33].
- **Our response:** One detector recipe (same features, settings and clean-up) on six inputs, for two kinds of change (forest loss and urban growth), on held-out regions.
- **Measured by:** 6 inputs × 2 kinds of change × {clear, cloudy} F1 matrix.

### G6. Pixel-level and feature-level fusion are rarely compared head-to-head for change detection.

- **Evidence:** Fusion can happen at pixel, feature or decision level [13], [32], [31]. Decision-level [48]–[50] and deep feature-level [41], [44], [45] methods are each tested on their own. One of the few direct comparisons covers urban land-cover classification, not change [46].
- **Our response:** Three pixel-level fusions (IHS, PCA, wavelet) against a feature-level band stack, under the same detector.
- **Measured by:** F1 of IHS, PCA and wavelet vs the stacked bands.

### G7. SAR-based forest-loss monitoring is concentrated in flat lowland tropics; monsoon hill forest is under-studied.

- **Evidence:** Operational SAR deforestation work centres on the Congo Basin [82], French Guiana [84], the Amazon [85] and other lowland tropics [80], [83], [86]. North-East India is a deforestation hotspot [89], [90] in a monsoon climate [91], and its slopes distort C-band backscatter, which needs terrain flattening [7], [8].
- **Our response:** Training regions in the hills of North-East India, with no overlap between training and test regions. Radar-only weakness on hill forest is reported, not hidden.
- **Measured by:** Forest-loss F1 on NE-India held-out blocks; radar-only vs fused gap.

### G8. Change reference data is noisy and partly built from the optical sensor being tested.

- **Evidence:** Global 10 m land-cover products disagree substantially with each other [100]. Several, including Dynamic World [99] and the Esri / Impact Observatory map, are made from Sentinel-2, which biases scoring towards optical-only input. Good-practice guidance asks for independent reference data and area-adjusted accuracy [101]–[103]. Landsat-based Global Forest Change [78] is independent of Sentinel-2.
- **Our response:** Forest loss is scored against Global Forest Change, an independent Landsat-based reference. The Sentinel-2-derived urban reference is disclosed as a limitation.
- **Measured by:** Forest-loss F1 per input against Global Forest Change; urban F1 against Impact Observatory, with the bias stated.

### Summary for the slide

| # | Gap | Key refs | Our response |
|---|---|---|---|
| G1 | No true reference for fused SAR–optical images | [15] [22] [38] | Score a downstream task, not the image |
| G2 | Radar–optical cross-modal gap still open | [30] [40] [53] [71] | Measure what the gap costs in F1 |
| G3 | Quality metrics not checked against usefulness | [22] [27] [28] | Report both; disagreement is a result |
| G4 | Cloud robustness judged on pixels, not the task | [10] [57] [58] [80] | Synthetic-cloud stress test |
| G5 | No same-detector comparison across kinds of change | [27] [28] [33] [91] | 6 inputs × 2 kinds of change, one detector |
| G6 | Pixel- vs feature-level fusion not compared for change | [13] [32] [46] | IHS/PCA/wavelet vs band stack |
| G7 | Monsoon hill forest under-studied | [82] [84] [85] [89] [7] | NE-India training regions |
| G8 | Reference labels noisy and Sentinel-2-derived | [99] [100] [101] [78] | Score forest loss on Global Forest Change; disclose urban bias |

## 4. References

IEEE style. All DOIs checked against Crossref.

[1] R. Torres et al., "GMES Sentinel-1 mission," *Remote Sensing of Environment*, vol. 120, pp. 9–24, 2012. https://doi.org/10.1016/j.rse.2011.05.028

[2] M. Drusch et al., "Sentinel-2: ESA's Optical High-Resolution Mission for GMES Operational Services," *Remote Sensing of Environment*, vol. 120, pp. 25–36, 2012. https://doi.org/10.1016/j.rse.2011.11.026

[3] A. Moreira et al., "A tutorial on synthetic aperture radar," *IEEE Geoscience and Remote Sensing Magazine*, vol. 1, no. 1, pp. 6–43, 2013. https://doi.org/10.1109/mgrs.2013.2248301

[4] J.S. Lee, "Digital Image Enhancement and Noise Filtering by Use of Local Statistics," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. PAMI-2, no. 2, pp. 165–168, 1980. https://doi.org/10.1109/tpami.1980.4766994

[5] J.S. Lee, "Refined filtering of image noise using local statistics," *Computer Graphics and Image Processing*, vol. 15, no. 4, pp. 380–389, 1981. https://doi.org/10.1016/s0146-664x(81)80018-4

[6] F. Argenti et al., "A Tutorial on Speckle Reduction in Synthetic Aperture Radar Images," *IEEE Geoscience and Remote Sensing Magazine*, vol. 1, no. 3, pp. 6–35, 2013. https://doi.org/10.1109/mgrs.2013.2277512

[7] D. Small, "Flattening Gamma: Radiometric Terrain Correction for SAR Imagery," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 49, no. 8, pp. 3081–3093, 2011. https://doi.org/10.1109/tgrs.2011.2120616

[8] J. Truckenbrodt et al., "Towards Sentinel-1 SAR Analysis-Ready Data: A Best Practices Assessment on Preparing Backscatter Data for the Cube," *Data*, vol. 4, no. 3, art. 93, 2019. https://doi.org/10.3390/data4030093

[9] A. Mullissa et al., "Sentinel-1 SAR Backscatter Analysis Ready Data Preparation in Google Earth Engine," *Remote Sensing*, vol. 13, no. 10, art. 1954, 2021. https://doi.org/10.3390/rs13101954

[10] A.K. Whitcraft et al., "Cloud cover throughout the agricultural growing season: Impacts on passive optical earth observations," *Remote Sensing of Environment*, vol. 156, pp. 438–447, 2015. https://doi.org/10.1016/j.rse.2014.10.009

[11] M.D. King et al., "Spatial and Temporal Distribution of Clouds Observed by MODIS Onboard the Terra and Aqua Satellites," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 51, no. 7, pp. 3826–3852, 2013. https://doi.org/10.1109/tgrs.2012.2227333

[12] S. Skakun et al., "Cloud Mask Intercomparison eXercise (CMIX): An evaluation of cloud masking algorithms for Landsat 8 and Sentinel-2," *Remote Sensing of Environment*, vol. 274, art. 112990, 2022. https://doi.org/10.1016/j.rse.2022.112990

[13] C. Pohl and J.L. Van Genderen, "Multisensor image fusion in remote sensing: Concepts, methods and applications," *International Journal of Remote Sensing*, vol. 19, no. 5, pp. 823–854, 1998. https://doi.org/10.1080/014311698215748

[14] T.M. Tu et al., "A new look at IHS-like image fusion methods," *Information Fusion*, vol. 2, no. 3, pp. 177–186, 2001. https://doi.org/10.1016/s1566-2535(01)00036-7

[15] G. Vivone et al., "A Critical Comparison Among Pansharpening Algorithms," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 53, no. 5, pp. 2565–2586, 2015. https://doi.org/10.1109/tgrs.2014.2361734

[16] J. Nunez et al., "Multiresolution-based image fusion with additive wavelet decomposition," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 37, no. 3, pp. 1204–1211, 1999. https://doi.org/10.1109/36.763274

[17] K. Amolins, Y. Zhang and P. Dare, "Wavelet based image fusion techniques — An introduction, review and comparison," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 62, no. 4, pp. 249–263, 2007. https://doi.org/10.1016/j.isprsjprs.2007.05.009

[18] S.G. Mallat, "A theory for multiresolution signal decomposition: the wavelet representation," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 11, no. 7, pp. 674–693, 1989. https://doi.org/10.1109/34.192463

[19] H. Ghassemian, "A review of remote sensing image fusion methods," *Information Fusion*, vol. 32, pp. 75–89, 2016. https://doi.org/10.1016/j.inffus.2016.03.003

[20] J. Zhang, "Multi-source remote sensing data fusion: status and trends," *International Journal of Image and Data Fusion*, vol. 1, no. 1, pp. 5–24, 2010. https://doi.org/10.1080/19479830903561035

[21] S. Li et al., "Pixel-level image fusion: A survey of the state of the art," *Information Fusion*, vol. 33, pp. 100–112, 2017. https://doi.org/10.1016/j.inffus.2016.05.004

[22] S.C. Kulkarni and P.P. Rege, "Pixel level fusion techniques for SAR and optical images: A review," *Information Fusion*, vol. 59, pp. 13–29, 2020. https://doi.org/10.1016/j.inffus.2020.01.003

[23] L. Alparone et al., "Landsat ETM+ and SAR image fusion based on generalized intensity Modulation," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 42, no. 12, pp. 2832–2839, 2004. https://doi.org/10.1109/tgrs.2004.838344

[24] Y. Chibani, "Additive integration of SAR features into multispectral SPOT images by means of the à trous wavelet decomposition," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 60, no. 5, pp. 306–314, 2006. https://doi.org/10.1016/j.isprsjprs.2006.05.001

[25] G. Hong, Y. Zhang and B. Mercer, "A Wavelet and IHS Integration Method to Fuse High Resolution SAR with Moderate Resolution Multispectral Images," *Photogrammetric Engineering & Remote Sensing*, vol. 75, no. 10, pp. 1213–1223, 2009. https://doi.org/10.14358/pers.75.10.1213

[26] S.K. Pal, T.J. Majumdar and A.K. Bhattacharya, "ERS-2 SAR and IRS-1C LISS III data fusion: A PCA approach to improve remote sensing based geological interpretation," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 61, no. 5, pp. 281–297, 2007. https://doi.org/10.1016/j.isprsjprs.2006.10.001

[27] S. Abdikan et al., "A comparative data-fusion analysis of multi-sensor satellite images," *International Journal of Digital Earth*, vol. 7, no. 8, pp. 671–687, 2014. https://doi.org/10.1080/17538947.2012.748846

[28] F.B. Sanli et al., "Evaluation of image fusion methods using PALSAR, RADARSAT-1 and SPOT images for land use/ land cover classification," *Journal of the Indian Society of Remote Sensing*, vol. 45, no. 4, pp. 591–601, 2017. https://doi.org/10.1007/s12524-016-0625-y

[29] B. Aiazzi et al., "MTF-tailored Multiscale Fusion of High-resolution MS and Pan Imagery," *Photogrammetric Engineering & Remote Sensing*, vol. 72, no. 5, pp. 591–596, 2006. https://doi.org/10.14358/pers.72.5.591

[30] M. Schmitt and X.X. Zhu, "Data Fusion and Remote Sensing: An ever-growing relationship," *IEEE Geoscience and Remote Sensing Magazine*, vol. 4, no. 4, pp. 6–23, 2016. https://doi.org/10.1109/mgrs.2016.2561021

[31] P. Ghamisi et al., "Multisource and Multitemporal Data Fusion in Remote Sensing: A Comprehensive Review of the State of the Art," *IEEE Geoscience and Remote Sensing Magazine*, vol. 7, no. 1, pp. 6–39, 2019. https://doi.org/10.1109/mgrs.2018.2890023

[32] L. Gomez-Chova et al., "Multimodal Classification of Remote Sensing Images: A Review and Future Directions," *Proceedings of the IEEE*, vol. 103, no. 9, pp. 1560–1584, 2015. https://doi.org/10.1109/jproc.2015.2449668

[33] N. Joshi et al., "A Review of the Application of Optical and Radar Remote Sensing Data Fusion to Land Use Mapping and Monitoring," *Remote Sensing*, vol. 8, no. 1, art. 70, 2016. https://doi.org/10.3390/rs8010070

[34] Z. Wang et al., "Image quality assessment: from error visibility to structural similarity," *IEEE Transactions on Image Processing*, vol. 13, no. 4, pp. 600–612, 2004. https://doi.org/10.1109/tip.2003.819861

[35] Z. Wang and A.C. Bovik, "A universal image quality index," *IEEE Signal Processing Letters*, vol. 9, no. 3, pp. 81–84, 2002. https://doi.org/10.1109/97.995823

[36] F.A. Kruse et al., "The spectral image processing system (SIPS)—interactive visualization and analysis of imaging spectrometer data," *Remote Sensing of Environment*, vol. 44, no. 2-3, pp. 145–163, 1993. https://doi.org/10.1016/0034-4257(93)90013-n

[37] G. Qu, D. Zhang and P. Yan, "Information measure for performance of image fusion," *Electronics Letters*, vol. 38, no. 7, pp. 313–315, 2002. https://doi.org/10.1049/el:20020212

[38] L. Alparone et al., "Multispectral and Panchromatic Data Fusion Assessment Without Reference," *Photogrammetric Engineering & Remote Sensing*, vol. 74, no. 2, pp. 193–200, 2008. https://doi.org/10.14358/pers.74.2.193

[39] X.X. Zhu et al., "Deep Learning in Remote Sensing: A Comprehensive Review and List of Resources," *IEEE Geoscience and Remote Sensing Magazine*, vol. 5, no. 4, pp. 8–36, 2017. https://doi.org/10.1109/mgrs.2017.2762307

[40] X.X. Zhu et al., "Deep Learning Meets SAR: Concepts, models, pitfalls, and perspectives," *IEEE Geoscience and Remote Sensing Magazine*, vol. 9, no. 4, pp. 143–172, 2021. https://doi.org/10.1109/mgrs.2020.3046356

[41] D. Hong et al., "More Diverse Means Better: Multimodal Deep Learning Meets Remote-Sensing Imagery Classification," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 59, no. 5, pp. 4340–4354, 2021. https://doi.org/10.1109/tgrs.2020.3016820

[42] G. Masi et al., "Pansharpening by Convolutional Neural Networks," *Remote Sensing*, vol. 8, no. 7, art. 594, 2016. https://doi.org/10.3390/rs8070594

[43] G. Scarpa et al., "A CNN-Based Fusion Method for Feature Extraction from Sentinel Data," *Remote Sensing*, vol. 10, no. 2, art. 236, 2018. https://doi.org/10.3390/rs10020236

[44] D. Ienco et al., "Combining Sentinel-1 and Sentinel-2 Satellite Image Time Series for land cover mapping via a multi-source deep learning architecture," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 158, pp. 11–22, 2019. https://doi.org/10.1016/j.isprsjprs.2019.09.016

[45] P. Benedetti et al., "M3Fusion: A Deep Learning Architecture for Multiscale Multimodal Multitemporal Satellite Data Fusion," *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing*, vol. 11, no. 12, pp. 4939–4949, 2018. https://doi.org/10.1109/jstars.2018.2876357

[46] H. Zhang and R. Xu, "Exploring the optimal integration levels between SAR and optical data for better urban land cover mapping in the Pearl River Delta," *International Journal of Applied Earth Observation and Geoinformation*, vol. 64, pp. 87–95, 2018. https://doi.org/10.1016/j.jag.2017.08.013

[47] H. Zhang, H. Lin and Y. Li, "Impacts of Feature Normalization on Optical and SAR Data Fusion for Land Use/Land Cover Classification," *IEEE Geoscience and Remote Sensing Letters*, vol. 12, no. 5, pp. 1061–1065, 2015. https://doi.org/10.1109/lgrs.2014.2377722

[48] B. Waske and J.A. Benediktsson, "Fusion of Support Vector Machines for Classification of Multisensor Data," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 45, no. 12, pp. 3858–3866, 2007. https://doi.org/10.1109/tgrs.2007.898446

[49] B. Waske and S. van der Linden, "Classifying Multilevel Imagery From SAR and Optical Sensors by Decision Fusion," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 46, no. 5, pp. 1457–1466, 2008. https://doi.org/10.1109/tgrs.2008.916089

[50] Z. Shao et al., "Mapping Urban Impervious Surface by Fusing Optical and SAR Data at the Decision Level," *Remote Sensing*, vol. 8, no. 11, art. 945, 2016. https://doi.org/10.3390/rs8110945

[51] M. Belgiu and L. Drăguţ, "Random forest in remote sensing: A review of applications and future directions," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 114, pp. 24–31, 2016. https://doi.org/10.1016/j.isprsjprs.2016.01.011

[52] L. Ma et al., "Deep learning in remote sensing applications: A meta-analysis and review," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 152, pp. 166–177, 2019. https://doi.org/10.1016/j.isprsjprs.2019.04.015

[53] M. Fuentes Reyes et al., "SAR-to-Optical Image Translation Based on Conditional Generative Adversarial Networks—Optimization, Opportunities and Limits," *Remote Sensing*, vol. 11, no. 17, art. 2067, 2019. https://doi.org/10.3390/rs11172067

[54] L. Wang et al., "SAR-to-Optical Image Translation Using Supervised Cycle-Consistent Adversarial Networks," *IEEE Access*, vol. 7, pp. 129136–129149, 2019. https://doi.org/10.1109/access.2019.2939649

[55] Y. Ye et al., "Robust Registration of Multimodal Remote Sensing Images Based on Structural Similarity," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 55, no. 5, pp. 2941–2958, 2017. https://doi.org/10.1109/tgrs.2017.2656380

[56] L.H. Hughes, M. Schmitt and X.X. Zhu, "Mining Hard Negative Samples for SAR-Optical Image Matching Using Generative Adversarial Networks," *Remote Sensing*, vol. 10, no. 10, art. 1552, 2018. https://doi.org/10.3390/rs10101552

[57] A. Meraner et al., "Cloud removal in Sentinel-2 imagery using a deep residual neural network and SAR-optical data fusion," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 166, pp. 333–346, 2020. https://doi.org/10.1016/j.isprsjprs.2020.05.013

[58] P. Ebel et al., "Multisensor Data Fusion for Cloud Removal in Global and All-Season Sentinel-2 Imagery," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 59, no. 7, pp. 5866–5878, 2021. https://doi.org/10.1109/tgrs.2020.3024744

[59] H. Shen et al., "Missing Information Reconstruction of Remote Sensing Data: A Technical Review," *IEEE Geoscience and Remote Sensing Magazine*, vol. 3, no. 3, pp. 61–85, 2015. https://doi.org/10.1109/mgrs.2015.2441912

[60] J.D. Bermudez et al., "Synthesis of Multispectral Optical Images From SAR/Optical Multitemporal Data Using Conditional Generative Adversarial Networks," *IEEE Geoscience and Remote Sensing Letters*, vol. 16, no. 8, pp. 1220–1224, 2019. https://doi.org/10.1109/lgrs.2019.2894734

[61] J. Gao et al., "Cloud Removal with Fusion of High Resolution Optical and SAR Images Using Generative Adversarial Networks," *Remote Sensing*, vol. 12, no. 1, art. 191, 2020. https://doi.org/10.3390/rs12010191

[62] Q. Zhang et al., "Missing Data Reconstruction in Remote Sensing Image With a Unified Spatial–Temporal–Spectral Deep Convolutional Neural Network," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 56, no. 8, pp. 4274–4288, 2018. https://doi.org/10.1109/tgrs.2018.2810208

[63] A. Garioud et al., "Recurrent-based regression of Sentinel time series for continuous vegetation monitoring," *Remote Sensing of Environment*, vol. 263, art. 112419, 2021. https://doi.org/10.1016/j.rse.2021.112419

[64] A. Singh, "Digital change detection techniques using remotely-sensed data," *International Journal of Remote Sensing*, vol. 10, no. 6, pp. 989–1003, 1989. https://doi.org/10.1080/01431168908903939

[65] D. Lu et al., "Change detection techniques," *International Journal of Remote Sensing*, vol. 25, no. 12, pp. 2365–2401, 2004. https://doi.org/10.1080/0143116031000139863

[66] M. Hussain et al., "Change detection from remotely sensed images: From pixel-based to object-based approaches," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 80, pp. 91–106, 2013. https://doi.org/10.1016/j.isprsjprs.2013.03.006

[67] F. Bovolo and L. Bruzzone, "A Theoretical Framework for Unsupervised Change Detection Based on Change Vector Analysis in the Polar Domain," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 45, no. 1, pp. 218–236, 2007. https://doi.org/10.1109/tgrs.2006.885408

[68] Y. Bazi, L. Bruzzone and F. Melgani, "An unsupervised approach based on the generalized Gaussian model to automatic change detection in multitemporal SAR images," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 43, no. 4, pp. 874–887, 2005. https://doi.org/10.1109/tgrs.2004.842441

[69] M. Gong et al., "Change Detection in Synthetic Aperture Radar Images Based on Deep Neural Networks," *IEEE Transactions on Neural Networks and Learning Systems*, vol. 27, no. 1, pp. 125–138, 2016. https://doi.org/10.1109/tnnls.2015.2435783

[70] W. Shi et al., "Change Detection Based on Artificial Intelligence: State-of-the-Art and Challenges," *Remote Sensing*, vol. 12, no. 10, art. 1688, 2020. https://doi.org/10.3390/rs12101688

[71] J. Liu et al., "A Deep Convolutional Coupling Network for Change Detection Based on Heterogeneous Optical and Radar Images," *IEEE Transactions on Neural Networks and Learning Systems*, vol. 29, no. 3, pp. 545–559, 2018. https://doi.org/10.1109/tnnls.2016.2636227

[72] L.T. Luppino et al., "Unsupervised Image Regression for Heterogeneous Change Detection," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 57, no. 12, pp. 9960–9975, 2019. https://doi.org/10.1109/tgrs.2019.2930348

[73] G. Mercier, G. Moser and S.B. Serpico, "Conditional Copulas for Change Detection in Heterogeneous Remote Sensing Images," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 46, no. 5, pp. 1428–1441, 2008. https://doi.org/10.1109/tgrs.2008.916476

[74] R. Touati, M. Mignotte and M. Dahmane, "Multimodal Change Detection in Remote Sensing Images Using an Unsupervised Pixel Pairwise-Based Markov Random Field Model," *IEEE Transactions on Image Processing*, vol. 29, pp. 757–767, 2020. https://doi.org/10.1109/tip.2019.2933747

[75] S. Saha, F. Bovolo and L. Bruzzone, "Unsupervised Deep Change Vector Analysis for Multiple-Change Detection in VHR Images," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 57, no. 6, pp. 3677–3693, 2019. https://doi.org/10.1109/tgrs.2018.2886643

[76] Z. Zhu, "Change detection using landsat time series: A review of frequencies, preprocessing, algorithms, and applications," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 130, pp. 370–384, 2017. https://doi.org/10.1016/j.isprsjprs.2017.06.013

[77] C.E. Woodcock et al., "Transitioning from change detection to monitoring with remote sensing: A paradigm shift," *Remote Sensing of Environment*, vol. 238, art. 111558, 2020. https://doi.org/10.1016/j.rse.2019.111558

[78] M.C. Hansen et al., "High-Resolution Global Maps of 21st-Century Forest Cover Change," *Science*, vol. 342, no. 6160, pp. 850–853, 2013. https://doi.org/10.1126/science.1244693

[79] M.C. Hansen et al., "Humid tropical forest disturbance alerts using Landsat data," *Environmental Research Letters*, vol. 11, no. 3, art. 034008, 2016. https://doi.org/10.1088/1748-9326/11/3/034008

[80] J. Reiche et al., "Fusing Landsat and SAR time series to detect deforestation in the tropics," *Remote Sensing of Environment*, vol. 156, pp. 276–293, 2015. https://doi.org/10.1016/j.rse.2014.10.001

[81] J. Reiche et al., "Combining satellite data for better tropical forest monitoring," *Nature Climate Change*, vol. 6, no. 2, pp. 120–122, 2016. https://doi.org/10.1038/nclimate2919

[82] J. Reiche et al., "Forest disturbance alerts for the Congo Basin using Sentinel-1," *Environmental Research Letters*, vol. 16, no. 2, art. 024005, 2021. https://doi.org/10.1088/1748-9326/abd0a8

[83] A. Bouvet et al., "Use of the SAR Shadowing Effect for Deforestation Detection with Sentinel-1 Time Series," *Remote Sensing*, vol. 10, no. 8, art. 1250, 2018. https://doi.org/10.3390/rs10081250

[84] M. Ballère et al., "SAR data for tropical forest disturbance alerts in French Guiana: Benefit over optical imagery," *Remote Sensing of Environment*, vol. 252, art. 112159, 2021. https://doi.org/10.1016/j.rse.2020.112159

[85] J. Doblas et al., "Optimizing Near Real-Time Detection of Deforestation on Tropical Rainforests Using Sentinel-1 Data," *Remote Sensing*, vol. 12, no. 23, art. 3922, 2020. https://doi.org/10.3390/rs12233922

[86] M. Watanabe et al., "Early-Stage Deforestation Detection in the Tropics With L-band SAR," *IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing*, vol. 11, no. 6, pp. 2127–2133, 2018. https://doi.org/10.1109/jstars.2018.2810857

[87] N. Joshi et al., "Mapping dynamics of deforestation and forest degradation in tropical forests using radar satellite data," *Environmental Research Letters*, vol. 10, no. 3, art. 034014, 2015. https://doi.org/10.1088/1748-9326/10/3/034014

[88] A.L. Mitchell, A. Rosenqvist and B. Mora, "Current remote sensing approaches to monitoring forest degradation in support of countries measurement, reporting and verification (MRV) systems for REDD+," *Carbon Balance and Management*, vol. 12, no. 1, 2017. https://doi.org/10.1186/s13021-017-0078-9

[89] C. Sudhakar Reddy et al., "Quantification and monitoring of deforestation in India over eight decades (1930–2013)," *Biodiversity and Conservation*, vol. 25, no. 1, pp. 93–116, 2016. https://doi.org/10.1007/s10531-015-1033-2

[90] N. Lele and P.K. Joshi, "Analyzing deforestation rates, spatial forest cover changes and identifying critical areas of forest cover changes in North-East India during 1972–1999," *Environmental Monitoring and Assessment*, vol. 156, no. 1-4, pp. 159–170, 2009. https://doi.org/10.1007/s10661-008-0472-6

[91] M.J. Steinhausen et al., "Combining Sentinel-1 and Sentinel-2 data for improved land use and land cover mapping of monsoon regions," *International Journal of Applied Earth Observation and Geoinformation*, vol. 73, pp. 595–604, 2018. https://doi.org/10.1016/j.jag.2018.08.011

[92] N. Clerici, C.A. Valbuena Calderón and J.M. Posada, "Fusion of Sentinel-1A and Sentinel-2A data for land cover mapping: a case study in the lower Magdalena region, Colombia," *Journal of Maps*, vol. 13, no. 2, pp. 718–726, 2017. https://doi.org/10.1080/17445647.2017.1372316

[93] P.A. Tavares et al., "Integration of Sentinel-1 and Sentinel-2 for Classification and LULC Mapping in the Urban Area of Belém, Eastern Brazilian Amazon," *Sensors*, vol. 19, no. 5, art. 1140, 2019. https://doi.org/10.3390/s19051140

[94] J. Haas and Y. Ban, "Sentinel-1A SAR and sentinel-2A MSI data fusion for urban ecosystem service mapping," *Remote Sensing Applications: Society and Environment*, vol. 8, pp. 41–53, 2017. https://doi.org/10.1016/j.rsase.2017.07.006

[95] H. Taubenböck et al., "Monitoring urbanization in mega cities from space," *Remote Sensing of Environment*, vol. 117, pp. 162–176, 2012. https://doi.org/10.1016/j.rse.2011.09.015

[96] T. Esch et al., "Urban Footprint Processor—Fully Automated Processing Chain Generating Settlement Masks From Global Data of the TanDEM-X Mission," *IEEE Geoscience and Remote Sensing Letters*, vol. 10, no. 6, pp. 1617–1621, 2013. https://doi.org/10.1109/lgrs.2013.2272953

[97] J. Hu, P. Ghamisi and X.X. Zhu, "Feature Extraction and Selection of Sentinel-1 Dual-Pol Data for Global-Scale Local Climate Zone Classification," *ISPRS International Journal of Geo-Information*, vol. 7, no. 9, art. 379, 2018. https://doi.org/10.3390/ijgi7090379

[98] N. Kussul et al., "Deep Learning Classification of Land Cover and Crop Types Using Remote Sensing Data," *IEEE Geoscience and Remote Sensing Letters*, vol. 14, no. 5, pp. 778–782, 2017. https://doi.org/10.1109/lgrs.2017.2681128

[99] C.F. Brown et al., "Dynamic World, Near real-time global 10 m land use land cover mapping," *Scientific Data*, vol. 9, no. 1, 2022. https://doi.org/10.1038/s41597-022-01307-4

[100] Z.S. Venter et al., "Global 10 m Land Use Land Cover Datasets: A Comparison of Dynamic World, World Cover and Esri Land Cover," *Remote Sensing*, vol. 14, no. 16, art. 4101, 2022. https://doi.org/10.3390/rs14164101

[101] P. Olofsson et al., "Good practices for estimating area and assessing accuracy of land change," *Remote Sensing of Environment*, vol. 148, pp. 42–57, 2014. https://doi.org/10.1016/j.rse.2014.02.015

[102] G.M. Foody, "Status of land cover classification accuracy assessment," *Remote Sensing of Environment*, vol. 80, no. 1, pp. 185–201, 2002. https://doi.org/10.1016/s0034-4257(01)00295-4

[103] R.G. Pontius and M. Millones, "Death to Kappa: birth of quantity disagreement and allocation disagreement for accuracy assessment," *International Journal of Remote Sensing*, vol. 32, no. 15, pp. 4407–4429, 2011. https://doi.org/10.1080/01431161.2011.552923

[104] M.A. Wulder et al., "Land cover 2.0," *International Journal of Remote Sensing*, vol. 39, no. 12, pp. 4254–4284, 2018. https://doi.org/10.1080/01431161.2018.1452075

[105] N. Gorelick et al., "Google Earth Engine: Planetary-scale geospatial analysis for everyone," *Remote Sensing of Environment*, vol. 202, pp. 18–27, 2017. https://doi.org/10.1016/j.rse.2017.06.031

[106] H. Tamiminia et al., "Google Earth Engine for geo-big data applications: A meta-analysis and systematic review," *ISPRS Journal of Photogrammetry and Remote Sensing*, vol. 164, pp. 152–170, 2020. https://doi.org/10.1016/j.isprsjprs.2020.04.001

[107] V. Gomes, G. Queiroz and K. Ferreira, "An Overview of Platforms for Big Earth Observation Data Management and Analysis," *Remote Sensing*, vol. 12, no. 8, art. 1253, 2020. https://doi.org/10.3390/rs12081253

[108] J.H. Friedman, "Greedy function approximation: A gradient boosting machine," *The Annals of Statistics*, vol. 29, no. 5, 2001. https://doi.org/10.1214/aos/1013203451
