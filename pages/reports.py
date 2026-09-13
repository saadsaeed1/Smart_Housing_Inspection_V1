from pathlib import Path
from datetime import date
import io
import base64
import streamlit as st
import pandas as pd

import config
from data_manager import PROJECT_ROOT, load_inspections, normalize_plot_number


def image_to_base64(img_path_str: str) -> str:
    """Converts a local image path to a base64 data URI for reliable HTML document embedding."""
    if not img_path_str or str(img_path_str).strip() in ["", "nan", "None"]:
        return ""
    
    raw_str = str(img_path_str).strip()
    candidate_paths = [
        Path(raw_str),
        PROJECT_ROOT / raw_str,
        Path.cwd() / raw_str,
    ]
    
    target_path = None
    for p in candidate_paths:
        if p.exists() and p.is_file():
            target_path = p
            break

    if not target_path:
        return ""

    try:
        suffix = target_path.suffix.lower().replace(".", "")
        mime = "image/jpeg" if suffix in ["jpg", "jpeg"] else f"image/{suffix}"
        with open(target_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""


def show_reports_page():
    st.header("📄 Statutory Notices & Municipal Export Engine")
    st.caption("Generate formal legal directives, print official Stop Work notices, and export municipal audit logs.")

    df_raw = load_inspections()

    if df_raw.empty:
        st.info("No inspection records available in the database to generate reports.")
        return

    df = df_raw.copy()
    df["Parsed_Date"] = pd.to_datetime(df["Inspection Date"], errors="coerce")
    df["Parsed_Deadline"] = pd.to_datetime(df["Deadline"], errors="coerce")
    df["Is_Stopped"] = df["Work Stopped"].apply(
        lambda x: True if str(x).strip().lower() in ["true", "yes", "1"] else False
    )

    tab_notices, tab_exports = st.tabs([
        "⚖️ Official Statutory Notices (Printable)",
        "📊 Municipal Registry & Audit Export"
    ])

    # ==================================================================
    # TAB 1: OFFICIAL STATUTORY NOTICES
    # ==================================================================
    with tab_notices:
        st.markdown("#### 🏛️ Statutory Notice & Executive Order Generator")
        st.caption("Select an inspection record to format an official municipal document with letterhead, evidence, and signature blocks.")

        col_n1, col_n2 = st.columns([1.5, 1.5])

        with col_n1:
            notice_type = st.selectbox(
                "Notice Classification",
                [
                    "🚨 Immediate Stop Work Notice & Site Sealing Order",
                    "⚠️ 7-Day Notice of Structural Non-Compliance",
                    "⚖️ Final Default Notice & Penalty Summons",
                    "✅ Official Site Clearance & Resumption Certificate",
                ]
            )

        if "Stop Work" in notice_type:
            candidate_df = df[df["Is_Stopped"] == True]
            if candidate_df.empty:
                candidate_df = df
        elif "7-Day" in notice_type or "Final Default" in notice_type:
            candidate_df = df[df["Compliance Status"] != "Compliant"]
            if candidate_df.empty:
                candidate_df = df
        else:
            candidate_df = df[df["Compliance Status"] == "Compliant"]
            if candidate_df.empty:
                candidate_df = df

        with col_n2:
            record_options = {
                f"{r['Plot Number']} (Sector {r['Sector']}) | {r['Inspection ID']} — {r['Construction Activity']} [{r['Compliance Status']}]": r
                for _, r in candidate_df.sort_values(by="Inspection Date", ascending=False).iterrows()
            }
            selected_label = st.selectbox("Select Target Plot & Inspection Record", list(record_options.keys()))

        record = record_options[selected_label]

        clean_plot = str(record.get('Plot Number', 'N/A')).strip().replace(' ', '')
        notice_id = f"MNC-PLOT-{clean_plot}-{date.today().strftime('%y%m')}"
        issue_date = date.today().strftime("%d %B %Y")
        insp_date_str = record['Inspection Date'] if pd.notna(record['Inspection Date']) else "N/A"
        deadline_str = record['Deadline'] if str(record.get('Deadline', '')).strip() not in ['', 'nan', 'None'] else "Immediate (Within 48 Hours)"

        front_b64 = image_to_base64(record.get("Front-view Site Image", ""))
        defect_b64 = image_to_base64(record.get("Defect Evidence Image", ""))

        v_type = str(record.get("Violation Type", "Standard Building Code Non-Compliance"))
        by_law_citation = "Building By-Laws (2024 Revised), Structural Safety Code Sec. 14-B"
        if "Boundary" in v_type or "Encroach" in v_type:
            by_law_citation = "Municipal Demarcation & Setback Ordinance, Sec. 08 (Right-of-Way Protection)"
        elif "Drawing" in v_type:
            by_law_citation = "Statutory Planning Act, Clause 19 (Unapproved Structural Modifications)"

        st.divider()
        tb_col1, tb_col2 = st.columns([3, 1])
        with tb_col1:
            st.markdown(f"**Notice Reference:** `{notice_id}` | **Target Site:** `Plot {record['Plot Number']}, Sector {record['Sector']}`")
        with tb_col2:
            st.caption("🖨️ *To print or save as PDF, use your browser's print command (`Ctrl + P`).*")

        notice_html = f"""
        <div style="background-color: #ffffff; color: #1a1a1a; font-family: 'Times New Roman', Times, serif; border: 2px solid #333; padding: 40px; margin: 10px auto; max-width: 850px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 4px;">
            <div style="text-align: center; border-bottom: 3px double #333; padding-bottom: 15px; margin-bottom: 25px;">
                <h3 style="margin: 0; font-size: 16px; letter-spacing: 2px; text-transform: uppercase; color: #555;">Municipal Housing Development Authority</h3>
                <h1 style="margin: 5px 0; font-size: 24px; text-transform: uppercase; letter-spacing: 1px; color: #111;">Directorate of Building Control & Quality Enforcement</h1>
                <p style="margin: 0; font-size: 13px; font-style: italic; color: #666;">Statutory Inspection, Structural Integrity & Code Compliance Wing</p>
            </div>

            <table style="width: 100%; font-size: 13px; margin-bottom: 20px; border-collapse: collapse;">
                <tr>
                    <td style="width: 60%; padding: 4px 0;"><strong>Notice Ref. No:</strong> {notice_id}</td>
                    <td style="width: 40%; text-align: right; padding: 4px 0;"><strong>Date of Issuance:</strong> {issue_date}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Inspection ID:</strong> {record['Inspection ID']}</td>
                    <td style="text-align: right; padding: 4px 0;"><strong>Site Inspection Date:</strong> {insp_date_str}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Statutory Authority:</strong> {by_law_citation}</td>
                    <td style="text-align: right; padding: 4px 0;"><strong>Compliance Deadline:</strong> <span style="color: #b02a37; font-weight: bold;">{deadline_str}</span></td>
                </tr>
            </table>

            <div style="background-color: {'#f8d7da' if 'Stop Work' in notice_type or 'Default' in notice_type else '#d1e7dd'}; border: 1px solid {'#f5c2c7' if 'Stop Work' in notice_type or 'Default' in notice_type else '#badbcc'}; padding: 12px; text-align: center; margin-bottom: 25px;">
                <h2 style="margin: 0; font-size: 18px; text-transform: uppercase; letter-spacing: 1px; color: {'#842029' if 'Stop Work' in notice_type or 'Default' in notice_type else '#0f5132'};">
                    {notice_type}
                </h2>
            </div>

            <div style="font-size: 14px; line-height: 1.6; margin-bottom: 20px;">
                <p style="margin: 0 0 5px 0;"><strong>TO THE OWNER / OCCUPIER:</strong> {record.get('Owner', 'Unassigned').upper()}</p>
                <p style="margin: 0 0 5px 0;"><strong>EXECUTING BUILDER / CONTRACTOR:</strong> {record.get('Contractor', 'Unassigned')}</p>
                <p style="margin: 0 0 15px 0;"><strong>SITE PREMISES:</strong> Plot No. {record['Plot Number']}, Sector {record['Sector']}, Phase 1 Residential Scheme.</p>
                <p style="margin: 0; text-align: justify;">
                    WHEREAS, in exercise of statutory supervisory powers conferred under municipal building regulations, an official field inspection was carried out on <strong>{insp_date_str}</strong> at the above-referenced premises during the progress of <strong>{record.get('Construction Activity', 'Construction Works')}</strong> at <strong>{record.get('Level / Floor', 'Site Level')}</strong>.
                </p>
            </div>

            <div style="background-color: #fdfdfd; border-left: 4px solid #333; padding: 12px 15px; margin-bottom: 20px; font-size: 13.5px; line-height: 1.6;">
                <p style="margin: 0 0 6px 0;"><strong>FIELD OBSERVATIONS:</strong> {record.get('Observation', 'Routine site check completed.')}</p>
                <p style="margin: 0 0 6px 0;"><strong>INFRACTION / CODE DEFECT:</strong> <span style="color: #b02a37;">{record.get('Defects', 'None logged.')}</span></p>
                <p style="margin: 0;"><strong>STATUTORY CLASSIFICATION:</strong> {record.get('Violation Type', 'None')} ({record.get('Severity', 'Standard')} Severity)</p>
            </div>

            <div style="font-size: 14px; line-height: 1.6; margin-bottom: 25px; text-align: justify;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px; text-transform: uppercase;">MANDATORY DIRECTIVE & CORRECTIVE ORDERS:</h4>
                <p style="margin: 0 0 10px 0;">
                    {record.get('Recommended Action', 'Ensure all ongoing structural works conform strictly to approved architectural and structural engineering designs.')}
                </p>
                <p style="margin: 0; font-size: 12.5px; color: #555;">
                    {'TAKE NOTICE: All construction activities on the subject plot are ordered HALTED WITH IMMEDIATE EFFECT. Any continuation of construction without explicit written clearance from the undersigned directorate constitutes an offense punishable by heavy administrative penalties, disconnection of utility lines, and physical sealing of site premises.' if 'Stop Work' in notice_type else 'Failure to rectify the aforementioned defects before the statutory deadline will result in the immediate issuance of a formal Stop Work order and referral to the municipal legal wing.'}
                </p>
            </div>

            <div style="margin-bottom: 35px; border-top: 1px dashed #ccc; padding-top: 15px;">
                <h4 style="margin: 0 0 12px 0; font-size: 13px; text-transform: uppercase; color: #444;">ANNEXURE A: FORENSIC PHOTOGRAPHIC AUDIT RECORD</h4>
                <table style="width: 100%; border-collapse: collapse; text-align: center;">
                    <tr>
                        <td style="width: 50%; padding: 5px; vertical-align: top;">
                            <div style="border: 1px solid #ddd; padding: 5px; background: #fafafa;">
                                {'<img src="' + front_b64 + '" style="width: 100%; height: 200px; object-fit: cover; border: 1px solid #ccc;" />' if front_b64 else '<div style="height: 150px; line-height: 150px; background: #eee; color: #888; font-size: 12px;">Front-View Photo Not on Disk</div>'}
                                <p style="margin: 5px 0 0 0; font-size: 11px; color: #555;"><strong>Plate 1:</strong> Site Macro View (Plot {record['Plot Number']})</p>
                            </div>
                        </td>
                        <td style="width: 50%; padding: 5px; vertical-align: top;">
                            <div style="border: 1px solid #ddd; padding: 5px; background: #fafafa;">
                                {'<img src="' + defect_b64 + '" style="width: 100%; height: 200px; object-fit: cover; border: 1px solid #ccc;" />' if defect_b64 else '<div style="height: 150px; line-height: 150px; background: #eee; color: #888; font-size: 12px;">Defect Evidence Photo Not on Disk</div>'}
                                <p style="margin: 5px 0 0 0; font-size: 11px; color: #555;"><strong>Plate 2:</strong> Micro Defect Evidence ({record.get('Violation Type', 'Site')})</p>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>

            <div style="margin-top: 40px; border-top: 1px solid #333; padding-top: 20px;">
                <table style="width: 100%; font-size: 13px; text-align: center;">
                    <tr>
                        <td style="width: 33%; vertical-align: bottom; padding: 10px;">
                            <div style="font-family: 'Courier New', Courier, monospace; font-size: 13px; margin-bottom: 25px;">{record.get('Inspector', 'Eng. Saad')}</div>
                            <div style="border-top: 1px solid #555; width: 80%; margin: 0 auto; padding-top: 4px;">
                                <strong>Reporting Field Inspector</strong><br/>
                                <span style="font-size: 11px; color: #666;">Directorate Building Control</span>
                            </div>
                        </td>
                        <td style="width: 33%; vertical-align: bottom; padding: 10px;">
                            <div style="font-family: 'Courier New', Courier, monospace; font-size: 13px; margin-bottom: 25px;">Eng. M. Tariq (PE)</div>
                            <div style="border-top: 1px solid #555; width: 80%; margin: 0 auto; padding-top: 4px;">
                                <strong>Senior Structural Engineer</strong><br/>
                                <span style="font-size: 11px; color: #666;">Quality Audit Bureau</span>
                            </div>
                        </td>
                        <td style="width: 33%; vertical-align: bottom; padding: 10px;">
                            <div style="font-family: 'Courier New', Courier, monospace; font-size: 13px; margin-bottom: 25px;">Director Building Control</div>
                            <div style="border-top: 1px solid #555; width: 80%; margin: 0 auto; padding-top: 4px;">
                                <strong>Competent Municipal Authority</strong><br/>
                                <span style="font-size: 11px; color: #666;">Seal & Enforcement Wing</span>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        """
        st.components.v1.html(notice_html, height=1050, scrolling=True)

    # ==================================================================
    # TAB 2: REGISTRY & AUDIT EXPORT ENGINE
    # ==================================================================
    with tab_exports:
        st.markdown("#### 📥 Filtered Registry & Society Audit Export")
        st.caption("Generate formal Excel workbooks or CSV spreadsheets for municipal archive, departmental reporting, or litigation records.")

        f_c1, f_c2, f_c3, f_c4 = st.columns([1.2, 1.2, 1.5, 1.5])

        with f_c1:
            sec_filter = st.selectbox("Sector", ["All Sectors"] + sorted(list(df["Sector"].dropna().unique())), key="exp_sec")
        with f_c2:
            stat_filter = st.selectbox("Compliance", ["All Records", "Compliant Only", "Non-Compliant Only", "Stop Work Only"], key="exp_stat")
        with f_c3:
            con_filter = st.selectbox("Contractor", ["All Contractors"] + sorted(list(df["Contractor"].dropna().unique())), key="exp_con")
        with f_c4:
            valid_dates = df["Parsed_Date"].dropna()
            if not valid_dates.empty and valid_dates.min().date() != valid_dates.max().date():
                exp_dates = st.date_input("Date Window", value=(valid_dates.min().date(), valid_dates.max().date()), key="exp_date")
            else:
                exp_dates = None

        export_df = df.copy()

        if sec_filter != "All Sectors":
            export_df = export_df[export_df["Sector"] == sec_filter]

        if stat_filter == "Compliant Only":
            export_df = export_df[export_df["Compliance Status"] == "Compliant"]
        elif stat_filter == "Non-Compliant Only":
            export_df = export_df[export_df["Compliance Status"] != "Compliant"]
        elif stat_filter == "Stop Work Only":
            export_df = export_df[export_df["Is_Stopped"] == True]

        if con_filter != "All Contractors":
            export_df = export_df[export_df["Contractor"] == con_filter]

        if exp_dates and isinstance(exp_dates, tuple) and len(exp_dates) == 2:
            s_d, e_d = exp_dates
            export_df = export_df[
                (export_df["Parsed_Date"].dt.date >= s_d) &
                (export_df["Parsed_Date"].dt.date <= e_d)
            ]

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Selected Records", len(export_df))
        m2.metric("Active Sites", export_df["Plot Number"].nunique())
        m3.metric("Stop Work Violations", len(export_df[export_df["Is_Stopped"] == True]))
        m4.metric("First-Time Quality", f"{(len(export_df[export_df['Compliance Status'] == 'Compliant']) / len(export_df) * 100):.1f}%" if len(export_df) else "0%")

        clean_export_cols = [
            "Inspection ID", "Inspection Date", "Sector", "Plot Number", "Owner", "Contractor",
            "Inspector", "Inspection Type", "Construction Activity", "Level / Floor", "Progress %",
            "Compliance Status", "Violation Type", "Severity", "Work Stopped", "Deadline",
            "Observation", "Defects", "Recommended Action"
        ]
        available_exp_cols = [c for c in clean_export_cols if c in export_df.columns]
        final_exp_df = export_df[available_exp_cols].reset_index(drop=True)

        st.dataframe(final_exp_df, use_container_width=True, hide_index=True)

        dl_c1, dl_c2 = st.columns([1, 1])

        csv_buffer = final_exp_df.to_csv(index=False).encode("utf-8")
        with dl_c1:
            st.download_button(
                label="📥 Download Audit Log (CSV)",
                data=csv_buffer,
                file_name=f"municipal_inspection_audit_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        excel_buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                final_exp_df.to_excel(writer, sheet_name="Site Inspections Audit", index=False)
            with dl_c2:
                st.download_button(
                    label="📊 Download Formatted Registry (Excel .xlsx)",
                    data=excel_buffer.getvalue(),
                    file_name=f"municipal_registry_export_{date.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except Exception:
            with dl_c2:
                st.info("Excel export requires openpyxl (`pip install openpyxl`).")
