import pandas as pd
from dash import html
def generate_domain_narrative(domain_name, df):
    """
    Generate a narrative for a single domain.

    Parameters:
        domain_name (str): Name of the domain.
        df (pd.DataFrame): Filtered DataFrame for the domain.

    Returns:
        str: Narrative for the domain.
    """
    if df.empty:
        return f"No data available for {domain_name}.\n"

    narrative = ""

    if domain_name == "DM":  # Demographics
        subjid = df.get("SUBJID", [None]).iloc[0]
        site = subjid.split('-')[0] if subjid else None
        age = df.get("AGE", [None]).iloc[0]
        sex = df.get("SEX", [None]).iloc[0]
        race = df.get("RACE", [None]).iloc[0]
        if "BRTHDTC" in df.columns:
            brthdtc = df.get("BRTHDTC", [None]).iloc[0]
        else:
            brthdtc = 'Missing'  # Default value if ARMNRS does not exist
        #brthdtc = df.get("BRTHDTC", [None]).iloc[0]
        rficdtc = df.get("RFICDTC", [None]).iloc[0]
        rfstdtc = df.get("RFSTDTC", [None]).iloc[0]
        rfendtc = df.get("RFENDTC", [None]).iloc[0]
        rfxstdtc = df.get("RFXSTDTC", [None]).iloc[0]
        rfxendtc = df.get("RFXENDTC", [None]).iloc[0]
        arm = df.get("ARM", [None]).iloc[0]
        actarm = df.get("ACTARM", [None]).iloc[0]
        
        # Check if ARMNRS exists in the DataFrame
        if "ARMNRS" in df.columns:
            armnrs = df.get("ARMNRS", [None]).iloc[0]
        else:
            armnrs = None  # Default value if ARMNRS does not exist

        # Check if ARMNRS is non-missing
        if armnrs:
            narrative += (
                f"The subject identified as {subjid} is a {age}-year-old, {sex}, {race} individual born on {brthdtc}, "
                f"enrolled at site {site}. Participant signed the informed consent on {rficdtc}.\n"
            )
            narrative += (
                f"The subject was not assigned to a treatment arm and is categorized under '{armnrs}'. "
                f"Planned Arm and Actual Arm are not applicable (null).\n"
            )
        else:
            narrative += (
                f"The subject identified as {subjid} is a {age}-year-old, {sex}, {race} individual born on {brthdtc}, "
                f"enrolled at site {site}. Participant signed the informed consent on {rficdtc}, began study participation "
                f"on {rfstdtc} and ended on {rfendtc}. \n"
            )
            narrative += (
                f"Participant first study treatment is on {rfxstdtc} and last study treatment is on {rfxendtc}.\n"
            )
            narrative += f"Subject Planned Arm is {arm} and Actual Arm is {actarm}.\n"


    elif domain_name == "AE":  # Adverse Events
        narrative = [html.P("The subject experienced the following adverse events:")]

        for _, row in df.iterrows():
            ae_desc = row.get("AEDECOD", "Unknown event")
            ae_date = row.get("AESTDTC", "Unknown date")
            ae_end_date = row.get("AEENDTC", None)  # End date
            ae_enrtpt = row.get("AEENRTPT", None)  # Ongoing flag
            aeser = row.get("AESER", "Unknown")  # Serious Event
            aerel = row.get("AEREL", "Unknown")  # Relationship to study drug
            aesdth = row.get("AESDTH", "N")  # Death flag
            aesdth_date = row.get("AESDTDTC", "Unknown date")  # Date of death

            # Handle severity
            if "AESEV" in row and not pd.isna(row["AESEV"]):
                ae_sev = row["AESEV"]
            elif "AETOXGR" in row and not pd.isna(row["AETOXGR"]):
                ae_toxgr = pd.to_numeric(row["AETOXGR"], errors="coerce")
                if ae_toxgr > 3:
                    ae_sev = html.Span(f"Toxicity Grade: {ae_toxgr}", style={"color": "red"})
                else:
                    ae_sev = f"Toxicity Grade: {ae_toxgr}"
            else:
                ae_sev = "Unknown severity"

            # Format Serious Event (AESER)
            aeser_text = "SERIOUS" if aeser == "Y" else "NOT SERIOUS"

            # Format Relationship to Study Drug (AEREL)
            aerel_text = aerel if aerel else "Unknown relationship"

            # Handle end date logic
            if ae_end_date:
                end_text = f"ended on {ae_end_date}"
            elif ae_enrtpt == "ONGOING":
                end_text = html.Span("Ongoing", style={"color": "violet"})
            else:
                end_text = html.Span("Missing end date", style={"color": "Red"})

            # Build narrative for each adverse event
            if aesdth == "Y":
                narrative.append(html.P([
                    f"- {ae_desc} on {ae_date} (", end_text, f") with {ae_sev}. ",
                    f"This event was ({aeser_text}), and {aerel_text} to the study drug, ",
                    f"and the subject died on {aesdth_date}."
                ]))
            else:
                narrative.append(html.Div([
                    f"- {ae_desc} on {ae_date} (", end_text, f") with {ae_sev}. ",
                    f"This event was ({aeser_text}) and {aerel_text} to the study drug."
                ]))

    elif domain_name == "LB":  # Lab Results
        narrative += "The following flagged lab results were recorded:\n"

        # Filter records with LBNRIND values LOW or HIGH
        flagged_records = df[df["LBNRIND"].isin(["LOW", "HIGH"])]

        if flagged_records.empty:
            narrative += "No lab results with HIGH or LOW flags were recorded.\n"
        else:
            for _, row in flagged_records.iterrows():
                lb_test = row.get("LBTEST", "Unknown test")
                lb_result = row.get("LBSTRESC", "Unknown result")
                lb_flag = row.get("LBNRIND", "No flag")
                visit = row.get("VISIT", "Unknown visit")
                lb_tox = row.get("LBTOX", None)  # Handle LBTOX if it exists
                lb_toxgr = row.get("LBTOXGR", None)  # Handle LBTOXGR if it exists

                # Construct the narrative for each record
                result_text = f"- {lb_test}: {lb_result} ({lb_flag}) during {visit}"
                if lb_tox:
                    result_text += f", Toxicity: {lb_tox}"
                if lb_toxgr:
                    if pd.to_numeric(lb_toxgr, errors='coerce') > 3:
                        result_text += f", Toxicity Grade: <span style='color: red;'>{lb_toxgr}</span>"
                    else:
                        result_text += f", Toxicity Grade: {lb_toxgr}"
                result_text += ".\n"

                narrative += result_text

    elif domain_name == "SE":  # Study Elements
        narrative += "The subject participated in the following study elements:\n"
        for _, row in df.iterrows():
            element = row.get("ELEMENT", "Unknown element")
            start_date = row.get("SESTDTC", "Unknown start date")
            end_date = row.get("SEENDTC", "Unknown end date")
            narrative += f"- {element} from {start_date} to {end_date}.\n"
    elif domain_name == "SV":  # Study Visits
        # Filter out 'UNSHED' visits and count scheduled visits
        scheduled_visits = df[~df["VISIT"].str.upper().str.contains("UNSCHED", na=False)]
        unscheduled_visits = df[df["VISIT"].str.upper().str.contains("UNSCHED", na=False)]

        num_scheduled_visits = scheduled_visits.shape[0]
        num_unscheduled_visits = unscheduled_visits.shape[0]

        # Safeguard: Check if 'SVSTDTC' exists and exclude null/empty values
        if "SVSTDTC" in scheduled_visits.columns:
            valid_dates = scheduled_visits["SVSTDTC"].dropna().loc[scheduled_visits["SVSTDTC"] != ""]
            
            # Get the screening date and its corresponding visit
            if not valid_dates.empty:
                screening_index = valid_dates.idxmin()
                screening_date = scheduled_visits.loc[screening_index, "SVSTDTC"]
                screening_visit = scheduled_visits.loc[screening_index, "VISIT"]
            else:
                screening_date = "Unknown screening date"
                screening_visit = "Unknown visit"
            
            # Get the last visit date and its corresponding visit
            if not valid_dates.empty:
                last_visit_index = valid_dates.idxmax()
                last_visit_date = scheduled_visits.loc[last_visit_index, "SVSTDTC"]
                last_visit_name = scheduled_visits.loc[last_visit_index, "VISIT"]
            else:
                last_visit_date = "Unknown last visit date"
                last_visit_name = "Unknown visit"
        else:
            screening_date = "Unknown screening date"
            screening_visit = "Unknown visit"
            last_visit_date = "Unknown last visit date"
            last_visit_name = "Unknown visit"

        # Construct the narrative
        narrative += f"The subject completed {num_scheduled_visits} scheduled visits and {num_unscheduled_visits} unscheduled visits.\n"
        narrative += f"First Visit: {screening_visit} on {screening_date}\n"
        narrative += f"Last Visit: {last_visit_name} on {last_visit_date}\n"
    elif domain_name == "CM":  # Concomitant Medications
        # Extract subject-level details
        subjid = df.get("USUBJID", [None]).iloc[0]
        
        # Initialize narrative as a list of Dash HTML components
        narrative = [
            html.P(f"The subject identified as {subjid} received the following concomitant medications during the study:")
        ]

        # Group medications by CMCAT (Category)
        if "CMCAT" in df.columns:
            categories = df["CMCAT"].unique()
            for category in categories:
                if pd.isna(category) or category == "":
                    category = "Uncategorized"
                narrative.append(html.P(f"Under {category}:"))
                
                grouped_df = df[df["CMCAT"] == category]
                for _, row in grouped_df.iterrows():
                    cmtrt = row.get("CMTRT", "Unknown medication")
                    cmroute = row.get("CMROUTE", "Unknown route")
                    cmdose = row.get("CMDOSE", "Unknown dose")
                    cmdosu = row.get("CMDOSU", "Unknown unit")
                    cmindc = row.get("CMINDC", "Unknown indication")
                    cmstdtc = row.get("CMSTDTC", "Unknown start date")
                    cmendtc = row.get("CMENDTC", None)
                    cmongo = row.get("CMONGO", "N")

                    # Handle null CMENDTC
                    if pd.isna(cmendtc) or cmendtc == "":
                        if "CMENRTPT" in row and not pd.isna(row["CMENRTPT"]):
                            cmendtc_text = html.Span(row["CMENRTPT"], style={"color": "violet"})
                        else:
                            cmendtc_text = html.Span("End date is missing", style={"color": "red"})
                    else:
                        cmendtc_text = html.Span(cmendtc)

                    # Format ongoing medications
                    if cmongo == "Y":
                        narrative.append(html.P([
                            f"- {cmtrt} (administered {cmroute}, dose: {cmdose} {cmdosu}) was ongoing for the indication of {cmindc} and started on {cmstdtc}. Ended: ",
                            cmendtc_text
                        ]))
                    else:
                        narrative.append(html.Div([
                            f"- {cmtrt} (administered {cmroute}, dose: {cmdose} {cmdosu}) was taken for the indication of {cmindc} from {cmstdtc} to ",
                            cmendtc_text,
                            "."
                        ]))
        else:
            # Handle case where CMCAT is not present
            narrative.append(html.P("No category information is available for the concomitant medications."))

    elif domain_name == "EX":
        subjid = df.get("USUBJID", [None]).iloc[0]
        narrative = []
        narrative.append(
                html.P(
                    f"The subject identified as {subjid} received follow treatments: "
                   
                )
            )        
        # Group by EXTRT (Treatment)
        for extrt, group in df.groupby("EXTRT"):
            group = group.sort_values(by=["EXSTDTC"])  # Sort within each group by start date

            # Get minimum start date and maximum end date with corresponding visits
            min_start_date = group["EXSTDTC"].min()
            max_end_date = group["EXENDTC"].max()
            visit_start = group.loc[group["EXSTDTC"] == min_start_date, "VISIT"].iloc[0] if "VISIT" in group.columns else "Unknown visit"
            visit_end = group.loc[group["EXENDTC"] == max_end_date, "VISIT"].iloc[0] if "VISIT" in group.columns else "Unknown visit"

            # Add treatment-level summary
            narrative.append(
                html.P(
                    f"{extrt} starting on {min_start_date} during {visit_start} "
                    f"and ending on {max_end_date} during {visit_end}."
                )
            )

            # Initialize variables to track the previous dose and treatment
            prev_dose = None
            prev_dosu = None

            # Track dose change messages
            dose_changes = []

            for _, row in group.iterrows():
                exdose = row.get("EXDOSE", "Unknown dose")
                exdosu = row.get("EXDOSU", "Unknown unit")
                exstdtc = row.get("EXSTDTC", "Unknown start date")
                visit = row.get("VISIT", "Unknown visit")

                # Check if there is a dose change compared to the previous record
                if prev_dose is not None:
                    if exdose > prev_dose:
                        dose_changes.append(
                            html.Div(
                                f"- The dose of {extrt} was increased from {prev_dose} {prev_dosu} to {exdose} {exdosu} "
                                f"on {exstdtc} during {visit}."
                            )
                        )
                    elif exdose < prev_dose:
                        dose_changes.append(
                            html.Div(
                                f"- The dose of {extrt} was reduced from {prev_dose} {prev_dosu} to {exdose} {exdosu} "
                                f"on {exstdtc} during {visit}."
                            )
                        )

                # Update previous values for the next iteration
                prev_dose = exdose
                prev_dosu = exdosu

            # If no dose changes were recorded, add a default message
            if not dose_changes:
                dose_changes.append(html.Div(f"No dose changes were recorded for {extrt}."))

            # Add dose change messages to the narrative
            narrative.extend(dose_changes)
    elif domain_name == "DS":  # Disposition
        narrative = [html.Div("The subject had the following disposition events during the study:")]

        # Group the data by DSCAT (Disposition Category)
        grouped_df = df.groupby("DSCAT")

        for dscat, group in grouped_df:
            # Add category-level heading
            narrative.append(html.P(f"Category: {dscat if pd.notna(dscat) else 'Unknown Category'}"))

            # Further group by DSSCAT
            if "DSSCAT" in group.columns:
                sub_grouped_df = group.groupby("DSSCAT")
                for dsscat, sub_group in sub_grouped_df:
                    # Add subcategory-level heading
                    narrative.append(html.Div(f"Subcategory: {dsscat if pd.notna(dsscat) else 'Unknown Subcategory'}"))

                    for _, row in sub_group.iterrows():
                        ds_term = row.get("DSTERM", "Unknown disposition term")
                        ds_decod = row.get("DSDECOD", "Unknown coded term")
                        ds_date = row.get("DSSTDTC", None)  # Disposition date

                        # Handle missing DSSTDTC
                        if pd.isna(ds_date):
                            ds_date_text = html.Span("date missing (DSSTDTC)", style={"color": "red"})
                        else:
                            ds_date_text = f"on {ds_date}"

                        # Add narrative entry for each record
                        narrative.append(html.Div([
                            f"- The subject experienced the disposition event '{ds_term}' ",
                            f"(coded as '{ds_decod}') ", ds_date_text, "."
                        ]))
            else:
                # If DSSCAT does not exist, only group by DSCAT
                for _, row in group.iterrows():
                    ds_term = row.get("DSTERM", "Unknown disposition term")
                    ds_decod = row.get("DSDECOD", "Unknown coded term")
                    ds_date = row.get("DSSTDTC", None)  # Disposition date

                    # Handle missing DSSTDTC
                    if pd.isna(ds_date):
                        ds_date_text = html.Span("date missing (DSSTDTC)", style={"color": "red"})
                    else:
                        ds_date_text = f"on {ds_date}"

                    # Add narrative entry for each record
                    narrative.append(html.Div([
                        f"- The subject experienced the disposition event '{ds_term}' ",
                        f"(coded as '{ds_decod}') ", ds_date_text, "."
                    ]))



    # Add logic for other domains as needed
    # else:
    #     narrative += f"Key data points from {domain_name}:\n"
    #     narrative += df.to_string(index=False)

    return narrative

