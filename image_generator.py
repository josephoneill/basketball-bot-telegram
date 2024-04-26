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
proximaNovaFont = ImageFont.truetype("assets/fonts/proximanova-regular.ttf", font_size)

def generate_score_img(team_scores):
    print(team_scores)
    img = Image.new(mode='RGBA', size=(score_img_width, score_img_height), color=(0, 0, 0, 0))
    team_a_img = generate_team_image(img, team_scores["team_a_name"], f"({team_scores['team_a_record']})")
    team_b_img = generate_team_image(img, team_scores["team_b_name"], f"({team_scores['team_b_record']})", True)
    score_and_status_img = generate_score_and_status_img(
        img,
        team_scores["team_a_score"],
        team_scores["team_b_score"],
        team_scores["game_status"]
    )
    img.paste(team_a_img, box=(horizontal_padding, get_img_half_coord(score_img_height, team_a_img.size[1])))
    img.paste(
        score_and_status_img,
        box=(
            get_img_half_coord(score_img_width, score_and_status_img.size[0]),
            get_img_half_coord(score_img_height, score_and_status_img.size[1])
        )
    )
    img.paste(team_b_img, box=(img.size[0] - team_b_img.size[0] - horizontal_padding, get_img_half_coord(score_img_height, team_b_img.size[1])))
    return img_to_byte_array(img)


def add_text_to_image(img, text, coord):
    draw = ImageDraw.Draw(img)
    draw.text(coord, text, (0, 0, 0), font=proximaNovaFont)
    return img


# Determines the upper left coordinate needed for an image to be centered vertically
def get_img_half_coord(baseImgDim, refImgDim):
    return int(baseImgDim / 2 - refImgDim / 2)


def generate_team_image(refImg, team_name, team_record, align_text_end = False):
    y = vertical_padding
    team_logo = load_team_logo(team_name, int(score_img_height / 2))
    height = team_logo.size[1] + vertical_padding + (int(text_padding * 1)) + (font_size * 2)

    team_text_width = get_text_width(refImg, team_name)
    record_text_width = get_text_width(refImg, team_record)
    img_width = max(team_text_width, record_text_width, team_logo.size[0])
    img = Image.new(mode='RGBA', size=(img_width, height), color=(0, 0, 0, 0))
    img.paste(team_logo, box=(0, y))

    team_text_x = img_width - team_text_width - int(text_padding / 2) if align_text_end else 0
    record_text_x = img_width - record_text_width - int(text_padding / 2) if align_text_end else 0

    y += team_logo.size[1]
    add_text_to_image(img, team_name, (team_text_x, y))
    y += text_padding
    add_text_to_image(img, team_record, (record_text_x, y))
    return img


def generate_score_and_status_img(refImg, team_a_score, team_b_score, game_status):
    score_text = "";
    img_height = font_size
    texts_widths = list()
    texts_widths.append(get_text_width(refImg, game_status))
    game_has_started = team_a_score is not None and team_b_score is not None

    if game_has_started:
        score_text = f"{team_a_score}-{team_b_score}"
        img_height += text_padding + font_size

    texts_widths.append(get_text_width(refImg, score_text))
    img_width = int(max(texts_widths))

    img = Image.new(mode='RGBA', size=(img_width, img_height), color=(0, 0, 0, 0))
    add_text_to_image(img, game_status, (0,0))
    if game_has_started:
        add_text_to_image(img, score_text, (0, font_size + text_padding))

    return img


def get_text_width(img, text, font = proximaNovaFont):
    draw = ImageDraw.Draw(img)
    return draw.textlength(text, font)

def load_team_logo(team_name, height=200):
    team_logo = Image.open(f'assets/img/{team_name}.png').convert('RGBA')
    team_logo = resize_height(team_logo, height)
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
