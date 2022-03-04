from decouple import config
from python_bitvavo_api.bitvavo import Bitvavo


COINS = ['BTC']


def buy(client: Bitvavo, amount, coin):
    return client.placeOrder('%s-EUR' % coin, 'buy', 'market', {'amountQuote': str(amount)})


def send_to_ledger(client: Bitvavo, amount):
    address = config('LEDGER_ADDRESS', default='')
    return client.withdrawAssets('BTC', amount, address, {})


def main():
    client = Bitvavo({
        'APIKEY': config('API_KEY', default=''),
        'APISECRET': config('API_SECRET', default=''),
        'RESTURL': 'https://api.bitvavo.com/v2',
        'WSURL': 'wss://ws.bitvavo.com/v2/',
        'ACCESSWINDOW': 10000,
        'DEBUGGING': False
    })

    total_crypto = {}

    total_paid = 0.0
    total_received = 0.0
    total_fees_paid = 0.0

    total_balance_eur_in_order = 0.0
    total_balance_eur_available = 0.0

    total_balance_btc_available = 0.0
    total_balance_btc_in_order = 0.0

    total_deposit = 0.0
    total_deposit_fee = 0.0

    total_value = 0.0

    print("""
╔═══╗╔═══╗╔═══╗    ╔══╗ ╔═══╗╔════╗
╚╗╔╗║║╔═╗║║╔═╗║    ║╔╗║ ║╔═╗║║╔╗╔╗║
 ║║║║║║ ╚╝║║ ║║    ║╚╝╚╗║║ ║║╚╝║║╚╝
 ║║║║║║ ╔╗║╚═╝║    ║╔═╗║║║ ║║  ║║  
╔╝╚╝║║╚═╝║║╔═╗║    ║╚═╝║║╚═╝║ ╔╝╚╗ 
╚═══╝╚═══╝╚╝ ╚╝    ╚═══╝╚═══╝ ╚══╝ """)
    print("-----------------------------------")

    # Check if we have EUR balance
    for balance in client.balance({'symbol': 'EUR'}):
        total_balance_eur_available += float(balance.get('available'))
        total_balance_eur_in_order += float(balance.get('inOrder'))

    print("Available € %f" % total_balance_eur_available)
    # If we have EUR balance, buy BTC
    if total_balance_eur_available > 1.0:
        print("Buying BTC")
        order = buy(client, total_balance_eur_available, 'BTC')
        print("Order: %s" % order)

    # Check if we have BTC balance
    for balance in client.balance({'symbol': 'BTC'}):
        total_balance_btc_available += float(balance.get('available'))
        total_balance_btc_in_order += float(balance.get('inOrder'))

    print("Available ₿ %f" % total_balance_btc_available)
    # If we have BTC balance, send it to Ledger Wallet
    if total_balance_btc_available > 0:
        print("Sending to ledger")
        withdrawal = send_to_ledger(client, total_balance_btc_available)
        print("Withdrawal: %s" % withdrawal)

    for deposit in client.depositHistory({'symbol': 'EUR'}):
        total_deposit += float(deposit.get('amount'))
        total_deposit_fee += float(deposit.get('fee'))

    for coin in COINS:
        total_crypto[coin] = 0.0

        for order in client.getOrders('%s-EUR' % coin, {}):
            total_paid += float(order.get('amountQuote'))
            total_received += float(order.get('filledAmountQuote'))
            total_fees_paid += float(order.get('feePaid'))

            total_crypto[coin] += float(order.get('filledAmount'))

        price = float(client.tickerPrice({'market': '%s-EUR' % coin}).get('price', '0'))

        total_value += price * total_crypto.get(coin, 0.0)

    print("-----------------------------------")
    print("TOTAL PAID: € %f" % total_deposit)
    print("TOTAL VALUE: € %f" % total_value)
    print("RESULT: %f%%" % (((total_value - total_deposit) / total_deposit) * 100))
    print("-----------------------------------")


if __name__ == '__main__':
    main()
