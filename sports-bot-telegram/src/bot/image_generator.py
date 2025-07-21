import uuid

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import io
import os
from sports_bot_telegram_plugin.types.MatchScores import MatchScores

score_img_width = 1200
score_img_height = 600
font_size = 48
vertical_padding = 32
horizontal_padding = 64
text_padding = 48
logo_img_width = 200
proximaNovaFont = ImageFont.truetype("assets/fonts/proximanova-regular.ttf", font_size)

def generate_score_img(team_scores: MatchScores):
    img = Image.new(mode='RGBA', size=(score_img_width, score_img_height), color=(255, 255, 255, 255))
    home_team_img = generate_team_image(img, team_scores.home_team, f"({team_scores.home_team_record})")
    away_team_img = generate_team_image(img, team_scores.away_team, f"({team_scores.away_team_record})", True)
    team_score_img = generate_team_score_img(
        img,
        team_scores.home_score,
        team_scores.away_score,
    )
    img.paste(home_team_img, box=(horizontal_padding, get_img_half_coord(score_img_height, home_team_img.size[1])))
    img.paste(away_team_img, box=(img.size[0] - away_team_img.size[0] - horizontal_padding, get_img_half_coord(score_img_height, away_team_img.size[1])))
    img.paste(
        team_score_img,
        box=(
            get_img_half_coord(score_img_width, team_score_img.size[0]),
            get_img_half_coord(score_img_height, int(team_score_img.size[1])) - font_size + int(text_padding / 2)
        )
    )

    game_stats_img = generate_game_status(img, team_scores.game_status.strip(), team_scores.game_curr_time.strip())
    img.paste(
        game_stats_img,
        box=(
            get_img_half_coord(score_img_width, game_stats_img.size[0]),
            int((score_img_height * 0.75) - (game_stats_img.size[1] / 2))
        )
    )
    return save_img_as_webp(img)


def add_text_to_image(img, text, coord, font = proximaNovaFont):
    draw = ImageDraw.Draw(img)
    draw.text(coord, text, (0, 0, 0), font=font)
    return img


# Determines the upper left coordinate needed for an image to be centered vertically
def get_img_half_coord(baseImgDim, refImgDim):
    return int(baseImgDim / 2 - refImgDim / 2)


def generate_team_image(refImg, team_name, team_record, align_text_end = False):
    y = vertical_padding
    team_logo = load_team_logo(team_name, int(logo_img_width))
    height = team_logo.size[1] + vertical_padding + (int(text_padding * 1)) + (font_size * 2)

    team_text_width = get_text_width(refImg, team_name)
    record_text_width = get_text_width(refImg, team_record)
    img_width = int(max(team_text_width, record_text_width, team_logo.size[0])) + 32 # 32 for kernleing issue
    img = Image.new(mode='RGBA', size=(img_width, height), color=(255, 255, 255, 255))
    img_x = img_width - team_logo.size[0] if align_text_end else 0
    img.paste(team_logo, (img_x, y), team_logo)

    team_text_x = img_width - team_text_width - int(text_padding / 2) if align_text_end else 0
    record_text_x = img_width - record_text_width - int(text_padding / 2) if align_text_end else 0

    y += team_logo.size[1]
    add_text_to_image(img, team_name, (team_text_x, y))
    y += text_padding
    add_text_to_image(img, team_record, (record_text_x, y))
    return img


def generate_game_status(refImg, game_status, live_pc_time):
    game_status_width = get_text_width(refImg, game_status)
    live_pc_time_width = get_text_width(refImg, live_pc_time)
    img_width = int(max(game_status_width, live_pc_time_width))
    img = Image.new(mode='RGBA', size=(img_width, font_size * 2), color=(255, 255, 255, 255))
    add_text_to_image(img, live_pc_time, (get_img_half_coord(img_width, live_pc_time_width), 0))
    add_text_to_image(img, game_status, (0, font_size))
    return img


def generate_team_score_img(refImg, home_score, away_score):
    score_font = ImageFont.truetype("assets/fonts/proximanova-regular.ttf", 96)
    score_padding = 32
    img_height = font_size
    home_score_width = 0
    away_score_width = 0
    game_has_started = home_score is not None and away_score is not None

    if not game_has_started:
        return Image.new(mode='RGBA', size=(0,0), color=(0,0,0,0))

    home_score_width = get_text_width(refImg, str(home_score), score_font)
    away_score_width = get_text_width(refImg, str(away_score), score_font)
    img_height += text_padding + font_size

    img_width = int(score_img_width - (horizontal_padding + logo_img_width) * 2) - score_padding

    img = Image.new(mode='RGBA', size=(img_width, img_height), color=(255, 255, 255, 255))
    add_text_to_image(img, str(home_score), (score_padding, 0), score_font)
    add_text_to_image(img, str(away_score), (int(img_width - away_score_width - score_padding), 0), score_font)

    return img


def save_img_as_webp(img):
    img_name = f"{uuid.uuid4()}.webp"
    img.save(img_name, format='WebP')
    return img_name


def delete_img(img_path):
    os.remove(img_path)

def get_text_width(img, text, font=proximaNovaFont):
    draw = ImageDraw.Draw(img)
    return draw.textlength(text, font)

def load_team_logo(team_name, width=200):
    team_logo = Image.open(f'assets/img/{team_name.lower()}.png')
    team_logo = resize_width(team_logo, width)
    return team_logo


def img_to_byte_array(img: Image) -> bytes:
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def resize_width(img, width):
    (w, h) = img.size
    ratio = w/h
    return img.resize((width, int(width * ratio)))


def resize_height(img, height):
    (w, h) = img.size
    ratio = w/h
    return img.resize((int(height * ratio), height))
