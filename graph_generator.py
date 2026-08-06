import uuid
import plotly.express as px


def generate_graph(
    dataframe,
    chart_type,
    x=None,
    y=None
):

    if chart_type == "Bar Chart":

        figure = px.bar(
            dataframe,
            x=x,
            y=y
        )

        title = f"{x} vs {y}"


    elif chart_type == "Line Chart":

        figure = px.line(
            dataframe,
            x=x,
            y=y
        )

        title = f"{x} vs {y}"


    elif chart_type == "Scatter Plot":

        figure = px.scatter(
            dataframe,
            x=x,
            y=y
        )

        title = f"{y} vs {x}"


    elif chart_type == "Histogram":

        figure = px.histogram(
            dataframe,
            x=x
        )

        title = f"Distribution of {x}"


    elif chart_type == "Pie Chart":

        figure = px.pie(
            dataframe,
            names=x,
            values=y
        )

        title = f"{y} by {x}"


    elif chart_type == "Box Plot":

        figure = px.box(
            dataframe,
            y=y
        )

        title = f"Box Plot of {y}"


    else:

        return None


    return {

        "id": str(uuid.uuid4()),

        "title": title,

        "type": chart_type,

        "figure": figure,

        "width": "half"

    }