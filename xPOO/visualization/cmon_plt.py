import numpy as np
import matplotlib.pyplot as plt


__all__ = ['addLines', 'BorderPlot']


class _pltutils(object):

    """
    **kwargs
    ----------
    title : title of plot [def: '']
    xlabel : label of x-axis [def : '']
    ylabel : label of y-axis [def : '']
    xlim : limit of the x-axis [def : [], current limit of x]
    ylim : limit of the y-axis [def : [], current limit of y]
    xticks : ticks of x-axis [def : [], current x-ticks]
    yticks : ticks of y-axis [def : [], current y-ticks]
    xticklabels : label of the x-ticks [def : [], current x-ticklabels]
    yticklabels : label of the y-ticks [def : [], current y-ticklabels]
    style : style of the plot [def : 'seaborn-poster']
    """

    def __init__(self, ax, title='', xlabel='', ylabel='', xlim=[], ylim=[],
                 xticks=[], yticks=[], xticklabels=[], yticklabels=[],
                 style='seaborn-poster'):

        if not hasattr(self, '_xType'):
            self._xType = int
        if not hasattr(self, '_yType'):
            self._yType = int
        # Axes ticks :
        if np.array(xticks).size:
            ax.set_xticks(xticks)
        if np.array(yticks).size:
            ax.set_yticks(yticks)
        # Axes ticklabels :
        if xticklabels:
            ax.set_xticklabels(xticklabels)
        if yticklabels:
            ax.set_yticklabels(yticklabels)
        # Axes labels :
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        # Axes limit :
        if np.array(xlim).size:
            ax.set_xlim(xlim)
        if np.array(ylim).size:
            ax.set_ylim(ylim)
        ax.set_title(title, y=1.02)
        # Style :
        plt.style.use(style)


class ndplot(object):

    """ndplot with automatic management of sublot

    Methods
    ----------
    -> plot1D : 1D plot
    -> plot2D : 2D plot
    """

    def __init__(self, num=None, figsize=None, dpi=None, title='', **kwargs):
        self._fig = plt.figure(num=num, figsize=figsize, dpi=dpi, **kwargs)
        if title is not '':
            self.fig.suptitle(title, fontsize=14, fontweight='bold')

    def plot1D(self, y, x=None, maxplot=10, kind='plot', **kwargs):
        """Simple one dimentional plot

        Parameters
        ----------
        y : array
            Data to plot. y can either have one, two or three dimensions.
            If y is a vector, it will be plot in a simple window. If y is
            a matrix, all values inside are going to be superimpose. If y
            is a 3D matrix, the first dimension control the number of subplots.

        x : array, optional, [def : None]
            x vector for plotting data.

        maxplot : int, optional, [def : 10]
            Control the maximum number of subplot to prevent very large plot.
            By default, maxplot is 10 which mean that only 10 subplot can be
            defined.

        kind : string, optional, [def : 'plot']
            Control the type of plot. Choose between 'plot' and 'scatter'.
        """
        # Check y shape :
        y = self._checkarray(y)
        if x is None:
            x = np.arange(y.shape[1])
        # Plotting function :

        def _fcn(y):
            if kind == 'plot':
                plt.plot(x, y)
            elif kind == 'scatter':
                plt.scatter(x, y)
            _pltutils(plt.gca(), **kwargs)
        # Run function for each yi :
        return self._subplotND(y, _fcn, maxplot)

    def plot2D(self, y, xvec=None, yvec=None, maxplot=10, cmap='inferno',
               interpolation='none', colorbar=True, vmin=None, vmax=None,
               **kwargs):
        """Plot y as an image

        Parameters
        ----------
        y : array
            Data to plot. y can either have one, two or three dimensions.
            If y is a vector, it will be plot in a simple window. If y is
            a matrix, all values inside are going to be superimpose. If y
            is a 3D matrix, the first dimension control the number of subplots.

        xvec, yvec : array, optional, [def : None]
            Vectors for y and x axis of each picture

        maxplot : int, optional, [def : 10]
            Control the maximum number of subplot to prevent very large plot.
            By default, maxplot is 10 which mean that only 10 subplot can be
            defined.

        cmap : string, optional, [def : 'inferno']
            Choice of the colormap

        interpolation : string, optional, [def : 'none']
            Plot interpolation

        colorbar : bool, optional, [def : True]
            Add or not a colorbar to your plot

        vmin, vmax : int/float, optional, [def : None]
            Control minimum and maximum of the image
        """
        # Check y shape :
        y = self._checkarray(y)
        if xvec is None:
            xvec = np.arange(y.shape[-1])
        if yvec is None:
            yvec = np.arange(y.shape[1])
        # Plotting function :

        def _fcn(y):
            im = plt.imshow(y, aspect='auto', cmap=cmap,
                            interpolation=interpolation, vmin=vmin, vmax=vmax,
                            extent=[xvec[0], xvec[-1], yvec[-1], yvec[0]])
            ax = plt.gca()
            _pltutils(ax, **kwargs)
            plt.colorbar(im)
            ax.invert_yaxis()
        # Run function for each yi :
        return self._subplotND(y, _fcn, maxplot)

    def _checkarray(self, y):
        """Check input shape
        """
        # Vector :
        if y.ndim == 1:
            y = y[np.newaxis, ..., np.newaxis]
        # 2D array :
        elif y.ndim == 2:
            y = y[np.newaxis]
        # more than 3D array :
        elif y.ndim > 3:
            raise ValueError('array to plot should not have more than '
                             '3 dimensions')
        return y

    def _subplotND(self, y, fcn, maxplot):
        """Manage subplots
        """
        L = y.shape[0]
        if L <= maxplot:
            fig = self.fig
            if L < 4:
                ncol, nrow = L, 1
            else:
                ncol = round(np.sqrt(L)).astype(int)
                nrow = round(L/ncol).astype(int)
                while nrow*ncol < L:
                    nrow += 1
            for k in range(L):
                fig.add_subplot(nrow, ncol, k+1)
                fcn(y[k, ...])
            return plt.gca()
        else:
            raise ValueError('Warning : the "maxplot" parameter prevent to a'
                             'large number of plot. To increase the number'
                             ' of plot, change "maxplot"')

ndplot.plot1D.__doc__ += _pltutils.__doc__
ndplot.plot2D.__doc__ += _pltutils.__doc__


class addLines(object):

    """Add vertical and horizontal lines to an existing plot.

    Parameters
    ----------
    ax : matplotlib axes
        The axes to add lines. USe for example plt.gca()

    vLines : list, [def : []]
        Define vertical lines. vLines should be a list of int/float

    vColor : list of strings, [def : ['gray']]
        Control the color of the vertical lines. The length of the
        vColor list must be the same as the length of vLines

    vShape : list of strings, [def : ['--']]
        Control the shape of the vertical lines. The length of the
        vShape list must be the same as the length of vLines

    hLines : list, [def : []]
        Define horizontal lines. hLines should be a list of int/float

    hColor : list of strings, [def : ['black']]
        Control the color of the horizontal lines. The length of the
        hColor list must be the same as the length of hLines

    hShape : list of strings, [def : ['-']]
        Control the shape of the horizontal lines. The length of the
        hShape list must be the same as the length of hLines
    """

    def __init__():
        pass

    def __new__(self, ax,
                vLines=[], vColor=None, vShape=None, vWidth=None,
                hLines=[], hColor=None, hWidth=None, hShape=None):
        # Get the axes limits :
        xlim = list(ax.get_xlim())
        ylim = list(ax.get_ylim())

        # Get the number of vertical and horizontal lines :
        nV = len(vLines)
        nH = len(hLines)

        # Define the color :
        if not vColor:
            vColor = ['gray']*nV
        if not hColor:
            hColor = ['black']*nH

        # Define the width :
        if not vWidth:
            vWidth = [1]*nV
        if not hWidth:
            hWidth = [1]*nH

        # Define the shape :
        if not vShape:
            vShape = ['--']*nV
        if not hShape:
            hShape = ['-']*nH

        # Plot Verticale lines :
        for k in range(0, nV):
            ax.plot((vLines[k], vLines[k]), (ylim[0], ylim[1]), vShape[k],
                    color=vColor[k], linewidth=vWidth[k])
        # Plot Horizontal lines :
        for k in range(0, nH):
            ax.plot((xlim[0], xlim[1]), (hLines[k], hLines[k]), hShape[k],
                    color=hColor[k], linewidth=hWidth[k])


class BorderPlot(_pltutils):

    """Plot a signal with it associated deviation. The function plot the
    mean of the signal, and the deviation (std) or standard error on the mean
    (sem) in transparency.

    Parameters
    ----------
    time : array/limit
        The time vector of the plot (len(time)=N)

    x : numpy array
        The signal to plot. One dimension of x must be the length of time N.
        The other dimension will be consider to define the deviation. For
        example, x.shape = (N, M)

    y : numpy array, optional, [def : np.array([])]
        Label vector to separate the x signal in diffrent classes. The length
        of y must be M. If no y is specified, the deviation will be computed
        for the entire array x. If y is composed with integers
        (example : y = np.array([1,1,1,1,2,2,2,2])), the functino will geneate
        as many curve as the number of unique classes in y. In this case, two
        curves are going to be considered.

    kind : string, optional, [def : 'sem']
        Choose between 'std' for standard deviation and 'sem', standard error
        on the mean (wich is: std(x)/sqrt(N-1))

    color : string or list of strings, optional
        Specify the color of each curve. The length of color must be the same
        as the length of unique classes in y.

    alpha : int/float, optional [def : 0.2]
        Control the transparency of the deviation.

    linewidth : int/float, optional, [def : 2]
        Control the width of the mean curve.

    legend : string or list of strings, optional, [def : '']
        Specify the label of each curve and generate a legend. The length of
        legend must be the same as the length of unique classes in y.

    ncol : integer, optional, [def : 1]
        Number of colums for the legend

    Return
    ----------
    The axes of the plot.
    """
    __doc__ += _pltutils.__doc__

    def __init__(self, time, x, y=np.array([]), kind='sem', color='',
                 alpha=0.2, linewidth=2, legend='', ncol=1, **kwargs):
        pass

    def __new__(self, time, x, y=np.array([]), kind='sem', color='', alpha=0.2,
                linewidth=2, legend='', ncol=1, **kwargs):

        self.xType = type(time[0])
        self.yType = type(x[0, 0])

        # Check arguments :
        if x.shape[1] == len(time):
            x = x.T
        npts, dev = x.shape
        if not y.size:
            y = np.array([0]*dev)
        yClass = np.unique(y)
        nclass = len(yClass)
        if not color:
            color = ['darkblue', 'darkgreen', 'darkred',
                     'darkorange', 'purple', 'gold', 'dimgray', 'k']
        else:
            if type(color) is not list:
                color = [color]
            if len(color) is not nclass:
                color = color*nclass
        if not legend:
            legend = ['']*dev
        else:
            if type(legend) is not list:
                legend = [legend]
            if len(legend) is not nclass:
                legend = legend*nclass

        # For each class :
        for k in yClass:
            _BorderPlot(time, x[:, np.where(y == k)[0]], color[k], kind=kind,
                        alpha=alpha, linewidth=linewidth, legend=legend[k])
        ax = plt.gca()
        plt.axis('tight')

        _pltutils.__init__(self, ax, **kwargs)

        return plt.gca()


def _BorderPlot(time, x, color, kind='sem', alpha=0.2, legend='', linewidth=2):
    npts, dev = x.shape
    # Get the deviation/sem :
    xStd = np.std(x, axis=1)
    if kind is 'sem':
        xStd = xStd/np.sqrt(npts-1)
    xMean = np.mean(x, 1)
    xLow, xHigh = xMean-xStd, xMean+xStd

    # Plot :
    ax = plt.plot(time, xMean, color=color, label=legend, linewidth=linewidth)
    plt.fill_between(time, xLow, xHigh, alpha=alpha, color=ax[0].get_color())
