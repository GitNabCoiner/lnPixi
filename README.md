# lnPixi
Get idea of how to initally price lightning channels

Ugly, unefficient code, which builds a heap of html files, that may be served to a browser.

Those sites shall show all channels of a lightning network node.
With each channel comes a bunch of numbers, which represent:
  med : the median of fees, all other direct connected nodes charge towards that particular node
  avg : the average of all fees, others charge towards this node
  cavg : like avg, but the 20% highest fees are left out of calculation
  current fee : currently set fee towards this node
  new fee : the number, that will be used in the copy menu (initalized with average of previous numbers)

copy menu (buggy):
  Copys varios data to clipboard.
  ln-cli : lncli-comand to adjust this channels fee to value from 'new fee'
  c-lightning : same as 'ln-cli' but for c-lighting (dysfuct)
  fee: value from 'new fee'
  chan-id: that channels id
  chan-point: that channels blockchain contact point
  node-pubkey: yes! exactly, what it suggests to be.
  
  
  usage:
  - get a describegraph.json from lnd (currently only tested with lncli's output)
  - run python3 get_remote_inc_fee.py placeholder ./path/to/lnds/describegraph.json
  - enjoy some nice tea until it is finished
  - scp -r ./out/* user@awsome.webserv.er:/path/to/srv/www/lnpixi
