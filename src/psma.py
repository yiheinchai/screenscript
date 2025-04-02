from macro import play_macro
from pathlib import Path

BASE_PATH = "/Users/yiheinchai/Documents/Learn/screenscript/src/"


def has_psma_pet():
    play_macro(
        "/Users/yiheinchai/Documents/personal/uro audit macros/has_psma_pet.pmr",
        speed=2,
        repeat_times=0,
    )
