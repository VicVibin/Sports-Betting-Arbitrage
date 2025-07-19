import numpy as np


# Sports Betting Arb takes in decimal payouts

class Sports_betting_Arbitrage(object):

    def payoff_matrix(self, wager, bets, payouts, payout_type="american"):
        if payout_type == "american" or "American":
            payouts = american_to_decimal(payouts)
        if payout_type == "fractional" or "Fractional":
            payouts = fractional_to_decimal(payouts)
        if len(bets) != len(payouts):
            return None
        if not self.quick_arb(payouts):
            return None
        else:
            print(f"Arbitrage Detected")
        c = self.quick_arb(payouts) * payouts[-1]

        fraction = 1 / c
        payout = wager * payouts[-1] * fraction
        premium = round(payout - wager, 2)
        print(f"Max profit of ${premium} per ${wager} bet")
        print(f"Optimal allocation: {self.optimal_allocation(payouts, payout, bets)}")
        return True

    @staticmethod
    def quick_arb(payouts):
        c = 0
        for i in range(len(payouts)):
            c += 1 / payouts[i]
        if c > 1:
            print(f"No Arbitrage Detected")
            print(f"C value :{c}")
            return False
        else:
            return c

    @staticmethod
    def optimal_allocation(payouts, payout, bets):
        bet_dictionary = {}
        if len(bets) != len(payouts):
            return None
        for bet, fraction in zip(bets, payouts):
            print(f"{bet} : ${round(payout / fraction, 2)}")
            bet_dictionary[bet] = [round(payout / fraction, 2), fraction]
        return bet_dictionary


def american_to_decimal(odds: list[int]):
    decimal_odds = []
    for i in range(len(odds)):
        if odds[i] < 0:
            decimal = round(100 /abs(odds[i]) + 1, 5)
            decimal_odds.append(decimal)
        if odds[i] >= 0:
            decimal = round(odds[i] / 100 + 1, 5)
            decimal_odds.append(decimal)
    return decimal_odds


def fractional_to_decimal(odds: list[int]):
    decimal_odds = list(np.array(odds) + 1)
    return decimal_odds

bookmakers = ["Draft Kin", "FanDuel"]
bet = ["L.Castelnuovo", "Lutkin"]
payouts = [125, -125]

Sports_betting_Arbitrage().payoff_matrix(10, bet, payouts, payout_type="american")
