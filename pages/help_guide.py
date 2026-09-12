import streamlit as st


def show_help_page():
    st.header("📖 Site Engineering & Analytics Knowledge Base")
    st.caption("Standard definitions, municipal statutory rules, and quality assurance principles.")

    tab_qa, tab_struct, tab_legal = st.tabs([
        "📊 QA/QC & Analytics Metrics",
        "🏗️ Structural Rules & Sequences",
        "⚖️ Municipal Enforcement & Legal Notices"
    ])

    with tab_qa:
        st.markdown("### Quality Assurance & Analytical Metrics")

        with st.expander("📈 Pareto Analysis (CII 80/20 Principle)", expanded=True):
            st.markdown("""
            * **What it means:** Derived from the Construction Industry Institute (CII) quality benchmarks. In construction management, **80% of structural failures, site delays, and rework costs stem from just 20% of defect types.**
            * **How to read the chart:**
                * **Red Bars (Left Axis):** The raw frequency of violations logged for each specific trade.
                * **Blue Line (Right Axis):** The cumulative percentage of total site risk.
                * **80% Threshold Line:** Highlights the critical cutoff point. Any trade to the left of this dotted line accounts for the bulk of project quality risk and requires prioritized site inspection.
            """)

        with st.expander("🎯 First-Time Quality (FTQ / RFT Yield)"):
            st.markdown("""
            * **What it means:** Also known as *Right-First-Time*. It measures the percentage of physical inspections that pass building code standards on the initial site visit without requiring non-conformance notices.
            * **Formula:** $\\text{FTQ} = \\frac{\\text{Compliant Inspections}}{\\text{Total Inspections Conducted}} \\times 100$
            * **Benchmark:** World-class residential developments aim for $\\ge 90\\%$. Scores below $70\\%$ indicate contractor quality deficiency or inadequate on-site supervision.
            """)

        with st.expander("🚨 Site Risk Priority Index (SRPI)"):
            st.markdown("""
            * **What it means:** An empirical hazard score assigned to each active plot to identify repeat violators before structural failures occur.
            * **Weighting Formula:**
                $$\\text{Risk Score} = (4 \\times \\text{Active Stop Work}) + (3 \\times \\text{Critical Violations}) + (2 \\times \\text{High Violations}) + (1 \\times \\text{Minor Defect})$$
            * **Action Tiers:**
                * **Score $\\ge 6$ (Red):** Severe structural or boundary violation. Immediate administrative intervention required.
                * **Score $3 - 5$ (Amber):** Repeat non-compliances. Increased inspection frequency required.
                * **Score $< 3$ (Clear):** Standard routine monitoring.
            """)

        with st.expander("🏢 Contractor Reliability Scorecard"):
            st.markdown("""
            * **What it means:** A comparative index tracking the execution quality of independent builders across the society.
            * **Key Indicators:** Evaluates total visits conducted, pass percentage, and count of official Stop Work orders issued.
            """)

    with tab_struct:
        st.markdown("### Structural Engineering Logic & Hierarchy")

        with st.expander("🧱 Monotonic Structural Ascent (Vertical Hierarchy)", expanded=True):
            st.markdown("""
            * **The Rule:** Construction must follow strict vertical physical progression:
              $$\\text{Foundation / Sub-structure} \\longrightarrow \\text{Ground Floor} \\longrightarrow \\text{First Floor} \\longrightarrow \\text{Second Floor} \\longrightarrow \\text{Rooftop}$$
            * **Why it is enforced:** You cannot cast a First Floor slab before casting the Ground Floor frame. The system blocks backward concrete casting logs to prevent data entry errors.
            """)

        with st.expander("🔨 Finishing Trade Pre-requisites"):
            st.markdown("""
            * **The Rule:** Architectural and finishing trades (e.g., Plastering, Flooring, Electrical Conduit Piping) cannot be logged on a floor until that floor's reinforced concrete frame has been inspected and approved.
            """)

        with st.expander("📉 Progress Non-Regression"):
            st.markdown("""
            * **The Rule:** Physical completion percentage for a plot cannot drop below previously verified milestones (e.g., a site at 45% progress cannot log a subsequent routine visit at 30% without explicit structural demolition documentation).
            """)

    with tab_legal:
        st.markdown("### Municipal Enforcement & Statutory Notices")

        with st.expander("🚨 Stop Work Notice (Sealing Order)", expanded=True):
            st.markdown("""
            * **What it means:** An immediate statutory directive halting all construction activities on site.
            * **Trigger Conditions:** Encroachment into roads/setbacks, deviation from approved structural design, casting without inspection sign-off, or life-safety violations.
            """)

        with st.expander("⏳ Rectification Aging Brackets"):
            st.markdown("""
            * **What it means:** Tracks the delinquency of outstanding non-compliance notices based on statutory rectification deadlines:
                * **Within Window:** Builder is within the permitted cure period.
                * **1–7 Days Overdue:** Notice expired; first official reminder issued.
                * **8–14 Days Overdue:** Second reminder; administrative penalty assessed.
                * **>30 Days Default:** Legal referral for utility disconnection or site sealing.
            """)