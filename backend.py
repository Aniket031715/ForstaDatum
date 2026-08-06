import numpy as np
import pandas as pd


def load_dataset(uploaded_file):

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        dataframe = pd.read_csv(uploaded_file)

    elif filename.endswith((".xlsx")):
        dataframe = pd.read_excel(uploaded_file)

    else:
        raise ValueError("Unsupported file format.")

    return dataframe


def analyze_dataset(dataframe):

    missing_values = int(
        dataframe.isna().sum().sum()
    )

    duplicate_rows = int(
        dataframe.duplicated().sum()
    )

    if missing_values == 0 and duplicate_rows == 0:
        dataset_status = "🟢 Ready for Analysis"

    elif missing_values <= 20 and duplicate_rows <= 10:
        dataset_status = "🟡 Needs Cleaning"

    else:
        dataset_status = "🔴 Poor Data Quality"

    return {

        "rows": len(dataframe),

        "columns": len(dataframe.columns),

        "memory_usage": round(
            dataframe.memory_usage(deep=True).sum() / (1024 ** 2),
            4
        ),
        "missing_values": missing_values,

        "duplicate_rows": duplicate_rows,

        "numeric_columns": len(
            dataframe.select_dtypes(include="number").columns
        ),

        "categorical_columns": len(
            dataframe.select_dtypes(
                include=["object", "category"]
            ).columns
        ),

        "dataset_status": dataset_status

    }

def generate_dashboard_insights(df):
    """
    Generate all insights required for the Home Dashboard.
    """

    insights = {}

    # =========================
    # Overall Summary
    # =========================

    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_columns = df.select_dtypes(include=["datetime"]).columns.tolist()

    memory_usage = round(df.memory_usage(deep=True).sum() / (1024 ** 2), 4)

    insights["overall_summary"] = {
        "rows": len(df),
        "columns": len(df.columns),
        "memory_usage": memory_usage,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
    }

    # =========================
    # Data Quality
    # =========================

    missing_by_column = (
        df.isnull()
        .sum()
        .loc[lambda x: x > 0]
        .to_dict()
    )

    empty_columns = [
        col
        for col in df.columns
        if df[col].isnull().all()
    ]

    constant_columns = [
        col
        for col in df.columns
        if df[col].nunique(dropna=False) == 1
    ]

    insights["data_quality"] = {
        "total_missing": int(df.isnull().sum().sum()),
        "missing_by_column": missing_by_column,
        "duplicate_rows": int(df.duplicated().sum()),
        "empty_columns": empty_columns,
        "constant_columns": constant_columns,
    }

    # =========================
    # Numeric Insights
    # =========================
    
    if numeric_columns:
    
        summary_statistics = (
            df[numeric_columns]
            .describe()
        )
    
        variances = df[numeric_columns].var()
    
        highest_variance_column = variances.idxmax()
        highest_variance = variances.max()
    
        outlier_counts = {}
    
        for column in numeric_columns:
    
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
    
            iqr = q3 - q1
    
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
    
            count = (
                (df[column] < lower) |
                (df[column] > upper)
            ).sum()
    
            outlier_counts[column] = int(count)
    
        insights["numeric_insights"] = {
            "available": True,
            "summary_statistics": summary_statistics,
            "highest_variance_column": highest_variance_column,
            "highest_variance": round(highest_variance, 2),
            "outlier_counts": outlier_counts
        }
    
    else:
    
        insights["numeric_insights"] = {
            "available": False
        }

    # =========================
    # Categorical Insights
    # =========================

    if categorical_columns:

        category_summary = {}

        high_cardinality = []

        binary_columns = []

        for column in categorical_columns:

            unique_count = int(df[column].nunique(dropna=True))

            mode = df[column].mode(dropna=True)

            most_common = (
                mode.iloc[0]
                if not mode.empty
                else "N/A"
            )

            frequency = int(
                df[column]
                .value_counts(dropna=True)
                .max()
            ) if unique_count > 0 else 0

            category_summary[column] = {
                "unique_values": unique_count,
                "most_common": most_common,
                "frequency": frequency
            }

            if unique_count > 20:
                high_cardinality.append(column)

            if unique_count == 2:
                binary_columns.append(column)

        insights["categorical_insights"] = {
            "available": True,
            "summary": category_summary,
            "high_cardinality": high_cardinality,
            "binary_columns": binary_columns
        }

    else:

        insights["categorical_insights"] = {
            "available": False
        }

    # =========================
    # Correlation Insights
    # =========================

    if len(numeric_columns) >= 2:

        correlation_matrix = (
            df[numeric_columns]
            .corr(numeric_only=True)
        )

        insights["correlation_insights"] = {
            "available": True,
            "matrix": correlation_matrix
        }

    else:

        insights["correlation_insights"] = {
            "available": False
        }

    # =========================
    # Time Series Insights
    # =========================

    datetime_column = None

    for column in df.columns:

        if df[column].dtype in ["object", "string"]:

            try:

                converted = pd.to_datetime(
                    df[column],
                    errors="coerce",
                    format="mixed"
                )

            except Exception:
                continue

            if converted.notna().sum() >= len(df) * 0.8:

                datetime_column = column
                df[column] = converted
                break

    if datetime_column is not None:

        date_range = (
            df[datetime_column].min(),
            df[datetime_column].max()
        )

        numeric_metrics = [
            column
            for column in numeric_columns
            if column != datetime_column
        ]

        insights["time_series_insights"] = {
            "available": True,
            "datetime_column": datetime_column,
            "date_range": date_range,
            "metrics": numeric_metrics,
            "data" : df
        }

    else:

        insights["time_series_insights"] = {
            "available": False
        }
    
    return insights