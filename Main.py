import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta

class Backtester:
    def __init__(self, data):
        self.data = data
    
    def run_strategy(self, strategy_func):
        positions = strategy_func(self.data)
        return positions
    
    def calculate_returns(self, positions):
        returns = self.data['Close'].pct_change() * positions.shift(1)
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
    # Stratégie consiste à acheter si le prix de clôture est supérieur à la moyenne mobile simple sur 50 jours, sinon vendre.
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    positions = np.where(data['Close'] > data['SMA_50'], 1, -1)
    return positions

# Chargement des données (à remplacer par votre propre source de données)
data = pd.read_csv('data.csv')  # Assurez-vous que le fichier 'data.csv' contient les colonnes OHLCV

# Création de l'instance du backtester
backtester = Backtester(data)

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
