"""Dance the moles back into their holes instead of whacking them."""

import argparse
import enum
import fractions
import importlib.resources
import os.path
import pathlib
import random
import sys
import time
from typing import Optional, Final, List, MutableMapping

import pygame
from icontract import require, invariant, ensure

import danceamole
import danceamole.events
from danceamole.common import assert_never

assert danceamole.__doc__ == __doc__

PACKAGE_DIR = (
    pathlib.Path(str(importlib.resources.files(__package__)))
    if __package__ is not None
    else pathlib.Path(os.path.realpath(__file__)).parent
)


class Paths:
    """Wire the paths to media files."""

    def __init__(self) -> None:
        self.all = []  # type: List[str]

        @require(lambda path: not os.path.isabs(path))
        def prepend_package_dir_and_register(path: str) -> str:
            """Register the path with :py:attr:`all_paths`."""
            absolute = os.path.join(PACKAGE_DIR, path)
            self.all.append(absolute)
            return absolute

        self.background = prepend_package_dir_and_register(
            "media/sprites/background.png"
        )
        self.lingering_images = [
            prepend_package_dir_and_register(f"media/sprites/lingering{i}.png")
            for i in range(1)
        ]
        self.dizzy_images = [
            prepend_package_dir_and_register(f"media/sprites/dizzy{i}.png")
            for i in range(6)
        ]
        self.going_down_images = [
            prepend_package_dir_and_register(f"media/sprites/going_down{i}.png")
            for i in range(6)
        ]
        self.going_up_images = [
            prepend_package_dir_and_register(f"media/sprites/going_up{i}.png")
            for i in range(6)
        ]
        self.up_images = [
            prepend_package_dir_and_register(f"media/sprites/up{i}.png")
            for i in range(2)
        ]

        self.vegetable_images = [
            prepend_package_dir_and_register(f"media/sprites/vegetable{i}.png")
            for i in range(12)
        ]

        self.hourglass_images = [
            prepend_package_dir_and_register(f"media/sprites/hourglass{i}.png")
            for i in range(5)
        ]

        self.hit_sound = prepend_package_dir_and_register("media/sfx/hit.ogg")

        self.font = prepend_package_dir_and_register("media/freesansbold.ttf")


def check_all_files_exist(paths: Paths) -> Optional[str]:
    """Check that all files exist, and return an error, if any."""
    for path in paths.all:
        if not os.path.exists(path):
            return f"The media file does not exist: {path}"

    return None


class MoleAction(enum.Enum):
    """Represent the mole action in the game."""

    LINGERING_BENEATH = 0
    GOING_UP = 1
    LOOKING_AROUND = 2
    GOING_DOWN = 3
    DIZZYING_DOWN = 4


@invariant(lambda self: self.start <= self.end)
class MoleState:
    """Represent the current state of a mole."""

    #: Current action
    action: MoleAction

    #: Timestamp when the state started, seconds since epoch
    start: float

    #: Expected time for the state to end, seconds since epoch
    end: float

    def __init__(self, action: MoleAction, start: float, end: float) -> None:
        """Initialize with the given values."""
        self.action = action
        self.start = start
        self.end = end


class State:
    """Capture the global state of the game."""

    #: Set if we received the signal to quit the game
    received_quit: bool

    #: Timestamp when the game started, seconds since epoch
    game_start: Final[float]

    #: Current clock in the game, seconds since epoch
    now: float

    #: Timestamp when the game is to end, seconds since epoch
    game_end: Final[float]

    mole_states: Final[List[MoleState]]

    #: Set when the time is up
    game_over: bool

    @require(lambda game_start, game_end: game_start <= game_end)
    @ensure(lambda self: len(self.mole_states) == 8)
    def __init__(self, game_start: float, game_end: float) -> None:
        """Initialize with the given values and the defaults."""
        self.received_quit = False
        self.score = 0
        self.misses = 0
        self.game_start = game_start
        self.now = game_start
        self.game_end = game_end

        self.mole_states = [
            MoleState(
                action=MoleAction.LINGERING_BENEATH,
                start=game_start,
                end=game_start + 2 + int(random.random() * 13),
            )
            for _ in range(8)
        ]

        self.game_over = False


BUTTON_TO_MOLE = {
    danceamole.events.Button.CROSS: 0,
    danceamole.events.Button.UP: 1,
    danceamole.events.Button.CIRCLE: 2,
    danceamole.events.Button.RIGHT: 3,
    danceamole.events.Button.SQUARE: 4,
    danceamole.events.Button.DOWN: 5,
    danceamole.events.Button.TRIANGLE: 6,
    danceamole.events.Button.LEFT: 7,
}
assert len(BUTTON_TO_MOLE) == 8, "One button for each mole"
assert sorted(BUTTON_TO_MOLE.values()) == list(
    range(8)
), "Exactly all 8 targets covered"

SOUND_CACHE = dict()  # type: MutableMapping[str, pygame.mixer.Sound]


def play_sound(path: str) -> float:
    """Start playing the sound and returns its length."""
    sound = SOUND_CACHE.get(path, None)
    if sound is None:
        sound = pygame.mixer.Sound(path)
        SOUND_CACHE[path] = sound

    sound.play()
    return sound.get_length()


GOING_DOWN_IN_SECONDS = 0.25
GOING_UP_IN_SECONDS = 0.25


def handle_in_game_over(
    state: State, our_event_queue: List[danceamole.events.EventUnion], paths: Paths
) -> None:
    """Consume the first action in the queue during the game over."""
    if len(our_event_queue) == 0:
        return

    event = our_event_queue.pop(0)

    if isinstance(event, danceamole.events.ReceivedQuit):
        state.received_quit = True
    else:
        pass


def handle_in_game(
    state: State, our_event_queue: List[danceamole.events.EventUnion], paths: Paths
) -> None:
    """Consume the first action in the queue during the game."""
    if len(our_event_queue) == 0:
        return

    now = time.time()
    event = our_event_queue.pop(0)

    if isinstance(event, danceamole.events.ReceivedQuit):
        state.received_quit = True

    elif isinstance(event, danceamole.events.GameOver):
        state.game_over = True

    elif isinstance(event, danceamole.events.ButtonDown):
        if state.game_over:
            return

        mole_index = BUTTON_TO_MOLE.get(event.button, None)
        if mole_index is not None:
            # The mole can be hit only if it is looking around.
            if state.mole_states[mole_index].action is MoleAction.LOOKING_AROUND:
                state.mole_states[mole_index].action = MoleAction.DIZZYING_DOWN
                state.mole_states[mole_index].start = state.now
                state.mole_states[mole_index].end = state.now + GOING_DOWN_IN_SECONDS

                state.score += 1

                play_sound(paths.hit_sound)

    elif isinstance(event, danceamole.events.Tick):
        if state.game_over:
            return

        # Handle the time
        state.now = now

        if now > state.game_end:
            our_event_queue.append(danceamole.events.GameOver())
        else:
            for mole_state in state.mole_states:
                if now > mole_state.end:
                    if mole_state.action is MoleAction.LINGERING_BENEATH:
                        mole_state.action = MoleAction.GOING_UP
                        mole_state.start = now
                        mole_state.end = now + GOING_UP_IN_SECONDS
                    elif mole_state.action is MoleAction.GOING_UP:
                        mole_state.action = MoleAction.LOOKING_AROUND
                        mole_state.start = now
                        mole_state.end = now + 3.5
                    elif mole_state.action is MoleAction.LOOKING_AROUND:
                        mole_state.action = MoleAction.GOING_DOWN
                        mole_state.start = now
                        mole_state.end = now + GOING_DOWN_IN_SECONDS

                        state.misses += 1
                    elif (
                        mole_state.action is MoleAction.GOING_DOWN
                        or mole_state.action is MoleAction.DIZZYING_DOWN
                    ):
                        mole_state.action = MoleAction.LINGERING_BENEATH
                        mole_state.start = now
                        mole_state.end = now + 2 + random.random() * 13

                    else:
                        assert_never(mole_state.action)

    else:
        assert_never(event)


def handle(
    state: State, our_event_queue: List[danceamole.events.EventUnion], paths: Paths
) -> None:
    """Consume the first action in the queue."""
    if state.game_over:
        handle_in_game_over(state, our_event_queue, paths)
    else:
        handle_in_game(state, our_event_queue, paths)


def render_quitting(
    state: State, surface: pygame.surface.Surface, paths: Paths
) -> None:
    """Render the "Quitting..." dialogue."""
    oneph = max(1, int(0.01 * surface.get_height()))
    onepw = max(1, int(0.01 * surface.get_height()))

    surface.fill((0, 0, 0))

    font_large = pygame.font.Font(paths.font, 5 * oneph)
    quitting = font_large.render("Quitting the game...", True, (255, 255, 255))

    quitting_xy = (10 * onepw, 10 * oneph)
    surface.blit(quitting, quitting_xy)


def render_game_over(
    state: State, surface: pygame.surface.Surface, paths: Paths
) -> None:
    """Render the "game over" dialogue."""
    oneph = max(1, int(0.01 * surface.get_height()))
    onepw = max(1, int(0.01 * surface.get_height()))

    surface.fill((0, 0, 0))

    font_large = pygame.font.Font(paths.font, 5 * oneph)
    game_over = font_large.render("Game Over", True, (255, 255, 255))
    game_over_xy = (10 * onepw, 10 * oneph)
    surface.blit(game_over, game_over_xy)

    score = font_large.render(f"Score: {state.score}", True, (255, 255, 255))
    score_xy = (game_over_xy[0], game_over_xy[1] + game_over.get_height() + oneph)
    surface.blit(score, score_xy)

    vegetable_score = max(len(paths.vegetable_images) - state.misses, 0)

    result = font_large.render(
        f"Vegetables saved: {vegetable_score}", True, (255, 255, 255)
    )
    result_xy = (score_xy[0], score_xy[1] + score.get_height() + 6 * oneph)
    surface.blit(result, result_xy)

    vegetable_origin_xy = (result_xy[0], result_xy[1] + result.get_height() + 2 * oneph)

    vegetable_size = onepw * 20
    vegetable_size_with_padding = onepw * 22

    for i, vegetable_image in enumerate(paths.vegetable_images):
        vegetable_xy = (
            vegetable_origin_xy[0] + vegetable_size_with_padding * (i % 4),
            vegetable_origin_xy[1] + vegetable_size_with_padding * int(i / 4),
        )

        vegetable = load_image_or_retrieve_from_cache(vegetable_image)
        vegetable = pygame.transform.scale(vegetable, (vegetable_size, vegetable_size))

        if i >= vegetable_score:
            vegetable.fill((255, 0, 0, 220), None, pygame.BLEND_RGBA_MULT)

        surface.blit(vegetable, vegetable_xy)

    font_small = pygame.font.Font(paths.font, 2 * oneph)
    escape = font_small.render('Press ESC or "q" to quit', True, (255, 255, 255))
    surface.blit(
        escape,
        (onepw, surface.get_height() - escape.get_height() - 2 * oneph),
    )


#: Mole positions relative to the background image
MOLES_XY_ON_SCENE = [
    (156, 189),
    (442, 137),
    (755, 177),
    (737, 379),
    (726, 526),
    (402, 498),
    (152, 490),
    (179, 333),
]


def render_game(state: State, surface: pygame.surface.Surface, paths: Paths) -> None:
    """Render the game on the screen."""
    # Draw everything on the background, then rescale the background.
    #
    # This is a much easier approach than scaling everything to percentages of
    # the screen size as we can simply use absolute pixel values for positioning.

    scene = load_image_or_retrieve_from_cache(paths.background).copy()

    font_large = pygame.font.Font(PACKAGE_DIR / "media/freesansbold.ttf", 32)
    score = font_large.render(f"Score: {state.score}", True, (0, 0, 255))
    score_xy = (5, 5)
    scene.blit(score, score_xy)

    for i, mole_xy in enumerate(MOLES_XY_ON_SCENE):
        mole_state = state.mole_states[i]

        total_time_in_state = mole_state.end - mole_state.start
        time_passed_in_state = state.now - mole_state.start

        # NOTE (mristin, 2022-12-23):
        # Beware that due to slow-downs on the system, we might be in the state too
        # long, past the mole_state.end. Hence, the fraction can be above 1.0, which
        # we need to take into account below.

        fraction_of_time = time_passed_in_state / total_time_in_state

        image_paths = None  # type: Optional[List[str]]
        if mole_state.action is MoleAction.LINGERING_BENEATH:
            image_paths = paths.lingering_images

        elif mole_state.action is MoleAction.GOING_UP:
            image_paths = paths.going_up_images

        elif mole_state.action is MoleAction.LOOKING_AROUND:
            image_paths = paths.up_images

        elif mole_state.action is MoleAction.GOING_DOWN:
            image_paths = paths.going_down_images

        elif mole_state.action is MoleAction.DIZZYING_DOWN:
            image_paths = paths.dizzy_images
        else:
            assert_never(mole_state.action)

        step = min(int(fraction_of_time * len(image_paths)), len(image_paths) - 1)

        mole = load_image_or_retrieve_from_cache(image_paths[step])

        scene.blit(mole, mole_xy)

    game_time_fraction = (state.now - state.game_start) / (
        state.game_end - state.game_start
    )

    hourglass_step = min(
        int(game_time_fraction * len(paths.hourglass_images)),
        len(paths.hourglass_images) - 1,
    )

    hourglass_path = paths.hourglass_images[hourglass_step]

    hourglass = load_image_or_retrieve_from_cache(hourglass_path)
    scene.blit(
        hourglass,
        (
            scene.get_width() - hourglass.get_width() - 3,
            3,
        ),
    )

    font_small = pygame.font.Font(paths.font, 16)
    escape = font_small.render('Press ESC or "q" to quit', True, (0, 0, 255))
    scene.blit(escape, (4, scene.get_height() - escape.get_height() - 2))

    # Now draw the scene on the screen.

    surface.fill((0, 0, 0))

    surface_aspect_ratio = fractions.Fraction(surface.get_width(), surface.get_height())

    scene_aspect_ratio = fractions.Fraction(scene.get_width(), scene.get_height())

    if scene_aspect_ratio < surface_aspect_ratio:
        new_scene_height = surface.get_height()
        new_scene_width = scene.get_width() * (new_scene_height / scene.get_height())

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        margin = int((surface.get_width() - scene.get_width()) / 2)

        surface.blit(scene, (margin, 0))

    elif scene_aspect_ratio == surface_aspect_ratio:
        new_scene_width = surface.get_width()
        new_scene_height = scene.get_height()

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        surface.blit(scene, (0, 0))
    else:
        new_scene_width = surface.get_width()
        new_scene_height = int(
            scene.get_height() * (new_scene_width / scene.get_width())
        )

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        margin = int((surface.get_height() - scene.get_height()) / 2)

        surface.blit(scene, (0, margin))


IMAGE_CACHE = dict()  # type: MutableMapping[str, pygame.surface.Surface]


def load_image_or_retrieve_from_cache(path: str) -> pygame.surface.Surface:
    """Load the image or retrieve it from the memory cache."""
    image = IMAGE_CACHE.get(path, None)
    if image is not None:
        return image

    image = pygame.image.load(path).convert_alpha()
    IMAGE_CACHE[path] = image
    return image


def render(state: State, surface: pygame.surface.Surface, paths: Paths) -> None:
    """Render the state on the screen."""
    if state.received_quit:
        render_quitting(state, surface, paths)
    elif state.game_over:
        render_game_over(state, surface, paths)
    else:
        render_game(state, surface, paths)


def main(prog: str) -> int:
    """
    Execute the main routine.

    :param prog: name of the program to be displayed in the help
    :return: exit code
    """
    pygame.joystick.init()
    joysticks = [
        pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
    ]

    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument(
        "--version", help="show the current version and exit", action="store_true"
    )

    parser.add_argument(
        "--list_joysticks", help="List joystick GUIDs and exit", action="store_true"
    )
    if len(joysticks) >= 1:
        parser.add_argument(
            "--joystick",
            help="Joystick to use for the game",
            choices=[joystick.get_guid() for joystick in joysticks],
            default=joysticks[0].get_guid(),
        )

    # NOTE (mristin, 2022-12-16):
    # The module ``argparse`` is not flexible enough to understand special options such
    # as ``--version`` so we manually hard-wire.
    if "--version" in sys.argv and "--help" not in sys.argv:
        print(danceamole.__version__)
        return 0

    if "--list_joysticks" in sys.argv and "--help" not in sys.argv:
        for joystick in joysticks:
            print(f"Joystick {joystick.get_name()}, GUID: {joystick.get_guid()}")
        return 0

    args = parser.parse_args()

    # noinspection PyUnusedLocal
    active_joystick = None  # type: Optional[pygame.joystick.Joystick]
    if len(joysticks) == 0:
        print(
            "There are no joysticks plugged in. Judo-dance requires a joystick.",
            file=sys.stderr,
        )
        return 1

    else:
        active_joystick = next(
            joystick for joystick in joysticks if joystick.get_guid() == args.joystick
        )

    assert active_joystick is not None
    print(
        f"Using the joystick: {active_joystick.get_name()} {active_joystick.get_guid()}"
    )

    # NOTE (mristin, 2022-12-16):
    # We have to think a bit better about how to deal with keyboard and joystick input.
    # For rapid development, we simply map the buttons of our concrete dance mat to
    # button numbers.
    button_map = {
        6: danceamole.events.Button.CROSS,
        2: danceamole.events.Button.UP,
        7: danceamole.events.Button.CIRCLE,
        3: danceamole.events.Button.RIGHT,
        5: danceamole.events.Button.SQUARE,
        1: danceamole.events.Button.DOWN,
        4: danceamole.events.Button.TRIANGLE,
        0: danceamole.events.Button.LEFT,
    }

    pygame.init()
    pygame.mixer.pre_init()
    pygame.mixer.init()

    pygame.display.set_caption("Dance-a-mole")
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    paths = Paths()
    error = check_all_files_exist(paths)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    now = time.time()

    game_duration = 120  # in seconds

    state = State(
        game_start=now,
        game_end=now + game_duration,
    )

    our_event_queue = []  # type: List[danceamole.events.EventUnion]

    # Reuse the tick object so that we don't have to create it every time
    tick_event = danceamole.events.Tick()

    try:
        while not state.received_quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    our_event_queue.append(danceamole.events.ReceivedQuit())

                elif (
                    event.type == pygame.JOYBUTTONDOWN
                    and joysticks[event.instance_id] is active_joystick
                ):
                    # Map joystick buttons to our canonical buttons;
                    #
                    # This is necessary if we ever want to support other dance mats.
                    our_button = button_map.get(event.button, None)
                    if our_button is not None:
                        our_event_queue.append(danceamole.events.ButtonDown(our_button))

                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_q,
                ):
                    our_event_queue.append(danceamole.events.ReceivedQuit())

                else:
                    # Ignore the event that we do not handle
                    pass

            our_event_queue.append(tick_event)

            while len(our_event_queue) > 0:
                handle(state, our_event_queue, paths)

            render(state, surface, paths)
            pygame.display.flip()
    finally:
        print("Quitting the game...")
        tic = time.time()
        pygame.joystick.quit()
        pygame.quit()
        print(f"Quit the game after: {time.time() - tic:.2f} seconds")

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="judo-dance")


if __name__ == "__main__":
    sys.exit(main(prog="judo-dance"))
