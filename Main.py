import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta 

class Backtester: 
    url = "https://api.binance.com/api/v3/klines"
    
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = self.load_data()
    
    def load_data(self): 
        params = {
            'symbol': self.symbol,
            'interval': '1d',
            'startTime': int(pd.Timestamp(self.start_date).timestamp() * 1000),
            'endTime': int(pd.Timestamp(self.end_date).timestamp() * 1000)
        }
        response = requests.get(self.url, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        return df
    
    def run_strategy(self, strategy_func):
        positions = strategy_func(self.data)
        return positions
    
    def calculate_returns(self, positions):
        positions_df = pd.DataFrame(positions, index=self.data.index, columns=['Position'])
        returns = self.data['close'].pct_change() * positions_df['Position'].shift(1)
        returns = returns.replace([np.inf, -np.inf], np.nan)  
        returns = returns.dropna()  
        return returns

    def calculate_basic_statistics(self, returns):
        mean_return = returns.mean()
        variance = returns.var()
        beta_value = beta.fit(returns)[0]
        return mean_return, variance, beta_value
    
    def generate_performance_chart(self, returns):
        cumulative_returns = (1 + returns).cumprod() - 1
        cumulative_returns.plot(figsize=(10, 6))
        plt.title('Performance de la stratégie')
        plt.xlabel('Date')
        plt.ylabel('Rendement cumulatif')
        plt.grid(True)
        plt.show()
    
    def calculate_advanced_statistics(self, returns):
        downside_beta = beta.fit(returns[returns < 0])[0]
        max_drawdown = (1 + returns).cumprod().div((1 + returns).cumprod().cummax()) - 1
        max_drawdown = max_drawdown.min()
        return downside_beta, max_drawdown

# Fonction de stratégie
def simple_strategy(data):
    data['SMA_10'] = data['close'].rolling(window=10).mean()  # Utiliser la SMA sur 10 jours
    distance_from_sma = data['close'] - data['SMA_10']
    long_condition = data['close'] > data['SMA_10'] * 1.10  # Entrer en long lorsque le prix est 10% supérieur à la SMA 10
    short_condition = data['close'] < data['SMA_10'] * 0.90  # Entrer en short lorsque le prix est 10% inférieur à la SMA 10
    positions = np.where(long_condition, 1, np.where(short_condition, -1, 0))
    return positions


# Demander à l'utilisateur de saisir le symbole de la crypto-monnaie
symbol = input("Entrez le symbole de la crypto-monnaie (par exemple, BTCUSDT): ")

# Paramètres de date 
start_date = '2022-01-01'
end_date = '2023-01-01'

# Création de l'instance du backtester
backtester = Backtester(symbol, start_date, end_date)

# Exécution de la stratégie
positions = backtester.run_strategy(simple_strategy)

# Calcul des rendements
returns = backtester.calculate_returns(positions)

# Calcul des statistiques de base
mean_return, variance, beta_value = backtester.calculate_basic_statistics(returns)

# Affichage des statistiques de base
print("Rendement moyen:", mean_return)
print("Variance:", variance)
print("Bêta:", beta_value)

# Génération du graphique de performance
backtester.generate_performance_chart(returns)

# Calcul des statistiques avancées
downside_beta, max_drawdown = backtester.calculate_advanced_statistics(returns)

# Affichage des statistiques avancées
print("Bêta en baisse:", downside_beta)
print("Drawdown maximal:", max_drawdown)
