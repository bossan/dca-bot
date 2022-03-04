import logging, time, sys

from decouple import config
from python_bitvavo_api.bitvavo import Bitvavo


COINS = ['BTC']


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def buy(client: Bitvavo, amount, coin):
    logger.info("Buying BTC")
    return client.placeOrder('%s-EUR' % coin, 'buy', 'market', {'amountQuote': str(amount)})


def send_to_ledger(client: Bitvavo, amount):
    address = config('LEDGER_ADDRESS', default='')
    logger.info("Sending ₿ %f to %s", amount, address)
    return client.withdrawAssets('BTC', amount, address, {})


def run(client: Bitvavo):
    logger.info("Started new run")

    total_balance_eur_in_order = 0.0
    total_balance_eur_available = 0.0
    total_balance_btc_available = 0.0
    total_balance_btc_in_order = 0.0

    # Check if we have EUR balance
    for balance in client.balance({'symbol': 'EUR'}):
        total_balance_eur_available += float(balance.get('available'))
        total_balance_eur_in_order += float(balance.get('inOrder'))

    logger.info("Available € %f", total_balance_eur_available)
    # If we have EUR balance, buy BTC
    if total_balance_eur_available > 1.0:
        order = buy(client, total_balance_eur_available, 'BTC')
        logger.debug("Order: %s", order)

    # Check if we have BTC balance
    for balance in client.balance({'symbol': 'BTC'}):
        total_balance_btc_available += float(balance.get('available'))
        total_balance_btc_in_order += float(balance.get('inOrder'))

    logger.info("Available ₿ %f" % total_balance_btc_available)
    # If we have BTC balance, send it to Ledger Wallet
    if total_balance_btc_available > 0:
        withdrawal = send_to_ledger(client, total_balance_btc_available)
        logger.debug("Withdrawal: %s", withdrawal)

    logger.info("Finished run")


def calculate_result(client: Bitvavo):
    total_crypto = {}

    total_paid = 0.0
    total_received = 0.0
    total_fees_paid = 0.0
    total_deposit = 0.0
    total_deposit_fee = 0.0
    total_value = 0.0

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

    logger.info("TOTAL PAID: € %f" % total_deposit)
    logger.info("TOTAL VALUE: € %f" % total_value)
    logger.info("RESULT: %f%%" % (((total_value - total_deposit) / total_deposit) * 100))


def main():
    while True:
        client = Bitvavo({
            'APIKEY': config('API_KEY', default=''),
            'APISECRET': config('API_SECRET', default=''),
            'RESTURL': 'https://api.bitvavo.com/v2',
            'WSURL': 'wss://ws.bitvavo.com/v2/',
            'ACCESSWINDOW': 10000,
            'DEBUGGING': False
        })

        run(client)
        time.sleep(60 * 60)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s')

    logger.info("""Starting
    ╔═══╗╔═══╗╔═══╗    ╔══╗ ╔═══╗╔════╗
    ╚╗╔╗║║╔═╗║║╔═╗║    ║╔╗║ ║╔═╗║║╔╗╔╗║
     ║║║║║║ ╚╝║║ ║║    ║╚╝╚╗║║ ║║╚╝║║╚╝
     ║║║║║║ ╔╗║╚═╝║    ║╔═╗║║║ ║║  ║║  
    ╔╝╚╝║║╚═╝║║╔═╗║    ║╚═╝║║╚═╝║ ╔╝╚╗ 
    ╚═══╝╚═══╝╚╝ ╚╝    ╚═══╝╚═══╝ ╚══╝ """)

    try:
        logger.info("Press CTRL + C to stop the process")
        main()
    except KeyboardInterrupt:
        sys.exit(1)
