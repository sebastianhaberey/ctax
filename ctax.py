import argparse
import logging

from src.Application import init_logging, init_db, save_orders, load_orders, find_exchange_rates, \
    delete_transaction_data, delete_exchange_rate_data, calculate_profit_loss, import_files
from src.Configuration import Configuration


def get_command_line_arguments():
    parser = argparse.ArgumentParser(description='Crypto currency tax calculator.')
    subparsers = parser.add_subparsers(dest='mode')

    subparsers.add_parser('import-trades', help='import trades')
    subparsers.add_parser('import-exchange-rates', help='import exchange rates for all transactions')
    parser_calculate_profit = subparsers.add_parser('calculate-profit', help='calculate profit / loss')

    parser_calculate_profit.add_argument('-o', '--output-file', help='output file')

    return parser.parse_args()


if __name__ == "__main__":

    arguments = get_command_line_arguments()
    mode = arguments.mode

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
        orders = load_orders(session)
        delete_exchange_rate_data(session)
        find_exchange_rates(session, orders, configuration)

    elif mode == 'calculate-profit':

        logging.info('calculating profit / loss')
        orders = load_orders(session)
        calculate_profit_loss(orders, configuration, arguments.output_file)

    logging.info('done')
