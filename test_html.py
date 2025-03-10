import os
import json
import pyreadstat
from utils import load_data

data_path = "G:/users/inarisetty/private/sdtm_checks_311/cdisc"  # <-- update this path
import os
import json
import pyreadstat
import pandas as pd
from collections import OrderedDict

# === IMPORT YOUR CHECK FUNCTIONS (ensure these modules are available) ===
from dm_checks import (check_dm_actarm_arm,
                       check_dm_ae_ds_death,
                       check_dm_age_missing,
                       check_dm_armnrs_missing,
                       check_dm_armcd,
                       check_dm_dthfl_dthdtc,
                       check_dm_usubjid_ae_usubjid,
                       check_dm_usubjid_dup,
                       check_dm_arm_scrnfl,
                       check_dm_ds_icdtc,
                       check_dm_rficdtc,
                       generate_dm_plots)
from ae_checks import (check_ae_aeacn_ds_disctx_covid,
                       check_ae_aeacnoth,
                       check_ae_aeacnoth_ds_disctx,
                       check_ae_aeacnoth_ds_stddisc_covid,
                       check_ae_aedecod,
                       check_ae_aedthdtc_aesdth,
                       check_ae_aedthdtc_ds_death,
                       check_ae_aeout,
                       check_ae_aeout_aeendtc_aedthdtc,
                       check_ae_aeout_aeendtc_nonfatal,
                       check_ae_aerel,
                       check_ae_aesdth_aedthdtc,
                       check_ae_aestdtc_after_aeendtc,
                       check_ae_aestdtc_after_dd,
                       check_ae_aetoxgr,
                       check_ae_death,
                       check_ae_ds_partial_death_dates,
                       check_ae_dup,
                       check_ae_fatal,
                       check_ae_withdr_ds_discon,
                       generate_ae_plots)
# ... (import other check modules as needed)
from specs_transform import specs_transform
from dates_all_chk import process_datasets
from narrative import generate_domain_narrative

# === RUN CHECKS FUNCTION ===
def run_checks(data_path):
    results = [
        check_dm_actarm_arm(data_path),
        check_dm_ae_ds_death(data_path),
        check_dm_age_missing(data_path),
        # ... (include all your desired checks)
        check_ae_aeacn_ds_disctx_covid(data_path),
        check_ae_aeacnoth(data_path),
        check_ae_aeacnoth_ds_disctx(data_path),
        check_ae_aeacnoth_ds_stddisc_covid(data_path),
        check_ae_aedecod(data_path),
        check_ae_aedthdtc_aesdth(data_path),
        check_ae_aedthdtc_ds_death(data_path),
        check_ae_aeout(data_path),
        check_ae_aeout_aeendtc_aedthdtc(data_path),
        check_ae_aeout_aeendtc_nonfatal(data_path),
        check_ae_aerel(data_path),
        check_ae_aesdth_aedthdtc(data_path),
        check_ae_aestdtc_after_aeendtc(data_path),
        check_ae_aestdtc_after_dd(data_path),
        check_ae_aetoxgr(data_path),
        check_ae_death(data_path),
        check_ae_ds_partial_death_dates(data_path),
        check_ae_dup(data_path),
        check_ae_fatal(data_path),
        check_ae_withdr_ds_discon(data_path)
    ]
    combined_results = pd.concat(results, ignore_index=True)
  
    unique_datasets = set()
    for ds in combined_results["Datasets"]:
        if isinstance(ds, str):
            for dataset in ds.split(", "):
                unique_datasets.add(dataset.upper())
  
    all_files = [f for f in os.listdir(data_path) if f.endswith('.sas7bdat') and not f.lower().startswith('supp')]
    file_datasets = set([os.path.splitext(f)[0].upper() for f in all_files])
    missing_files = list(file_datasets - unique_datasets)
  
    summary_data = []
    detailed_data = {}
    for i, result in enumerate(results):
        if result.empty:
            continue
        check_name = result["CHECK"].iloc[0]
        status = str(result["Message"].iloc[0])
        notes = result["Notes"].iloc[0] if 'Notes' in result.columns else ""
        ds_val = result["Datasets"].iloc[0] if 'Datasets' in result.columns else ""
        if "Fail" in status:
            detailed_data[check_name] = result
            data_link = "View Data"
        else:
            data_link = ""
        summary_data.append({
            "CHECK": check_name,
            "Message": status,
            "Notes": notes,
            "Datasets": ds_val,
            "Data": data_link
        })
  
    missing_files_notes = f'Checks not performed for datasets: {", ".join(missing_files)}'
    summary_data.append({
        "CHECK": "Checks not performed",
        "Message": "Fail",
        "Notes": missing_files_notes,
        "Datasets": "",
        "Data": ""
    })
  
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df[~summary_df["Message"].str.contains("dataset not found at the specified location", na=False, case=False)]
    return summary_df, detailed_data

# === MAIN SECTION ===

# Update this path to point to your SAS datasets folder.
#data_path = r"C:\path\to\your\sasdata"  # <-- update this path

# Run the checks to produce the summary DataFrame.
summary_df, detailed_data = run_checks(data_path)

# Read each SAS dataset into a dictionary (excluding supplemental files).
dataframes = {}
for file in os.listdir(data_path):
    if file.lower().endswith(".sas7bdat") and not file.lower().startswith('supp'):
        file_path = os.path.join(data_path, file)
        try:
            df, meta = pyreadstat.read_sas7bdat(file_path)
            dataset_name = os.path.splitext(file)[0]
            dataframes[dataset_name] = df.to_dict(orient="records")
            print(f"Loaded dataset {dataset_name} with {len(df)} rows.")
        except Exception as e:
            print(f"Error loading {file}: {e}")

# Combine the summary and the datasets into an ordered dictionary.
overall_data = OrderedDict()
overall_data["Summary"] = summary_df.to_dict(orient="records")
for key in sorted(dataframes.keys()):
    overall_data[key] = dataframes[key]

# Convert overall_data to JSON.
overall_data_json = json.dumps(overall_data, default=str)

# === Generate HTML Content ===
html_content = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>SAS Data Viewer</title>
    <!-- AgGrid CSS (Alpine theme) -->
    <link rel="stylesheet" href="https://unpkg.com/ag-grid-community@26.2.0/dist/styles/ag-grid.css">
    <link rel="stylesheet" href="https://unpkg.com/ag-grid-community@26.2.0/dist/styles/ag-theme-alpine.css">
    <style>
      body {{
        font-family: Arial, sans-serif;
        margin: 20px;
      }}
      h1 {{
        text-align: center;
        color: #2E8B57;
        margin-bottom: 20px;
      }}
      .tab-buttons {{
        text-align: center;
        margin-bottom: 20px;
      }}
      .tab-buttons button {{
        padding: 10px 20px;
        margin: 0 5px;
        background-color: #2E8B57;
        border: none;
        border-radius: 5px;
        color: white;
        font-size: 16px;
        cursor: pointer;
      }}
      .tab-buttons button:hover {{
        background-color: #246d45;
      }}
      .tab-buttons button.active {{
        background-color: #FFA07A;
      }}
      .tab-content {{
        display: none;
      }}
      .tab-content.active {{
        display: block;
      }}
      .grid-container {{
        height: 500px;
        width: 100%;
        margin-bottom: 20px;
      }}
      .additional-content {{
        margin-bottom: 20px;
      }}
    </style>
  </head>
  <body>
    <h1>SAS Data Viewer</h1>
    <div id="tabButtons" class="tab-buttons"></div>
    <div id="tabContents"></div>
  
    <!-- AgGrid JavaScript (version 26.2.0) -->
    <script src="https://unpkg.com/ag-grid-community@26.2.0/dist/ag-grid-community.noStyle.js"></script>
    <script>
      // Embedded overall data object.
      var datasets = {overall_data_json};
  
      /**
       * Initialize AgGrid for a given container with the provided data.
       * Uses 'agSetColumnFilter' with a callback that computes unique values.
       * @param {{string}} containerId - The container div ID.
       * @param {{Array}} data - The array of data records.
       * @param {{boolean}} extended - If true, uses extended grid options.
       */
      function initializeGrid(containerId, data, extended) {{
        var columns = [];
        if (data.length > 0) {{
          columns = Object.keys(data[0]).map(function(key, index) {{
            var col = {{
              headerName: key,
              field: key,
              filter: 'agSetColumnFilter',
              filterParams: {{
                values: function(params) {{
                  var uniqueValues = Array.from(new Set(data.map(function(row) {{
                    return row[key];
                  }})));
                  params.success(uniqueValues);
                }}
              }},
              sortable: true
            }};
            if (extended && index === 0) {{
              col.checkboxSelection = true;
            }}
            return col;
          }});
        }}
  
        var gridOptions = {{
          columnDefs: columns,
          rowData: data,
          defaultColDef: {{
            resizable: true,
            filter: 'agSetColumnFilter',
            sortable: true,
            menuTabs: ["generalMenuTab", "filterMenuTab", "aggregationMenuTab"]
          }},
          rowSelection: extended ? 'multiple' : 'single',
          pagination: extended,
          paginationAutoPageSize: extended,
          sideBar: extended,
          rowDragManaged: extended,
          rowDragMultiRow: extended,
          rowDragEnterable: extended,
          enableMultiRowDragging: extended,
          components: {{
            agCheckbox: '<label class="ag-checkbox-label"><div class="ag-checkbox"></div></label>'
          }}
        }};
  
        var container = document.getElementById(containerId);
        container.innerHTML = "";
        new agGrid.Grid(container, gridOptions);
      }}
  
      /**
       * Create additional content for dataset tabs (non-Summary).
       * Adds a dropdown for filtering by USUBJID (if present) and a placeholder for summary checks.
       * @param {{string}} tabName - The dataset tab name.
       * @param {{Array}} data - The dataset records.
       */
      function createAdditionalContent(tabName, data) {{
        var container = document.getElementById(tabName);
        var extraHTML = "";
  
        if (data.length > 0 && data[0].hasOwnProperty("USUBJID")) {{
          var usubjids = Array.from(new Set(data.map(function(row) {{
            return row["USUBJID"];
          }})));
          extraHTML += "<div class='additional-content'>";
          extraHTML += "<label style='font-weight:bold;'>Select USUBJID to filter:</label><br/>";
          extraHTML += "<select id='usubjid-dropdown-" + tabName + "'><option value=''>-- All --</option>";
          usubjids.forEach(function(id) {{
            extraHTML += "<option value='" + id + "'>" + id + "</option>";
          }});
          extraHTML += "</select>";
          extraHTML += "<div id='filtered-grid-" + tabName + "' style='margin-top:15px; min-height:300px;'></div>";
          extraHTML += "</div>";
        }}
  
        container.insertAdjacentHTML("afterbegin", extraHTML);
  
        var dropdown = document.getElementById("usubjid-dropdown-" + tabName);
        if (dropdown) {{
          dropdown.addEventListener("change", function() {{
            var selected = this.value;
            var filteredData = selected ? data.filter(function(row) {{
              return row["USUBJID"] == selected;
            }}) : data;
            console.log("For tab " + tabName + ", filtering by USUBJID =", selected);
            var filteredContainer = document.getElementById("filtered-grid-" + tabName);
            if (filteredData.length === 0) {{
              filteredContainer.innerHTML = "<p style='text-align:center; color:red;'>No matching records.</p>";
            }} else {{
              initializeGrid("filtered-grid-" + tabName, filteredData, true);
            }}
          }});
        }}
  
        // Append a placeholder for summary checks.
        container.insertAdjacentHTML("beforeend", "<div class='additional-content'><h3 style='text-align:center;'>Summary Checks for " + tabName + " (Placeholder)</h3></div>");
      }}
  
      /**
       * Dynamically create tab buttons and content containers.
       * The first tab ("Summary") shows the summary_df.
       * Other tabs are for individual datasets and include additional content.
       */
      function createTabs() {{
        var tabButtonsContainer = document.getElementById("tabButtons");
        var tabContentsContainer = document.getElementById("tabContents");
  
        tabButtonsContainer.innerHTML = "";
        tabContentsContainer.innerHTML = "";
  
        var datasetNames = Object.keys(datasets);
  
        datasetNames.forEach(function(name, index) {{
          var btn = document.createElement("button");
          btn.className = "tab-btn";
          btn.textContent = name;
          btn.setAttribute("data-target", name);
          if (index === 0) {{
            btn.classList.add("active");
          }}
          tabButtonsContainer.appendChild(btn);
  
          var contentDiv = document.createElement("div");
          contentDiv.id = name;
          contentDiv.className = "tab-content ag-theme-alpine grid-container";
          contentDiv.innerHTML = "<p style='text-align:center;'>Loading " + name + "...</p>";
          if (index === 0) {{
            contentDiv.classList.add("active");
          }}
          tabContentsContainer.appendChild(contentDiv);
  
          if (name === "Summary") {{
            initializeGrid(name, datasets[name], false);
          }} else {{
            initializeGrid(name, datasets[name], true);
            createAdditionalContent(name, datasets[name]);
          }}
        }});
  
        var tabButtons = document.querySelectorAll(".tab-btn");
        tabButtons.forEach(function(btn) {{
          btn.addEventListener("click", function() {{
            tabButtons.forEach(function(b) {{ b.classList.remove("active"); }});
            document.querySelectorAll(".tab-content").forEach(function(c) {{ c.classList.remove("active"); }});
            this.classList.add("active");
            var target = this.getAttribute("data-target");
            document.getElementById(target).classList.add("active");
          }});
        }});
      }}
  
      document.addEventListener("DOMContentLoaded", function() {{
        createTabs();
      }});
    </script>
  </body>
</html>
"""

# Write the HTML content to a file.
output_filename = "sas_data_viewer.html"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML file generated: {output_filename}")
