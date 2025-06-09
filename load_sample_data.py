import random
import string
from datetime import date, timedelta
from decimal import Decimal

from products.models import Category, Price, Product

Category.objects.all().delete()
Product.objects.all().delete()
Price.objects.all().delete()

category_names = ["Electronics", "Books", "Clothing", "Home", "Toys"]

categories = [Category.objects.create(name=name) for name in category_names]


def generate_sku(prefix="PRD", length=6):
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


today = date.today()
for i in range(1, 21):
    category = random.choice(categories)
    name = f"Product {i}"
    sku = generate_sku()
    description = f"This is a description for {name}."
    product = Product.objects.create(name=name, category=category, sku=sku, description=description)

    for j in range(3):
        start = today + timedelta(days=30 * j)
        if j < 2:
            end = start + timedelta(days=29)
        else:
            end = None
        price_value = Decimal(random.uniform(10.0, 500.0)).quantize(Decimal("0.01"))
        Price.objects.create(product=product, price=price_value, start_date=start, end_date=end)
