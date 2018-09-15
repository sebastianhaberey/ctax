import argparse
import logging

from src.Application import init_logging, init_db, save_orders, load_orders, find_exchange_rates, \
    delete_transaction_data, delete_exchange_rate_data, calculate_profit_loss, import_files
from src.Configuration import Configuration


def get_mode_from_command_line():
    parser = argparse.ArgumentParser(description='Crypto currency tax calculator.')
    parser.add_argument('mode', help='operation mode',
                        choices=['import-trades', 'import-exchange-rates', 'calculate-profit'])
    args = parser.parse_args()
    return args.mode


if __name__ == "__main__":

    mode = get_mode_from_command_line()

    configuration = Configuration.from_file('settings.yml')
    init_logging(configuration)
    session = init_db(configuration)

    if mode == 'import-trades':

        logging.info('importing trades')
        delete_transaction_data(session)
        # orders = query_transactions(configuration)
        orders = import_files(configuration)
        save_orders(session, orders)

    elif mode == 'import-exchange-rates':

        logging.info('importing exchange rates')
        orders = load_orders(session, configuration)
        delete_exchange_rate_data(session)
        find_exchange_rates(session, orders, configuration)

    elif mode == 'calculate-profit':

        logging.info('calculating profit / loss')
        orders = load_orders(session, configuration)
        calculate_profit_loss(orders, configuration)

    logging.info('done')
