# Power BI Web Smoke Test

Purpose: confirm that the Power BI service in a browser supports what the report needs, before any report is built. The input `data/samples/powerbi_smoke_test_SYNTHETIC.xlsx` holds **synthetic values**, not EIA data. It has three sheets: `FactHourly` (672 rows), `DimDate` and `DimBA`.

1. **Import.** Go to app.powerbi.com, open **My workspace**, then **New item → Semantic model** (or **+ New → Upload a file**). Upload the workbook and select all three sheets.
2. **Relationships.** Open the semantic model and choose **Open data model** (in some tenants: **Edit tables**). Create:
   - `FactHourly[ref_date]` → `DimDate[date]` (many-to-one, single direction)
   - `FactHourly[ba_code]` → `DimBA[ba_code]` (many-to-one)
3. **DAX measures.** On `FactHourly`, choose **New measure**:
   ```DAX
   Abs Error MW = SUMX ( FactHourly, ABS ( FactHourly[forecast_mw] - FactHourly[actual_mw] ) )
   WAPE = DIVIDE ( [Abs Error MW], SUM ( FactHourly[actual_mw] ) )
   Weekend WAPE = CALCULATE ( [WAPE], DimDate[is_weekend] = TRUE () )
   ```
4. **Report.** Choose **Create report** (blank). Add a **slicer** on `DimBA[ba_code]` and a **line chart** with `FactHourly[ref_hour]` on the x-axis and `WAPE` as the value. Changing the slicer should change the chart. Save.
5. **Export checks.** Record the results of each:
   - Report: **File → Export → PDF**. Does it work?
   - Semantic model settings or **⋯** menu: is there **Download this file** (.pbix)?
   - Workspace settings: is **Git integration** available? That exports TMDL, but needs Fabric/Premium capacity.
   - Is there a **TMDL view** or **Export model** option in web modeling?
   - Your license type: Free, Pro or PPU (shown under the profile icon).

Report back pass/fail for steps 1–5 and what step 5 showed.

## Result (2026-09-24, browser automation)

**Verified** (synthetic data only; model "DFP smoke test SYNTHETIC" in My workspace):
- **Account:** university organizational account, Microsoft Fabric (Free) license, My workspace.
- **Local `.xlsx` upload:** rejected by the service ("no longer supports the upload of Excel files from local folders").
- **OneDrive route:** the workbook uploaded privately to OneDrive for Business and read through the Power Query Online Excel connector. All three sheets were visible.
- **Table selection:** the navigator checkboxes aren't exposed to automation. Worked around with Power Query **Blank query** M expressions (`Excel.Workbook(Web.Contents(url))`) plus explicit types. All three tables loaded with correct types, including `date` and `datetime`.
- **Semantic model:** "Create a semantic model only" succeeded.
- **Web model editing:** it opened in Editing mode, showing Model view, **DAX query view**, **TMDL View (Preview)**, and Manage relationships and New measure buttons (screenshot: `docs/evidence/powerbi_web_model_editing_SYNTHETIC.png`).

**Not verified**, because the modeling surface is an iframe the automation's accessibility snapshot doesn't expose:
- creating relationships;
- DAX measures;
- the slicer and chart;
- slicer interaction;
- PDF export;
- .pbix download;
- whether TMDL view content can be exported or saved;
- Git integration.

Findings for the real build: use CSV with ISO dates (`data/bi/`) and set types explicitly. Excel produced serial dates and unpromoted headers.
