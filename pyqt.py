import os
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QMessageBox,
    QTabWidget,
    QHeaderView
)
import pandas as pd
from pandasgui import show
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QComboBox,
    QTableView, QPushButton, QLabel, QMessageBox, QWidget, QLineEdit, QTabWidget
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtCore import Qt, QAbstractTableModel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from utils import load_data
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
                       generate_dm_plots
                       )
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
                      generate_ae_plots
                )

from ce_checks import (check_ce_missing_month
                       )

from cm_checks import (check_cm_cmdecod,
                       check_cm_cmindc,
                       check_cm_cmlat,
                       check_cm_missing_month
                       )
from dd_checks import (check_dd_ae_aedthdtc_ds_dsstdtc,
                       check_dd_ae_aeout_aedthdtc,
                       check_dd_death_date
                       )
from ds_checks import (check_ds_ae_discon,
                       check_ds_dsdecod_death,
                       check_ds_dsdecod_dsstdtc,
                       check_ds_dsscat,
                       check_ds_dsterm_death_due_to,
                       check_ds_duplicate_randomization,
                       check_ds_ex_after_discon,
                       check_ds_multdeath_dsstdtc,
                       check_ds_sc_strat,
                       comp_status_dis,
                       study_status_arm,
                       dispo_time,
                       sub_stat_epoch,
                       dispo_event,
                       dispo_reas
                       )
from dv_checks import (check_dv_ae_aedecod_covid,
                       check_dv_covid
                       )
from eg_checks import (check_eg_egdtc_visit_ordinal_error
                       )
from ex_checks import (check_ex_dup,
                       check_ex_exdose_exoccur,
                       check_ex_exdose_pos_exoccur_no,
                       check_ex_exdosu,
                       check_ex_exoccur_exdose_exstdtc,
                       check_ex_exoccur_mis_exdose_nonmis,
                       check_ex_exstdtc_after_dd,
                       check_ex_exstdtc_visit_ordinal_error,
                       check_ex_extrt_exoccur,
                       check_ex_infusion_exstdtc_exendtc,
                       check_ex_visit,
                       dose_overtime,
                       dose_cumdose
                       )
from lb_checks import (check_lb_lbdtc_after_dd,
                       check_lb_lbdtc_visit_ordinal_error,
                       check_lb_lbstnrlo_lbstnrhi,
                       check_lb_lbstresc_char,
                       check_lb_lbstresn_missing,
                       check_lb_lbstresu,
                       check_lb_missing_month,
                       check_dtc_time_format,
                       generate_lbtest_plot,
                       update_param_plot
                       )
from mh_checks import (check_mh_missing_month
                       )
from mi_checks import (check_mi_mispec
                       )
from pr_checks import (check_pr_missing_month,
                       check_pr_prlat
                       )
from qs_checks import (check_qs_dup,
                       check_qs_qsdtc_after_dd,
                       check_qs_qsdtc_visit_ordinal_error,
                       check_qs_qsstat_qsreasnd,
                       check_qs_qsstat_qsstresc
                       
                       )
from rs_checks import (check_rs_rscat_rsscat,
                       check_rs_rsdtc_across_visit,
                       check_rs_rsdtc_visit
                      )
from sc_checks import (check_sc_dm_eligcrit
                       )
from ss_checks import (check_ss_ssdtc_alive_dm,
                       check_ss_ssdtc_dead_ds,
                       check_ss_ssdtc_dead_dthdtc,
                       surv_dist
                       #check_ss_ssstat_ssorres
                       )
from tr_checks import (check_tr_dup,
                       check_tr_trdtc_across_visit,
                       check_tr_trdtc_visit_ordinal_error,
                       check_tr_trstresn_ldiam
                       )
from ts_checks import (check_ts_aedict,
                       check_ts_cmdict,
                       check_ts_sstdtc_ds_consent
                       )
from tu_checks import (check_tu_rs_new_lesions,
                       check_tu_tudtc,
                       check_tu_tudtc_across_visit,
                       check_tu_tudtc_visit_ordinal_error,
                       check_tu_tuloc_missing
                       )
from vs_checks import (check_vs_height,
                       check_vs_sbp_lt_dbp,
                       check_vs_vsdtc_after_dd
                       )
from sv_checks import (check_sv_svstdtc_visit_ordinal_error,
                       check_sv_dupc_visit,
                       subject_compliance_plot,
                       visit_timing_distribution_plot,
                       visit_sequence_plot,
                       cumulative_visit_completion_plot,
                       subject_dropout_analysis_plot


                       )
from se_checks import (subject_timeline,
                       subject_time_spent,
                       subject_duration,
                       study_elements
                        )           
from cdisc_gil_req_vars import(req_vars)
from mean_plot import(generate_test_plot)
from specs_transform import specs_transform
from dates_all_chk import process_datasets
from narrative import generate_domain_narrative
#project = "p123"
#study = "s123456"

#ata_path = f"G:/projects/{project}/{study}/csdtm_dev/draft1/sdtmdata"


   
# Load the dataframe]
# Run the check function
#result = check_ae_aeacn_ds_disctx_covid()
def run_checks(data_path):
    print(f"Running checks in data path: {data_path}")
    results = [

        check_dm_actarm_arm(data_path),
        check_dm_ae_ds_death(data_path),
        check_dm_age_missing(data_path),
        #check_dm_armnrs_missing(data_path),
        #check_dm_armcd(data_path),
        #check_dm_arm_scrnfl(data_path),
        check_dm_ds_icdtc(data_path),
        #check_dm_rficdtc(data_path),
        #check_dm_usubjid_ae_usubjid(data_path),
        check_dm_usubjid_dup(data_path),
        check_dm_dthfl_dthdtc(data_path),
        #check_dm_usubjid_ae_usubjid(data_path),
        check_dm_usubjid_dup(data_path),
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
        check_ae_withdr_ds_discon(data_path),
        check_ce_missing_month(data_path),
        check_cm_cmdecod(data_path),
        #check_cm_cmindc(data_path)
        check_cm_cmlat(data_path),
        check_cm_missing_month(data_path),
        check_dd_ae_aedthdtc_ds_dsstdtc(data_path),
        check_dd_ae_aeout_aedthdtc(data_path),
        check_dd_death_date(data_path),
        check_ds_ae_discon(data_path),
        check_ds_dsdecod_death(data_path),
        check_ds_dsdecod_dsstdtc(data_path),
        check_ds_dsscat(data_path),
        check_ds_dsterm_death_due_to(data_path),
        check_ds_duplicate_randomization(data_path),
        check_ds_ex_after_discon(data_path),
        check_ds_multdeath_dsstdtc(data_path),
        check_ds_sc_strat(data_path),
        check_dv_ae_aedecod_covid(data_path),
        check_dv_covid(data_path),
        check_eg_egdtc_visit_ordinal_error(data_path),
        check_ex_dup(data_path),
        check_ex_exdose_exoccur(data_path),
        check_ex_exdose_pos_exoccur_no(data_path),
        check_ex_exdosu(data_path),
        #check_ex_exoccur_exdose_exstdtc(data_path) check this later on date time function 
        check_ex_exoccur_mis_exdose_nonmis(data_path),
        check_ex_exstdtc_after_dd(data_path),
        check_ex_exstdtc_visit_ordinal_error(data_path),
        check_ex_extrt_exoccur(data_path),
        check_ex_infusion_exstdtc_exendtc(data_path),
        check_ex_visit(data_path),
        check_lb_lbdtc_after_dd(data_path),
        check_lb_lbdtc_visit_ordinal_error(data_path),#re-check
        check_lb_lbstnrlo_lbstnrhi(data_path), #re-check
        check_lb_lbstresc_char(data_path),
        check_lb_lbstresn_missing(data_path),
        check_lb_lbstresu(data_path),
        check_lb_missing_month(data_path),
        check_dtc_time_format(data_path),
        check_mh_missing_month(data_path),
        check_mi_mispec(data_path),
        check_pr_missing_month(data_path),
        #check_pr_prlat(data_path) #modify this later 
        check_qs_dup(data_path),
        check_qs_qsdtc_after_dd(data_path),
        check_qs_qsdtc_visit_ordinal_error(data_path),
        check_qs_qsstat_qsreasnd(data_path),
        check_qs_qsstat_qsstresc(data_path),
        check_rs_rscat_rsscat(data_path),
        check_rs_rsdtc_across_visit(data_path),
        check_rs_rsdtc_visit(data_path),
        check_sc_dm_eligcrit(data_path),
        check_ss_ssdtc_alive_dm(data_path),
        check_ss_ssdtc_dead_ds(data_path),
        check_ss_ssdtc_dead_dthdtc(data_path),
        #check_ss_ssstat_ssorres(data_path),
        check_tr_dup(data_path),
        check_tr_trdtc_across_visit(data_path),
        check_tr_trdtc_visit_ordinal_error(data_path),
        check_tr_trstresn_ldiam(data_path),
        check_ts_aedict(data_path),
        check_ts_cmdict(data_path),
        check_ts_sstdtc_ds_consent(data_path),
        check_tu_rs_new_lesions(data_path),
        check_tu_tudtc(data_path),
        check_tu_tudtc_across_visit(data_path),
        check_tu_tudtc_visit_ordinal_error(data_path),
        check_tu_tuloc_missing(data_path),
        check_vs_height(data_path),
        check_vs_sbp_lt_dbp(data_path),
        check_vs_vsdtc_after_dd(data_path),
        check_sv_svstdtc_visit_ordinal_error(data_path),
        check_sv_dupc_visit(data_path)


        
    ]

    combined_results = pd.concat(results, ignore_index=True)

    # Extract unique datasets from 'Datasets' column
    unique_datasets = set()
    for datasets in combined_results["Datasets"]:
        if isinstance(datasets, str):
            for dataset in datasets.split(", "):
                unique_datasets.add(dataset.upper())

    # List of all dataset files
    all_files = [f for f in os.listdir(data_path) if f.endswith('.sas7bdat') and not f.lower().startswith('supp')]
    file_datasets = set([os.path.splitext(f)[0].upper() for f in all_files])

    # Find missing files
    missing_files = list(file_datasets - unique_datasets)

    # Prepare summary data
    summary_data = []
    detailed_data = {}
    for i, result in enumerate(results):
        if result.empty:
            continue

        check_name = result["CHECK"].iloc[0]
        status = str(result["Message"].iloc[0])
        notes = result["Notes"].iloc[0] if 'Notes' in result.columns else ""
        datasets = result["Datasets"].iloc[0] if 'Datasets' in result.columns else ""
        
        if "Fail" in status:
            sheet_name = f'Sheet{i+1}'
            detailed_data[check_name] = result  # Store the detailed DataFrame
            data_link = f"View Data"
        else:
            data_link = ""
        summary_data.append({
            "CHECK": check_name,
            "Message": status,
            "Notes": notes,
            "Datasets": datasets,
            "Data": data_link
        })

    # Adding missing files to summary
    missing_files_notes = f'Checks not performed for datasets: {", ".join(missing_files)}'
    summary_data.append({
        "CHECK": "Checks not performed",
        "Message": "Fail",
        "Notes": missing_files_notes,
        "Datasets": "",
        "Data": ""
    })

    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df[
    ~summary_df["Message"].str.contains("dataset not found at the specified location", na=False, case=False)
]
    return summary_df, detailed_data

# Main Window

class PandasTableModel(QStandardItemModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.load_data()

    def load_data(self):
        # Load pandas DataFrame into QStandardItemModel
        for col_index, column in enumerate(self._data.columns):
            self.setHorizontalHeaderItem(col_index, QStandardItem(column))
        for row_index, row in self._data.iterrows():
            for col_index, value in enumerate(row):
                self.setItem(row_index, col_index, QStandardItem(str(value)))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDTM Quality Checks")
        self.setGeometry(100, 100, 1200, 800)

        # Main widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Dropdowns for project, study, and analysis folder
        self.project_dropdown = QComboBox()
        self.study_dropdown = QComboBox()
        self.analysis_folder_dropdown = QComboBox()
        self.project_dropdown.addItems(self.get_projects())

        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Project:"))
        dropdown_layout.addWidget(self.project_dropdown)
        dropdown_layout.addWidget(QLabel("Study:"))
        dropdown_layout.addWidget(self.study_dropdown)
        dropdown_layout.addWidget(QLabel("Analysis Folder:"))
        dropdown_layout.addWidget(self.analysis_folder_dropdown)
        self.layout.addLayout(dropdown_layout)

        # Run Checks Button
        self.run_checks_button = QPushButton("Run Checks")
        self.run_checks_button.clicked.connect(self.run_checks)
        self.layout.addWidget(self.run_checks_button)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Load data dynamically when project/study/folder changes
        self.project_dropdown.currentTextChanged.connect(self.update_study_dropdown)
        self.study_dropdown.currentTextChanged.connect(self.update_analysis_folders)

    def get_projects(self):
        base_dir = "G:/users/inarisetty"
        return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    def update_study_dropdown(self):
        selected_project = self.project_dropdown.currentText()
        if not selected_project:
            return
        project_path = os.path.join("G:/users/inarisetty", selected_project)
        self.study_dropdown.clear()
        self.study_dropdown.addItems(
            [d for d in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, d))]
        )

    def update_analysis_folders(self):
        selected_project = self.project_dropdown.currentText()
        selected_study = self.study_dropdown.currentText()
        if not selected_project or not selected_study:
            return
        study_path = os.path.join("G:/users/inarisetty", selected_project, selected_study)
        self.analysis_folder_dropdown.clear()
        self.analysis_folder_dropdown.addItems(
            [d for d in os.listdir(study_path) if os.path.isdir(os.path.join(study_path, d))]
        )

    def run_checks(self):
        # Validate dropdown selections
        selected_project = self.project_dropdown.currentText()
        selected_study = self.study_dropdown.currentText()
        selected_folder = self.analysis_folder_dropdown.currentText()

        if not selected_project or not selected_study or not selected_folder:
            QMessageBox.warning(self, "Error", "Please select a project, study, and folder.")
            return

        # Construct data path
        data_path = os.path.join("G:/users/inarisetty", selected_project, selected_study, selected_folder)

        try:
            # Run checks and load results
            global summary_df, detailed_data
            summary_df, detailed_data = run_checks(data_path)

            # Dynamically find datasets in the folder
            dataset_files = [
                f for f in os.listdir(data_path) if f.endswith('.sas7bdat') and not f.lower().startswith('supp')
            ]
            dataset_names = [os.path.splitext(f)[0].upper() for f in dataset_files]

            # Display the summary tab
            self.display_summary_tab(summary_df)

            # Display dataset-specific tabs
            self.display_dataset_tabs(dataset_names, data_path)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while running checks:\n{str(e)}")


    def display_dataset_tabs(self, dataset_names, data_path):
        # Add a tab for each dataset
        for dataset_name in dataset_names:
            try:
                # Create a new tab for the dataset
                tab = QWidget()
                layout = QVBoxLayout(tab)

                # Load a dummy DataFrame (replace with actual data loading logic)
                dataset_df = load_data(data_path, dataset_name)

                # Create a QTableView to display the dataset
                filter_layout = QHBoxLayout()
                filter_inputs = []

                model = PandasTableModel(dataset_df)
                proxy_model = QSortFilterProxyModel()
                proxy_model.setSourceModel(model)
                proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

                table = QTableView()
                table.setModel(proxy_model)
                table.setSortingEnabled(True)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                layout.addWidget(table)

                # Add dynamic filter inputs for each column
                for i, col_name in enumerate(dataset_df.columns):
                    label = QLabel(f"Filter {col_name}:")
                    line_edit = QLineEdit()
                    line_edit.setPlaceholderText(f"Enter filter for {col_name}")
                    line_edit.textChanged.connect(lambda text, col=i: self.apply_filter(proxy_model, col, text))
                    filter_layout.addWidget(label)
                    filter_layout.addWidget(line_edit)
                    filter_inputs.append(line_edit)

                layout.addLayout(filter_layout)

                # Add the tab to the main tab widget
                self.tabs.addTab(tab, dataset_name)
            
            except Exception as e:
                # Handle errors gracefully and inform the user
                error_label = QLabel(f"Error loading dataset '{dataset_name}': {str(e)}")
                error_label.setStyleSheet("color: red; font-weight: bold;")
                tab = QWidget()
                layout = QVBoxLayout(tab)
                layout.addWidget(error_label)
                self.tabs.addTab(tab, dataset_name)

    def apply_filter(self, proxy_model, column_index, filter_text):
        # Apply filter for the given column
        proxy_model.setFilterKeyColumn(column_index)
        proxy_model.setFilterRegularExpression(filter_text)

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
