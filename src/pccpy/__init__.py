"""pccpy - Control Estadístico de Procesos (SPC) en Python, al estilo Minitab."""
from ._constants import c4, c5, control_chart_constants, d2, d3
from .capability import (
    CapabilityResult,
    NonNormalCapabilityResult,
    capability_analysis,
    capability_boxcox,
    capability_nonnormal,
)
from .charts import (
    c_chart,
    cusum_chart,
    ewma_chart,
    g_chart,
    imr_chart,
    imr_rs_chart,
    laney_p_chart,
    laney_u_chart,
    ma_chart,
    np_chart,
    p_chart,
    t_chart,
    u_chart,
    xbar_r_chart,
    xbar_s_chart,
    zmr_chart,
    zone_chart,
)
from .multivariate import (
    generalized_variance_chart,
    mcusum_chart,
    mcusum_limit,
    mewma_chart,
    mewma_limit,
    t2_chart,
)
from .normality import NormalityResult, normality_test
from .plotting import capability_sixpack, plot_capability, plot_control_chart, probability_plot
from .quality_tools import pareto, plot_pareto
from .results import ControlChart, MultivariateChart, Panel

__version__ = "0.4.5"

__all__ = [
    "CapabilityResult",
    "ControlChart",
    "MultivariateChart",
    "NonNormalCapabilityResult",
    "NormalityResult",
    "Panel",
    "c4",
    "c5",
    "c_chart",
    "capability_analysis",
    "capability_boxcox",
    "capability_nonnormal",
    "capability_sixpack",
    "control_chart_constants",
    "cusum_chart",
    "d2",
    "d3",
    "ewma_chart",
    "g_chart",
    "generalized_variance_chart",
    "imr_chart",
    "imr_rs_chart",
    "laney_p_chart",
    "laney_u_chart",
    "ma_chart",
    "mcusum_chart",
    "mcusum_limit",
    "mewma_chart",
    "mewma_limit",
    "normality_test",
    "np_chart",
    "p_chart",
    "pareto",
    "plot_capability",
    "plot_control_chart",
    "plot_pareto",
    "probability_plot",
    "t2_chart",
    "t_chart",
    "u_chart",
    "xbar_r_chart",
    "xbar_s_chart",
    "zmr_chart",
    "zone_chart",
]
