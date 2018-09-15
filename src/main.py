import logging

from src.Application import init_logging, init_db, save_orders, load_orders, find_exchange_rates, \
    delete_transaction_data, delete_exchange_rate_data, calculate_profit_loss, import_files
from src.Configuration import Configuration

configuration = Configuration.from_file('settings.yaml')
init_logging(configuration)
session = init_db(configuration)

start_step = configuration.get_mandatory('start-step')

if start_step <= 1:

    # logging.info('step 1: querying exchanges')
    # delete_transaction_data(session)
    # orders = query_transactions(configuration)
    # save_orders(session, orders)

    logging.info('step 1: importing files')
    delete_transaction_data(session)
    orders = import_files(configuration)
    save_orders(session, orders)

orders = load_orders(session, configuration)

if start_step <= 2:
    logging.info('step 2: finding exchange rates')
    delete_exchange_rate_data(session)
    find_exchange_rates(session, orders, configuration)

if start_step <= 3:
    logging.info('step 3: calculating profit / loss')
    calculate_profit_loss(orders, configuration)

logging.info('done')
