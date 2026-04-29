from src.models.backpack import Backpack
from src.models.item import Item

if __name__ == "__main__":
    # 初始化背包
    bp = Backpack()

    # 测试物品
    item1 = Item("i001", "Excalibur", "legendary", "weapon.sword")
    item2 = Item("i002", "Health Potion", "common", "consumable.potion", stack_size_max=16)
    item3 = Item("i003", "Iron Shield", "epic", "armor.shield")
    item4 = Item("i002", "Health Potion", "common", "consumable.potion", stack_size_max=16)

    # 添加
    bp.add_item(item1)
    bp.add_item(item2)
    bp.add_item(item3)
    bp.add_item(item4)

    # 展示
    bp.show()

    # 正序展示（不改变原顺序）
    print("\n-- 按稀有度正序展示 --")
    sorted_list = bp.sort_by_rarity(reverse=False)
    for slot in sorted_list:
        print(f"{slot.item.name} | {slot.item.rarity} | x{slot.count}")

    # 逆序展示（不改变原顺序）
    print("\n-- 按稀有度逆序展示 --")
    sorted_list = bp.sort_by_rarity(reverse=True)
    for slot in sorted_list:
        print(f"{slot.item.name} | {slot.item.rarity} | x{slot.count}")

    # 验证原顺序不变
    print("\n-- 原始背包顺序 --")
    bp.show()

    # 删除（堆叠物品减数量）
    print("\n-- 移除 1 瓶 Health Potion --")
    bp.remove_item("i002", count=1)
    bp.show()

    # 删除（不可堆叠物品直接移除整格）
    print("\n-- 移除 Excalibur --")
    bp.remove_item("i001")
    bp.show()

    # 异常测试：背包满
    print("\n-- 容量满测试 --")
    small_bp = Backpack()
    small_bp.MAX_CAPACITY = 2
    small_bp.add_item(item1)
    small_bp.add_item(item3)
    try:
        small_bp.add_item(item2)
    except Exception as e:
        print(f"正确拦截: {e}")

    print("\n=== 所有测试完成 ===")