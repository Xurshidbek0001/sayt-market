SITES = [
    {
        "id": 1,
        "slug": "kiyim",
        "name": "Kiyim do'koni",
        "description": "Kiyim-kechak sotuvchilari uchun zamonaviy online do'kon.",
        "price": "300 000 so'mdan",
    },
    {
        "id": 2,
        "slug": "kosmetika",
        "name": "Kosmetika do'koni",
        "description": "Kosmetika va go'zallik mahsulotlari uchun online katalog.",
        "price": "300 000 so'mdan",
    },
    {
        "id": 3,
        "slug": "mebel",
        "name": "Mebel do'koni",
        "description": "Mebel sotuvchilari uchun mahsulot katalogi va buyurtma tizimi.",
        "price": "400 000 so'mdan",
    },
    {
        "id": 4,
        "slug": "elektronika",
        "name": "Telefon va elektronika",
        "description": "Telefon, aksessuar va elektronika mahsulotlari uchun sayt.",
        "price": "350 000 so'mdan",
    },
]


def get_sites_text():
    lines = ["🛒 <b>Mavjud saytlar:</b>\n"]

    for site in SITES:
        lines.append(
            f"🔹 <b>{site['name']}</b>\n"
            f"{site['description']}\n"
            f"💰 {site['price']}\n"
        )

    return "\n".join(lines)


def get_site_names():
    return [site["name"] for site in SITES]


def get_site_by_name(name):
    for site in SITES:
        if site["name"] == name:
            return site
    return None


def get_site_by_slug(slug):
    if not slug:
        return None

    for site in SITES:
        if site["slug"] == slug:
            return site

    return None
