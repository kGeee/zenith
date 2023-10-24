from oms import OMS
import utils
import eth_account
from eth_account.signers.local import LocalAccount
import asyncio

config = utils.get_config()
account: LocalAccount = eth_account.Account.from_key(config["secret_key"])
# Change this address to a vault that you lead
vault = "0xa30b8edbc93b0a10f32fff1d425031f67741b5fe"

o = OMS(config, account, vault)
for i in range(5):
    orders = o.range(False, 4, "DYDX", (2.19,2.195), 50, 10)
    o.bulk(orders)

# o.create_grid("ETH", 1, (1673.5, 1675), (1672, 1670), 5, 10)
# o.oms.order("ETH", False, .01, 1670, {"limit": {"tif": "Gtc"}})
