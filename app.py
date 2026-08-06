import streamlit as st
import pandas as pd
import plotly.express as px
import uuid
from backend import load_dataset, analyze_dataset, generate_dashboard_insights
from graph_generator import generate_graph
from streamlit_floating_container import FloatingContainer

if "next_page" not in st.session_state:
    st.session_state.next_page = None

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []

if "conversation" not in st.session_state:

    st.session_state.conversation = None

if "chat_messages" not in st.session_state:

    st.session_state.chat_messages = []

from database import (
    connect_database,
    save_dataset,
    get_saved_datasets,
    load_saved_dataset,
    delete_dataset,
)

from AIbackend import (
    prepare_ai_context,
    generate_dataset_report,
    generate_visualization_recommendations,
    generate_visualization_request,
    chat_with_dataset,
    initialize_conversation
)

# ----------------------------

st.set_page_config(
    page_title="ForstaDatum",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ForstaDatum")

st.subheader("Upload. Understand. Discover.")

# ----------------------------

try:
    connect_database()

except Exception as e:
    st.error(e)
    st.stop()

# ----------------------------

if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

if "filename" not in st.session_state:
    st.session_state.filename = None

if "selected_dataset_name" not in st.session_state:
    st.session_state.selected_dataset_name = "None"

if "save_status" not in st.session_state:
    st.session_state.save_status = None

if "delete_status" not in st.session_state:
    st.session_state.delete_status = False

if "graphs" not in st.session_state:
    st.session_state.graphs = []

# ==========================
# Navigation
# ==========================

st.sidebar.title("📊 ForstaDatum")
st.sidebar.caption("Upload. Understand. Discover.")

# Remember the current page
PAGES = [
    "🏠 Home",
    "📄 Dataset Explorer",
    "📊 Graph Explorer"
]

if "page" not in st.session_state:
    st.session_state.page = PAGES[0]

if st.session_state.next_page is not None:

    st.session_state.page = st.session_state.next_page

    st.session_state.next_page = None

page = st.sidebar.radio(
    "",
    PAGES,
    key="page"
)

st.sidebar.divider()

# ==========================
# Sidebar
# ==========================

st.sidebar.subheader("📁 Saved Datasets")
st.sidebar.success("🟢 MongoDB Connected")

datasets = get_saved_datasets()

selected_dataset = None

if datasets:

    search = st.sidebar.text_input(
        "🔍 Search Dataset"
    )

    filtered_datasets = [
        dataset
        for dataset in datasets
        if search.lower() in dataset["filename"].lower()
    ]

    st.sidebar.markdown("---")

    options = ["🏠 Home"] + [
        f"📄 {dataset['filename']}"
        for dataset in filtered_datasets
    ]

    if "dataset_pill" not in st.session_state:
        st.session_state.dataset_pill = "🏠 Home"

    if st.session_state.dataset_pill not in options:
        st.session_state.dataset_pill = "🏠 Home"

    selection = st.sidebar.pills(
        "Saved Datasets",
        options,
        selection_mode="single",
        key="dataset_pill"
    )

    selected = (
        "None"
        if selection in (None, "🏠 Home")
        else selection.replace("📄 ", "")
    )

    st.session_state.selected_dataset_name = selected

    if selected != "None":

        for dataset in datasets:

            if dataset["filename"] == selected:
                selected_dataset = dataset

                if True:

                    dataframe = load_saved_dataset(
                        str(selected_dataset["_id"])
                    )

                    st.session_state.dataframe = dataframe
                    st.session_state.filename = selected_dataset["filename"]

                break

    else:

        st.session_state.dataframe = None
        st.session_state.filename = None

    if selected_dataset is not None:

        st.sidebar.divider()

        st.sidebar.subheader("Dataset Details")

        st.sidebar.write(f"**📄 File:** {selected_dataset['filename']}")
        st.sidebar.write(f"**📂 Type:** {selected_dataset['file_type'].upper()}")
        st.sidebar.write(f"**📊 Rows:** {selected_dataset['rows']}")
        st.sidebar.write(f"**📑 Columns:** {selected_dataset['columns']}")

        upload_time = selected_dataset["upload_time"]

        try:
            upload_time = upload_time.strftime("%d %b %Y, %I:%M %p")
        except:
            pass

        st.sidebar.write(f"**🕒 Saved:** {upload_time}")

st.sidebar.divider()

def render_graph(graph, index):

    with st.container(border=True):

        st.markdown(f"### 📊 {graph['title']}")
        st.caption(graph["type"])

        st.plotly_chart(
            graph["figure"],
            use_container_width=True,
            key=graph["id"]
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:

            if st.button(
                "⬆",
                key=f"up_{graph['id']}",
                disabled=(index == 0),
                use_container_width=True
            ):

                st.session_state.graphs[index], st.session_state.graphs[index - 1] = (
                    st.session_state.graphs[index - 1],
                    st.session_state.graphs[index]
                )

                st.rerun()

        with col2:

            if st.button(
                "⬇",
                key=f"down_{graph['id']}",
                disabled=(index == len(st.session_state.graphs) - 1),
                use_container_width=True
            ):

                st.session_state.graphs[index], st.session_state.graphs[index + 1] = (
                    st.session_state.graphs[index + 1],
                    st.session_state.graphs[index]
                )

                st.rerun()

        with col3:

            st.button(
                "✏",
                key=f"edit_{graph['id']}",
                disabled=True,
                use_container_width=True
            )

        with col4:

            button_text = "⬜" if graph["width"] == "half" else "◫"

            if st.button(
                button_text,
                key=f"width_{graph['id']}",
                use_container_width=True
            ):

                graph["width"] = (
                    "full"
                    if graph["width"] == "half"
                    else "half"
                )

                st.rerun()

        with col5:

            if st.button(
                "🗑",
                key=f"delete_{graph['id']}",
                use_container_width=True
            ):

                st.session_state.graphs.pop(index)
                st.rerun()

# ==========================
# Main Page
# ==========================

if page == "🏠 Home":

    if st.session_state.save_status == "saved":
        st.success("✅ Dataset saved successfully!")
        st.session_state.save_status = None

    elif st.session_state.save_status == "updated":
        st.info("ℹ️ Dataset already exists. It has been updated.")
        st.session_state.save_status = None

    if st.session_state.delete_status:
        st.success("🗑 Dataset deleted successfully!")
        st.session_state.delete_status = False

    uploaded_file = st.file_uploader(
        "Upload Dataset",
        type=["csv", "xlsx"]
    )
    if uploaded_file is not None:

        dataframe = load_dataset(uploaded_file)

        st.session_state.dataframe = dataframe
        st.session_state.filename = uploaded_file.name

    if st.session_state.dataframe is not None:

        dataframe = st.session_state.dataframe

        filename = st.session_state.filename

        analysis = analyze_dataset(dataframe)
        dashboard_insights = generate_dashboard_insights(dataframe)

        ai_context = prepare_ai_context(
            analysis,
            dashboard_insights
        )

        st.session_state.ai_context = ai_context

        if "conversation" not in st.session_state:
            st.session_state.conversation = None

        if "ai_report" not in st.session_state:
            st.session_state.ai_report = None

        # ==========================
        # Dataset Header
        # ==========================

        with st.container(border=True):

            st.markdown(f"## 📄 {filename}")

            st.caption(analysis["dataset_status"])

            st.write(
                f"**{analysis['rows']:,} Rows** • "
                f"**{analysis['columns']} Columns** • "
                f"**{analysis['memory_usage']} MB**"
            )

            st.write("")

            col1, col2 = st.columns(2)

            with col1:

                if st.button("💾 Save Dataset", use_container_width=True):

                    status = save_dataset(filename, dataframe)

                    st.session_state.save_status = status

                    st.rerun()

            with col2:

                if st.button("🗑 Delete Dataset", use_container_width=True):

                    delete_dataset(str(selected_dataset["_id"]))

                    st.session_state.selected_dataset_name = "None"
                    st.session_state.dataframe = None
                    st.session_state.filename = None
                    st.session_state.delete_status = True

                    st.rerun()

                    st.session_state.delete_status = True

                    st.rerun()

        st.divider()

        # ==========================
            # Quick Statistics
        # ==========================

        left_col, right_col = st.columns([2, 1])

        with left_col:

            with st.container(border=True):

                st.subheader("📊 Quick Statistics")

                c1, c2, c3 = st.columns(3)

                c1.metric("Rows", f"{analysis['rows']:,}")
                c2.metric("Columns", analysis["columns"])
                c3.metric("Missing", analysis["missing_values"])

                c4, c5, c6 = st.columns(3)

                c4.metric("Duplicates", analysis["duplicate_rows"])
                c5.metric("Numeric", analysis["numeric_columns"])
                c6.metric("Categorical", analysis["categorical_columns"])

        with right_col:

            with st.container(border=True):

                st.subheader("🩺 Dataset Health")

                data_quality = dashboard_insights["data_quality"]

                st.success(analysis["dataset_status"])

                st.write(f"**Missing Values:** {data_quality['total_missing']}")
                st.write(f"**Duplicate Rows:** {data_quality['duplicate_rows']}")
                st.write(f"**Empty Columns:** {len(data_quality['empty_columns'])}")
                st.write(f"**Constant Columns:** {len(data_quality['constant_columns'])}")

        # ==========================
        # AI Summary
        # ==========================

        if "generate_report" not in st.session_state:

            st.session_state.generate_report = True


        if (
            st.session_state.ai_report is None
            and st.session_state.generate_report
        ):

            with st.spinner("🤖 Generating AI Report..."):

                st.session_state.ai_report = generate_dataset_report(
                    ai_context
                )

            st.session_state.generate_report = False

            st.rerun()

        if st.session_state.ai_report is not None:

            ai_report = st.session_state.ai_report
        
            sections = {}

            current_heading = None

            for line in ai_report.splitlines():

                line = line.strip()

                if line.startswith("#"):

                    current_heading = line.replace("#", "").strip()

                    sections[current_heading] = []

                elif current_heading:

                    sections[current_heading].append(line)

            for heading in sections:

                    sections[heading] = "\n".join(sections[heading]).strip()


            with st.container(border=True):

                st.header("🤖 AI Dataset Report")


                if "Executive Summary" in sections:

                    st.subheader("📄 Executive Summary")

                    st.markdown(sections["Executive Summary"])

                    st.divider()


                if "Key Findings" in sections:

                    st.subheader("🔍 Key Findings")

                    st.markdown(sections["Key Findings"])

                    st.divider()


                if "Recommended Visualizations" in sections:

                    st.write("")

                    st.subheader("📊 Recommended Visualizations")

                    st.caption(
                        "Generate AI-recommended charts with one click."
                    )

                    visualizations = generate_visualization_recommendations(
                        ai_context
                    )

                    cols = st.columns(3)

                    for index, visualization in enumerate(visualizations):

                        with cols[index % 3]:

                            with st.container(border=True):

                                st.markdown(
                                    f"#### 📊 {visualization['description']}"
                                )

                                st.write("")
                                st.write("")

                                if st.button(
                                    "✨ Generate Chart",
                                    key=f"ai_vis_{index}",
                                    use_container_width=True
                                ):

                                    chart_request = generate_visualization_request(
                                        visualization["prompt"],
                                        dataframe.columns.tolist()
                                    )

                                    import json

                                    chart_request = json.loads(chart_request)

                                    chart_name = {
                                        "bar":"Bar Chart",
                                        "line":"Line Chart",
                                        "scatter":"Scatter Plot",
                                        "histogram":"Histogram",
                                        "pie":"Pie Chart",
                                        "box":"Box Plot"
                                    }[chart_request["chart"]]

                                    graph = generate_graph(
                                        dataframe,
                                        chart_name,
                                        x=chart_request.get("x"),
                                        y=chart_request.get("y")
                                    )

                                    st.session_state.graphs.append(graph)

                                    st.session_state.next_page = "📊 Graph Explorer"

                                    st.rerun()

        numeric = dashboard_insights["numeric_insights"]
        categorical = dashboard_insights["categorical_insights"]
        correlation = dashboard_insights["correlation_insights"]
        time_series = dashboard_insights["time_series_insights"]

        with st.container(border = True):

            st.markdown("## 📈 Time Series Insights")
        
            if time_series["available"]:
        
                        st.markdown("### 📅 Date Information")
        
                        col1, col2 = st.columns(2)
        
                        with col1:
                            st.metric(
                                "Datetime Column",
                                time_series["datetime_column"]
                            )
        
                        with col2:
                            start_date, end_date = time_series["date_range"]
        
                            st.metric(
                                "Date Range",
                                f"{start_date.date()} → {end_date.date()}"
                            )
        
                        st.markdown("### 📊 Records Over Time")
        
                        selected_metric = st.selectbox(
                            "📊 Select Metric",
                            time_series["metrics"]
                        )
        
                        show_all_metrics = st.checkbox(
                            "Show all metrics together"
                        )
        
                        if show_all_metrics:
        
                            figure = px.line(
                                time_series["data"],
                                x=time_series["datetime_column"],
                                y=time_series["metrics"],
                                markers=True
                            )
        
                        else:
        
                            figure = px.line(
                                time_series["data"],
                                x=time_series["datetime_column"],
                                y=selected_metric,
                                markers=True
                            )
        
                        figure.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Records",
                            height=500
                        )
        
                        st.plotly_chart(
                            figure,
                            use_container_width=True
                        )
        
            else:
        
                st.info(
                    "No datetime column detected in this dataset."
                )

        st.divider()

        left_col, right_col = st.columns([2, 1])
        
        with right_col:
        
            st.markdown("## 📋 Correlation Summary")
        
            with st.container(border=True):
        
                if correlation["available"]:
        
                    corr_matrix = correlation["matrix"].copy()
        
                    # Remove self-correlations
                    for column in corr_matrix.columns:
                        corr_matrix.loc[column, column] = None
        
                    # Convert to long format
                    corr_pairs = (
                        corr_matrix.stack()
                        .reset_index()
                    )
        
                    corr_pairs.columns = [
                        "Column 1",
                        "Column 2",
                        "Correlation"
                        ]
        
                    # Remove duplicate pairs
                    corr_pairs["Pair"] = corr_pairs.apply(
                        lambda row: tuple(sorted([row["Column 1"], row["Column 2"]])),
                        axis=1
                    )
        
                    corr_pairs = corr_pairs.drop_duplicates("Pair")
        
                    strongest_positive = corr_pairs.loc[
                        corr_pairs["Correlation"].idxmax()
                    ]
        
                    strongest_negative = corr_pairs.loc[
                        corr_pairs["Correlation"].idxmin()
                        ]
        
                    st.markdown("### 📈 Strongest Positive")
        
                    st.success(
                        f"**{strongest_positive['Column 1']}** ↔ **{strongest_positive['Column 2']}**\n\n"
                        f"Correlation: **{strongest_positive['Correlation']:.3f}**"
                    )
        
                    st.markdown("### 📉 Strongest Negative")
        
                    st.warning(
                        f"**{strongest_negative['Column 1']}** ↔ **{strongest_negative['Column 2']}**\n\n"
                        f"Correlation: **{strongest_negative['Correlation']:.3f}**"
                    )
        
                else:
        
                    st.info(
                        "Correlation summary unavailable."
                    )
        
        with left_col:
        
            with st.container(border = True):
        
                st.markdown("## 🔥 Correlation Heatmap")
        
                if correlation["available"]:
        
                    figure = px.imshow(
                        correlation["matrix"],
                        text_auto=True,
                        aspect="auto",
                        color_continuous_scale="RdBu_r",
                        zmin=-1,
                        zmax=1
                    )
        
                    figure.update_layout(
                        height=600
                    )
        
                    st.plotly_chart(
                        figure,
                        use_container_width=True
                    )

                else:
        
                    st.info(
                        "At least two numeric columns are required to generate a correlation heatmap."
                    )
        
        st.divider()

        left_col, right_col = st.columns(2)

        with left_col:

            with st.container(border=True):

                with st.expander(
                    f"📈 Numeric Insights ({analysis['numeric_columns']} columns)",
                    expanded=False,
                ):

                    if numeric["available"]:

                        st.markdown("### 📊 Summary Statistics")

                        st.dataframe(
                            numeric["summary_statistics"],
                            use_container_width=True
                        )
        
                        st.markdown("### 📊 Highest Variance")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric(
                                "Column",
                                numeric["highest_variance_column"]
                            )

                        with col2:
                            st.metric(
                                "Variance",
                                numeric["highest_variance"]
                            )

                        st.markdown("### 🚨 Outlier Detection")

                        outlier_df = pd.DataFrame({
                            "Column": list(numeric["outlier_counts"].keys()),
                            "Outliers": list(numeric["outlier_counts"].values())
                        })

                        st.dataframe(
                            outlier_df,
                            use_container_width=True
                    )

                    else:

                        st.info(
                            "No numeric columns detected. Numeric Insights are unavailable for this dataset."
                        )

        with right_col:

            with st.container(border=True):

                with st.expander(
                    f"🏷️ Categorical Insights ({analysis['categorical_columns']} columns)",
                    expanded=False,
                ):

                    if categorical["available"]:

                        summary_df = pd.DataFrame.from_dict(
                            categorical["summary"],
                            orient="index"
                        ).reset_index()

                        summary_df.columns = [
                            "Column",
                            "Unique Values",
                            "Most Common Value",
                            "Frequency"
                        ]

                        st.markdown("### 📋 Category Summary")

                        st.dataframe(
                            summary_df,
                            use_container_width=True
                        )

                        st.markdown("### 🚩 High Cardinality Columns")

                        if categorical["high_cardinality"]:
                            st.warning(
                                ", ".join(categorical["high_cardinality"])
                            )
                        else:
                            st.success(
                                "No high-cardinality columns detected."
                            )

                        st.markdown("### ✅ Binary Columns")

                        if categorical["binary_columns"]:
                            st.success(
                                ", ".join(categorical["binary_columns"])
                            )
                        else:
                            st.info(
                                "No binary categorical columns found."
                            )

                    else:

                        st.info(
                            "No categorical columns detected. Categorical Insights are unavailable for this dataset."
                        )

        st.divider()

    else:
        st.info("Upload a dataset or choose one from the sidebar.")

elif page == "📄 Dataset Explorer":

    st.header("📄 Dataset Explorer")

    if st.session_state.dataframe is not None:

        dataframe = st.session_state.dataframe

        st.subheader("Dataset Preview")
        st.dataframe(
            dataframe,
            use_container_width=True
        )

        st.divider()

        st.subheader("Dataset Schema")

        dtypes = pd.DataFrame({
            "Column": dataframe.columns,
            "Data Type": dataframe.dtypes.astype(str)
        })

        st.dataframe(
            dtypes,
            use_container_width=True
        )

    else:

        st.info("Upload or select a dataset first.")

elif page == "📊 Graph Explorer":

    st.header("📊 Graph Explorer")

    if st.session_state.dataframe is not None:

        dataframe = st.session_state.dataframe

        graph_type = st.selectbox(
            "Graph Type",
            [
                "Bar Chart",
                "Line Chart",
                "Scatter Plot",
                "Histogram",
                "Pie Chart",
                "Box Plot"
            ]
        )

        figure = None

        columns = dataframe.columns.tolist()

        numeric_columns = dataframe.select_dtypes(
            include="number"
        ).columns.tolist()

        if graph_type == "Bar Chart":

            x_axis = st.selectbox(
                "X-Axis",
                columns
            )

            y_axis = st.selectbox(
                "Y-Axis",
                numeric_columns
            )

            if st.button(
                "Generate Graph",
                use_container_width=True
            ):

                graph = generate_graph(
                    dataframe,
                    "Bar Chart",
                    x=x_axis,
                    y=y_axis
                )

                st.session_state.graphs.append(graph)

        elif graph_type == "Line Chart":

            x_axis = st.selectbox(
            "X-Axis",
            columns
            )

            y_axis = st.selectbox(
            "Y-Axis",
            numeric_columns
            )

            if st.button(
                "Generate Graph",
                use_container_width=True
            ):

                graph = generate_graph(
                    dataframe,
                    "Line Chart",
                    x=x_axis,
                    y=y_axis
                )

                st.session_state.graphs.append(graph)

        elif graph_type == "Scatter Plot":

            x_axis = st.selectbox(
                "X-Axis",
                numeric_columns
            )

            y_axis = st.selectbox(
                "Y-Axis",
                numeric_columns
            )

            if st.button(
                "Generate Graph",
                use_container_width=True
            ):

                graph = generate_graph(
                    dataframe,
                    "Scatter Plot",
                    x=x_axis,
                    y=y_axis
                )

                st.session_state.graphs.append(graph)

        elif graph_type == "Histogram":

            column = st.selectbox(
                "Column",
                numeric_columns
            )

            if st.button(
                "Generate Graph",
                use_container_width=True
            ):

                graph = generate_graph(
                    dataframe,
                    "Histogram",
                    x=column
                )

                st.session_state.graphs.append(graph)

        elif graph_type == "Pie Chart":

            labels = st.selectbox(
                "Labels",
                columns
            )

            values = st.selectbox(
                "Values",
                numeric_columns
            )

            if st.button(
                "Generate Graph",
                use_container_width=True
            ):

                graph = generate_graph(
                    dataframe,
                    "Pie Chart",
                    x=labels,
                    y=values
                )

                st.session_state.graphs.append(graph)

        elif graph_type == "Box Plot":

            column = st.selectbox(
                "Column",
                numeric_columns
            )

            if st.button(
                "Generate Graph",
                use_container_width=True
            ):

                graph = generate_graph(
                    dataframe,
                    "Box Plot",
                    y=column
                )

                st.session_state.graphs.append(graph)

        if st.session_state.graphs:

            for graph in st.session_state.graphs:

                if "width" not in graph:
                    graph["width"] = "half"

            st.divider()

            st.subheader("Dashboard")

            pending_half = None

            for index, graph in enumerate(st.session_state.graphs):

                if graph["width"] == "full":

                    if pending_half is not None:

                        left, right = st.columns(2)

                        with left:
                            render_graph(
                                st.session_state.graphs[pending_half],
                                pending_half
                            )

                        pending_half = None

                    render_graph(graph, index)

                else:

                    if pending_half is None:

                        pending_half = index

                    else:

                        left, right = st.columns(2)

                        with left:
                            render_graph(
                                st.session_state.graphs[pending_half],
                                pending_half
                            )

                        with right:
                            render_graph(graph, index)

                        pending_half = None


            if pending_half is not None:

                left, right = st.columns(2)

                with left:
                    render_graph(
                        st.session_state.graphs[pending_half],
                        pending_half
                    )
    else:
        st.info("Please Upload or Select a Dataset.")

# ==========================================================
# Floating AI Assistant
# ==========================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

fp = FloatingContainer(
    icon="🤖",
    label="ForstaDatum AI",
    start_position="bottom",
    key="forstadatum_ai",
    glassmorphic=False,
)

with fp.panel():

    st.title("🤖 ForstaDatum AI")

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask anything...")

    if prompt:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking..."):

            answer = chat_with_dataset(

                user_message=prompt,

                dataframe=st.session_state.dataframe,

                ai_context=st.session_state.ai_context,

                chat_history=st.session_state.chat_history

            )

        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )