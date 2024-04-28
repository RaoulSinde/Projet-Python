import requests
import pandas as pd
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from scipy.stats import beta
from tkinter import ttk
from tkcalendar import Calendar


class Backtester:
    """
        Cette classe est responsable du chargement des données historiques, de l'exécution de la stratégie de trading, 
        du calcul des rendements et des statistiques, ainsi que de la génération de graphiques de performance.
    """
    url = "https://api.binance.com/api/v3/klines"

    def __init__(self, symbol, start_date, end_date):
        """
        Initialisation des différents attributs de la classe.
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = self.load_data()

    def load_data(self):
        """
        Cette fonction utilise l'API de Binance pour charger les données historiques de prix de la crypto-monnaie spécifiée 
        dans l'intervalle de dates donné.
        """
        params = {
            'symbol': self.symbol,
            'interval': '1d',
            'startTime': int(pd.Timestamp(self.start_date).timestamp() * 1000),
            'endTime': int(pd.Timestamp(self.end_date).timestamp() * 1000)
        }
        response = requests.get(self.url, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                         'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                                         'taker_buy_quote_asset_volume', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        return df

    def run_strategy(self, strategy_func):
        """
        Cette fonction exécute la stratégie de trading définie plus loin sur les données historiques récupérées.
        """
        positions = strategy_func(self.data)
        return positions

    def calculate_returns(self, positions):
        """
        Cette fonction calcule les rendements en fonction des positions prises par la stratégie de trading.
        """
        positions_df = pd.DataFrame(positions, index=self.data.index, columns=['Position'])
        returns = self.data['close'].pct_change() * positions_df['Position'].shift(1)
        returns = returns.replace([np.inf, -np.inf], np.nan)
        returns = returns.dropna()
        return returns


def calculate_basic_statistics(returns):
    """
    Cette fonction calcule des statistiques de base telles que le rendement moyen, la variance et le bêta à partir des rendements générés.
    """
    mean_return = returns.mean()
    variance = returns.var()
    beta_value = beta.fit(returns)[0]
    return mean_return, variance, beta_value


def generate_performance_chart(returns):
    """
    Cette fonction génère un graphique de performance montrant les rendements cumulés de la stratégie de trading.
    """
    cumulative_returns = (1 + returns).cumprod() - 1
    cumulative_returns.plot(figsize=(10, 6))
    plt.title('Performance de la stratégie')
    plt.xlabel('Date')
    plt.ylabel('Rendement cumulé')
    plt.grid(True)
    plt.show()


def calculate_advanced_statistics(returns):
    """
    Cette fonction calcule des statistiques avancées telles que le bêta en baisse et le drawdown maximal à partir des rendements générés.
    """
    downside_beta = beta.fit(returns[returns < 0])[0]
    max_drawdown = (1 + returns).cumprod().div((1 + returns).cumprod().cummax()) - 1
    max_drawdown = max_drawdown.min()
    return downside_beta, max_drawdown


# Fonction de stratégie
def simple_strategy(data):
    """
    Cette fonction implémente une stratégie de trading simple basée sur la moyenne mobile sur 10 jours (SMA_10) du crypto-actif.
    """
    data['SMA_10'] = data['close'].rolling(window=10).mean()  # Utiliser la SMA sur 10 jours
    distance_from_sma = data['close'] - data['SMA_10']
    long_condition = data['close'] > data['SMA_10'] * 1.10  # Entrer en long lorsque le prix est 10% > SMA 10
    short_condition = data['close'] < data['SMA_10'] * 0.90  # Entrer en short lorsque le prix est 10% < SMA> 10
    positions = np.where(long_condition, 1, np.where(short_condition, -1, 0))
    return positions


# Demander à l'utilisateur de saisir le symbole de la crypto-monnaie
# et prend USDT en seconde valeur de la paire par défaut
symbol = input("Entrez le symbole de la crypto-monnaie (par exemple, BTC): ") + "USDT"

print("Vous allez sélectionner les dates : préférez un intervalle moyen/long terme")


class BacktestExecution:
    """
    Cette classe gère l'interface utilisateur pour sélectionner les dates de début et de fin de l'intervalle de test. 
    Elle permet aussi de mettre en route le backtest.
    """
    def __init__(self, root):
        # Construction de la fenêtre qui affiche les calendriers pour la sélection des dates
        self.root = root
        self.root.title("Sélection des dates")

        self.start_date_label = ttk.Label(root, text="Date de début :")
        self.start_date_label.grid(row=0, column=0, padx=10, pady=5)
        self.start_date_calendar = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd')
        self.start_date_calendar.grid(row=0, column=1, padx=10, pady=5)

        self.end_date_label = ttk.Label(root, text="Date de fin :")
        self.end_date_label.grid(row=1, column=0, padx=10, pady=5)
        self.end_date_calendar = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd')
        self.end_date_calendar.grid(row=1, column=1, padx=10, pady=5)

        self.submit_button = ttk.Button(root, text="Confirmer", command=self.submit_dates_run)
        self.submit_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    def submit_dates_run(self):
        """
        Cette fonction est déclenchée lorsque l'utilisateur clique sur le bouton "Confirmer" pour soumettre les dates sélectionnées.
        C'est le bloc d'exécution du backtest.
        """
        start_date = self.start_date_calendar.get_date()
        end_date = self.end_date_calendar.get_date()

        # Création de l'instance du backtester
        backtester = Backtester(symbol, start_date, end_date)

        # Exécution de la stratégie
        positions = backtester.run_strategy(simple_strategy)

        # Calcul des rendements
        returns = backtester.calculate_returns(positions)

        # Calcul des statistiques de base
        mean_return, variance, beta_value = calculate_basic_statistics(returns)

        # Affichage des statistiques de base
        print("Rendement moyen:", mean_return)
        print("Variance:", variance)
        print("Bêta:", beta_value)

        # Génération du graphique de performance
        generate_performance_chart(returns)

        # Calcul des statistiques avancées
        downside_beta, max_drawdown = calculate_advanced_statistics(returns)

        # Affichage des statistiques avancées
        print("Bêta en baisse:", downside_beta)
        print("Drawdown maximal:", max_drawdown)


if __name__ == "__main__":
    root = tk.Tk()
    app = BacktestExecution(root)
    root.mainloop()


