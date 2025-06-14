from matplotlib.ticker import FuncFormatter
from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import numpy as np
import seaborn as sns

import qstrader.statistics.performance as perf
from qstrader.statistics.statistics import Statistics
from qstrader import settings
from qstrader import __version__ as ver


class TearsheetStatisticsMulti(Statistics):
    """
    Displays a Matplotlib-generated 'one-pager' as often
    found in institutional strategy performance reports.
    """
    def __init__(
        self,
        strategy_equity,
        benchmark_equity=None,
        title=None,
        periods=252
    ):
        self.strategy_equity = strategy_equity
        self.benchmark_equity = benchmark_equity
        self.title = title
        self.periods = periods
        self.__version__ = ver
        self.name = "<class> TearsheetStatisticsMulti"
        self.colors = ['green','red','blue','black']

    def __str__(self):
        return f"{self.name}({self.__version__})"

    def get_results(self, equity_df):
        """
        Return a dict with all important results & stats.
        """
        # Returns
        equity_df["returns"] = equity_df["Equity"].pct_change().fillna(0.0)

        # Cummulative Returns
        equity_df["cum_returns"] = np.exp(np.log(1 + equity_df["returns"]).cumsum())

        # Drawdown, max drawdown, max drawdown duration
        dd_s, max_dd, dd_dur = perf.create_drawdowns(equity_df["cum_returns"])

        # Equity statistics
        statistics = {}
        statistics["sharpe"] = perf.create_sharpe_ratio(
            equity_df["returns"], self.periods
        )
        statistics["drawdowns"] = dd_s
        statistics["max_drawdown"] = max_dd
        statistics["max_drawdown_pct"] = max_dd
        statistics["max_drawdown_duration"] = dd_dur
        statistics["equity"] = equity_df["Equity"]
        statistics["returns"] = equity_df["returns"]
        statistics["cum_returns"] = equity_df["cum_returns"]
        return statistics

    def _plot_equity(self, strat_stats, bench_stats=None, ax=None, **kwargs):
        """
        Plots cumulative rolling returns versus some benchmark.
        """
        def format_two_dec(x, pos):
            return '%.2f' % x

        equity = strat_stats['cum_returns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_two_dec)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.xaxis.set_tick_params(reset=True)
        ax.yaxis.grid(linestyle=':')
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.grid(linestyle=':')

        equity.plot(lw=2, color='green', alpha=0.6, x_compat=False,
                    label='Strategy', ax=ax, **kwargs)
        if bench_stats is not None:
            bench_stats['cum_returns'].plot(
                lw=2, color='gray', alpha=0.6, x_compat=False,
                label='Benchmark', ax=ax, **kwargs
            )

        ax.axhline(1.0, linestyle='--', color='black', lw=1)
        ax.set_ylabel('Cumulative returns')
        ax.legend(loc='best')
        ax.set_xlabel('')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
        return ax

    def _plot_drawdown(self, stats, ax=None, **kwargs):
        """
        Plots the underwater curve
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        drawdown = stats['drawdowns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')
        ax.xaxis.set_tick_params(reset=True)
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.grid(linestyle=':')

        underwater = -100 * drawdown
        underwater.plot(ax=ax, lw=2, kind='area', color='red', alpha=0.3, **kwargs)
        ax.set_ylabel('')
        ax.set_xlabel('')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
        ax.set_title('Drawdown (%)', fontweight='bold')
        return ax

    def _plot_monthly_returns(self, stats, ax=None, **kwargs):
        """
        Plots a heatmap of the monthly returns.
        """
        returns = stats['returns']
        if ax is None:
            ax = plt.gca()

        monthly_ret = perf.aggregate_returns(returns, 'monthly')
        monthly_ret = monthly_ret.unstack()
        monthly_ret = np.round(monthly_ret, 3)
        monthly_ret.rename(
            columns={1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                     5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
                     9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'},
            inplace=True
        )

        sns.heatmap(
            monthly_ret.fillna(0) * 100.0,
            annot=True,
            fmt="0.1f",
            annot_kws={"size": 8},
            alpha=1.0,
            center=0.0,
            cbar=False,
            cmap=cm.RdYlGn,
            ax=ax, **kwargs)
        ax.set_title('Monthly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_xlabel('')

        return ax

    def _plot_yearly_returns(self, stats, ax=None, **kwargs):
        """
        Plots a barplot of returns by year.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        returns = stats['returns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')

        yly_ret = perf.aggregate_returns(returns, 'yearly') * 100.0
        yly_ret.plot(ax=ax, kind="bar")
        ax.set_title('Yearly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        ax.xaxis.grid(False)

        return ax

    def _plot_txt_curve(self, strat_stats_list, bench_stats=None, ax=None, **kwargs):
        """
        Outputs the statistics for the equity curve.
        """
        if not type(strat_stats_list) is list:
                print(self.name + " requires strategies as a list")
                raise TypeError("Only lists are allowed")
        
        def format_perc(x, pos):
            return '%.0f%%' % x

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))


        ax.set_title('Multi Curve box', fontweight='bold')
        ax.grid(False)
        ax.spines['top'].set_linewidth(2.0)
        ax.spines['bottom'].set_linewidth(2.0)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.set_ylabel('himi')
        ax.set_xlabel('lou')

        #BUG extend top and bottom lines
        linelen = 10 * len(strat_stats_list)
        ax.axis([0, 10, 0, 10])

        
        y_txtlocation = 6.9
        x_txtlocation = 5.00
        coloridx = 0
        colors = self.colors
        #text box for returns -Labels-
        ax.text(7.50, 8.2, 'Strategy', fontweight='bold', horizontalalignment='right', fontsize=8, color=colors[coloridx])
        ax.text(0.25, y_txtlocation, 'Total Return', fontsize=8)
        ax.text(0.25, y_txtlocation-1, 'CAGR', fontsize=8)
        ax.text(0.25, y_txtlocation-2, 'Sharpe Ratio', fontsize=8)
        ax.text(0.25, y_txtlocation-3, 'Sortino Ratio', fontsize=8)
        ax.text(0.25, y_txtlocation-4, 'Annual Volatility', fontsize=8)
        ax.text(0.25, y_txtlocation-5, 'Max Daily Drawdown', fontsize=8)
        ax.text(0.25, y_txtlocation-6, 'Max Drawdown Duration (Days)', fontsize=8)
        
        
        #calc strategy values for returns box
        for strat_stats in strat_stats_list:

            x_txtlocation += 2.50
            returns = strat_stats["returns"]
            cum_returns = strat_stats["cum_returns"]
            tot_ret = cum_returns.iloc[-1] - 1.0
            cagr = perf.create_cagr(cum_returns, self.periods)
            sharpe = perf.create_sharpe_ratio(returns, self.periods)
            sortino = perf.create_sortino_ratio(returns, self.periods)
            dd, dd_max, dd_dur = perf.create_drawdowns(cum_returns)

            #total return val
            ax.text(x_txtlocation, y_txtlocation, '{:.0%}'.format(tot_ret),color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            #CAGR val
            ax.text(x_txtlocation, y_txtlocation-1, '{:.2%}'.format(cagr),color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            #SHARP
            ax.text(x_txtlocation, y_txtlocation-2, '{:.2f}'.format(sharpe),color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            #sortno
            ax.text(x_txtlocation, y_txtlocation-3, '{:.2f}'.format(sortino),color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            #annual Vol
            ax.text(x_txtlocation, y_txtlocation-4, '{:.2%}'.format(returns.std() * np.sqrt(252)),color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            #max drawdown
            ax.text(x_txtlocation, y_txtlocation-5, '{:.2%}'.format(dd_max), color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            #draw down duration
            ax.text(x_txtlocation, y_txtlocation-6, '{:.0f}'.format(dd_dur), color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
        #end for loop
        x_txtlocation += 2.50
        coloridx += 1
        
        if bench_stats is not None:
            #calculate values for benchmark backtest if provided
            bench_returns = bench_stats["returns"]
            bench_cum_returns = bench_stats["cum_returns"]
            bench_tot_ret = bench_cum_returns.iloc[-1] - 1.0
            bench_cagr = perf.create_cagr(bench_cum_returns, self.periods)
            bench_sharpe = perf.create_sharpe_ratio(bench_returns, self.periods)
            bench_sortino = perf.create_sortino_ratio(bench_returns, self.periods)
            _, bench_dd_max, bench_dd_dur = perf.create_drawdowns(bench_cum_returns)
            #Display benchmark title and values
            ax.text(x_txtlocation, 8.2, 'Benchmark', color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(x_txtlocation, y_txtlocation, '{:.0%}'.format(bench_tot_ret), color=colors[coloridx],fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(x_txtlocation, y_txtlocation-1, '{:.2%}'.format(bench_cagr), color=colors[coloridx],fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(x_txtlocation, y_txtlocation-2, '{:.2f}'.format(bench_sharpe), color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(x_txtlocation, y_txtlocation-3, '{:.2f}'.format(bench_sortino), color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(x_txtlocation, y_txtlocation-4, '{:.2%}'.format(bench_returns.std() * np.sqrt(252)), color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(x_txtlocation, y_txtlocation-5, '{:.2%}'.format(bench_dd_max), color=colors[coloridx], fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(x_txtlocation, y_txtlocation-6, '{:.0f}'.format(bench_dd_dur), color=colors[coloridx],fontweight='bold', horizontalalignment='right', fontsize=8)

        return ax

    def plot_results(self, filename=None):
        """
        Plot the Tearsheet

        Parameters
        ==========
        filename : `str`
            Option to save the tearsheet output when a filename is specified.
        """
        rc = {
            'lines.linewidth': 1.0,
            'axes.facecolor': '0.995',
            'figure.facecolor': '0.97',
            'font.family': 'serif',
            'font.serif': 'Ubuntu',
            'font.monospace': 'Ubuntu Mono',
            'font.size': 10,
            'axes.labelsize': 10,
            'axes.labelweight': 'bold',
            'axes.titlesize': 10,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 10,
            'figure.titlesize': 12
        }
        sns.set_context(rc)
        sns.set_style("whitegrid")
        sns.set_palette("deep", desat=.6)

        vertical_sections = 5
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle(self.title, y=0.94, weight='bold')
        gs = gridspec.GridSpec(vertical_sections, 3, wspace=0.25, hspace=0.5)

        stats = self.get_results(self.strategy_equity)
        statslist = [stats]
        statslist.append(stats)
        bench_stats = None
        if self.benchmark_equity is not None:
            bench_stats = self.get_results(self.benchmark_equity)

        ax_equity = plt.subplot(gs[:2, :])
        ax_drawdown = plt.subplot(gs[2, :])
        ax_monthly_returns = plt.subplot(gs[3, :2])
        ax_yearly_returns = plt.subplot(gs[3, 2])
        ax_txt_curve = plt.subplot(gs[4, 0])
        # ax_txt_trade = plt.subplot(gs[4, 1])
        # ax_txt_time = plt.subplot(gs[4, 2])

        self._plot_equity(stats, bench_stats=bench_stats, ax=ax_equity)
        self._plot_drawdown(stats, ax=ax_drawdown)
        self._plot_monthly_returns(stats, ax=ax_monthly_returns)
        self._plot_yearly_returns(stats, ax=ax_yearly_returns)
        self._plot_txt_curve(statslist, bench_stats=bench_stats, ax=ax_txt_curve)
        # self._plot_txt_trade(stats, ax=ax_txt_trade)
        # self._plot_txt_time(stats, ax=ax_txt_time)

        # Save the figure
        if filename:
            if settings.PRINT_EVENTS:
                print(f"Saving tearsheet to {filename}")
            fig = plt.gcf()    
            fig.savefig(filename)

        # Plot the figure
        if settings.PRINT_EVENTS:
            print('Plotting the tearsheet...')
        plt.show()




class TearsheetStatisticsMultiList(Statistics):
    """
    Displays a Matplotlib-generated 'one-pager' for one or more strategies.
    """
    def __init__(self, strategy_equities, benchmark_equity=None, title=None, periods=252, strategy_labels=None):
        if not isinstance(strategy_equities, list):
            raise ValueError("strategy_equities must be a list of DataFrames.")
        self.strategy_equities = strategy_equities
        self.benchmark_equity = benchmark_equity
        self.title = title
        self.periods = periods
        self.strategy_labels = strategy_labels or [f"Strategy {i+1}" for i in range(len(strategy_equities))]

    def get_results(self, equity_df):
        equity_df = equity_df.copy()
        equity_df["returns"] = equity_df["Equity"].pct_change().fillna(0.0)
        equity_df["cum_returns"] = np.exp(np.log(1 + equity_df["returns"]).cumsum())
        dd_s, max_dd, dd_dur = perf.create_drawdowns(equity_df["cum_returns"])
        return {
            "sharpe": perf.create_sharpe_ratio(equity_df["returns"], self.periods),
            "drawdowns": dd_s,
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd,
            "max_drawdown_duration": dd_dur,
            "equity": equity_df["Equity"],
            "returns": equity_df["returns"],
            "cum_returns": equity_df["cum_returns"]
        }

    def _plot_equity(self, strat_stats_list, bench_stats=None, ax=None):
        def format_two_dec(x, pos): return '%.2f' % x
        if ax is None: ax = plt.gca()
        ax.yaxis.set_major_formatter(FuncFormatter(format_two_dec))
        ax.xaxis.set_tick_params(reset=True)
        ax.yaxis.grid(linestyle=':')
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.grid(linestyle=':')

        for i, stats in enumerate(strat_stats_list):
            stats["cum_returns"].plot(lw=2, alpha=0.6, label=self.strategy_labels[i], ax=ax)

        if bench_stats:
            bench_stats['cum_returns'].plot(lw=2, color='gray', alpha=0.6, label='Benchmark', ax=ax)

        ax.axhline(1.0, linestyle='--', color='black', lw=1)
        ax.set_ylabel('Cumulative returns')
        ax.set_xlabel('')
        ax.legend(loc='best')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
        return ax

    def _plot_drawdown(self, strat_stats_list, ax=None):
        def format_perc(x, pos): return '%.0f%%' % x
        if ax is None: ax = plt.gca()
        ax.yaxis.set_major_formatter(FuncFormatter(format_perc))
        ax.yaxis.grid(linestyle=':')
        ax.xaxis.set_tick_params(reset=True)
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.grid(linestyle=':')

        for i, stats in enumerate(strat_stats_list):
            underwater = -100 * stats["drawdowns"]
            underwater.plot(ax=ax, lw=2, kind='area', alpha=0.3, label=self.strategy_labels[i])

        ax.set_title('Drawdown (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.legend(loc='best')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
        return ax

    def _plot_monthly_returns(self, strat_stats, ax=None):
        if ax is None: ax = plt.gca()
        returns = strat_stats["returns"]
        monthly_ret = perf.aggregate_returns(returns, 'monthly').unstack().round(3)
        monthly_ret.rename(columns={1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                                    5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
                                    9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}, inplace=True)

        sns.heatmap(monthly_ret.fillna(0) * 100.0, annot=True, fmt="0.1f",
                    annot_kws={"size": 8}, center=0.0, cbar=False,
                    cmap=cm.RdYlGn, ax=ax)
        ax.set_title('Monthly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        return ax

    def _plot_yearly_returns(self, strat_stats, ax=None):
        def format_perc(x, pos): return '%.0f%%' % x
        if ax is None: ax = plt.gca()
        returns = strat_stats["returns"]
        yly_ret = perf.aggregate_returns(returns, 'yearly') * 100.0
        yly_ret.plot(ax=ax, kind="bar")
        ax.yaxis.set_major_formatter(FuncFormatter(format_perc))
        ax.set_title('Yearly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        ax.yaxis.grid(True)
        ax.xaxis.grid(False)
        return ax

    def _plot_txt_curve(self, strat_stats, bench_stats=None, ax=None):
        def format_perc(x, pos): return '%.0f%%' % x
        if ax is None: ax = plt.gca()
        ax.yaxis.set_major_formatter(FuncFormatter(format_perc))
        '''
        #Draw Equity Box titles and outline
        ax.set_title('Equity Curve', fontweight='bold')
        ax.axis([0, 10, 0, 10])
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.get_xaxis().set_visible(False)
        '''

        #text box for returns -Labels-
        ax.text(7.50, 8.2, 'Strategy', fontweight='bold', horizontalalignment='right', fontsize=8, color='green')
        ax.text(0.25, 6.9, 'Total Return', fontsize=8)
        ax.text(0.25, 5.9, 'CAGR', fontsize=8)
        ax.text(0.25, 4.9, 'Sharpe Ratio', fontsize=8)
        ax.text(0.25, 3.9, 'Sortino Ratio', fontsize=8)
        ax.text(0.25, 2.9, 'Annual Volatility', fontsize=8)
        ax.text(0.25, 1.9, 'Max Daily Drawdown', fontsize=8)
        ax.text(0.25, 0.9, 'Max Drawdown Duration (Days)', fontsize=8)

        #calc strategy values for returns box
        returns = strat_stats["returns"]
        cum_returns = strat_stats["cum_returns"]
        tot_ret = cum_returns.iloc[-1] - 1.0
        cagr = perf.create_cagr(cum_returns, self.periods)
        sharpe = perf.create_sharpe_ratio(returns, self.periods)
        sortino = perf.create_sortino_ratio(returns, self.periods)
        dd, dd_max, dd_dur = perf.create_drawdowns(cum_returns)

        #total return val
        ax.text(7.50, 6.9, '{:.0%}'.format(tot_ret), fontweight='bold', horizontalalignment='right', fontsize=8)
        #CAGR val
        ax.text(7.50, 5.9, '{:.2%}'.format(cagr), fontweight='bold', horizontalalignment='right', fontsize=8)
        #SHARP
        ax.text(7.50, 4.9, '{:.2f}'.format(sharpe), fontweight='bold', horizontalalignment='right', fontsize=8)
        #sortno
        ax.text(7.50, 3.9, '{:.2f}'.format(sortino), fontweight='bold', horizontalalignment='right', fontsize=8)
        #annual Vol
        ax.text(7.50, 2.9, '{:.2%}'.format(returns.std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=8)
        #max drawdown
        ax.text(7.50, 1.9, '{:.2%}'.format(dd_max), color='red', fontweight='bold', horizontalalignment='right', fontsize=8)
        #draw down duration
        ax.text(7.50, 0.9, '{:.0f}'.format(dd_dur), fontweight='bold', horizontalalignment='right', fontsize=8)

        if bench_stats is not None:
            #calculate values for benchmark backtest if provided
            bench_returns = bench_stats["returns"]
            bench_cum_returns = bench_stats["cum_returns"]
            bench_tot_ret = bench_cum_returns.iloc[-1] - 1.0
            bench_cagr = perf.create_cagr(bench_cum_returns, self.periods)
            bench_sharpe = perf.create_sharpe_ratio(bench_returns, self.periods)
            bench_sortino = perf.create_sortino_ratio(bench_returns, self.periods)
            _, bench_dd_max, bench_dd_dur = perf.create_drawdowns(bench_cum_returns)
            #Display benchmark title and values
            ax.text(10.0, 8.2, 'Benchmark', fontweight='bold', horizontalalignment='right', fontsize=8, color='gray')
            ax.text(10.0, 6.9, '{:.0%}'.format(bench_tot_ret), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(10.0, 5.9, '{:.2%}'.format(bench_cagr), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(10.0, 4.9, '{:.2f}'.format(bench_sharpe), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(10.0, 3.9, '{:.2f}'.format(bench_sortino), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(10.0, 2.9, '{:.2%}'.format(bench_returns.std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(10.0, 1.9, '{:.2%}'.format(bench_dd_max), color='red', fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(10.0, 0.9, '{:.0f}'.format(bench_dd_dur), fontweight='bold', horizontalalignment='right', fontsize=8)

        
        return ax

    def plot_results(self, filename=None):
        rc = {
            'lines.linewidth': 1.0,
            'axes.facecolor': '0.995',
            'figure.facecolor': '0.97',
            'font.family': 'serif',
            'font.serif': 'Ubuntu',
            'font.monospace': 'Ubuntu Mono',
            'font.size': 10,
            'axes.labelsize': 10,
            'axes.labelweight': 'bold',
            'axes.titlesize': 10,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 10,
            'figure.titlesize': 12
        }
        sns.set_context(rc)
        sns.set_style("whitegrid")
        sns.set_palette("deep", desat=.6)

        vertical_sections = 5
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle(self.title, y=0.94, weight='bold')
        gs = gridspec.GridSpec(vertical_sections, 3, wspace=0.25, hspace=0.5)

        strat_stats_list = [self.get_results(df) for df in self.strategy_equities]
        bench_stats = self.get_results(self.benchmark_equity) if self.benchmark_equity is not None else None

        self._plot_equity(strat_stats_list, bench_stats=bench_stats, ax=plt.subplot(gs[:2, :]))
        self._plot_drawdown(strat_stats_list, ax=plt.subplot(gs[2, :]))
        self._plot_monthly_returns(strat_stats_list[0], ax=plt.subplot(gs[3, :2]))
        self._plot_yearly_returns(strat_stats_list[0], ax=plt.subplot(gs[3, 2]))
        self._plot_txt_curve(strat_stats_list[0], bench_stats=bench_stats, ax=plt.subplot(gs[4, 0]))

        if filename:
            if settings.PRINT_EVENTS:
                print(f"Saving tearsheet to {filename}")
            fig.savefig(filename)

        if settings.PRINT_EVENTS:
            print("Plotting the tearsheet...")
        plt.show()
