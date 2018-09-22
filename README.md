# THIS PROJECT IS NOT READY YET

...so don't bother downloading it.

# ctax

A crypto currency tax calculator. 

[![Build Status](https://travis-ci.org/sebastianhaberey/ctax.svg?branch=master)](https://travis-ci.org/sebastianhaberey/ctax)
[![Coverage Status](https://coveralls.io/repos/github/sebastianhaberey/ctax/badge.svg?branch=master)](https://coveralls.io/github/sebastianhaberey/ctax?branch=master)

## Introduction

ctax aims to determine profits and losses made by trading crypto currencies.
It will import trades from input files and / or exchange APIs and use currency exchange rates 
from various sources to calculate profits and losses in the respective tax year. 
The result is CSV data that can be handed in with the tax declaration. 

## Disclaimer

It is entirely possible that there are bugs or incorrect assumptions
in the code so **YOU SHOULD ALWAYS VERIFY THE RESULTS VERY CAREFULLY.** 
There are no guarantees of any kind here. Seriously. Verify the results.

## Quick Start

TODO

## Configuration

TODO

## Support

There is no support. You are welcome to ask questions / report issues / fix errors / add features / 
file pull requests, but do not expect fast responses.

## Algorithm

This section describes the rationale behind ctax' profit / loss algorithm. Input and corrections are welcome.

### Introduction

The algorithm that calculates profit and loss is a rather simple FIFO / LIFO algorithm, as
this seems to be the mode stipulated by tax laws in the majority of countries. The handling of fees
can be a bit more complex than it seems on first glance, which is why it's described in the following chapter.

### Glossary

- **tax currency:** the currency the tax will have to be paid in
- **base currency:** the source currency in a conversion
- **quote currency:** the target currency in a conversion
- **cost of purchase:** money paid when buying an asset (in tax currency)
- **proceeds:** money received when selling an asset (in tax currency)
- **profit / loss (P/L):** proceeds minus cost of purchase (in tax currency)

### Fees

ctax assumes that fees are tax deductible (TODO introduce non-deductible mode).

#### How exchanges charge fees

Exchanges charge fees in varying ways. The main difference is the 
currency in which the fee is deducted. Here are some examples.

##### Example trade:

- **initial account balance:** 1100 EUR / 0.1 BTC
- **trade:** buy 1 BTC @ 1000 EUR
- **fee:** 10% (for simplicity)

##### Case 1: fee deducted from base currency

```
EUR    BTC
1100   0.1 -> deduct fee 100 EUR
1000   0.1 -> convert 1000 EUR to 1 BTC
   0   1.1

cost of purchase: 1100 EUR for 1.0 BTC (1100 EUR/BTC)
```

##### Case 2: fee deducted from quote currency

```
EUR    BTC
1100   0.1 -> deduct fee 0.1 BTC
1100   0.0 -> convert 1000 EUR to 1 BTC
 100   1.0

cost of purchase: 1000 EUR for 0.9 BTC (1111.11 EUR/BTC)
```

Note that the fee deduction mode directly influences the cost of purchase.
This took me a while to get my head around. Why should the currency matter,
as long as the value is equivalent? I came to the conclusion that in case #2,
a lesser amount of quote currency was effectively received, 
meaning less of the service purchased (but for the same fee), 
meaning higher cost of purchase. 

#### Special cases

Bitfinex has a special case called "settlement" where Bitfinex wants to deduct the fees 
and the actual amount from base currency, but there's not enough balance to cover both.

Bitfinex then deducts the fee from base currency and converts the entire amount in question 
from base currency to quote currency. After this, there is a negative balance on the base 
currency account. Bitfinex now converts some of the quote currency back to base currrency 
to "settle" the negative balance.

##### Case 3: Bitfinex settlement

```
EUR    BTC
1030   0.00 -> deduct fee 100 EUR
 930   0.00 -> convert 1000 EUR to 1 BTC
 -70   1.00 -> convert 0.07 BTC back to 70 EUR
   0   0.93 

cost of purchase: 1030 EUR for 0.930 BTC (1107.52 EUR/BTC)
```

Similarly, Kraken sometimes deducts as much of the fee as possible from base currency, 
then deducts the remainder from quote currency.

##### Case 4: Kraken split fee

```
EUR    BTC
1030   0.00 -> deduct part of fee 30 EUR
1000   0.00 -> convert 1000 EUR to 1 BTC
   0   1.00 -> deduct remainder of fee 0.07 BTC
   0   0.93 

cost of purchase: 1030 EUR for 0.930 BTC (1107.52 EUR/BTC)
```

The problem with cases such as #3 and #4 is that exchanges may not list two separate fees here. 
Or rather, they might list them in one place (e.g. downloaded ledger CSV data) but not in the other 
(e.g. data received from API, downloaded trade CSV data). Since the cost of purchase directly
depends on the fee deduction mode, the resulting P/L will vary slightly, depending on the
input data.

##### Fees: Conclusion

As with any software, ctax' results are only as good as its input data. 
The data received from exchanges may be inconsistent regarding fees and may not always 
reflect the reality 100 percent. I observed several cases like #3 and #4 above, 
where the API data would say one thing, but the downloaded ledger CSV data would say another. 

My take on this is that the data supplied officially by the exchange should be good
enough for the tax declaration, this way or the other. I believe the best way is to hand 
in the raw data from the exchange together with ctax' results based on that raw data.

## Acknowledgements

Thank you to the people over at [ccxt](https://github.com/ccxt/ccxt) for doing a great job.