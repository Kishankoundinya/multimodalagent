from langchain_core.prompts import PromptTemplate

SYSTEM_PROMPT_BASE = """You are a financial document analysis assistant. Use only the supplied source context. Do not use unsupported knowledge. If the answer cannot be found in the context, say that the information was not found in the provided documents. Never fabricate numbers, dates, or sources."""

RESEARCH_PROMPT_TEMPLATE = """Context:
{context}

Question:
{question}

Instructions:
1. Answer the question using ONLY the facts provided in the Context above.
2. If the context does not contain the answer, reply: "Information not found in the provided documents."
3. Every factual claim or number must cite its exact source document and page number in this format: [Source: <document_name>, p. <page>]
4. Structure your response clearly with headings, bullet points, and an ending "## Sources" section listing each unique cited source and page.
5. Do not invent any numbers, percentages, or ratios."""

EXTRACTION_PROMPT_TEMPLATE = """Context:
{context}

Target Company: {company}
Fiscal Year: {fiscal_year}

Instructions:
Extract the following key financial metrics from the context if explicitly stated.
Metrics to extract:
- Revenue
- Net Income
- Operating Income
- EBITDA
- Total Assets
- Total Liabilities
- Total Debt
- Cash
- Equity
- EPS
- Operating Margin
- Net Profit Margin
- Current Ratio

For each metric you find, output in the exact format:
METRIC: <Metric Name> | VALUE: <Value with unit e.g. $383,285 million> | PERIOD: <Period e.g. FY2024> | PAGE: <Page number> | TEXT: <Exact short sentence from context>

Rules:
- If a metric is not present in the context, DO NOT output a line for it or state VALUE: null.
- Never guess or calculate unstated values in this step.
- Only extract what is clearly written in the provided context snippets."""

RED_FLAG_PROMPT_TEMPLATE = """Context:
{context}

Company: {company}
Fiscal Year: {fiscal_year}

Instructions:
Analyze the context for genuine, document-supported financial warning signs and red flags.
Potential indicators:
- Increasing debt levels or high debt burdens
- Declining revenue or net income
- Falling profit margins
- Negative operating or free cash flow
- Increasing liabilities or liquidity stress
- Auditor qualifications, adverse opinions, or going concern statements
- Explicit risks or lawsuits with material financial impact

Rules:
- For every red flag identified, output in this exact structure:
FLAG: <Title>
SEVERITY: <LOW | MEDIUM | HIGH>
PAGE: <Page number>
EVIDENCE: <Exact quote or direct observation with numbers from the text>
DESCRIPTION: <Brief explanation of why this represents a financial risk>

- If no red flags are found in the provided context, output: "NO_FLAGS_IDENTIFIED"
- NEVER invent or speculate on risks not directly evidenced in the text."""

COMPARISON_PROMPT_TEMPLATE = """Context for {company_a}:
{context_a}

Context for {company_b}:
{context_b}

Instructions:
Compare the financial performance of {company_a} and {company_b} based strictly on the context provided above.
1. Compare key metrics: Revenue, Net Income, Total Assets, Total Debt, Profit Margins, etc.
2. State the exact reported values for both companies with their exact page citations: [Source: <doc>, p. <page>].
3. Note numerical differences objectively (e.g., "{company_a} reported $X billion compared to {company_b}'s $Y billion").
4. Do NOT give subjective opinions or say one company is "better" or "the best".
5. If data for a metric is missing for one company, clearly state: "Not reported in provided documents"."""

REPORT_SUMMARY_PROMPT_TEMPLATE = """Context:
{context}

Company: {company}
Fiscal Year: {fiscal_year}

Generate a professional Executive Summary and Financial Performance narrative for {company} ({fiscal_year}).
- Highlight revenue, net income, key operating trends, and risk profile based solely on the provided context.
- Cite sources with page numbers: [Source: <document>, p. <page>].
- Do not fabricate any information."""

# LangChain PromptTemplate abstractions
research_prompt_template = PromptTemplate.from_template(RESEARCH_PROMPT_TEMPLATE)
extraction_prompt_template = PromptTemplate.from_template(EXTRACTION_PROMPT_TEMPLATE)
red_flag_prompt_template = PromptTemplate.from_template(RED_FLAG_PROMPT_TEMPLATE)
comparison_prompt_template = PromptTemplate.from_template(COMPARISON_PROMPT_TEMPLATE)
report_summary_prompt_template = PromptTemplate.from_template(REPORT_SUMMARY_PROMPT_TEMPLATE)
