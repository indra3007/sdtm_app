import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

def summary_stats_fig(df, count_var, visit_col_n, visit_col, test_col):
    """
    Generalized function to calculate summary statistics for any test column.
    """
    # Aggregate summary statistics
    fig_summary_stats = df.groupby([visit_col_n, visit_col, test_col], as_index=False).agg(
        N=(count_var, "count"),
        Mean=(count_var, "mean"),
        SEM=(count_var, "sem"),
        SD=(count_var, "std"),
        Min=(count_var, "min"),
        Max=(count_var, "max"),
        Median=(count_var, "median")
    )
    return fig_summary_stats
def generate_test_plot(df, test_value, test_col, visit_col_n, visit_col):
    """
    Generalized function to generate plots for any test column and dynamically detected value column.
    """
    # Dynamically detect the value column ending with "STRESN"
    plots = []
    value_columns = [col for col in df.columns if col.endswith("STRESN")]
    if not value_columns:
        return html.Div("No column ending with 'STRESN' found in the data.")

    value_col = value_columns[0]  # Use the first detected value column

    # Filter data for the selected test value and drop rows with NaN in the value column
    filtered_data = df[df[test_col] == test_value].dropna(subset=[value_col])

    # Ensure necessary columns exist
    required_columns = {test_col, value_col, visit_col_n, visit_col}
    if not required_columns.issubset(filtered_data.columns):
        return html.Div(f"Required columns {', '.join(required_columns)} not found in data.")

    # Calculate summary statistics
    summary_stats = summary_stats_fig(filtered_data, value_col, visit_col_n, visit_col, test_col)
    summary_stats["LCLM"] = summary_stats["Mean"] - summary_stats["SEM"]
    summary_stats["UCLM"] = summary_stats["Mean"] + summary_stats["SEM"]

    # Define x-axis order based on visit column
    x_order = filtered_data.sort_values(by=[visit_col_n])[visit_col].unique()

    # Create line plot with error bars
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=summary_stats[visit_col],
            y=summary_stats["Mean"],
            mode="lines",
            name=test_value,
            error_y=dict(
                type="data",
                array=summary_stats["SEM"],
                symmetric=True,
                color="purple"
            ),
            line=dict(width=2)
        )
    )

    # Update layout of the plot
    fig.update_layout(
        title=f"Mean Plot of {test_value} by Visit",
        xaxis=dict(title="Visit", categoryorder="array", categoryarray=x_order),
        yaxis=dict(title=f"Mean {test_value}"),
        hovermode="x",
        height=500,
        width=1200  # Specify a numeric width in pixels
    )
    #plot_html = fig.to_html(full_html=False)
    #lots.append(plot_html)
    #return plots
    return dcc.Graph(figure=fig)

