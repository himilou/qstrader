import os
import pandas as pd
import pytz
import datetime
from dateutil.relativedelta import relativedelta
from qstrader import __version__ as ver

#Helpers is a collection of classes and modules to be used to obtain and clean data for qstrader
#TODO Convert Helpers into part of the qstrader module

class WorkingDirs():
    '''
    WorkingDirs attempts to determine where the initial script is being lanched from
    as well as where the other helper directories are for the running install
    '''
    name = ''
    examplesDirs= ''
    traderDir = ''
    scriptsDir = ''
    dataDir = ''

    def __init__(self):
        self
        self.name = "<class> WorkingDirs"
        self.examplesDirs= ''
        self.traderDir = ''
        self.scriptsDir = ''
        self.dataDir = ''

    def __str__(self):
        return f"{self.name}({self.__version__})"
    
    def getdirs(self):
        current = os.getcwd()
        dirs = os.path.split(current)
        
        tomatch = dirs[1].lower()
        match tomatch:
            case 'examples':
                self.dataDir = dirs[0] + '\\' + 'data'
                self.scriptsDir = dirs[0] + '\\' + 'scripts'
                self.examplesDir = dirs[0] + '\\' + 'examples'
                self.traderDir = dirs[0]
            case 'qstrader':
                self.dataDir = dirs[0] + '\\' + 'qstrader' + '\\' + 'data'
                self.traderDir = dirs[0] + '\\' + 'qstrader' 
                self.examplesDir = dirs[0] + '\\' + 'qstrader' + '\\' + 'examples'
                self.scriptsDir = dirs[0] + '\\' + 'qstrader' + '\\' + 'scripts'
            
            case 'scripts':
                self.dataDir = dirs[0] + '\\' + 'data'
                self.scriptsDir = dirs[0] + '\\' + 'scripts'
                self.examplesDir = dirs[0] + '\\' + 'examples'
                self.traderDir = dirs[0]
            case _:
                print("Unknown directory structure. Please execute strategy script from \\Examples dir")
                raise Exception('Unknown path. Are you installed in the qstrader directory?')

    def printall(self):
        print(self.name)
        print('Data Dir:' + self.dataDir)
        print('Base Dir' + self.traderDir)
        print('Scripts Dir' + self.scriptsDir)
        print('Examples Dir' + self.examplesDir)
    
class Timespan():
    '''Timespan is a helper class to handle backtesting dates. 
    parameters:
        begintime : time to start backtest in the format of YYYY-mm-dd
        endtime : time to end the backtest in the format of YYYY-mm-dd
        frequency : time period to comare data . 1d, 1w, 1h, 1m
        If no parameters are specified endtime is today, begintime is 2 years prior
        and frequency is 1d
        Yahoo constrains the time periods you can download data for depending on the frequency
    '''
    name = "<class Timespan>"
    
    def __init__(self,begintime = None,endtime = None,frequency = None):
        self.endtime = endtime
        self.frequency = frequency
        self.begintime = begintime

        dt =  datetime.datetime.now()
        if (self.begintime is None):
            bt = dt - relativedelta(years=2)            #start backtrace 2 years before today
            self.begintime = bt.strftime("%Y-%m-%d")
        else:
            self.begintime = begintime
        
        if(self.endtime is None):
            self.endtime = dt.strftime("%Y-%m-%d")
        else:
            self.endtime = endtime
        if(self.frequency is None):
            self.frequency = "1d"
        else:
            self.frequency = frequency
        
    def __str__(self):
        pass
    
    def printall(self):
        print(self.name)
        print("Begin time:" + self.begintime)
        print("End time:" + self.endtime)
        print("Frequency:" + self.frequency)

    



