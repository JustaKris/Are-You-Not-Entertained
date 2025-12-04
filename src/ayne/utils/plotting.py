"""Plotting utilities for TV-HML notebooks.

Provides consistent dark-mode matplotlib styling and common visualization patterns
used across analysis notebooks.
"""

import matplotlib.pyplot as plt
import seaborn as sns


def configure_dark_mode(palette: str = "bright") -> None:
    """Configure matplotlib for consistent dark-mode plotting across notebooks.

    This function sets up:
    - Dark background matching VS Code theme
    - White text and axes labels
    - Properly sized fonts for readability
    - Grid styling
    - Color palette

    Args:
        palette: Seaborn palette name (default: "bright" for high contrast).

    Example:
        >>> from tv_hml.utils.plotting import configure_dark_mode
        >>> configure_dark_mode()
        >>> plt.figure()
        >>> plt.plot([1, 2, 3])
        >>> plt.show()

    Notes:
        Call this function once at the start of your notebook.
        Colors: Dark backgrounds match VS Code (#1e1e1e, #2d2d2d).
        All text is white for maximum contrast.
        Includes edge colors and grid styling.
    """
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
