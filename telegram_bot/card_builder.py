"""
High-Resolution Dynamic Card & Banner Generator for Telegram Username Bot
Generates Status Cards (FREE, TAKEN, FRAGMENT) and Profile Banners using Pillow.
"""
import io
import os
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont


def get_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidate_paths = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_rounded_rect(draw: ImageDraw.ImageDraw, coords: tuple, radius: int, fill: tuple, outline: Optional[tuple] = None, width: int = 1):
    draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)


def create_username_card(username: str, valuation: Dict[str, Any], status_type: str = "FREE") -> io.BytesIO:
    """
    Generates a card customized for FREE, TAKEN, or FRAGMENT status.
    Resolution: 1000x560 px
    """
    W, H = 1000, 560
    img = Image.new("RGBA", (W, H), color=(12, 13, 22, 255))
    draw = ImageDraw.Draw(img)

    # 1. Background gradient
    for y in range(H):
        ratio = y / H
        r = int(14 + ratio * 12)
        g = int(15 + ratio * 10)
        b = int(28 + ratio * 24)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Color themes by status
    if status_type == "TAKEN":
        accent_color = (255, 75, 95)
        glow_primary = (255, 45, 75, 30)
        badge_text = "STATUS: TAKEN  •  ЗАНЯТ"
        badge_fill = (55, 20, 28, 255)
        badge_dot = (255, 60, 80, 255)
    elif status_type == "FRAGMENT":
        accent_color = (255, 195, 50)
        glow_primary = (255, 175, 40, 30)
        badge_text = "STATUS: FRAGMENT NFT SALE"
        badge_fill = (50, 40, 15, 255)
        badge_dot = (255, 195, 50, 255)
    else:  # FREE
        accent_color = (60, 240, 140)
        glow_primary = (40, 220, 130, 30)
        badge_text = "STATUS: AVAILABLE  •  СВОБОДЕН"
        badge_fill = (20, 48, 35, 255)
        badge_dot = (60, 240, 140, 255)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([(-80, -80), (380, 380)], fill=glow_primary)
    glow_draw.ellipse([(650, 180), (1080, 620)], fill=(120, 90, 255, 25))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    card_margin = 28
    draw_rounded_rect(
        draw, 
        (card_margin, card_margin, W - card_margin, H - card_margin), 
        radius=26, 
        fill=(20, 22, 38, 215), 
        outline=(accent_color[0], accent_color[1], accent_color[2], 120), 
        width=2
    )

    # Top Status Badge
    f_badge = get_font(18, bold=True)
    draw_rounded_rect(draw, (55, 52, 410, 94), radius=12, fill=badge_fill, outline=(accent_color[0], accent_color[1], accent_color[2], 100), width=1)
    draw.ellipse([(72, 67), (84, 79)], fill=badge_dot)
    draw.text((95, 63), badge_text, font=f_badge, fill=(240, 245, 255, 255))

    f_top_right = get_font(18, bold=True)
    draw.text((W - 300, 63), "⚡ TELEGRAM RADAR", font=f_top_right, fill=(150, 160, 210, 255))

    # Center Spotlight Username
    center_y = 185
    draw_rounded_rect(draw, (55, 125, W - 55, 275), radius=20, fill=(16, 18, 32, 230), outline=(accent_color[0], accent_color[1], accent_color[2], 120), width=2)
    
    f_user = get_font(68, bold=True)
    display_user = f"@{username.lower().lstrip('@')}"
    bbox = draw.textbbox((0, 0), display_user, font=f_user)
    text_w = bbox[2] - bbox[0]
    draw.text(((W - text_w) // 2, center_y - 25), display_user, font=f_user, fill=(255, 255, 255, 255))

    # Bottom Metrics Boxes
    box_y1 = 310
    box_y2 = 475
    box_w = 205
    box_gap = 22
    start_x = 55

    metrics = [
        ("ДЛИНА", f"{valuation.get('length', len(display_user)-1)} СИМВОЛОВ", (140, 180, 255)),
        ("ОЦЕНКА СТОИМОСТИ", f"~{valuation.get('ton', 25)} TON", (60, 240, 160)),
        ("ЭКВИВАЛЕНТ", f"${valuation.get('usd', 150)} / ~{valuation.get('rub', 14000):,} ₽".replace(",", " "), (255, 205, 80)),
        ("РЕДКОСТЬ", f"{valuation.get('tier', 'Редкий').split()[0]} {valuation.get('stars', '★★★★☆')[:3]}", (245, 120, 240))
    ]

    for i, (title, val, color) in enumerate(metrics):
        bx1 = start_x + i * (box_w + box_gap)
        bx2 = bx1 + box_w
        draw_rounded_rect(draw, (bx1, box_y1, bx2, box_y2), radius=16, fill=(24, 27, 48, 220), outline=(65, 75, 120, 90), width=1)
        
        f_lbl = get_font(14, bold=True)
        draw.text((bx1 + 18, box_y1 + 22), title, font=f_lbl, fill=(140, 150, 180, 255))
        
        f_val = get_font(21, bold=True)
        draw.text((bx1 + 18, box_y1 + 65), val, font=f_val, fill=color)

    f_bot = get_font(14, bold=False)
    draw.text((58, 500), "Telegram & Fragment Web Analytics • Official Radar Checker", font=f_bot, fill=(100, 110, 140, 255))

    output = io.BytesIO()
    img.save(output, format="PNG", quality=95)
    output.seek(0)
    return output


def create_profile_card(user_data: Dict[str, Any]) -> io.BytesIO:
    W, H = 1000, 520
    img = Image.new("RGBA", (W, H), color=(10, 12, 20, 255))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        ratio = y / H
        r = int(12 + ratio * 14)
        g = int(14 + ratio * 8)
        b = int(24 + ratio * 28)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    is_premium = user_data.get("is_premium", 0)
    primary_glow = (255, 180, 50, 35) if is_premium else (80, 140, 255, 30)
    glow_draw.ellipse([(-60, -60), (380, 380)], fill=primary_glow)
    glow_draw.ellipse([(650, 150), (1050, 550)], fill=(160, 80, 255, 25))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    draw_rounded_rect(
        draw, 
        (26, 26, W - 26, H - 26), 
        radius=26, 
        fill=(18, 21, 36, 215), 
        outline=(75, 85, 135, 100), 
        width=2
    )

    avatar_x, avatar_y, avatar_r = 110, 150, 65
    avatar_border = (255, 200, 60, 255) if is_premium else (110, 140, 255, 255)
    avatar_bg = (40, 34, 15, 255) if is_premium else (24, 30, 58, 255)
    
    draw.ellipse(
        [(avatar_x - avatar_r, avatar_y - avatar_r), (avatar_x + avatar_r, avatar_y + avatar_r)], 
        fill=avatar_bg, 
        outline=avatar_border, 
        width=3
    )

    name = user_data.get("full_name") or "Пользователь"
    initial = (name[0] if name else "U").upper()
    f_avatar = get_font(56, bold=True)
    draw.text((avatar_x - 22, avatar_y - 34), initial, font=f_avatar, fill=avatar_border)

    f_name = get_font(34, bold=True)
    draw.text((205, 100), name[:20], font=f_name, fill=(255, 255, 255, 255))

    f_id = get_font(18, bold=False)
    tg_user = f"@{user_data['username']}" if user_data.get("username") else f"ID: {user_data.get('user_id')}"
    draw.text((205, 148), f"{tg_user}  •  ID: {user_data.get('user_id')}", font=f_id, fill=(140, 150, 185, 255))

    f_status = get_font(17, bold=True)
    if is_premium:
        draw_rounded_rect(draw, (205, 185, 520, 225), radius=10, fill=(60, 48, 15, 255), outline=(255, 195, 50, 200), width=1)
        draw.text((222, 194), "⭐️ PREMIUM PASS (БЕЗЛИМИТ)", font=f_status, fill=(255, 215, 75, 255))
    else:
        draw_rounded_rect(draw, (205, 185, 480, 225), radius=10, fill=(25, 38, 60, 255), outline=(80, 150, 255, 180), width=1)
        draw.text((222, 194), "⚡ БАЗОВЫЙ ТАРИФ (FREE)", font=f_status, fill=(130, 195, 255, 255))

    stat_y1 = 280
    stat_y2 = 445
    stat_w = 280
    stat_gap = 25
    start_x = 55

    q_left = "БЕЗЛИМИТ ∞" if is_premium else f"{user_data.get('queries_left', 0)} из 2"
    q_color = (255, 215, 75) if is_premium else (80, 240, 160)

    stats = [
        ("ОСТАТОК ЗАПРОСОВ", q_left, q_color),
        ("ВСЕГО ПОИСКОВ", str(user_data.get("total_searches", 0)), (130, 200, 255)),
        ("РЕГИСТРАЦИЯ", str(user_data.get("registered_at", "Сегодня")).split()[0], (220, 160, 255))
    ]

    for i, (title, val, color) in enumerate(stats):
        bx1 = start_x + i * (stat_w + stat_gap)
        bx2 = bx1 + stat_w
        draw_rounded_rect(draw, (bx1, stat_y1, bx2, stat_y2), radius=16, fill=(22, 26, 46, 220), outline=(65, 75, 120, 90), width=1)
        
        f_lbl = get_font(14, bold=True)
        draw.text((bx1 + 20, stat_y1 + 22), title, font=f_lbl, fill=(140, 150, 180, 255))
        
        f_val = get_font(26, bold=True)
        draw.text((bx1 + 20, stat_y1 + 65), val, font=f_val, fill=color)

    f_footer = get_font(14, bold=False)
    draw.text((58, 468), "Telegram Username Radar • Official Dashboard", font=f_footer, fill=(100, 110, 140, 255))

    output = io.BytesIO()
    img.save(output, format="PNG", quality=95)
    output.seek(0)
    return output
