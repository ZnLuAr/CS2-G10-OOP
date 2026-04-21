"""
业务逻辑层。

预期模块：
- market.py        市场撮合：挂单、购买、查询
- persistence.py   数据加载 / 保存（JSON 文件）
- seed.py          首次运行时生成初始数据集
"""
from ..models import Listing, ListingStatus, Transaction
from ..structures import PriceBST


class MarketService:
    """市场服务：挂单上架、撤销、查询、排序"""

    def __init__(self, player_service, item_service):
        # 别人的服务模块，你只调用它们的方法
        self.player_service = player_service
        self.item_service = item_service

        self.listings = {}  # listing_id -> Listing
        self.price_bst = PriceBST()  # 价格索引树
        self.next_id = 1

    def list_item(self, seller_id, item_id, price):
        """挂单上架"""
        # 校验卖家存在
        seller = self.player_service.get_player(seller_id)
        if not seller:
            raise ValueError(f"卖家 {seller_id} 不存在")

        # 校验卖家背包里有该物品
        if not self.player_service.has_item(seller_id, item_id):
            raise ValueError(f"卖家背包中没有物品 {item_id}")

        # 从背包移除物品
        item = self.player_service.remove_from_inventory(seller_id, item_id)

        # 创建挂单
        listing = Listing(self.next_id, seller_id, item, price)
        self.listings[self.next_id] = listing
        self.price_bst.insert(listing)
        self.next_id += 1
        return listing.listing_id

    def cancel_listing(self, seller_id, listing_id):
        """撤销挂单"""
        listing = self.listings.get(listing_id)
        if not listing or listing.status != ListingStatus.ACTIVE:
            raise ValueError(f"挂单 {listing_id} 不存在或已失效")
        if listing.seller_id != seller_id:
            raise PermissionError("只能撤销自己的挂单")

        # 物品退回背包
        self.player_service.add_to_inventory(seller_id, listing.item)

        # 更新状态
        listing.status = ListingStatus.CANCELLED
        self.price_bst.remove(listing_id, listing.price)

    def get_active_listings(self):
        """获取所有活跃挂单"""
        return [l for l in self.listings.values() if l.status == ListingStatus.ACTIVE]

    def query_by_price_range(self, min_price, max_price):
        """按价格区间查询"""
        return self.price_bst.range_query(min_price, max_price)

    def sort_by_price(self, ascending=True):
        """按价格排序"""
        listings = self.get_active_listings()
        return sorted(listings, key=lambda l: l.price, reverse=not ascending)

    def get_listing(self, listing_id):
        """根据ID获取挂单"""
        return self.listings.get(listing_id)


class TradeService:
    """交易服务：购买物品"""

    def __init__(self, market_service, player_service):
        self.market_service = market_service
        self.player_service = player_service
        self.transactions = []
        self.next_trans_id = 1

    def buy(self, buyer_id, listing_id):
        """购买物品"""
        # 获取挂单
        listing = self.market_service.get_listing(listing_id)
        if not listing or listing.status != ListingStatus.ACTIVE:
            raise ValueError(f"挂单 {listing_id} 不存在或已失效")

        # 自购拦截
        if listing.seller_id == buyer_id:
            raise ValueError("不能购买自己挂售的物品")

        # 校验买家金币
        buyer = self.player_service.get_player(buyer_id)
        if buyer.gold < listing.price:
            raise ValueError(f"金币不足，需要 {listing.price}，当前 {buyer.gold}")

        seller = self.player_service.get_player(listing.seller_id)

        # 事务开始（扣钱、加钱、转移物品）
        self.player_service.deduct_gold(buyer_id, listing.price)
        self.player_service.add_gold(listing.seller_id, listing.price)
        self.player_service.add_to_inventory(buyer_id, listing.item)

        # 更新挂单状态
        listing.status = ListingStatus.SOLD
        self.market_service.price_bst.remove(listing_id, listing.price)

        # 记录交易
        transaction = Transaction(
            self.next_trans_id, buyer_id, listing.seller_id,
            listing.item, listing.price
        )
        self.transactions.append(transaction)
        self.next_trans_id += 1

        return transaction.trans_id
