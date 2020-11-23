import pandas as pd


class Quotes:
    def __init__(self, dates, open_prices, close_prices, high_prices, low_prices, volumes):
        self.dates = dates
        self.open_prices = open_prices
        self.close_prices = close_prices
        self.high_prices = high_prices
        self.low_prices = low_prices
        self.volumes = volumes

    def _get_moving_average(self, data, window):
        moving_average = pd.Series(data).rolling(window).mean()
        self.__setattr__(f'moving_average_{data.name}_{window}', moving_average)
        return True

    def moving_average_prices(self, window):
        data = pd.Series(self.close_prices)
        data.name = 'price'
        self._get_moving_average(data, window)

    def moving_average_volumes(self, window):
        data = pd.Series(self.volumes)
        data.name = 'volume'
        self._get_moving_average(data, window)
