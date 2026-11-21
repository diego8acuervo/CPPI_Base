 # -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 12:14:50 2016

@author: Diego Fernando Ochoa C.

Calcula el portafolio resultante de Black-litterman a partir de ponderacones iniciales
( capitalizaciones d emercado) y expectativas de retorno y covarianza sobre los activos
"""
#%%Bibliotecas necesarias

import numpy as np #Cálculo de matrices y manejo de vectores
import pandas as pd #Funciones estadísticas
import scipy.optimize as sco #Optimización de algebra lineal
import datetime as dt
from pylab import *
import matplotlib.pyplot as plt #Otro graficador
plt.rcParams['figure.figsize']=(9,6)
from  sklearn.linear_model import LinearRegression
#Wrapper para extraer datos de Bloomberg (opcional: requiere Terminal Bloomberg + blpapi)
try:
    import blpapiwrapper as blp
    BLOOMBERG_DISPONIBLE = True
except ImportError:
    blp = None
    BLOOMBERG_DISPONIBLE = False

#%%#####################################################################################
#MODULO DE IMPORTACIÓN DE PRECIOS E INSUMOS: Validado Diciembre 28 2016 por Diego Ochoa
########################################################################################
"""
Importa los precios desde el API de Bloomberg. Deben entregarse las capitalizaciones bursátiles
en un diccionario con su respectivo nemo.
INPUTS:
        nemos: Listado de nemotécnicos de cada indice o ETF
        campo: cotización que se desea traer: ['PX_OPEN','PX_HIGH','PX_LOW','PX_LAST','ADJUSTED_PREV_LAST_PRICE']
        inicio: Fecha de inicio de la serie de datos 
        fin: Fecha de terminación de la serie de datos
        
OUTPUTS:
        nemos:Lista de nemotécnicos 
        precios: DataFrame de Pandas con los nemos, las fechas y los precios ajustados
        por dividendos para cada una de las especies.
        caps_out:Lista con las capitalizaciones bursátiles en el mismo orden de los nemos. 
"""
def preciosBlp(lista_nemos,frecuencia, campo, inicio, fin = dt.datetime.now()):
        
        inicio = dt.datetime.strptime(inicio, '%Y-%m-%d')
        if type(fin) is str:
            fin=dt.datetime.strptime(fin, '%Y-%m-%d')
        else:
            pass
        precios= blp.simpleHistoryRequest(lista_nemos,campo,startDate=inicio,endDate=dt.datetime.now(),periodicity=frecuencia)
        #nemos=lista_nemos
        #d={x: x for x in lista_nemos}        
        #caps_out=blp.simpleReferenceDataRequest(d,'INDX_MARKET_CAP')        
        return precios


def preciosExcel(lista_nemos, frecuencia='MONTHLY', campo=['PX_LAST'], inicio=None,
                 fin=None, ruta='SerieCPPI.xlsx'):
    """
    Alternativa sin conexión a preciosBlp: lee la exportación de Bloomberg guardada en
    SerieCPPI.xlsx (filas: Ticker / descripción / campo, luego fechas) y devuelve un
    DataFrame con el mismo formato que preciosBlp (columnas MultiIndex (nemo, campo)).
    La frecuencia la determina el archivo (mensual); el argumento se conserva por compatibilidad.
    """
    crudo = pd.read_excel(ruta, header=None)
    fila_nemos = crudo.index[crudo.iloc[:, 0].astype(str).str.strip() == 'Dates'][0] - 2
    nemos = crudo.iloc[fila_nemos, 1:].tolist()
    campos = crudo.iloc[fila_nemos + 2, 1:].tolist()
    datos = crudo.iloc[fila_nemos + 3:].copy()
    datos.index = pd.to_datetime(datos.iloc[:, 0])
    datos.index.name = 'date'
    datos = datos.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
    datos.columns = pd.MultiIndex.from_arrays([nemos, campos])
    faltantes = [n for n in lista_nemos if n not in nemos]
    if faltantes:
        raise KeyError(f"Nemos no encontrados en {ruta}: {faltantes}")
    datos = datos.loc[:, [(n, c) for n in lista_nemos for c in campo]]
    if inicio is not None:
        datos = datos[datos.index >= pd.to_datetime(inicio)]
    if fin not in (None, ''):
        datos = datos[datos.index <= pd.to_datetime(fin)]
    return datos


def precios(lista_nemos, frecuencia, campo, inicio, fin=None, ruta='SerieCPPI.xlsx'):
    """Usa Bloomberg si está disponible; si no, lee la serie guardada en Excel."""
    if BLOOMBERG_DISPONIBLE:
        try:
            return preciosBlp(lista_nemos, frecuencia, campo, inicio,
                              fin if fin else dt.datetime.now())
        except Exception as e:
            print(f"Bloomberg no disponible ({e}); usando {ruta}")
    return preciosExcel(lista_nemos, frecuencia, campo, inicio, fin, ruta)

def allianzFondos(perfil):
    perfil #['Moderado' 'Conservador' 'RFMP' 'AltaLiq','RFLP']
    unidades=pd.read_excel('FondosAllianz.xlsx',sheet_name=perfil,index_col=0)
    # Retornos logarítmicos periódicos y acumulados
    return unidades
        

#%% Estadísticas y riesgo
def skewness(r):
    """
    Alternative to scipy.stats.skew()
    Computes the skewness of the supplied Series or DataFrame
    Returns a float or a Series
    """
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**3).mean()
    return exp/sigma_r**3


def kurtosis(r):
    """
    Alternative to scipy.stats.kurtosis()
    Computes the kurtosis of the supplied Series or DataFrame
    Returns a float or a Series
    """
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**4).mean()
    return exp/sigma_r**4


def compound(r):
    """
    returns the result of compounding the set of returns in r
    """
    return np.expm1(np.log1p(r).sum())

                         
def annualize_rets(r, periods_per_year):
    """
    Annualizes a set of returns
    We should infer the periods per year
    but that is currently left as an exercise
    to the reader :-)
    """
    compounded_growth = (1+r).prod()
    n_periods = r.shape[0]
    return compounded_growth**(periods_per_year/n_periods)-1


def annualize_vol(r, periods_per_year):
    """
    Annualizes the vol of a set of returns
    We should infer the periods per year
    but that is currently left as an exercise
    to the reader :-)
    """
    return r.std()*(periods_per_year**0.5)


def sharpe_ratio(r, riskfree_rate, periods_per_year):
    """
    Computes the annualized sharpe ratio of a set of returns
    """
    # convert the annual riskfree rate to per period
    rf_per_period = (1+riskfree_rate)**(1/periods_per_year)-1
    excess_ret = r - rf_per_period
    ann_ex_ret = annualize_rets(excess_ret, periods_per_year)
    ann_vol = annualize_vol(r, periods_per_year)
    return ann_ex_ret/ann_vol

import scipy.stats
def drawdown(return_series: pd.Series):
    """Takes a time series of asset returns.
       returns a DataFrame with columns for
       the wealth index, 
       the previous peaks, and 
       the percentage drawdown
    """
    wealth_index = 1000*(1+return_series).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks)/previous_peaks
    return pd.DataFrame({"Wealth": wealth_index, 
                         "Previous Peak": previous_peaks, 
                         "Drawdown": drawdowns})



from scipy.stats import norm

def compound(r):
    """
    Devuelve el retorno compuesto de la serie de retornos r
    """
    return np.expm1(np.log1p(r).sum())

def anualiza_rets(r, periodos):
    """
    Anualiza un conjunto de retornos, 
    debería inferirse retornos por año pero esto es 
    trabajo adicional para la clase :-)
    """
    composicion = (1+r).prod()
    n_periodos = r.shape[0]
    return composicion**(periodos/n_periodos)-1

def anualiza_vol(r, periodos):
    """
    Anualiza la volatilidad para un periodo, 
    debería inferirse retornos por año pero esto es 
    trabajo adicional para la clase :-)
    """
    return r.std()*(periodos**0.5)

def sharpe_ratio(r, riskfree_rate, periods_per_year):
    """
    Computes the annualized sharpe ratio of a set of returns
    """
    # convert the annual riskfree rate to per period
    rf_per_period = (1+riskfree_rate)**(1/periods_per_year)-1
    excess_ret = r - rf_per_period
    ann_ex_ret = anualiza_rets(excess_ret, periods_per_year)
    ann_vol = anualiza_vol(r, periods_per_year)
    return ann_ex_ret/ann_vol

def drawdown(return_series: pd.Series):
    """Takes a time series of asset returns.
       returns a DataFrame with columns for
       the wealth index, 
       the previous peaks, and 
       the percentage drawdown
    """
    wealth_index = 1000*(1+return_series).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks)/previous_peaks
    return pd.DataFrame({"Wealth": wealth_index, 
                         "Previous Peak": previous_peaks, 
                         "Drawdown": drawdowns})


def gbm(n_years = 10, n_scenarios=1000, mu=0.07, sigma=0.15, steps_per_year=12, s_0=100.0, prices=True):
    """
    Evolution of Geometric Brownian Motion trajectories, such as for Stock Prices through Monte Carlo
    :param n_years:  The number of years to generate data for
    :param n_paths: The number of scenarios/trajectories
    :param mu: Annualized Drift, e.g. Market Return
    :param sigma: Annualized Volatility
    :param steps_per_year: granularity of the simulation
    :param s_0: initial value
    :return: a numpy array of n_paths columns and n_years*steps_per_year rows
    """
    # Derive per-step Model Parameters from User Specifications
    dt = 1/steps_per_year
    n_steps = int(n_years*steps_per_year) + 1
    # the standard way ...
    # rets_plus_1 = np.random.normal(loc=mu*dt+1, scale=sigma*np.sqrt(dt), size=(n_steps, n_scenarios))
    # without discretization error ...
    rets_plus_1 = np.random.normal(loc=(1+mu)**dt, scale=(sigma*np.sqrt(dt)), size=(n_steps, n_scenarios))
    rets_plus_1[0] = 1
    ret_val = s_0*pd.DataFrame(rets_plus_1).cumprod() if prices else rets_plus_1-1
    return ret_val




def summary_stats(r, riskfree_rate=0.03):
    """
    Return a DataFrame that contains aggregated summary stats for the returns in the columns of r
    """
    ann_r = r.aggregate(anualiza_rets, periodos=12)
    ann_vol = r.aggregate(anualiza_vol, periodos=12)
    ann_sr = r.aggregate(sharpe_ratio, riskfree_rate=riskfree_rate, periods_per_year=12)
    dd = r.aggregate(lambda r: drawdown(r).Drawdown.min())
    skew = r.aggregate(skewness)
    kurt = r.aggregate(kurtosis)
    cf_var5 = r.aggregate(var_gaussian, modified=True)
    hist_cvar5 = r.aggregate(cvar_historic)
    return pd.DataFrame({
        "Annualized Return": ann_r,
        "Annualized Vol": ann_vol,
        "Skewness": skew,
        "Kurtosis": kurt,
        "Cornish-Fisher VaR (5%)": cf_var5,
        "Historic CVaR (5%)": hist_cvar5,
        "Sharpe Ratio": ann_sr,
        "Max Drawdown": dd
    })



def run_cppi(risky_r, safe_r=None, m=3, start=1000, floor=0.95, riskfree_rate=0.05, drawdown=None):
    """
    Ejecuta el Backtest de una estrategia CPPI dados un conjunto de retornos para el 
    activo riesgoso (sweeking performance instrument) y una tasa de rentabilidad del 
    equivalente cierto. Devuelve un diccionario que contiene el histórico del NAV
    la historia del presupuesto de riesgo (Asignaciónb SPV/rf)
    """
    # Parámetros CPPI
    dates = risky_r.index
    n_steps = len(dates)
    account_value = start
    floor_value = start*floor
    peak = account_value
    risky_alloc=0
    if isinstance(risky_r, pd.Series): 
        risky_r = pd.DataFrame(risky_r, columns=["R"])

    if safe_r is None:
        safe_r = pd.DataFrame().reindex_like(risky_r)
        safe_r.values[:] = riskfree_rate/12 # Cualquier valor inicial
    # Contenedores que almacenan información para backtesting y demostracinoes 
    account_history = pd.DataFrame().reindex_like(risky_r)
    risky_w_history = pd.DataFrame().reindex_like(risky_r)
    cushion_history = pd.DataFrame().reindex_like(risky_r)
    floorval_history = pd.DataFrame().reindex_like(risky_r)
    peak_history = pd.DataFrame().reindex_like(risky_r)
    fee_history=pd.DataFrame().reindex_like(risky_r)
    rebalance_cost=pd.DataFrame().reindex_like(risky_r)
    for step in range(n_steps):
        if drawdown is not None:
            peak = np.maximum(peak, account_value)
            floor_value = peak*(1-drawdown)
        cushion = (account_value - floor_value)/account_value
        risky_w = m*cushion
        risky_w = np.minimum(risky_w, 1)
        risky_w = np.maximum(risky_w, 0)
        safe_w = 1-risky_w
        risky_prev_w=risky_alloc
        risky_alloc = account_value*risky_w
        safe_alloc = account_value*safe_w
        
        #####COMISIONES Y COSTOS DE TRANSACCIÓN#################
        transaction_cost=abs((risky_alloc-risky_prev_w))*(0.075/100)
        fees=account_value*((1+0.02)**(1/12)-1)+transaction_cost
        # rECALCULA EL VALOR AL FINAL DEL PASO
        account_value = risky_alloc*(1+risky_r.iloc[step]) + safe_alloc*(1+safe_r.iloc[step])-fees
        
        # Guarda la historia para análisis y gráficos 
        cushion_history.iloc[step] = cushion
        risky_w_history.iloc[step] = risky_w
        account_history.iloc[step] = account_value
        floorval_history.iloc[step] = floor_value
        peak_history.iloc[step] = peak
        fee_history.iloc[step]=fees-transaction_cost
        rebalance_cost.iloc[step]=transaction_cost
    risky_wealth = start*(1+risky_r).cumprod()
    backtest_result = {
        "Wealth": account_history,
        "Risky Wealth": risky_wealth, 
        "Risk Budget": cushion_history,
        "Risky Allocation": risky_w_history,
        "m": m,
        "start": start,
        "floor": floor,
        "risky_r":risky_r,
        "safe_r": safe_r,
        "drawdown": drawdown,
        "peak": peak_history,
        "floor": floorval_history,
        "fees":fee_history,
        "Turnover Cost":rebalance_cost
    }
    return backtest_result


def corre_cppi(risky_r,safe_r=None,m=3,start=1000,floor=0.8,rf_rate=0.02,trans_cost=0.00075,drawdown=None):

    #Fija los parámetros
    dates=risky_r.index
    n_steps=len(dates)
    account_value=start
    floor_value=start*floor
    peak=start
    risky_alloc=0
    if isinstance(risky_r,pd.Series):
        risky_r=pd.DataFrame(risky_r,columns=["R"])
    if safe_r is None:
        safe_r=pd.DataFrame().reindex_like(risky_r)
        safe_r.values[:]=rf_rate/12
    #Contenedores de información para salidas
    account_history=pd.DataFrame().reindex_like(risky_r)
    cushion_history=pd.DataFrame().reindex_like(risky_r)
    risky_w_history=pd.DataFrame().reindex_like(risky_r)
    transaction_cost_history=pd.DataFrame().reindex_like(risky_r)

    for step in range(n_steps):
        if drawdown is not None:
            peak=np.maximum(peak,account_value)
            floor_value=peak*(1-drawdown)
        cushion=(account_value-floor_value)/account_value
        risky_w=m*cushion
        risky_w=np.minimum(risky_w,1)
        risky_w=np.maximum(risky_w,0)
        safe_w=1-risky_w
        risky_prev_w=risky_alloc
        risky_alloc=account_value*risky_w
        safe_alloc=account_value*safe_w
        transaction_cost=abs((risky_alloc-risky_prev_w))*trans_cost
        ##Actualiza el valor de la cuenta
        account_value=risky_alloc*(1+risky_r.iloc[step])+safe_alloc*(1+safe_r.iloc[step])-transaction_cost
        # Guarda los valores para visualizarlos después
        cushion_history.iloc[step]=cushion
        risky_w_history.iloc[step]=risky_w
        account_history.iloc[step]=account_value
        transaction_cost_history.iloc[step]=transaction_cost
    risky_wealth=start*(1+risky_r).cumprod()
    backtest_result={
        "CPPI_NAV":account_history,
        "buy&hold":risky_wealth,
        "Risk Budget":cushion_history,
        "Risk Allocation":risky_w_history,
        "m":m,
        "start":start,
        "floor":floor,
        "risky_r":risky_r,
        "safe_r":safe_r      
        }
    return backtest_result


