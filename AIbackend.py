import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def prepare_ai_context(analysis, dashboard_insights):

    context = {}

    # ==========================
    # Dataset Overview
    # ==========================

    context["dataset"] = analysis

    # ==========================
    # Data Quality
    # ==========================

    context["data_quality"] = dashboard_insights["data_quality"]

    # ==========================
    # Numeric Insights
    # ==========================

    numeric = dashboard_insights["numeric_insights"]

    if numeric["available"]:

        context["numeric_insights"] = {
            "summary_statistics":
                numeric["summary_statistics"]
                .round(2)
                .to_dict(),

            "highest_variance_column":
                numeric["highest_variance_column"],

            "highest_variance":
                numeric["highest_variance"],

            "outlier_counts":
                numeric["outlier_counts"]
        }

    else:

        context["numeric_insights"] = {
            "available": False
        }

    # ==========================
    # Categorical
    # ==========================

    context["categorical_insights"] = dashboard_insights["categorical_insights"]

    # ==========================
    # Correlation
    # ==========================

    correlation = dashboard_insights["correlation_insights"]

    if correlation["available"]:

        context["correlation_insights"] = {
            "available": True,
            "matrix":
                correlation["matrix"]
                .round(2)
                .to_dict()
        }

    else:

        context["correlation_insights"] = {
            "available": False
        }

    # ==========================
    # Time Series
    # ==========================

    time_series = dashboard_insights["time_series_insights"]

    if time_series["available"]:

        context["time_series_insights"] = {
            "available": True,
            "datetime_column":
                time_series["datetime_column"],

            "date_range":
                time_series["date_range"],

            "metrics":
                time_series["metrics"]
        }

    else:

        context["time_series_insights"] = {
            "available": False
        }

    return context

def generate_dataset_report(ai_context):

    prompt = f"""
    You are a senior data analyst generating a professional dataset analysis report.

    You MUST ONLY use the information provided below.

    Do NOT assume values that are not present.
    Do NOT invent statistics.
    Do NOT recommend machine learning, dashboards, or analyses unless the provided information directly supports it.

    Dashboard Insights:
    {ai_context}

    Generate a report in Markdown using EXACTLY the following structure.

    # Executive Summary

    Write a concise summary (4–6 sentences) describing:

    - dataset size
    - data quality
    - overall characteristics
    - important observations

    # Key Findings

    Provide clear bullet points.

    Only mention findings supported by the provided data.

    Examples include:

    - missing values
    - duplicates
    - strongest correlations
    - highest variance columns
    - categorical distributions
    - time-series observations
    - outliers
    - skewness
    - memory usage

    Do not repeat information unnecessarily.

    # Recommended Visualizations

    Recommend between 3 and 5 visualizations.

    For each visualization use EXACTLY this format.

    ---

    ### Visualization

    Description:
    (One short sentence.)

    Prompt:
    (A natural language prompt that could be given to an AI graph generator.)

    Example:

    ### Visualization

    Description:
    Compare average salary across departments.

    Prompt:
    Show me a bar chart of Salary by Department.

    ---

    Only recommend visualizations that make sense for THIS dataset.

    Do NOT recommend Machine Learning or predictions.

    The Prompt should be a plain English request.

    Only recommend visualizations that make sense for THIS dataset.

    Do NOT recommend:

    - Machine Learning
    - Predictive Models
    - Interactive Dashboards
    - General-purpose charts without explanation

    The report should sound like it was written by an experienced professional data analyst.
    """

    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a senior data analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return chat_completion.choices[0].message.content

import json

def generate_visualization_recommendations(ai_context):

    prompt = f"""
You are a professional data visualization expert.

Dataset Information:

{ai_context}

Recommend up to 6 useful visualizations.

Only recommend charts that provide real analytical value.

If fewer than six meaningful visualizations exist, return fewer.

Return ONLY valid JSON.

Example:

[
    {{
        "description":"Compare average salary across departments.",
        "prompt":"Show me a bar chart of Salary by Department."
    }},
    {{
        "description":"Visualize salary distribution.",
        "prompt":"Show me a histogram of Salary."
    }}
]

Rules:

- Return JSON ONLY.
- No markdown.
- No explanations.
- No extra text.
- Description must be between 3 and 8 words.
- Keep descriptions concise.
- Only recommend charts supported by the dataset.
"""

    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role":"system",
                "content":"You are a data visualization expert."
            },
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return json.loads(
        chat_completion.choices[0].message.content
    )

def generate_visualization_request(
    user_request,
    dataframe_columns
):

    prompt = f"""
You are a data visualization assistant.

Available Columns:

{dataframe_columns}

User Request:

{user_request}

Return ONLY valid JSON.

Example:

{{
    "chart":"bar",
    "x":"Department",
    "y":"Salary"
}}

Allowed charts:

bar
line
scatter
histogram
box
pie

If histogram:

{{
    "chart":"histogram",
    "x":"Salary"
}}

Return JSON only.
"""

    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role":"system",
                "content":"Convert user requests into chart JSON."
            },
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return chat_completion.choices[0].message.content

def initialize_conversation(
    dataframe,
    ai_context
):

    dataset_preview = dataframe.head(20).to_markdown(index=False)

    system_prompt = """
You are ForstaDatum AI Assistant.

You are an intelligent AI assistant specialized in helping users understand uploaded datasets.

Rules:

1. Remember the uploaded dataset throughout this conversation.

2. NEVER invent information.

3. If information is not present, clearly say so.

4. Answer dataset questions using the uploaded dataset.

5. Answer general questions normally.

6. Keep responses concise unless the user asks for detail.
"""

    dataset_context = f"""
A dataset has just been uploaded.

Dataset Columns:

{dataframe.columns.tolist()}

Dataset Preview:

{dataset_preview}

Dataset Insights:

{ai_context}

Remember ALL of this information for the rest of the conversation.

Do not ask the user to upload the dataset again.

Simply reply that the dataset has been loaded and you are ready.
"""

    conversation = [

        {
            "role":"system",
            "content":system_prompt
        },

        {
            "role":"user",
            "content":dataset_context
        }

    ]

    completion = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=conversation

    )

    assistant_reply = completion.choices[0].message.content

    conversation.append(

        {

            "role":"assistant",

            "content":assistant_reply

        }

    )

    return conversation  

def chat_with_dataset(
    user_message,
    dataframe,
    ai_context,
    chat_history
):

    dataset_preview = dataframe.head(20).to_markdown(index=False)

    system_prompt = """
You are ForstaDatum AI Assistant.

You are an intelligent AI assistant specialized in helping users understand their uploaded datasets.

Rules:

1. If the question is about the uploaded dataset:
   - Use the dataset and provided insights.
   - Perform calculations when necessary.
   - Explain your reasoning.

2. If the question is about statistics, business, finance, programming, AI, machine learning, databases, Excel, data analysis, visualization or any educational topic:
   - Answer normally.
   - If relevant, relate your explanation to the uploaded dataset.

3. If the user asks any completely general question:
   - Answer normally as a helpful AI assistant.
   - Do NOT refuse.
   - Do NOT repeatedly mention you only analyze datasets.

4. Never invent information from the dataset.

5. If the dataset does not contain the requested information, clearly say so.

6. Remember the previous conversation and answer naturally.
"""

    prompt = f"""
Dataset Columns:

{dataframe.columns.tolist()}

Dataset Preview:

{dataset_preview}

Dataset Insights:

{ai_context}

Current User Question:

{user_message}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(chat_history)

    messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    return chat_completion.choices[0].message.content