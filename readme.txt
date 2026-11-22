CPPI - Constant Proportion Portfolio Insurance on a risky asset
===============================================================

What this is
------------
Two notebooks apply the same CPPI method to different risky assets:

  CPPI_2026.ipynb  Gold (XAU) in USD. Data from Yahoo Finance.
  CPPI_2021.ipynb  COLCAP / MSCI / GSCI in COP. Data from Bloomberg.

CPPI_2021.ipynb backtests and simulates a CPPI (Constant Proportion Portfolio
Insurance) strategy. The risky assets are Colombian and global indices priced
in COP: COLCAP, MSCI ACWI in COP and S&P GSCI in COP. The safe asset earns a
fixed rate. Notebook text is in Spanish.

The CPPI rule, applied each month:
  1. Cushion       = (account value - floor) / account value
  2. Risky weight  = m * cushion, clipped to [0, 1]; the rest goes to the safe asset
  3. Account value is updated with asset returns, minus transaction costs and fees

Notebook sections:
  - Data load: monthly prices from 2006-08 to 2021-04. Returns, cumulative
    returns and maximum drawdown.
  - Historical CPPI backtest: m = 3, floor = 95%. It is compared with buy-and-hold.
  - CPPI with a drawdown constraint: the floor is reset at 95% of the running peak.
  - Monte Carlo (Geometric Brownian Motion): interactive ipywidgets sliders for
    mu, sigma, m, floor and rf. They show the distribution of terminal wealth,
    the floor-violation probability and the expected shortfall.

CPPI_2026.ipynb (gold, USD)
---------------------------
  - Everything is in USD.
  - Risky asset: "Oro (USD)" = GC=F (COMEX front-month gold future, USD/oz).
    Yahoo Finance no longer publishes XAU spot (XAUUSD=X), so GC=F is the
    closest proxy. GLD (SPDR Gold Shares ETF) is shown as the investable
    alternative.
  - Safe asset: 3-month US T-Bill (^IRX, 13-week yield). The return for
    month t uses the yield observed at the end of month t-1.
  - Monthly rebalancing, backtest from 2005-02. Defaults: m = 3, floor = 95%,
    transaction cost 7.5 bp, management fee 2% per year.
  - Sections: data load, summary statistics, drawdown, CPPI backtest vs
    buy-and-hold, CPPI with a 10% drawdown constraint, and a Monte Carlo
    simulation calibrated to gold in USD. It has one static run and
    interactive sliders with a "Simular" button.
  - The notebook downloads prices on every run and saves a copy to
    data/precios_oro.csv. If the download fails or takes more than 60 s, it
    reads that copy.

Repository layout
-----------------
  CPPI_2026.ipynb            Gold CPPI notebook
  CPPI_2021.ipynb            COLCAP CPPI notebook
  Optiport.py                Library: data loaders, statistics, gbm(), run_cppi(), corre_cppi()
  aqmRisk.py                 Library: risk statistics (summary_stats, VaR/CVaR, drawdown, ...)
  data/precios_oro.csv       Saved copy of the Yahoo Finance prices: GC=F, GLD, ^IRX
  blpapiwrapper.py           Bloomberg API wrapper (used only if blpapi is installed)
  SerieCPPI.xlsx             Bloomberg export of the price series (offline data source)
  *.png                      Figures produced by the notebook
  requirements.txt           Pinned Python dependencies
  requirements-bloomberg.txt Optional Bloomberg API dependency
  Makefile                   Environment setup and run targets

Data source (CPPI_2021)
-----------------------
Optiport.precios() checks for the Bloomberg API first. If blpapi is installed
and a Bloomberg Terminal session is running, it downloads the series live.
Otherwise it reads the same tickers (COLCAP Index, MXWD Index,
SPGSCITR Index, COFX Index, CORRRMIN Index) from SerieCPPI.xlsx. The notebook
therefore runs on any machine without Bloomberg.

Requirements
------------
  - Python 3.11 (tested with 3.11.9; 3.10-3.12 should work)
  - GNU make (preinstalled on macOS/Linux; on Windows use WSL or run the
    commands below by hand)

Quick start
-----------
  make setup      # creates .venv, installs requirements, registers Jupyter kernel
  make lab        # opens JupyterLab in the project folder

In Jupyter, choose the kernel "Python 3 (CPPI .venv)". Both notebooks already
select it by default.

Other targets (run "make help" for the full list):
  make run        # execute both notebooks top to bottom and save outputs in place
  make run NB=CPPI_2026.ipynb   # run a single notebook (works with check too)
  make check      # execute without modifying the notebooks (output in build/)
  make gold-data  # refresh data/precios_oro.csv from Yahoo Finance
  make bloomberg  # optional: install blpapi for live Bloomberg data
  make clean      # remove __pycache__, .ipynb_checkpoints, build/
  make distclean  # also remove .venv and the Jupyter kernel

Manual setup (without make)
---------------------------
  python3 -m venv .venv
  source .venv/bin/activate          # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  python -m ipykernel install --user --name cppi --display-name "Python 3 (CPPI .venv)"
  jupyter lab

Notes
-----
  - pandas is pinned below 3.0. The CPPI routines in Optiport.py write through
    DataFrame.values, and pandas 3 copy-on-write does not allow that.
  - CPPI_2026 needs internet access to get the latest prices. Without it,
    the notebook uses data/precios_oro.csv.
  - The interactive Monte Carlo cell needs a live Jupyter kernel. The sliders
    do not render on GitHub's static notebook preview.
  - Matplotlib may warn that the "Arial" font is missing on some systems.
    This only affects how the plots look.

Author
------
Diego Fernando Ochoa C.
