# Crop-table verification extract — 2026-10-30

Every quoted value below was read from the saved artifact in `FieldShift_Data/raw/crops/` on 2026-10-30.
File hash lists are in `metadata/retrieval_log.jsonl`.

## 1. FAO-56 Ch.6 Tables 11/12 — artifact `fao56_ch6_tables11_12_fetched_20261030.txt` (sha256 36199f…)

Table 11 rows used (stages ini/dev/mid/late = total; plant date; source location):
* Cotton 30/50/60/55 = 195 · Mar–May · **"Egypt; Pakistan; Calif."** (only Egypt-labelled row)
* Barley/Oats/Wheat 20/50/60/30 = 160 · Dec · "Calif. Desert, USA"
* Maize (grain) 30/40/50/30 = 150 · April · "Spain (spr, sum.); Calif."
* Rice 30/30/60/30 = 150 · "Dec; May" · Tropics; Mediterranean
* Sugar beet 35/60/70/40 = 205 · Nov · Arid Regions
* Sorghum 20/35/45/30 · "Mar/April" · Arid Region — table prints total 140 but stages sum to 130 (inconsistency present in the original table; a second row 20/35/40/30 = 130 'May/June, USA, Pakis., Med.')
* Wheat: no T. aestivum stage row apart from Winter Wheat (Dec, Calif., USA 20/60…70/30=180 with footnote digits; Mediterranean Nov 30/140/40/30 = 240).

Table 12 single Kc: cereals ini 0.30; wheat mid 1.15 end 0.25–0.40 (footnote digit merges into "0.25-0.410"); winter wheat ini 0.7 non-frozen soils / 0.4 frozen; maize grain 1.20 mid, end 0.60–0.35 ("0.60-0.3511"); grain sorghum mid 1.00–1.10 end 0.55; rice 1.05/1.20/0.90–0.60; cotton 0.35/1.15–1.20/0.70–0.50; sugar beet 0.35/1.20/0.70 ("0.705" = footnote 5); fababean dry 0.50/1.15/0.30 (fresh end 1.10); "Clover hay, Berseem — averaged cutting effects 0.40/0.90/0.85, individual cutting periods 0.40/1.15/1.10".

## 2. FAO-29 Rev.1 — artifact `fao29_rev1_salt_tolerance_20261030.htm`

Table 4 "Crop tolerance and yield potential … (ECe/ECw at 100%/90%/75%/50%/0% yield)", ECe at 100% yield (dS/m):
* Wheat (Triticum aestivum) **6.0** (damages line contains footnote digits "4 , 6"); Wheat, durum 5.7
* Cotton (Gossypium **hirsutum**) **7.7**
* Sugarbeet **7.0** (footnote 5 digit), Sorghum **6.8**, Barley 8.0
* Rice (paddy) **3.0**, Corn (maize) **1.7**, Broadbean (Vicia faba) **1.5**, Bean (Phaseolus) 1.0
* **Berseem: no numeric row.** §5 "Relative salt tolerance …" lists **"Clover, Berseem (Trifolium alexandrinum)"** under the **MODERATELY SENSITIVE** group (alongside maize, rice, broadbean, alfalfa…). No ECe threshold printed.

## 3. FAO water management manual — artifacts in `fao_water_manual/`

Ch.2 (s2022e02) **Table 5 "Approximate values of seasonal crop water needs"** (mm/total growing period):
Barley/Oats/Wheat 450–650 · Bean 300–500 · Cotton 700–1300 · Maize 500–800 · Rice (paddy) 450–700 · Sorghum/Millet 450–650 · Sugarbeet 550–750 · **no berseem row** (alfalfa 800–1600 is a related forage but a different crop).

Ch.3 (s2022e07) **Table 14 "Indicative values of crop water needs and sensitivity to drought"** — printed classes:
Barley/Oats/Wheat **low-medium** · Bean **medium-high** · Cotton **low** · Maize **medium-high** · Rice (paddy) **high** · Sorghum/Millet **low** · Sugarbeet **low-medium** · berseem absent.
Ch.4 (s2022e08) paddy rice: SAT = 200 mm; PERC 4–8 mm/day (soil-dependent); WL 100 mm → ETc excludes percolation; gross water need higher.

FAO-66 (Steduto et al. 2012, i2800e) Ch.2 Table 1 "Seasonal Ky values from FAO I&D Paper No. 33": cotton 0.85, grain sorghum/millet 0.9, sugarbeet 1.0, maize 1.25, beans 1.15, winter wheat 1.05 / spring wheat 1.15, **no rice row**; berseem/clover absent.

## 4. FAO crop calendar (lastUpdated 26/02/2021) — artifacts `fao_dhlg_cropcalendar_egy_20261030.json` (DHLG API) and `fao_crop_calendar_by_country_all_20261030.csv` (data catalog); the two agree

Delta region sessions (Sowing → Harvest; DHLG `growing_period` days):
* Wheat, bread: Sowing 11-15 → 11-30; Harvest 04-25 → 05-25; growing_period 150–190
* Bean, broad (faba): Sowing 10-01 → 11-15; Harvest 04-15 → 05-01; growing_period 180–190
* Beet, sugar: Sowing 10-01 → 10-20; Harvest 04-10 → 05-01; growing_period 170–200
* Barley: Sowing 11-10 → 12-15; not in the 8-crop table (reference only)

No Delta session exists for **rice, grain maize, cotton, berseem** in either FAO calendar. The only rice session: Middle Egypt Region ("Fayoum") — Sowing 04-20 → 05-10; Harvest 08-01 → 09-30; growing_period 120–150. Sorghum: Middle Egypt ("Giza, Fayoum and Beni Sweaf") Sowing 05-10 → 06-01 (Upper Egypt later: 06-01 → 06-25); growing_period 110–130. Corn, sweet only: NDRORL "yellow grain types", Sowing 02-20 → 10-15, growing_period 75–100 (not grain maize).

## 5. FAO i3500e "Egyptian Clover" (Dost et al. 2014) — artifact `fao_i3500e_berseem_20261030.pdf`

* p.66 (1-based): "In Egypt farmers sow berseem from mid September till late November." + NFCRP yield effects of sowing date.
* p.32 (1-based): "Berseem grows during the entire winter from October to May" — a printed span, not a day count.
* p.26 agronomy chapter: sowing recommended "late September to end of October"; seed rate 20–25 kg/ha.
* No mm/season water-requirement figure printed (WUE ratios only) → berseem water need stays `missing`.

## 6. Egypt maize sowing dates (North Delta peer-reviewed trial)

Hegab, Fayed, Hamada et al., 2019, *Arab Universities Journal of Agricultural Sciences*, DOI **10.21608/ajs.2019.43523** — "Growth parameters, irrigation requirements and productivity of maize in relation to sowing dates under North-Delta of Egypt conditions": field trial at El-Bosaily (Northern Coastal Egypt), single-cross 10 hybrid, sowing dates **1 May / 1 June / 1 July**; productivity and WUE decreased as sowing delayed beyond 1 May; 1 July lowest. PDF not archivable (HTTP 429) — DOI + OpenAlex abstract snapshot recorded in `metadata/retrieval_log.jsonl`. Corroboration: FAO GIEWS Egypt Country Brief (ref. 30-06-2026): "sowing operations for the 2026 rice and maize crops also began in May".

## 7. EcoCrop mirror — artifact `EcoCrop_DB.csv` (sha256 4187e8…) + `Ecocrop_variable_lookup.csv` (units confirmed) + `ecocrop_extract_for_fieldshift.json`

Per-variety rows used (°C / pH): wheat (T. aestivum) 15–23 opt, 5–27 abs, KTMP 0; maize (Z. mays) 18–33 opt, 10–47 abs; rice (O. sativa) 20–30 opt, 10–36 abs; cotton (**G. barbadense**!) 22–32 opt, 15–38 abs; sugar beet (B. vulgaris) 15–25 opt, 4–35 abs, KTMP 0 / rest −3; faba (V. faba) 18–28 opt, 5–32 abs; berseem (T. alexandrinum) 16–27 opt, 3–35 abs, KTMP −2 / rest −8; sorghum (S. bicolor) 22–35 opt, 8–40 abs. Optimal/absolute pH in `ecocrop_extract_for_fieldshift.json`; cycle spans GMIN–GMAX recorded there only.
