from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import io

score_img_width = 1200
score_img_height = 600
font_size = 48
vertical_padding = 32
horizontal_padding = 64
text_padding = 48
logo_img_width = 200
proximaNovaFont = ImageFont.truetype("assets/fonts/proximanova-regular.ttf", font_size)

def generate_score_img(team_scores):
    print(team_scores)
    img = Image.new(mode='RGBA', size=(score_img_width, score_img_height), color=(0, 0, 0, 0))
    team_a_img = generate_team_image(img, team_scores["team_a_name"], f"({team_scores['team_a_record']})")
    team_b_img = generate_team_image(img, team_scores["team_b_name"], f"({team_scores['team_b_record']})", True)
    team_score_img = generate_team_score_img(
        img,
        team_scores["team_a_score"],
        team_scores["team_b_score"],
    )
    img.paste(team_a_img, box=(horizontal_padding, get_img_half_coord(score_img_height, team_a_img.size[1])))
    img.paste(
        team_score_img,
        box=(
            get_img_half_coord(score_img_width, team_score_img.size[0]),
            get_img_half_coord(score_img_height, int(team_score_img.size[1])) - font_size + int(text_padding / 2)
        )
    )
    img.paste(team_b_img, box=(img.size[0] - team_b_img.size[0] - horizontal_padding, get_img_half_coord(score_img_height, team_b_img.size[1])))

    game_stats_img = generate_game_status(img, team_scores["game_status"].strip(), team_scores["live_pc_time"].strip())
    img.paste(
        game_stats_img,
        box=(
            get_img_half_coord(score_img_width, game_stats_img.size[0]),
            int((score_img_height * 0.75) - (game_stats_img.size[1] / 2))
        )
    )
    return img_to_byte_array(img)


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
    img = Image.new(mode='RGBA', size=(img_width, height), color=(0, 0, 0, 0))
    img_x = img_width - team_logo.size[0] if align_text_end else 0
    img.paste(team_logo, box=(img_x, y))

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
    img = Image.new(mode='RGBA', size=(img_width, font_size * 2), color=(0, 0, 0, 0))
    add_text_to_image(img, live_pc_time, (get_img_half_coord(img_width, live_pc_time_width),0))
    add_text_to_image(img, game_status, (0, font_size))
    return img


def generate_team_score_img(refImg, team_a_score, team_b_score):
    score_font = ImageFont.truetype("assets/fonts/proximanova-regular.ttf", 96)
    score_padding = 32
    img_height = font_size
    team_a_score_width = 0
    team_b_score_width = 0
    game_has_started = team_a_score is not None and team_b_score is not None

    if not game_has_started:
        return Image.new(mode='RGBA', size=(0,0), color=(0,0,0,0))


    team_a_score_width = get_text_width(refImg, str(team_a_score), score_font)
    team_b_score_width = get_text_width(refImg, str(team_b_score), score_font)
    img_height += text_padding + font_size


    img_width = int(score_img_width - (horizontal_padding + logo_img_width) * 2) - score_padding

    img = Image.new(mode='RGBA', size=(img_width, img_height), color=(0, 0, 0, 0))
    add_text_to_image(img, str(team_a_score), (score_padding, 0), score_font)
    add_text_to_image(img, str(team_b_score), (int(img_width - team_b_score_width - score_padding), 0), score_font)

    return img


def get_text_width(img, text, font=proximaNovaFont):
    draw = ImageDraw.Draw(img)
    return draw.textlength(text, font)

def load_team_logo(team_name, width=200):
    team_logo = Image.open(f'assets/img/{team_name}.png').convert('RGBA')
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
