# Power BI Web Smoke Test

Purpose: confirm that the Power BI service in a browser supports what the report needs, before any report is built. The input `data/samples/powerbi_smoke_test_SYNTHETIC.xlsx` holds **synthetic values**, not EIA data. It has three sheets: `FactHourly` (672 rows), `DimDate` and `DimBA`.

1. **Import.** Go to app.powerbi.com, open **My workspace**, then **New item → Semantic model** (or **+ New → Upload a file**). Upload the workbook and select all three sheets.
2. **Relationships.** Open the semantic model and choose **Open data model** (in some tenants: **Edit tables**). Create:
   - `FactHourly[local_date]` → `DimDate[date]` (many-to-one, single direction)
   - `FactHourly[ba_code]` → `DimBA[ba_code]` (many-to-one)
3. **DAX measures.** On `FactHourly`, choose **New measure**:
   ```DAX
   Abs Error MW = SUMX ( FactHourly, ABS ( FactHourly[forecast_mw] - FactHourly[actual_mw] ) )
   WAPE = DIVIDE ( [Abs Error MW], SUM ( FactHourly[actual_mw] ) )
   Weekend WAPE = CALCULATE ( [WAPE], DimDate[is_weekend] = TRUE () )
   ```
4. **Report.** Choose **Create report** (blank). Add a **slicer** on `DimBA[ba_code]` and a **line chart** with `FactHourly[local_hour]` on the x-axis and `WAPE` as the value. Changing the slicer should change the chart. Save.
5. **Export checks.** Record the results of each:
   - Report: **File → Export → PDF**. Does it work?
   - Semantic model settings or **⋯** menu: is there **Download this file** (.pbix)?
   - Workspace settings: is **Git integration** available? That exports TMDL, but needs Fabric/Premium capacity.
   - Is there a **TMDL view** or **Export model** option in web modeling?
   - Your license type: Free, Pro or PPU (shown under the profile icon).

Report back pass/fail for steps 1–5 and what step 5 showed.
