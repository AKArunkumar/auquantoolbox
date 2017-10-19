from backtester.trading_system_parameters import TradingSystemParameters
from datetime import timedelta
from backtester.dataSource.yahoo_data_source import YahooStockDataSource
from backtester.executionSystem.simple_execution_system import SimpleExecutionSystem
from backtester.orderPlacer.backtesting_order_placer import BacktestingOrderPlacer
from backtester.trading_system import TradingSystem
from backtester.constants import *
from backtester.logger import *
from my_custom_feature import MyCustomFeature


class MyTradingParams(TradingSystemParameters):
    '''
    Returns an instance of class DataParser. Source of data for instruments
    '''
    def getDataParser(self):
        instrumentIds = ['IBM', 'AAPL', 'MSFT']
        startDateStr = '2017/05/10'
        endDateStr = '2017/06/09'
        instrumentIds = list(set(instrumentIds + [self.getBenchmark()]))
        return YahooStockDataSource(cachedFolderName='yahooData',
                                     instrumentIds=instrumentIds,
                                     startDateStr=startDateStr,
                                     endDateStr=endDateStr)

    '''
    Return the market instrument to benchmark your strategy's perfromancy. 
    Strategies that perform better than the benchmark are considered successful.
    For most cases, choose the broad stock market index, like S&P500(US) or Nifty50(India)
    '''

    def getBenchmark(self):
        return 'SPY'

    '''
    Return starting capital - the initial amount of money you're putting into your trading system
    '''
    def getStartingCapital(self):
        return 1000000

    '''
    Returns an instance of class TimeRule, which describes the times at which
    we should update all the features and try to execute any trades based on
    execution logic.
    For eg, for intra day data, you might have a system, where you get data
    from exchange at a very fast rate (ie multiple times every second). However,
    you might want to run your logic of computing features or running your execution
    system, only at some fixed intervals (like once every 5 seconds). This depends on your
    strategy whether its a high, medium, low frequency trading strategy. Also, performance
    is another concern. if your execution system and features computation are taking
    a lot of time, you realistically wont be able to keep upto pace.
    '''
    def getTimeRuleForUpdates(self):
        return NotImplementedError

    '''
    This is a way to use any custom features you might have made.
    Returns a dictionary where
    key: featureId to access this feature (Make sure this doesnt conflict with any of the pre defined feature Ids)
    value: Your custom Class which computes this feature. The class should be an instance of Feature
    Eg. if your custom class is MyCustomFeature, and you want to access this via featureId='my_custom_feature',
    you will import that class, and return this function as {'my_custom_feature': MyCustomFeature}
    '''
    def getCustomFeatures(self):
        return {'my_custom_feature': MyCustomFeature}

    '''
    Returns a dictionary with:
    key: string representing instrument type. Right now INSTRUMENT_TYPE_OPTION, INSTRUMENT_TYPE_STOCK, INSTRUMENT_TYPE_FUTURE
    value: Array of instrument feature config dictionaries
        feature config Dictionary has the following keys:
        featureId: a string representing the type of feature you want to use
        featureKey: {optional} a string representing the key you will use to access the value of this feature.
                    If not present, will just use featureId
        params: {optional} A dictionary with which contains other optional params if needed by the feature
    Example:
    positionConfigDict = {'featureId': 'position'}
    vwapConfigDict = {'featureKey': 'price',
                          'featureId': 'vwap'}
    movingAvg_30Dict = {'featureKey': 'mv_avg_30',
                          'featureId': 'moving_average',
                          'params': {'days': 30}}
    movingAvg_90Dict = {'featureKey': 'mv_avg_90',
                          'featureId': 'moving_average',
                          'params': {'days': 90}}
    return {INSTRUMENT_TYPE_FUTURE: [positionConfigDict, vwapConfigDict],
            INSTRUMENT_TYPE_STOCK: [positionConfigDict, movingAvg_30Dict, movingAvg_90Dict]}

    For each future instrument, you will have features keyed by position and price.
    For each stock instrument, you will have features keyed by position, mv_avg_30, mv_avg_90
    '''
    def getInstrumentFeatureConfigDicts(self):
        # ADD RELEVANT FEATURES HERE
        vwapConfigDict = {'featureKey': 'price',
                          'featureId': 'vwap',
                          'params': {}}
        customFeatureDict = {'featureKey': 'custom_inst_feature',
                             'featureId': 'my_custom_feature',
                             'params': {'param1': 'value1'}}
        return {INSTRUMENT_TYPE_STOCK: [customFeatureDict]}

    '''
    Returns an array of market feature config dictionaries
        market feature config Dictionary has the following keys:
        featureId: a string representing the type of feature you want to use
        featureKey: a string representing the key you will use to access the value of this feature.this
        params: A dictionary with which contains other optional params if needed by the feature
    '''
    def getMarketFeatureConfigDicts(self):
        # ADD RELEVANT FEATURES HERE
        customFeatureDict = {'featureKey': 'custom_mrkt_feature',
                             'featureId': 'my_custom_feature',
                             'params': {'param1': 'value1'}}
        return [customFeatureDict]

    '''
    Returns the feature key of instrument to use for price calculations ie pnl, fees etc.
    type: Type of Instrument
    For example, for stocks close should be fine.
    Defaults to close for all insturment types
    '''
    def getPriceFeatureKey(self):
        return 'close'

    '''
    A function that returns your predicted value based on your heuristics.
    Combine all the features to create a prediction function which should output the probability that a given instrument is a buy. 
    A predicted value of 1 means instrument is a guaranteed buy, 
    Value of -1 means a guaranteed sell and 0.5 means it's trading at fair price (neither a buy or a sell)
    If you are just trading one asset like a stock, prediction will be on the value of the stock.
    If you are doing pair trading, the prediction could be on the difference in the prices of the stocks.
    Arguments:
    time - When this prediction is being calculated
    currentMarketFeatures - Dictionary of market features which have been calculated at this update cycle.
    instrumentManager - Holder for all instruments and everything else if you need.
    '''
    def getPrediction(self, time, currentMarketFeatures, instrumentManager):
        lookbackMarketFeaturesDf = instrumentManager.getDataDf() # Does not include currentMarketFeatures yet
        # IMPLEMENT THIS
        predictions = {}
        for k in instrumentManager.getAllInstrumentsByInstrumentId():
            predictions[k] = 0.5
        return predictions

    '''
    Returns the type of execution system we want to use. Its an implementation of the class ExecutionSystem
    It converts prediction to intended trades for different instruments. 
    Instruments with probability predictions values above enter_threshold are bought and below (1-enter_threshold) are sold.
    Instrument positions with probability predictions values betweem (1-exit_threshold) and exit_threshold are closed 
    '''
    def getExecutionSystem(self):
        return SimpleExecutionSystem(enter_threshold=0.7, 
                                     exit_threshold=0.55, 
                                     longLimit=10000, 
                                     shortLimit=10000,
                                     capitalUsageLimit = 0.10*self.getStartingCapital(), 
                                     lotSize=10)

    '''
    Returns the type of order placer we want to use. its an implementation of the class OrderPlacer.
    It helps place an order, and also read confirmations of orders being placed.
    For Backtesting, you can just use the BacktestingOrderPlacer, which places the order which you want, and automatically confirms it too.
    '''
    def getOrderPlacer(self):
        return BacktestingOrderPlacer()

    '''
    Returns the amount of lookback data you want for your calculations. The historical market features and instrument features are only
    stored upto this amount.
    '''
    def getLookbackSize(self):
        return 500


if __name__ == "__main__":
    tsParams = MyTradingParams()
    tradingSystem = TradingSystem(tsParams)
    logInfo('THIS IS A SAMPLE TRADING SYSTEM' + '\n\n' + \
     'Use this as a template to implement features and prediction function' + '\n\n' + \
     'Uncomment the last line when you want to execute your trading system' + '\n\n' + \
     '--------------', True)
    tradingSystem.startTrading()
