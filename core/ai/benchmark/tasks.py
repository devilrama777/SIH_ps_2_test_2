"""
Standard Model Evaluation Benchmark Tasks — Section 31 of Master Implementation Specification.

Defines the 8 standardized evaluation tasks to benchmark local models (Gemma, Llama, Qwen, etc.)
against identical data inputs, ground truths, and citation expectations.
"""
from typing import Any, Dict, List
from pydantic import BaseModel


class BenchmarkTask(BaseModel):
    task_id: str
    task_name: str
    prompt: str
    context_data: Dict[str, Any]
    expected_citations: List[str]
    ground_truth_facts: List[str]


BENCHMARK_TASKS: List[BenchmarkTask] = [
    # Task 1: Summarize Evidence
    BenchmarkTask(
        task_id="task_1_summarize_evidence",
        task_name="Task 1: Summarize Evidence",
        prompt="Summarize production achievements and equipment utilization preserving all exact metrics and citations.",
        context_data={
            "evidence": (
                "Document [DOC:Annual_Production_FY25.pdf:P12]: Total raw coal production reached 773.60 MT in FY 2024-25, "
                "representing a growth of 10.1% over previous year. Dragline availability was 84.5%."
            )
        },
        expected_citations=["[DOC:Annual_Production_FY25.pdf:P12]"],
        ground_truth_facts=["773.60 MT", "10.1%", "84.5%"],
    ),

    # Task 2: Identify Relevant Evidence
    BenchmarkTask(
        task_id="task_2_identify_relevant_evidence",
        task_name="Task 2: Identify Relevant Evidence",
        prompt="Identify the relevant evidence document and page for coal washery beneficiation yield.",
        context_data={
            "corpus": [
                {"id": "[DOC:Mining_Op_Review.pdf:P05]", "text": "Overburden removal amounted to 1,650 Mm3."},
                {"id": "[DOC:Coal_Beneficiation_FY25.pdf:P18]", "text": "Non-coking washery yield improved to 72.4% at Patherdih."},
                {"id": "[DOC:CSR_Projects.pdf:P02]", "text": "Health camps benefited 45,000 villagers."},
            ]
        },
        expected_citations=["[DOC:Coal_Beneficiation_FY25.pdf:P18]"],
        ground_truth_facts=["Patherdih", "72.4%"],
    ),

    # Task 3: Generate Section
    BenchmarkTask(
        task_id="task_3_generate_section",
        task_name="Task 3: Generate Section",
        prompt="Generate the Capital Expenditure (Capex) executive summary section citing audited ledgers.",
        context_data={
            "evidence": (
                "Financial Ledger [COORD:Capex_FY25.xlsx:Summary:E14]: Capex achieved was ₹19,840.50 crores against budget of ₹16,500.00 crores. "
                "Major investments in First Mile Connectivity (FMC) projects [DOC:FMC_Report.pdf:P04]."
            )
        },
        expected_citations=["[COORD:Capex_FY25.xlsx:Summary:E14]", "[DOC:FMC_Report.pdf:P04]"],
        ground_truth_facts=["19,840.50", "16,500.00", "First Mile Connectivity"],
    ),

    # Task 4: Interpret Tables
    BenchmarkTask(
        task_id="task_4_interpret_tables",
        task_name="Task 4: Interpret Tables",
        prompt="Interpret the subsidiary off-take table and determine the highest dispatch mode percentage.",
        context_data={
            "table_data": (
                "Table [DOC:Dispatch_Modes_FY25.pdf:P22]:\n"
                "Mode | Dispatch (MT) | Share (%)\n"
                "Rail | 480.20 | 62.1%\n"
                "Road | 175.40 | 22.7%\n"
                "MGR  | 118.00 | 15.2%\n"
            )
        },
        expected_citations=["[DOC:Dispatch_Modes_FY25.pdf:P22]"],
        ground_truth_facts=["Rail", "62.1%", "480.20"],
    ),

    # Task 5: Identify Contradictions
    BenchmarkTask(
        task_id="task_5_identify_contradictions",
        task_name="Task 5: Identify Contradictions",
        prompt="Compare preliminary estimate with audited statement and identify the revenue discrepancy.",
        context_data={
            "source_a": "Press release [DOC:Press_April25.pdf:P01] states revenue was ₹1,35,000 crores.",
            "source_b": "Audited Balance Sheet [DOC:Audited_Financials_FY25.pdf:P44] confirms revenue from operations was ₹1,31,452.80 crores."
        },
        expected_citations=["[DOC:Press_April25.pdf:P01]", "[DOC:Audited_Financials_FY25.pdf:P44]"],
        ground_truth_facts=["1,35,000", "1,31,452.80", "discrepancy"],
    ),

    # Task 6: Edit Section
    BenchmarkTask(
        task_id="task_6_edit_section",
        task_name="Task 6: Edit Section",
        prompt="Revise the environmental compliance section to include updated tree plantation totals and mine water discharge.",
        context_data={
            "draft_text": "The subsidiary planted 1.2 million saplings during the financial year.",
            "updated_evidence": (
                "Verified Report [DOC:Env_Audit_FY25.pdf:P09]: Revised total was 2.15 million saplings covering 1,020 hectares. "
                "Mine water utilization reached 88.3 million m3 [DOC:Env_Audit_FY25.pdf:P14]."
            )
        },
        expected_citations=["[DOC:Env_Audit_FY25.pdf:P09]", "[DOC:Env_Audit_FY25.pdf:P14]"],
        ground_truth_facts=["2.15 million", "1,020", "88.3"],
    ),

    # Task 7: Follow Provenance
    BenchmarkTask(
        task_id="task_7_follow_provenance",
        task_name="Task 7: Follow Provenance",
        prompt="State the coal safety incident rate (FR) strictly citing the Director General of Mines Safety (DGMS) audit page.",
        context_data={
            "evidence": "DGMS Official Audit [DOC:DGMS_Safety_FY25.pdf:P31]: Fatal Accident Rate (per MT coal) dropped to 0.18."
        },
        expected_citations=["[DOC:DGMS_Safety_FY25.pdf:P31]"],
        ground_truth_facts=["0.18", "DGMS"],
    ),

    # Task 8: Generate Report Plan
    BenchmarkTask(
        task_id="task_8_generate_report_plan",
        task_name="Task 8: Generate Report Plan",
        prompt="Formulate a 4-chapter report structure integrating production, financials, environmental sustainability, and CSR.",
        context_data={
            "reference_chapters": ["Profile", "Operations", "Finance"],
            "discovered_topics": ["Renewable Energy Initiatives & Solar Expansion"]
        },
        expected_citations=[],
        ground_truth_facts=["Operations", "Finance", "CSR", "Renewable"],
    ),
]
