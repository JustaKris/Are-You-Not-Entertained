"""Plotting utilities for TV-HML notebooks.

Provides consistent dark-mode matplotlib styling and common visualization patterns
used across analysis notebooks.
"""

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
import seaborn as sns


def configure_dark_mode(palette: str = "bright") -> None:
    """Configure matplotlib and Plotly for consistent dark-mode plotting across notebooks.

    This function sets up:
    - Dark background matching VS Code theme
    - White text and axes labels
    - Properly sized fonts for readability
    - Grid styling
    - Color palette

    Args:
        palette: Seaborn palette name (default: "bright" for high contrast).

    Example:
        >>> from ayne.utils.plotting import configure_dark_mode
        >>> configure_dark_mode()
        >>> # Now both matplotlib and Plotly will use dark mode
        >>> plt.figure()
        >>> plt.plot([1, 2, 3])
        >>> plt.show()

    Notes:
        Call this function once at the start of your notebook.
        Colors: Dark backgrounds match VS Code (#1e1e1e, #2d2d2d).
        All text is white for maximum contrast.
        Includes edge colors and grid styling.
        Configures both matplotlib and Plotly themes.
    """
    # Configure matplotlib
    plt.style.use("dark_background")
    sns.set_palette(palette)

    # Unified dark mode configuration
    # Combines best-of-both: visual appeal + clean code formatting
    rcparams = {
        # Figure and axes colors (VS Code theme colors)
        "figure.facecolor": "#1e1e1e",
        "savefig.facecolor": "#1e1e1e",
        "axes.facecolor": "#2d2d2d",
        "axes.edgecolor": "#666666",
        # Text colors (white for contrast)
        "text.color": "white",
        "axes.labelcolor": "white",
        "xtick.color": "white",
        "ytick.color": "white",
        # Grid styling
        "grid.color": "#D1CBCB",
        "grid.alpha": 0.3,
        # Font sizes (balanced for readability)
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        # Font weights for emphasis
        "axes.titleweight": "bold",
        "figure.titlesize": 16,
        "figure.titleweight": "bold",
    }

    plt.rcParams.update(rcparams)

    # Configure Plotly dark mode
    # Create custom dark template matching VS Code theme with improved readability
    plotly_template = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="#1e1e1e",  # Outer background
            plot_bgcolor="#2d2d2d",   # Plot area background
            font={"color": "white", "size": 13, "family": "Arial, sans-serif"},
            title={
                "font": {"size": 18, "color": "white"},
                "x": 0.5,  # Center title
                "xanchor": "center",
                "pad": {"t": 20, "b": 10}  # Padding around title
            },
            # Enhanced margins to prevent text cutoff
            margin={"l": 80, "r": 40, "t": 80, "b": 80},
            xaxis={
                "gridcolor": "#666666",
                "linecolor": "#888888",
                "tickcolor": "white",
                "zerolinecolor": "#666666",
                "title": {"font": {"size": 14}, "standoff": 15},
                "tickfont": {"size": 12},
                "automargin": True,  # Auto-adjust margins for long labels
            },
            yaxis={
                "gridcolor": "#666666",
                "linecolor": "#888888",
                "tickcolor": "white",
                "zerolinecolor": "#666666",
                "title": {"font": {"size": 14}, "standoff": 15},
                "tickfont": {"size": 12},
                "automargin": True,  # Auto-adjust margins for long labels
            },
            legend={
                "bgcolor": "rgba(45, 45, 45, 0.8)",
                "bordercolor": "#666666",
                "borderwidth": 1,
                "font": {"size": 12},
                "x": 1.02,  # Position to the right
                "xanchor": "left",
                "y": 1,
                "yanchor": "top"
            },
            hoverlabel={
                "bgcolor": "#2d2d2d",
                "font": {"size": 13, "color": "white"},
                "bordercolor": "#888888"
            },
            # Annotation defaults for better readability
            annotationdefaults={
                "font": {"size": 12, "color": "white"},
                "bgcolor": "rgba(45, 45, 45, 0.8)",
                "bordercolor": "#666666",
                "borderwidth": 1,
                "borderpad": 4
            },
            colorway=[
                "#00d4ff",  # Cyan
                "#ff79c6",  # Pink
                "#c7ff00",  # Lime
                "#ff9500",  # Orange
                "#b19cd9",  # Purple
                "#ff6b9d",  # Magenta
            ],
        )
    )

    # Register and set as default template
    pio.templates["vscode_dark"] = plotly_template
    pio.templates.default = "vscode_dark"

    # Enable matplotlib inline for Jupyter
    # Note: This won't work in regular Python scripts
    try:
        get_ipython().run_line_magic("matplotlib", "inline")  # type: ignore[name-defined]
    except (NameError, AttributeError):
        # Not in Jupyter environment, skip magic command
        pass


def get_dark_palette(n_colors: int = 6) -> list[str]:
    """Get a bright, high-contrast color palette suitable for dark backgrounds.

    Args:
        n_colors: Number of colors to generate (default: 6 for model comparison).

    Returns:
        List of hex color codes optimized for dark backgrounds.

    Example:
        >>> colors = get_dark_palette(n_colors=4)
        >>> plt.bar(range(4), [1, 2, 3, 4], color=colors)
    """
    # Hand-picked colors that work well on dark backgrounds
    # Ordered by visual distinctness
    palette = [
        "#00d4ff",  # Cyan
        "#ff79c6",  # Pink (Linear Regression)
        "#ff6b9d",  # Magenta (Random Forest)
        "#c7ff00",  # Lime (LightGBM)
        "#ff9500",  # Orange (XGBoost)
        "#b19cd9",  # Purple (CatBoost)
    ]

    if n_colors <= len(palette):
        return palette[:n_colors]

    # If more colors needed, cycle through palette
    return [palette[i % len(palette)] for i in range(n_colors)]


def style_comparison_figure(
    title: str,
    suptitle_size: int = 18,
    title_pad: int = 15,
) -> tuple:
    """Create a styled figure for model comparison visualizations.

    Args:
        title: Figure title.
        suptitle_size: Font size for suptitle (default: 18).
        title_pad: Padding for title (default: 15).

    Returns:
        Tuple of (fig, axes) for plotting.

    Example:
        >>> fig, axes = style_comparison_figure('Model Metrics')
        >>> axes[0].bar(...)
        >>> plt.show()
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 11))
    fig.suptitle(title, fontsize=suptitle_size, fontweight="bold", y=0.995)
    return fig, axes


# Default configuration - call this in setup cells
__all__ = [
    "configure_dark_mode",
    "get_dark_palette",
    "style_comparison_figure",
]
